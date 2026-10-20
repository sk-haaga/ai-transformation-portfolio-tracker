"""Initiative master data and name resolution.

Status reports refer to each other loosely ("the Data Platform team",
"the Identity programme", "GOV-03"). The registry turns those mentions into
canonical initiative IDs so dependencies can be graphed and joined in Power BI.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

ID_PATTERN = re.compile(r"\b([A-Z]{2,4}-\d{2})\b")


@dataclass(frozen=True)
class Initiative:
    initiative_id: str
    name: str
    short_name: str
    theme: str
    owner: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


class Registry:
    def __init__(self, initiatives: list[Initiative]):
        self._by_id = {i.initiative_id: i for i in initiatives}

    @classmethod
    def from_csv(cls, path: Path) -> "Registry":
        with path.open(encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        return cls([
            Initiative(
                initiative_id=r["initiative_id"], name=r["name"], short_name=r["short_name"],
                theme=r["theme"], owner=r["owner"],
                aliases=tuple(a.strip().lower() for a in r.get("aliases", "").split("|") if a.strip()),
            )
            for r in rows
        ])

    def __iter__(self):
        return iter(self._by_id.values())

    def __len__(self) -> int:
        return len(self._by_id)

    def __getitem__(self, initiative_id: str) -> Initiative:
        return self._by_id[initiative_id]

    def ids(self) -> list[str]:
        return list(self._by_id)

    def resolve(self, mention: str, threshold: float = 0.72) -> str | None:
        """Map a free-text mention to an initiative ID, or None if unsure."""
        m = ID_PATTERN.search(mention.upper())
        if m and m.group(1) in self._by_id:
            return m.group(1)
        text = mention.lower().strip()
        best, best_score = None, 0.0
        for ini in self._by_id.values():
            for cand in (ini.name.lower(), ini.short_name.lower(), *ini.aliases):
                if cand and (cand in text or text in cand) and len(min(cand, text, key=len)) >= 4:
                    score = 0.95
                else:
                    score = SequenceMatcher(None, text, cand).ratio()
                if score > best_score:
                    best, best_score = ini.initiative_id, score
        return best if best_score >= threshold else None

    def id_from_filename(self, path: Path) -> str | None:
        m = ID_PATTERN.search(path.stem.upper().replace("_", " "))
        return m.group(1) if m and m.group(1) in self._by_id else None
