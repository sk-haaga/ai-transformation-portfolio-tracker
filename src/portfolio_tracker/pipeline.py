"""End-to-end run: reports -> LLM extraction -> analysis -> LLM synthesis -> Power BI + PPTX."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from . import brief, powerbi, roadmap, statuspack
from .analysis import (PortfolioAnalysis, analyse, edges_for_prompt, rank_portfolio_risks,
                       risk_table_for_prompt)
from .ingest import load_reports
from .llm import LLMProvider, save_run, to_prompt_json
from .registry import Registry
from .schema import PortfolioSynthesis, RankedPortfolioRisk

log = logging.getLogger(__name__)


@dataclass
class RunResult:
    analysis: PortfolioAnalysis
    synthesis: PortfolioSynthesis
    ranked: list[RankedPortfolioRisk]
    source_pages: int
    brief_path: Path
    powerbi_dir: Path
    roadmap_path: Path


def run(reports_dir: Path, registry_path: Path, provider: LLMProvider, out_dir: Path,
        provider_label: str = "", save_run_dir: Path | None = None) -> RunResult:
    registry = Registry.from_csv(registry_path)
    reports = load_reports(reports_dir, registry)
    log.info("Loaded %d reports (%d words)", len(reports), sum(r.word_count for r in reports))

    pages = statuspack.render(reports_dir, out_dir / "status_pack.pdf")
    log.info("Input status pack: %d pages", pages)

    extractions = []
    for r in reports:
        log.info("Extracting %s with %s", r.initiative_id, provider.name)
        extractions.append(provider.extract(r, registry))

    analysis = analyse(reports, extractions, registry)
    synthesis = provider.synthesise(
        analysis.period_end.isoformat(), to_prompt_json(extractions),
        edges_for_prompt(analysis), risk_table_for_prompt(analysis),
    )
    ranked = rank_portfolio_risks(synthesis, analysis, registry)
    if save_run_dir:
        save_run(save_run_dir, extractions, synthesis)

    tables = powerbi.build_tables(analysis, ranked, registry, {
        "provider": provider_label or provider.name, "source_reports": len(reports),
        "source_pages": pages, "source_words": sum(r.word_count for r in reports),
    })
    pbi_dir = out_dir / "powerbi"
    powerbi.export(tables, pbi_dir)
    roadmap_png = roadmap.render_roadmap(tables["fact_milestone"], tables["dim_initiative"],
                                         analysis.period_end, out_dir / "roadmap_preview.png")
    brief_path = brief.build_brief(analysis, synthesis, ranked, registry,
                                   out_dir / f"portfolio_brief_{analysis.period_end:%Y-%m-%d}.pptx",
                                   source_pages=pages, provider_label=provider_label)
    return RunResult(analysis, synthesis, ranked, pages, brief_path, pbi_dir, roadmap_png)
