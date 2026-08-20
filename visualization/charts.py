"""Targeted Visualization Charts for Data Skew Intelligence.

Implements required chart generators using the centralized NVIDIA-inspired theme.
All charts validate input data strictly before plotting.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import matplotlib

matplotlib.use("Agg")  # Non-interactive background rendering
import matplotlib.pyplot as plt
import numpy as np

from visualization.theme import (
    BACKGROUND,
    ERROR,
    GREEN,
    GREEN_2,
    GRID,
    MUTED,
    TEXT,
    WARNING,
    apply_matplotlib_theme,
)
from visualization.validators import (
    validate_experiment_series,
    validate_key_distribution,
    validate_partition_distribution,
)


def plot_key_distribution(data: Dict[str, int], output_path: str | Path) -> Path:
    """Horizontal bar chart of top keys. Highlights hot key with accent color."""
    clean_data = validate_key_distribution(data)
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort keys by record count ascending for horizontal bar chart
    items = sorted(clean_data.items(), key=lambda x: x[1])
    keys = [item[0] for item in items]
    counts = [item[1] for item in items]
    total_records = sum(counts) or 1

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

    # Highlight maximum count (hot key)
    max_count = max(counts)
    colors = [GREEN if c == max_count else MUTED for c in counts]

    bars = ax.barh(keys, counts, color=colors, edgecolor=GRID, height=0.6)

    # Value & Percentage Annotations
    for bar, count in zip(bars, counts):
        pct = (count / total_records) * 100.0
        label = f" {count:,} ({pct:.1f}%)"
        ax.text(
            bar.get_width() + (max_count * 0.01),
            bar.get_y() + bar.get_height() / 2,
            label,
            va="center",
            ha="left",
            color=TEXT if bar.get_facecolor()[:3] == matplotlib.colors.to_rgb(GREEN) else MUTED,
            fontsize=10,
            fontweight="bold" if bar.get_facecolor()[:3] == matplotlib.colors.to_rgb(GREEN) else "normal",
        )

    ax.set_title("Key Distribution (Top Keys Concentration)", fontsize=14, pad=15)
    ax.set_xlabel("Record Count", labelpad=10)
    ax.set_ylabel("Key Identifier", labelpad=10)
    ax.set_xlim(0, max_count * 1.25)

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path


def plot_partition_distribution(partition_sizes: List[int], output_path: str | Path) -> Path:
    """Plot partition index vs actual records with mean, median, max reference lines."""
    sizes = validate_partition_distribution(partition_sizes, "partition distribution")
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)
    indices = np.arange(len(sizes))

    mean_val = float(np.mean(sizes))
    median_val = float(np.median(sizes))
    max_val = int(np.max(sizes))

    # Highlight partition with max value
    colors = [GREEN if s == max_val and max_val > mean_val else MUTED for s in sizes]

    bars = ax.bar(indices, sizes, color=colors, edgecolor=GRID, width=0.6)

    # Reference lines
    ax.axhline(mean_val, color=GREEN_2, linestyle="--", linewidth=1.5, label=f"Mean: {mean_val:,.1f}")
    ax.axhline(median_val, color=WARNING, linestyle=":", linewidth=1.5, label=f"Median: {median_val:,.1f}")
    ax.axhline(max_val, color=ERROR, linestyle="-.", linewidth=1.2, label=f"Max: {max_val:,}")

    # Annotate bars
    for bar, size in zip(bars, sizes):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + (max_val * 0.02),
            f"{size:,}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=TEXT if size == max_val else MUTED,
        )

    ax.set_title("Physical Partition Record Distribution", fontsize=14, pad=15)
    ax.set_xlabel("Partition Index", labelpad=10)
    ax.set_ylabel("Records per Partition", labelpad=10)
    ax.set_xticks(indices)
    ax.set_xticklabels([f"P{i}" for i in indices])
    ax.set_ylim(0, max(max_val * 1.18, 10))
    ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path


def plot_before_after_partitions(before_sizes: List[int], after_sizes: List[int], output_path: str | Path) -> Path:
    """Compare baseline and mitigated partition record sizes."""
    b_sizes = validate_partition_distribution(before_sizes, "baseline partition distribution")
    a_sizes = validate_partition_distribution(after_sizes, "mitigated partition distribution")
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

    # Handle equal or unequal partition counts cleanly without fabricating values
    b_len = len(b_sizes)
    a_len = len(a_sizes)

    if b_len == a_len:
        indices = np.arange(b_len)
        width = 0.35
        ax.bar(indices - width/2, b_sizes, width, label="Baseline", color=MUTED, edgecolor=GRID)
        ax.bar(indices + width/2, a_sizes, width, label="Mitigated", color=GREEN, edgecolor=GRID)
        ax.set_xticks(indices)
        ax.set_xticklabels([f"P{i}" for i in indices])
    else:
        # Separate series for unequal partition counts
        ax.bar(np.arange(b_len), b_sizes, alpha=0.6, label=f"Baseline ({b_len} parts)", color=MUTED, edgecolor=GRID)
        ax.bar(np.arange(a_len), a_sizes, alpha=0.6, label=f"Mitigated ({a_len} parts)", color=GREEN, edgecolor=GRID)
        ax.set_xlabel("Partition Index")

    ax.set_title("Before vs After Partition Balance Comparison", fontsize=14, pad=15)
    ax.set_ylabel("Records per Partition", labelpad=10)
    ax.legend(loc="upper right")

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path


def plot_skew_vs_runtime(experiments: List[Dict[str, Any]], output_path: str | Path) -> Path:
    """Plot Skew Percentage vs Execution Time across observations."""
    series = validate_experiment_series(experiments)
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort observations by skew
    sorted_series = sorted(series, key=lambda s: s["skew"])
    skews = [s["skew"] * (100.0 if max(s["skew"] for s in sorted_series) <= 1.0 else 1.0) for s in sorted_series]
    runtimes = [s["runtime"] for s in sorted_series]

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

    ax.plot(skews, runtimes, marker="o", color=GREEN, linewidth=2.5, markersize=8, label="Runtime (s)")
    for x, y in zip(skews, runtimes):
        ax.text(x, y + (max(runtimes) * 0.03), f"{y:.2f}s", ha="center", va="bottom", fontsize=9, color=TEXT)

    ax.set_title("Key Skew vs Execution Time", fontsize=14, pad=15)
    ax.set_xlabel("Hot Key Skew Percentage (%)", labelpad=10)
    ax.set_ylabel("Execution Time (seconds)", labelpad=10)
    ax.set_ylim(0, max(runtimes) * 1.2 if runtimes else 10)
    ax.legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path


def plot_skew_vs_partition_cv(experiments: List[Dict[str, Any]], output_path: str | Path) -> Path:
    """Plot Skew Percentage vs Partition Coefficient of Variation (CV)."""
    series = validate_experiment_series(experiments)
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    sorted_series = sorted(series, key=lambda s: s["skew"])
    skews = [s["skew"] * (100.0 if max(s["skew"] for s in sorted_series) <= 1.0 else 1.0) for s in sorted_series]
    cvs = [s["partition_cv"] for s in sorted_series]

    fig, ax = plt.subplots(figsize=(12, 7), dpi=120)

    ax.plot(skews, cvs, marker="s", color=GREEN_2, linewidth=2.5, markersize=8, label="Partition CV")
    for x, y in zip(skews, cvs):
        ax.text(x, y + (max(cvs) * 0.03 if cvs else 0.05), f"{y:.2f}", ha="center", va="bottom", fontsize=9, color=TEXT)

    ax.set_title("Key Skew vs Partition Imbalance (Coefficient of Variation)", fontsize=14, pad=15)
    ax.set_xlabel("Hot Key Skew Percentage (%)", labelpad=10)
    ax.set_ylabel("Partition Coefficient of Variation (CV)", labelpad=10)
    ax.set_ylim(0, max(cvs) * 1.25 if cvs and max(cvs) > 0 else 1.5)
    ax.legend(loc="upper left")

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path


def plot_performance_comparison(metrics: Dict[str, Any], output_path: str | Path) -> Path:
    """Compare baseline vs mitigated performance metrics with separate/normalized axes."""
    apply_matplotlib_theme()

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    b_rt = metrics.get("baseline_execution_time", 0.0)
    m_rt = metrics.get("mitigated_execution_time", 0.0)
    b_max = metrics.get("baseline_max_partition_records", 0)
    m_max = metrics.get("mitigated_max_partition_records", 0)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6), dpi=120)

    # Chart 1: Execution Time (seconds)
    bars1 = ax1.bar(["Baseline", "Mitigated"], [b_rt, m_rt], color=[MUTED, GREEN], edgecolor=GRID, width=0.5)
    for bar, val in zip(bars1, [b_rt, m_rt]):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (max(b_rt, m_rt)*0.02 if max(b_rt, m_rt) > 0 else 0.1),
                 f"{val:.2f} s", ha="center", va="bottom", color=TEXT, fontweight="bold")
    ax1.set_title("Runtime Comparison (Lower is Better)")
    ax1.set_ylabel("Time (seconds)")
    ax1.set_ylim(0, max(b_rt, m_rt) * 1.25 if max(b_rt, m_rt) > 0 else 5)

    # Chart 2: Partition Imbalance Metrics
    x = np.arange(2)
    width = 0.35
    ax2.bar(x - width/2, [b_max, m_max], width, label="Max Partition Records", color=[MUTED, GREEN], edgecolor=GRID)
    ax2.set_xticks(x)
    ax2.set_xticklabels(["Baseline", "Mitigated"])
    ax2.set_title("Max Partition Size Reduction")
    ax2.set_ylabel("Record Count")

    plt.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight", facecolor=BACKGROUND)
    plt.close(fig)

    return out_path
