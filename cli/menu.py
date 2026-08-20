"""Interactive Results Console Menu for SkewCTL.

Provides rich terminal navigation across latest experiment metrics, historical runs,
dataset profile, Spark metrics, before/after comparison, ML results, and graph views.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from core.config import EXPERIMENTS_RESULTS_DIR, LATEST_RESULTS_DIR, RESULTS_DIR
from visualization.tables import (
    get_banner_panel,
    get_history_table,
    get_ml_results_table,
    get_summary_table,
)
from visualization.theme import ERROR, GREEN, GREEN_2, MUTED, SURFACE, TEXT, WARNING

console = Console()


def load_latest_experiment() -> Dict[str, Any]:
    """Loads results/latest/summary.json or latest timestamp directory summary."""
    latest_summary = LATEST_RESULTS_DIR / "summary.json"
    if latest_summary.exists():
        try:
            with open(latest_summary, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def load_experiment_history() -> List[Dict[str, Any]]:
    """Loads all saved experiment JSON records from results/experiments/."""
    history = []
    if EXPERIMENTS_RESULTS_DIR.exists():
        for path in sorted(EXPERIMENTS_RESULTS_DIR.glob("*.json"), reverse=True):
            try:
                with open(path, encoding="utf-8") as f:
                    payload = json.load(f)
                    history.append(payload)
            except Exception:
                pass
    return history


def show_menu_header() -> None:
    """Prints the main Results Console panel header matching the NVIDIA dark green visual theme."""
    menu_panel = Panel(
        f"[bold {GREEN}]1[/bold {GREEN}]  Latest Experiment Summary\n"
        f"[bold {GREEN}]2[/bold {GREEN}]  Experiment History\n"
        f"[bold {GREEN}]3[/bold {GREEN}]  Dataset Profile\n"
        f"[bold {GREEN}]4[/bold {GREEN}]  Spark Execution Metrics\n"
        f"[bold {GREEN}]5[/bold {GREEN}]  Before vs After Performance\n"
        f"[bold {GREEN}]6[/bold {GREEN}]  ML Classifier Diagnostics\n"
        f"[bold {GREEN}]7[/bold {GREEN}]  View Generated Graphs\n"
        f"[bold {GREEN}]8[/bold {GREEN}]  Run Pipeline Again\n"
        f"[bold {GREEN}]9[/bold {GREEN}]  Exit Console",
        title=f"[bold {GREEN}]RESULTS CONSOLE[/bold {GREEN}]",
        border_style=GREEN,
        expand=False,
        padding=(0, 3)
    )
    console.print(menu_panel)


def display_latest_summary(summary: Dict[str, Any]) -> None:
    """Option 1: Latest Experiment Summary."""
    if not summary:
        console.print(f"[{WARNING}]No recent experiment data found under results/latest.[/{WARNING}]")
        return

    exp_id = summary.get("experiment_id", "N/A")
    rows = summary.get("rows", 0)
    skew = summary.get("skew", summary.get("skew_ratio", 0.0))
    severity = summary.get("predicted_class", summary.get("severity", "NORMAL"))
    model = summary.get("ml_model", "N/A")
    mitigation = summary.get("mitigation", "NONE")

    base_time = summary.get("baseline_execution_time", summary.get("before", {}).get("execution_time_sec", 0.0))
    mit_time = summary.get("mitigated_execution_time", summary.get("after", {}).get("execution_time_sec", 0.0))

    base_std = summary.get("before", {}).get("partition_std", 0.0)
    mit_std = summary.get("after", {}).get("partition_std", 0.0)

    skew_val = float(skew) if skew is not None else 0.0

    content = (
        f"[bold {TEXT}]Experiment ID:[/]       {exp_id}\n"
        f"[bold {TEXT}]Records:[/]             {rows:,}\n"
        f"[bold {TEXT}]Skew Ratio:[/]          {skew_val * 100:.0f}%\n"
        f"[bold {TEXT}]Severity:[/]           [bold {GREEN if severity=='NORMAL' else (WARNING if severity=='LOW_SKEW' else ERROR)}]{severity}[/]\n"
        f"[bold {TEXT}]ML Classifier:[/]      {model}\n"
        f"[bold {TEXT}]Mitigation:[/]         [bold {GREEN}]{mitigation}[/bold {GREEN}]\n\n"
        f"[bold {TEXT}]Runtime Baseline:[/]    {base_time:.2f} s\n"
        f"[bold {TEXT}]Runtime Mitigated:[/]   {mit_time:.2f} s\n\n"
        f"[bold {TEXT}]Partition Std Before:[/] {base_std:.2f}\n"
        f"[bold {TEXT}]Partition Std After:[/]  {mit_std:.2f}"
    )
    console.print(Panel(content, title=f"[bold {GREEN}]EXPERIMENT SUMMARY[/bold {GREEN}]", border_style=GREEN, expand=False))


def display_history() -> None:
    """Option 2: Experiment History Table."""
    history = load_experiment_history()
    if not history:
        console.print(f"[{WARNING}]No experiment history records found in results/experiments/.[/{WARNING}]")
        return
    table = get_history_table(history)
    console.print(table)


def display_dataset_profile(summary: Dict[str, Any]) -> None:
    """Option 3: Dataset Profile."""
    profile_file = LATEST_RESULTS_DIR / "dataset_profile.json"
    profile_data = {}
    if profile_file.exists():
        try:
            with open(profile_file, encoding="utf-8") as f:
                profile_data = json.load(f)
        except Exception:
            pass

    table = Table(title="DATASET PROFILE", header_style=f"bold {GREEN}", border_style=GREEN)
    table.add_column("Property", style=TEXT)
    table.add_column("Value", justify="right", style=GREEN)

    table.add_row("Total Records", f"{profile_data.get('total_rows', summary.get('rows', 0)):,}")
    table.add_row("Unique Keys", f"{profile_data.get('distinct_keys', 0):,}")
    table.add_row("Top-1 Key Concentration", f"{profile_data.get('top1_concentration', 0.0) * 100:.1f}%")
    table.add_row("Top-5 Keys Concentration", f"{profile_data.get('top5_concentration', 0.0) * 100:.1f}%")
    table.add_row("Mean Frequency per Key", f"{profile_data.get('mean_frequency', 0.0):,.1f}")
    table.add_row("Std Dev Key Frequency", f"{profile_data.get('std_frequency', 0.0):,.1f}")
    console.print(table)

    top_keys = profile_data.get("top_keys", {})
    if top_keys:
        k_table = Table(title="TOP KEYS DISTRIBUTION", header_style=f"bold {GREEN}", border_style=GREEN)
        k_table.add_column("Key", style=TEXT)
        k_table.add_column("Record Count", justify="right", style=GREEN)
        for k, v in list(top_keys.items())[:10]:
            k_table.add_row(str(k), f"{v:,}")
        console.print(k_table)


def display_spark_metrics() -> None:
    """Option 4: Spark Execution Metrics."""
    base_file = LATEST_RESULTS_DIR / "baseline_metrics.json"
    mit_file = LATEST_RESULTS_DIR / "mitigated_metrics.json"

    base_data = {}
    mit_data = {}

    if base_file.exists():
        with open(base_file, encoding="utf-8") as f:
            base_data = json.load(f)
    if mit_file.exists():
        with open(mit_file, encoding="utf-8") as f:
            mit_data = json.load(f)

    table = Table(title="SPARK EXECUTION TELEMETRY", header_style=f"bold {GREEN}", border_style=GREEN)
    table.add_column("Metric", style=TEXT)
    table.add_column("Baseline", justify="right", style=MUTED)
    table.add_column("Mitigated", justify="right", style=GREEN)

    table.add_row("Partitions", str(base_data.get("result_partitions", base_data.get("input_partitions", "—"))),
                  str(mit_data.get("result_partitions", "—")))
    table.add_row("Max Partition Records", f"{base_data.get('max_partition_size', 0):,}", f"{mit_data.get('max_partition_size', 0):,}")
    table.add_row("Mean Partition Records", f"{base_data.get('mean_partition_size', 0.0):,.1f}", f"{mit_data.get('mean_partition_size', 0.0):,.1f}")
    table.add_row("Partition Std Dev", f"{base_data.get('partition_std', 0.0):.2f}", f"{mit_data.get('partition_std', 0.0):.2f}")
    table.add_row("Partition CV", f"{base_data.get('coefficient_of_variation', 0.0):.2f}", f"{mit_data.get('coefficient_of_variation', 0.0):.2f}")
    table.add_row("Shuffle Read (bytes)", str(base_data.get("shuffle_read_bytes", "N/A")), str(mit_data.get("shuffle_read_bytes", "N/A")))
    table.add_row("Shuffle Write (bytes)", str(base_data.get("shuffle_write_bytes", "N/A")), str(mit_data.get("shuffle_write_bytes", "N/A")))
    table.add_row("Runtime (sec)", f"{base_data.get('execution_time_sec', 0.0):.2f} s", f"{mit_data.get('execution_time_sec', 0.0):.2f} s")

    console.print(table)


def display_before_after(summary: Dict[str, Any]) -> None:
    """Option 5: Before vs After Table."""
    table = get_summary_table(summary)
    console.print(table)


def display_ml_results() -> None:
    """Option 6: ML Results & Model Evaluation."""
    ml_file = LATEST_RESULTS_DIR / "ml_metrics.json"
    report_file = Path("results/reports/ml_comparison.json")

    ml_data = {}
    if report_file.exists():
        with open(report_file, encoding="utf-8") as f:
            ml_data = json.load(f)
    elif ml_file.exists():
        with open(ml_file, encoding="utf-8") as f:
            ml_data = json.load(f)

    if ml_data and "results" in ml_data:
        table = get_ml_results_table(ml_data)
        console.print(table)
    else:
        console.print(f"[{WARNING}]No trained ML classification report found.[/{WARNING}]")


def display_graphs_menu() -> None:
    """Option 7: Graph Viewer Submenu."""
    charts_dir = LATEST_RESULTS_DIR / "charts"
    if not charts_dir.exists():
        console.print(f"[{WARNING}]No charts directory found under results/latest/.[/{WARNING}]")
        return

    chart_files = {
        "1": ("Key Distribution", charts_dir / "key_distribution.png"),
        "2": ("Partition Distribution", charts_dir / "partition_distribution.png"),
        "3": ("Before / After Partitions", charts_dir / "before_after_partition.png"),
        "4": ("Skew vs Runtime", charts_dir / "skew_vs_runtime.png"),
        "5": ("Skew vs Partition CV", charts_dir / "skew_vs_partition_cv.png"),
        "6": ("Performance Comparison", charts_dir / "performance_comparison.png"),
    }

    console.print(Panel(
        "\n".join([f"[bold {GREEN}]{k}[/bold {GREEN}]  {v[0]} ({'✓ ready' if v[1].exists() else '✗ missing'})" for k, v in chart_files.items()]),
        title=f"[bold {GREEN}]GRAPH VIEWER[/bold {GREEN}]",
        border_style=GREEN,
        expand=False,
    ))

    choice = Prompt.ask("Select graph to inspect (or press Enter to return)", choices=list(chart_files.keys()) + [""])
    if choice in chart_files:
        title, chart_path = chart_files[choice]
        if chart_path.exists():
            console.print(f"\n[bold {GREEN}]✓ {title}[/bold {GREEN}] chart exported at:")
            console.print(f"   [bold {GREEN_2}]{chart_path.resolve()}[/bold {GREEN_2}]\n")
        else:
            console.print(f"[bold {ERROR}]Chart file '{chart_path.name}' does not exist.[/bold {ERROR}]")


def run_results_console() -> bool:
    """Launches interactive results console loop.

    Returns:
        True if the user chooses 'Run Again' (option 8), False if exiting.
    """
    summary = load_latest_experiment()

    while True:
        show_menu_header()
        choice = Prompt.ask(
            f"[bold {GREEN}]Select menu option[/bold {GREEN}]",
            choices=["1", "2", "3", "4", "5", "6", "7", "8", "9"],
            default="1",
        )

        if choice == "1":
            display_latest_summary(summary)
        elif choice == "2":
            display_history()
        elif choice == "3":
            display_dataset_profile(summary)
        elif choice == "4":
            display_spark_metrics()
        elif choice == "5":
            display_before_after(summary)
        elif choice == "6":
            display_ml_results()
        elif choice == "7":
            display_graphs_menu()
        elif choice == "8":
            return True  # Re-run pipeline
        elif choice == "9":
            console.print(f"[{MUTED}]Exiting Results Console. Goodbye![/{MUTED}]")
            return False

