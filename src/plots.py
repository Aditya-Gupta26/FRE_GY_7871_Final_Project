"""Shared figure style: one fixed palette (the dataviz skill's validated categorical order, light
mode), thin marks, recessive grids, no second y-axis, direct labels where few series."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
INK, INK2, MUTED, GRID, SHADE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#ecebe6"

plt.rcParams.update({
    "font.family": "Helvetica Neue", "font.size": 8.5, "axes.titlesize": 9, "axes.labelsize": 8.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.spines.top": False,
    "axes.spines.right": False, "legend.frameon": False, "legend.fontsize": 7.8, "figure.dpi": 200,
    "savefig.dpi": 200, "savefig.bbox": "tight", "lines.linewidth": 1.6, "axes.titleweight": "bold",
    "axes.titlelocation": "left",
})


def year_axis(ax, every: int = 2):
    ax.xaxis.set_major_locator(mdates.YearLocator(every))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))


def month_axis(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))


def shade(ax, start, end, label=None):
    ax.axvspan(start, end, color=SHADE, zorder=0, lw=0, label=label)
