"""Load raw status updates from a folder.

Reports arrive in whatever shape the initiative uses: Markdown templates,
pasted emails, meeting minutes. The pipeline does not try to parse them
structurally; it only needs the text and, ideally, which initiative it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .registry import Registry

SUPPORTED = {".md", ".txt", ".eml"}


@dataclass(frozen=True)
class StatusReport:
    initiative_id: str
    source_file: str
    text: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())


def load_reports(folder: Path, registry: Registry) -> list[StatusReport]:
    reports: list[StatusReport] = []
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in SUPPORTED:
            continue
        text = path.read_text(encoding="utf-8")
        initiative_id = registry.id_from_filename(path) or registry.resolve(text[:400])
        if initiative_id is None:
            raise ValueError(f"Cannot tell which initiative {path.name} belongs to; "
                             "prefix the file name with its ID, e.g. CRM-01_update.md")
        reports.append(StatusReport(initiative_id, path.name, text))
    if not reports:
        raise FileNotFoundError(f"No status reports ({', '.join(SUPPORTED)}) found in {folder}")
    seen = [r.initiative_id for r in reports]
    dupes = {i for i in seen if seen.count(i) > 1}
    if dupes:
        raise ValueError(f"More than one report for {sorted(dupes)}; keep only the latest per initiative.")
    return reports
