"""Deterministic analysis on top of the LLM output.

The LLM reads and judges; code does the arithmetic. Everything here is
reproducible and explainable to an auditor:

- risk score            = likelihood x impact                         (1-25)
- dependency reach      = initiatives directly waiting on this one through
                          a `blocking` / `at_risk` dependency
- portfolio score       = score x (1 + REACH_WEIGHT x reach)
- grounding check       = the risk's evidence quote must appear in the source
                          report, otherwise the risk is flagged as ungrounded
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date

import networkx as nx

from .ingest import StatusReport
from .registry import Registry
from .schema import (InitiativeExtraction, PortfolioSynthesis, RankedPortfolioRisk,
                     ScoredRisk)

log = logging.getLogger(__name__)

REACH_WEIGHT = 0.25
LIVE_STATUSES = {"blocking", "at_risk"}


@dataclass
class Edge:
    source: str          # initiative that is waiting
    target: str | None   # initiative it waits on (None if unresolved)
    mention: str
    what: str
    status: str
    needed_by: date | None


@dataclass
class PortfolioAnalysis:
    extractions: dict[str, InitiativeExtraction]
    reports: dict[str, StatusReport]
    edges: list[Edge]
    scored_risks: list[ScoredRisk]
    direct_reach: dict[str, int]
    transitive_reach: dict[str, int]
    warnings: list[str] = field(default_factory=list)

    @property
    def period_end(self) -> date:
        return max(e.period_end for e in self.extractions.values())

    @property
    def risk_index(self) -> dict[str, ScoredRisk]:
        return {r.risk_id: r for r in self.scored_risks}

    def rag_counts(self) -> dict[str, int]:
        counts = {"RED": 0, "AMBER": 0, "GREEN": 0}
        for e in self.extractions.values():
            counts[e.assessed_rag.value] += 1
        return counts


def _norm(text: str) -> str:
    text = re.sub(r"[*_`|>#]", " ", text.lower())
    text = text.replace("’", "'").replace("–", "-").replace("—", "-")
    return re.sub(r"\s+", " ", text).strip(" .,;:\"'")


def is_grounded(evidence: str, source_text: str) -> bool:
    """True if the evidence quote occurs (whitespace/markdown-insensitive) in the source."""
    ev = _norm(evidence)
    if len(ev) < 12:
        return False
    src = _norm(source_text)
    if ev in src:
        return True
    # tolerate an ellipsis joining two verbatim fragments
    parts = [p.strip() for p in re.split(r"\.\.\.|…", ev) if len(p.strip()) >= 12]
    return bool(parts) and all(p in src for p in parts)


def build_edges(extractions: list[InitiativeExtraction], registry: Registry) -> tuple[list[Edge], list[str]]:
    edges, warnings = [], []
    for e in extractions:
        for d in e.dependencies:
            target = registry.resolve(d.depends_on)
            if target is None:
                warnings.append(f"{e.initiative_id}: could not resolve dependency '{d.depends_on}'")
            elif target == e.initiative_id:
                continue
            edges.append(Edge(e.initiative_id, target, d.depends_on, d.what, d.status, d.needed_by))
    return edges, warnings


def dependency_graph(edges: list[Edge], live_only: bool = True) -> nx.DiGraph:
    g = nx.DiGraph()
    for edge in edges:
        if edge.target and (edge.status in LIVE_STATUSES or not live_only):
            g.add_edge(edge.source, edge.target)
    return g


def analyse(reports: list[StatusReport], extractions: list[InitiativeExtraction],
            registry: Registry) -> PortfolioAnalysis:
    by_id = {e.initiative_id: e for e in extractions}
    report_by_id = {r.initiative_id: r for r in reports}
    edges, warnings = build_edges(extractions, registry)

    g = dependency_graph(edges)
    direct = {i: (g.in_degree(i) if i in g else 0) for i in registry.ids()}
    transitive = {i: (len(nx.ancestors(g, i)) if i in g else 0) for i in registry.ids()}

    scored: list[ScoredRisk] = []
    for e in extractions:
        src = report_by_id[e.initiative_id].text
        for n, risk in enumerate(e.risks, 1):
            score = risk.likelihood * risk.impact
            grounded = is_grounded(risk.evidence, src)
            if not grounded:
                warnings.append(f"{e.initiative_id}.R{n} '{risk.title}': evidence not found in source report")
            scored.append(ScoredRisk(
                risk_id=f"{e.initiative_id}.R{n}", initiative_id=e.initiative_id, risk=risk, score=score,
                direct_dependents=direct[e.initiative_id],
                portfolio_score=round(score * (1 + REACH_WEIGHT * direct[e.initiative_id]), 2),
                grounded=grounded,
            ))
    scored.sort(key=lambda r: (-r.portfolio_score, -r.risk.impact, r.risk_id))

    try:
        cycle = nx.find_cycle(g)
        warnings.append(f"Circular dependency between initiatives: {cycle}")
    except nx.NetworkXNoCycle:
        pass

    for w in warnings:
        log.warning(w)
    return PortfolioAnalysis(by_id, report_by_id, edges, scored, direct, transitive, warnings)


def rank_portfolio_risks(synthesis: PortfolioSynthesis, analysis: PortfolioAnalysis,
                         registry: Registry) -> list[RankedPortfolioRisk]:
    """Rank the LLM's roll-up using scores computed in code, not the LLM's opinion."""
    index = analysis.risk_index
    known = set(registry.ids())
    ranked = []
    for pr in synthesis.portfolio_risks:
        linked = [index[r] for r in pr.linked_risk_ids if r in index]
        missing = [r for r in pr.linked_risk_ids if r not in index]
        if missing:
            analysis.warnings.append(f"Portfolio risk '{pr.title}' links unknown risk ids {missing}")
        bad_ids = [i for i in [pr.root_initiative, *pr.affected_initiatives] if i not in known]
        if bad_ids:
            analysis.warnings.append(f"Portfolio risk '{pr.title}' names unknown initiatives {bad_ids}")
        if not linked:
            analysis.warnings.append(f"Portfolio risk '{pr.title}' has no valid linked risks; ranked last")
        affected = ({i for i in pr.affected_initiatives if i in known} |
                    {r.initiative_id for r in linked}) - {pr.root_initiative}
        base = max((r.score for r in linked), default=0)
        ranked.append((pr, base, round(base * (1 + REACH_WEIGHT * len(affected)), 2),
                       sum(r.score for r in linked)))
    ranked.sort(key=lambda t: (-t[2], -t[1], -t[3], t[0].title))
    return [RankedPortfolioRisk(rank=i, risk=pr, base_score=b, portfolio_score=p)
            for i, (pr, b, p, _) in enumerate(ranked, 1)]


def edges_for_prompt(analysis: PortfolioAnalysis) -> str:
    return "\n".join(f"- {e.source} -> {e.target or '?'+e.mention} [{e.status}] {e.what}"
                     for e in analysis.edges)


def risk_table_for_prompt(analysis: PortfolioAnalysis) -> str:
    return "\n".join(f"- {r.risk_id} | {r.risk.title} | L{r.risk.likelihood} x I{r.risk.impact} = {r.score}"
                     f" | reach {r.direct_dependents}" for r in analysis.scored_risks)
