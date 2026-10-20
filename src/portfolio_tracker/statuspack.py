"""Render the raw status reports into a single A4 PDF "status pack".

This mimics what a PMO would circulate before a steering group: every
initiative's update, one after another, each starting on a new page.
It is used to measure the size of the input that the tracker condenses.

Usage:
    python -m portfolio_tracker.statuspack [reports_dir] [output_pdf]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parents[2]

styles = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15)
H1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=15, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4)
MONO = ParagraphStyle("mono", fontName="Courier", fontSize=8.5, leading=11)


def _inline(md: str) -> str:
    text = escape(md)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<i>\1</i>", text)
    return text


def report_flowables(path: Path) -> list:
    flow: list = []
    table_buf: list[str] = []

    def flush_table() -> None:
        if table_buf:
            flow.append(Preformatted("\n".join(table_buf), MONO))
            flow.append(Spacer(1, 6))
            table_buf.clear()

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if line.startswith("|"):
            table_buf.append(line)
            continue
        flush_table()
        if not line.strip():
            flow.append(Spacer(1, 5))
        elif line.startswith("# "):
            flow.append(Paragraph(_inline(line[2:]), H1))
        elif line.startswith(("## ", "### ")):
            flow.append(Paragraph(_inline(line.lstrip("# ")), H2))
        elif set(line.strip()) <= set("-=") :
            flow.append(Spacer(1, 3))
        elif re.match(r"^\s*([-*]|\d+\.)\s+", line):
            indent = 14 + 8 * (len(line) - len(line.lstrip()))
            bullet = ParagraphStyle("b", parent=BODY, leftIndent=indent, bulletIndent=indent - 10)
            content = re.sub(r"^\s*([-*]|\d+\.)\s+", "", line)
            flow.append(Paragraph(_inline(content), bullet, bulletText="•"))
        else:
            flow.append(Paragraph(_inline(line), BODY))
    flush_table()
    return flow


def render(reports_dir: Path, out_pdf: Path) -> int:
    files = sorted(p for p in reports_dir.iterdir() if p.suffix in {".md", ".txt"})
    story: list = []
    for i, f in enumerate(files):
        if i:
            story.append(PageBreak())
        story.extend(report_flowables(f))
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(
        str(out_pdf), pagesize=A4,
        leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
        title="Transformation portfolio — status pack",
    ).build(story)
    return len(PdfReader(str(out_pdf)).pages)


if __name__ == "__main__":
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "status_reports"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "output" / "status_pack.pdf"
    pages = render(src, dst)
    print(f"{dst} — {pages} pages from {len(list(src.glob('*.*')))} reports")
