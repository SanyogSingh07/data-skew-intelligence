"""NVIDIA-Inspired Centralized Engineering Theme.

Central source of truth for colors, typography, layout constants, Matplotlib,
Plotly, and Rich console styling across the Data Skew Intelligence engine.
"""
from __future__ import annotations

from typing import Any, Dict

# Palette Tokens
BACKGROUND = "#0B0F0C"
SURFACE = "#111713"
SURFACE_2 = "#182019"
GREEN = "#76B900"
GREEN_2 = "#A8E063"
TEXT = "#F2F5F2"
MUTED = "#9AA49D"
WARNING = "#F5B942"
ERROR = "#FF5C5C"
GRID = "#273029"

# Font Settings
FONT_FAMILY = "sans-serif"

def apply_matplotlib_theme() -> None:
    """Configures Matplotlib global rcParams to match NVIDIA-inspired engineering dark theme."""
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.facecolor": BACKGROUND,
        "figure.edgecolor": BACKGROUND,
        "axes.facecolor": SURFACE,
        "axes.edgecolor": GRID,
        "axes.grid": True,
        "axes.grid.which": "major",
        "axes.grid.axis": "both",
        "grid.color": GRID,
        "grid.linestyle": "--",
        "grid.linewidth": 0.6,
        "grid.alpha": 0.7,
        "text.color": TEXT,
        "axes.labelcolor": TEXT,
        "axes.titlecolor": TEXT,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.titlepad": 12,
        "axes.labelsize": 11,
        "axes.labelpad": 8,
        "legend.facecolor": SURFACE_2,
        "legend.edgecolor": GRID,
        "legend.fontsize": 10,
        "legend.framealpha": 0.9,
        "font.family": FONT_FAMILY,
    })


def get_plotly_layout_dict(title: str, x_title: str, y_title: str) -> Dict[str, Any]:
    """Returns a dictionary layout config for Plotly matching the NVIDIA engineering theme."""
    return {
        "paper_bgcolor": BACKGROUND,
        "plot_bgcolor": SURFACE,
        "font": {"color": TEXT, "family": FONT_FAMILY},
        "title": {
            "text": f"<b>{title}</b>",
            "font": {"size": 16, "color": TEXT},
            "x": 0.05,
            "xanchor": "left",
        },
        "xaxis": {
            "title": x_title,
            "color": TEXT,
            "gridcolor": GRID,
            "zerolinecolor": GRID,
            "tickcolor": MUTED,
        },
        "yaxis": {
            "title": y_title,
            "color": TEXT,
            "gridcolor": GRID,
            "zerolinecolor": GRID,
            "tickcolor": MUTED,
        },
        "legend": {
            "bgcolor": SURFACE_2,
            "bordercolor": GRID,
            "font": {"color": TEXT},
        },
        "margin": {"l": 50, "r": 40, "t": 60, "b": 50},
    }
