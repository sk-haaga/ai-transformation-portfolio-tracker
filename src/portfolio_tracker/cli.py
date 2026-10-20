"""Command line entry point: `portfolio-tracker run ...` or `python -m portfolio_tracker run ...`."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .llm import DEFAULT_MODEL, ClaudeProvider, ReplayProvider
from .pipeline import run

ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="portfolio-tracker",
                                 description="Turn initiative status reports into a leadership view.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="Run the full pipeline")
    r.add_argument("--reports", type=Path, default=ROOT / "data" / "status_reports")
    r.add_argument("--registry", type=Path, default=ROOT / "data" / "initiatives.csv")
    r.add_argument("--out", type=Path, default=ROOT / "output")
    r.add_argument("--provider", choices=["claude", "replay"], default="replay",
                   help="claude = live Anthropic API (needs ANTHROPIC_API_KEY); replay = saved outputs")
    r.add_argument("--replay-dir", type=Path, default=ROOT / "data" / "reference_run")
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--save-run", type=Path, help="Save LLM outputs here so the run can be replayed")
    r.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(level=logging.INFO if args.verbose else logging.WARNING,
                        format="%(levelname)s %(name)s: %(message)s")

    if args.provider == "claude":
        provider = ClaudeProvider(model=args.model, cache_dir=args.out / ".llm_cache")
        label = args.model
    else:
        provider = ReplayProvider(args.replay_dir)
        label = f"replay of {args.replay_dir.name}"

    res = run(args.reports, args.registry, provider, args.out, provider_label=label, save_run_dir=args.save_run)

    a = res.analysis
    counts = a.rag_counts()
    print(f"\n{len(a.reports)} reports ({res.source_pages} pages) -> 1 slide")
    print(f"Status: {counts['RED']} red, {counts['AMBER']} amber, {counts['GREEN']} green "
          f"({sum(e.reported_rag != e.assessed_rag for e in a.extractions.values())} re-rated)")
    print("Top risks:")
    for rp in res.ranked[:5]:
        print(f"  {rp.rank}. [{rp.portfolio_score:5.1f}] {rp.risk.title}")
    if a.warnings:
        print(f"{len(a.warnings)} data-quality warning(s); see slide notes.")
    print(f"\nBrief:    {res.brief_path}\nPower BI: {res.powerbi_dir}/\nRoadmap:  {res.roadmap_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
