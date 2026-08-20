"""Rich Terminal Tables and Panels with NVIDIA Engineering Theme.

Provides formatted Rich components matching the engineering theme across all CLI
display views.
"""
from __future__ import annotations

from typing import Any, Dict, List

from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from visualization.theme import ERROR, GREEN, GREEN_2, MUTED, TEXT, WARNING


def get_banner_panel() -> Panel:
    """Returns the main SkewCTL header banner panel."""
    content = Text()
    content.append("S K E W C T L\n", style=f"bold {GREEN}")
    content.append("INTELLIGENT DATA SKEW ENGINE", style=f"dim {TEXT}")
    return Panel(content, border_style=GREEN, expand=False)


def get_summary_table(summary: Dict[str, Any]) -> Table:
    """Creates a Rich table displaying experiment performance summary."""
    table = Table(show_header=True, header_style=f"bold {GREEN}", border_style="dim green")
    table.add_column("Metric", style=TEXT)
    table.add_column("Baseline", justify="right", style=MUTED)
    table.add_column("Mitigated", justify="right", style=f"bold {GREEN}")
    table.add_column("Improvement", justify="right", style=f"bold {GREEN_2}")

    base_time = summary.get("baseline_execution_time", summary.get("before", {}).get("execution_time_sec", 0.0))
    mit_time = summary.get("mitigated_execution_time", summary.get("after", {}).get("execution_time_sec", 0.0))
    imp_pct = summary.get("improvement_pct", 0.0)

    base_max = summary.get("before", {}).get("max_partition_size", 0)
    mit_max = summary.get("after", {}).get("max_partition_size", 0)

    base_std = summary.get("before", {}).get("partition_std", 0.0)
    mit_std = summary.get("after", {}).get("partition_std", 0.0)

    table.add_row(
        "Execution Time",
        f"{base_time:.2f} s",
        f"{mit_time:.2f} s",
        f"{imp_pct:+.1f}%" if imp_pct else "—",
    )
    table.add_row(
        "Max Partition Records",
        f"{base_max:,}",
        f"{mit_max:,}",
        "—",
    )
    table.add_row(
        "Partition Std Dev",
        f"{base_std:.2f}",
        f"{mit_std:.2f}",
        "—",
    )

    return table


def get_ml_results_table(ml_payload: Dict[str, Any]) -> Table:
    """Creates a Rich table comparing ML model performance metrics."""
    table = Table(title="MODEL COMPARISON", header_style=f"bold {GREEN}", border_style="dim green")
    table.add_column("Model", style=TEXT)
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right")

    best_name = ml_payload.get("best_model", "")
    for res in ml_payload.get("results", []):
        is_best = (res.get("model_name") == best_name)
        style = f"bold {GREEN}" if is_best else MUTED
        table.add_row(
            f"{'★ ' if is_best else '  '}{res.get('model_name')}",
            f"{res.get('precision_macro', 0.0):.4f}",
            f"{res.get('recall_macro', 0.0):.4f}",
            f"{res.get('f1_macro', 0.0):.4f}",
            style=style,
        )

    return table


def get_history_table(history: List[Dict[str, Any]]) -> Table:
    """Creates a Rich table displaying historical experiment runs."""
    table = Table(title="EXPERIMENT HISTORY", header_style=f"bold {GREEN}", border_style="dim green")
    table.add_column("ID", style=TEXT)
    table.add_column("Rows", justify="right", style=MUTED)
    table.add_column("Skew", justify="right", style=MUTED)
    table.add_column("Severity", style=TEXT)
    table.add_column("Mitigation", style=TEXT)
    table.add_column("Improvement", justify="right", style=f"bold {GREEN}")

    for item in history:
        exp_id = item.get("experiment_id", "N/A")
        rows = item.get("rows", 0)
        skew = item.get("skew", item.get("skew_ratio", 0.0))
        sev = item.get("predicted_class", item.get("severity", "NORMAL"))
        mit = item.get("mitigation", item.get("mitigation_strategy", "NONE"))
        imp = item.get("improvement_pct", 0.0)

        sev_style = ERROR if sev == "HIGH_SKEW" else (WARNING if sev == "LOW_SKEW" else GREEN)
        skew_val = float(skew) if skew is not None else 0.0
        skew_str = f"{skew_val * 100:.0f}%" if skew_val <= 1.0 else f"{skew_val:.1f}"

        table.add_row(
            str(exp_id),
            f"{rows:,}",
            skew_str,
            f"[{sev_style}]{sev}[/{sev_style}]",
            str(mit),
            f"{imp:+.1f}%" if imp else "—",
        )

    return table
