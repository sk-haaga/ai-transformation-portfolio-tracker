"""LLM providers.

`ClaudeProvider` calls the Anthropic Messages API and forces a tool call whose
input schema is generated from the pydantic models in `schema.py`, so output is
always structured. Responses are validated; on a validation error the model
gets the error back and one more attempt. Results are cached on disk keyed by
model + prompt, so re-running the pipeline does not re-spend tokens.

`ReplayProvider` reads previously saved outputs from a folder. It lets the
pipeline (and the tests) run with no API key, and makes any run reproducible.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from . import prompts
from .ingest import StatusReport
from .registry import Registry
from .schema import InitiativeExtraction, PortfolioSynthesis

log = logging.getLogger(__name__)
M = TypeVar("M", bound=BaseModel)

DEFAULT_MODEL = os.environ.get("PORTFOLIO_TRACKER_MODEL", "claude-sonnet-5-5")


class LLMProvider(Protocol):
    name: str

    def extract(self, report: StatusReport, registry: Registry) -> InitiativeExtraction: ...

    def synthesise(self, period_end: str, extractions_json: str, edges: str,
                   risk_table: str) -> PortfolioSynthesis: ...


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Return a JSON schema with every local $ref expanded (tool schemas stay self-contained)."""
    defs = schema.get("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                target = copy.deepcopy(defs[node["$ref"].split("/")[-1]])
                extra = {k: v for k, v in node.items() if k != "$ref"}
                return walk({**target, **extra})
            return {k: walk(v) for k, v in node.items() if k != "$defs"}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


def registry_block(registry: Registry) -> str:
    return "\n".join(f"- {i.initiative_id}: {i.name} (aka {', '.join(i.aliases[:3])})" for i in registry)


class ClaudeProvider:
    name = "claude"

    def __init__(self, model: str = DEFAULT_MODEL, cache_dir: Path | None = None, max_tokens: int = 4096):
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pip install anthropic to use the Claude provider") from exc
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY is not set. Use --provider replay to run offline.")
        self.client = anthropic.Anthropic()
        self.model = model
        self.max_tokens = max_tokens
        self.cache_dir = cache_dir
        if cache_dir:
            cache_dir.mkdir(parents=True, exist_ok=True)

    # -- public API ---------------------------------------------------------

    def extract(self, report: StatusReport, registry: Registry) -> InitiativeExtraction:
        user = prompts.EXTRACTION_USER.format(
            registry=registry_block(registry), initiative_id=report.initiative_id,
            source_file=report.source_file, text=report.text,
        )
        result = self._call_tool(
            prompts.EXTRACTION_SYSTEM, user, "record_initiative_status",
            "Record the structured status of one initiative.", InitiativeExtraction,
        )
        if result.initiative_id != report.initiative_id:
            log.warning("Model returned id %s for %s; correcting", result.initiative_id, report.initiative_id)
            result = result.model_copy(update={"initiative_id": report.initiative_id})
        return result

    def synthesise(self, period_end: str, extractions_json: str, edges: str, risk_table: str) -> PortfolioSynthesis:
        user = prompts.SYNTHESIS_USER.format(
            period_end=period_end, extractions=extractions_json, edges=edges, risk_table=risk_table,
        )
        return self._call_tool(
            prompts.SYNTHESIS_SYSTEM, user, "record_portfolio_view",
            "Record the cross-initiative portfolio view.", PortfolioSynthesis,
        )

    # -- internals ----------------------------------------------------------

    def _call_tool(self, system: str, user: str, tool_name: str, description: str, model_cls: type[M]) -> M:
        key = hashlib.sha256(f"{self.model}|{prompts.PROMPT_VERSION}|{tool_name}|{system}|{user}".encode()).hexdigest()[:20]
        cached = self.cache_dir / f"{tool_name}-{key}.json" if self.cache_dir else None
        if cached and cached.exists():
            return model_cls.model_validate_json(cached.read_text(encoding="utf-8"))

        tool = {"name": tool_name, "description": description,
                "input_schema": inline_refs(model_cls.model_json_schema())}
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]

        for attempt in range(2):
            resp = self.client.messages.create(
                model=self.model, max_tokens=self.max_tokens, system=system, tools=[tool],
                tool_choice={"type": "tool", "name": tool_name}, messages=messages,
            )
            block = next(b for b in resp.content if b.type == "tool_use")
            try:
                result = model_cls.model_validate(block.input)
                break
            except ValidationError as err:
                if attempt == 1:
                    raise
                log.info("Validation failed for %s, asking model to correct: %s", tool_name, err)
                messages += [
                    {"role": "assistant", "content": resp.content},
                    {"role": "user", "content": [{
                        "type": "tool_result", "tool_use_id": block.id, "is_error": True,
                        "content": f"Schema validation failed, call the tool again with fixes:\n{err}",
                    }]},
                ]
        if cached:
            cached.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        return result


class ReplayProvider:
    """Serve saved outputs: <dir>/extractions/<ID>.json and <dir>/synthesis.json."""

    name = "replay"

    def __init__(self, folder: Path):
        self.folder = folder

    def extract(self, report: StatusReport, registry: Registry) -> InitiativeExtraction:
        path = self.folder / "extractions" / f"{report.initiative_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"No saved extraction for {report.initiative_id} at {path}")
        return InitiativeExtraction.model_validate_json(path.read_text(encoding="utf-8"))

    def synthesise(self, period_end: str, extractions_json: str, edges: str, risk_table: str) -> PortfolioSynthesis:
        return PortfolioSynthesis.model_validate_json((self.folder / "synthesis.json").read_text(encoding="utf-8"))


def save_run(folder: Path, extractions: list[InitiativeExtraction], synthesis: PortfolioSynthesis) -> None:
    """Persist a run in the layout ReplayProvider reads, so any live run can be replayed."""
    (folder / "extractions").mkdir(parents=True, exist_ok=True)
    for e in extractions:
        (folder / "extractions" / f"{e.initiative_id}.json").write_text(
            e.model_dump_json(indent=2), encoding="utf-8")
    (folder / "synthesis.json").write_text(synthesis.model_dump_json(indent=2), encoding="utf-8")


def to_prompt_json(extractions: list[InitiativeExtraction]) -> str:
    """Compact JSON of extractions with stable risk IDs (e.g. DAT-02.R1) for the synthesis prompt."""
    out = []
    for e in extractions:
        d = json.loads(e.model_dump_json(exclude={"progress"}))
        for i, r in enumerate(d["risks"], 1):
            r["risk_id"] = f"{e.initiative_id}.R{i}"
            r.pop("evidence", None)
        out.append(d)
    return json.dumps(out, ensure_ascii=False, indent=1)
