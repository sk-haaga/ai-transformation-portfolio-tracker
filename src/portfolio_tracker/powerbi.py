"""Export the analysed portfolio as a small star schema for Power BI.

Tables (all CSV, UTF-8, ISO dates):

    dim_initiative          one row per initiative (RAG, % complete, reach)
    fact_milestone          baseline vs forecast per milestone -> roadmap
    fact_risk               every initiative-level risk with scores
    fact_dependency         initiative -> initiative edges
    portfolio_risk          ranked cross-initiative risks (the slide's list)
    bridge_portfolio_risk   portfolio risk <-> affected initiative (for slicing)
    run_metadata            one row describing the run

See powerbi/README.md for the model relationships, measures and visuals.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analysis import PortfolioAnalysis
from .registry import Registry
from .schema import RankedPortfolioRisk


def build_tables(analysis: PortfolioAnalysis, ranked: list[RankedPortfolioRisk], registry: Registry,
                 meta: dict) -> dict[str, pd.DataFrame]:
    dim, milestones, risks, deps = [], [], [], []

    for ini in registry:
        e = analysis.extractions.get(ini.initiative_id)
        if e is None:
            continue
        open_risks = [r for r in analysis.scored_risks if r.initiative_id == ini.initiative_id]
        dim.append({
            "initiative_id": ini.initiative_id, "name": ini.name, "short_name": ini.short_name,
            "theme": ini.theme, "owner": ini.owner, "period_end": e.period_end,
            "reported_rag": e.reported_rag.value, "assessed_rag": e.assessed_rag.value,
            "rag_sort": e.assessed_rag.rank, "rag_changed": e.reported_rag != e.assessed_rag,
            "rag_rationale": e.rag_rationale, "percent_complete": e.percent_complete,
            "headline": e.headline, "risk_count": len(open_risks),
            "max_risk_score": max((r.score for r in open_risks), default=0),
            "direct_dependents": analysis.direct_reach[ini.initiative_id],
            "transitive_dependents": analysis.transitive_reach[ini.initiative_id],
            "source_file": analysis.reports[ini.initiative_id].source_file,
        })
        for n, m in enumerate(e.milestones, 1):
            slip = (m.forecast - m.baseline).days if m.forecast and m.baseline else None
            milestones.append({
                "milestone_key": f"{ini.initiative_id}.M{n}", "initiative_id": ini.initiative_id,
                "milestone": m.name, "baseline_date": m.baseline, "forecast_date": m.forecast,
                "plot_date": m.forecast or m.baseline, "slip_days": slip, "status": m.status,
                "is_done": m.status == "done",
            })

    for r in analysis.scored_risks:
        risks.append({
            "risk_id": r.risk_id, "initiative_id": r.initiative_id, "title": r.risk.title,
            "description": r.risk.description, "category": r.risk.category,
            "likelihood": r.risk.likelihood, "impact": r.risk.impact, "score": r.score,
            "direct_dependents": r.direct_dependents, "portfolio_score": r.portfolio_score,
            "mitigation": r.risk.mitigation, "evidence": r.risk.evidence, "grounded": r.grounded,
        })

    for edge in analysis.edges:
        deps.append({
            "from_initiative_id": edge.source, "to_initiative_id": edge.target, "mention": edge.mention,
            "what": edge.what, "status": edge.status, "needed_by": edge.needed_by,
            "is_live": edge.status in {"blocking", "at_risk"},
        })

    port = [{
        "rank": rp.rank, "title": rp.risk.title, "root_initiative_id": rp.risk.root_initiative,
        "affected_initiatives": ", ".join(rp.risk.affected_initiatives),
        "affected_count": len(set(rp.risk.affected_initiatives)), "base_score": rp.base_score,
        "portfolio_score": rp.portfolio_score, "impact_statement": rp.risk.impact_statement,
        "recommended_action": rp.risk.recommended_action,
        "linked_risk_ids": ", ".join(rp.risk.linked_risk_ids),
    } for rp in ranked]
    bridge = [{"rank": rp.rank, "initiative_id": i}
              for rp in ranked for i in dict.fromkeys(rp.risk.affected_initiatives)]

    run = {**meta, "period_end": analysis.period_end,
           "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "initiatives": len(dim), "risks": len(risks), "warnings": len(analysis.warnings)}

    return {
        "dim_initiative": pd.DataFrame(dim),
        "fact_milestone": pd.DataFrame(milestones),
        "fact_risk": pd.DataFrame(risks),
        "fact_dependency": pd.DataFrame(deps),
        "portfolio_risk": pd.DataFrame(port),
        "bridge_portfolio_risk": pd.DataFrame(bridge),
        "run_metadata": pd.DataFrame([run]),
    }


def export(tables: dict[str, pd.DataFrame], folder: Path) -> list[Path]:
    folder.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, df in tables.items():
        path = folder / f"{name}.csv"
        df.to_csv(path, index=False, encoding="utf-8")
        paths.append(path)
    return paths
