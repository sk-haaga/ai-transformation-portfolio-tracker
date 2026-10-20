"""Static roadmap preview (PNG) of the same milestone table Power BI uses.

Handy for the README and for anyone without Power BI Desktop. Each milestone
is drawn as a hollow marker at its baseline and a filled marker at its
forecast, joined by a line when it has slipped.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

STATUS_COLOURS = {"done": "#7A8290", "on_track": "#2E7D32", "at_risk": "#E09A00",
                  "late": "#C62828", "tbc": "#E09A00"}


def render_roadmap(milestones: pd.DataFrame, initiatives: pd.DataFrame, period_end: date, out: Path) -> Path:
    order = initiatives.sort_values(["rag_sort", "initiative_id"])
    labels = [f"{r.short_name}  ({r.initiative_id})" for r in order.itertuples()]
    ypos = {iid: len(order) - i for i, iid in enumerate(order["initiative_id"])}

    fig, ax = plt.subplots(figsize=(13, 6.2), dpi=150)
    for m in milestones.itertuples():
        y = ypos[m.initiative_id]
        colour = STATUS_COLOURS[m.status]
        base, fc = m.baseline_date, m.forecast_date
        if pd.notna(base) and pd.notna(fc) and fc > base:
            ax.plot([base, fc], [y, y], color=colour, lw=2.2, alpha=.55, solid_capstyle="round", zorder=1)
            ax.scatter(base, y, s=46, facecolor="white", edgecolor=colour, lw=1.4, zorder=2)
        when = fc if pd.notna(fc) else base
        ax.scatter(when, y, s=64, color=colour, edgecolor="white", lw=.8, zorder=3,
                   marker="o" if pd.notna(fc) else "X")

    ax.axvline(pd.Timestamp(period_end), color="#2F5DA8", lw=1, ls="--")
    ax.text(pd.Timestamp(period_end), len(order) + .62, " status date", color="#2F5DA8", fontsize=8.5, va="bottom")
    ax.set_yticks(list(ypos.values()), labels, fontsize=10)
    ax.set_ylim(.5, len(order) + .9)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b\n%Y"))
    ax.tick_params(axis="x", labelsize=9, colors="#5F6670")
    ax.grid(axis="x", color="#E6E8EC", lw=.8)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color("#C9CED6")
    ax.set_title("Portfolio roadmap — baseline (hollow) vs forecast (filled)", loc="left",
                 fontsize=13, fontweight="bold", color="#14233B", pad=14)
    handles = [plt.Line2D([], [], marker="o", ls="", color=c, label=s.replace("_", " "))
               for s, c in STATUS_COLOURS.items() if s != "tbc"]
    handles.append(plt.Line2D([], [], marker="X", ls="", color=STATUS_COLOURS["tbc"], label="forecast TBC"))
    ax.legend(handles=handles, loc="lower right", bbox_to_anchor=(1, 1.0), frameon=False, fontsize=8.5, ncol=5)
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out
