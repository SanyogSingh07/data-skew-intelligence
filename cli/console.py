from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from visualization.theme import ERROR, GREEN, GREEN_2, MUTED, SURFACE, TEXT, WARNING

console = Console()


def print_banner():
    """Prints the NVIDIA-inspired dark green accent header banner."""
    content = Text()
    content.append("S K E W C T L\n", style=f"bold {GREEN}")
    content.append("INTELLIGENT DATA SKEW ENGINE\n", style=f"bold {TEXT}")
    content.append("Distributed Data • Spark Telemetry • ML Severity • Mitigation", style=f"dim {MUTED}")

    banner = Panel(
        content,
        border_style=GREEN,
        expand=False,
        padding=(0, 4)
    )
    console.print(banner)


def print_step(step_num: int, total_steps: int, name: str, status: str = "✓", details: Optional[str] = None):
    """Prints a compact progress indicator step matching the spec."""
    tag = f"[{step_num}/{total_steps}]"
    if status == "✓":
        status_str = f"[bold {GREEN}]✓[/bold {GREEN}]"
    elif status == "✗":
        status_str = f"[bold {ERROR}]✗[/bold {ERROR}]"
    elif status == "...":
        status_str = f"[bold {WARNING}]...[/bold {WARNING}]"
    else:
        status_str = f"[bold {GREEN_2}]{status}[/bold {GREEN_2}]"

    line = f"[bold {GREEN}]{tag:<6}[/bold {GREEN}] [bold {TEXT}]{name:<24}[/bold {TEXT}] {status_str}"
    if details:
        line += f"  [dim {MUTED}]({details})[/dim {MUTED}]"
    console.print(line)


def print_environment_table(checks: List[Dict[str, Any]]):
    """Prints the environment readiness check table."""
    table = Table(title="ENVIRONMENT READINESS CHECK", border_style=GREEN, header_style=f"bold {GREEN}")
    table.add_column("Component", style=f"bold {TEXT}")
    table.add_column("Required", style=f"dim {MUTED}")
    table.add_column("Detected", style=WARNING)
    table.add_column("Status", style=f"bold {GREEN}")

    for c in checks:
        status_display = f"[bold {GREEN}]✓ READY[/bold {GREEN}]" if c["passed"] else f"[bold {ERROR}]✗ MISSING[/bold {ERROR}]"
        table.add_row(c["name"], c["required"], c["detected"], status_display)

    console.print(table)


def print_comparison_table(comparison: Dict[str, Any]):
    """Prints the before/after performance comparison table matching the spec."""
    table = Table(title="PERFORMANCE COMPARISON (BASELINE vs MITIGATED)", border_style=GREEN, header_style=f"bold {GREEN}")
    table.add_column("Metric", style=f"bold {TEXT}")
    table.add_column("Baseline (Before)", style=f"bold {MUTED}")
    table.add_column("Mitigated (After)", style=f"bold {GREEN}")
    table.add_column("Improvement", style=f"bold {GREEN_2}")

    imp = comparison.get("improvement_pct", 0.0)
    imp_str = f"+{imp:.1f}%" if imp > 0 else f"{imp:.1f}%"

    table.add_row("Execution Wall-Clock Time", f"{comparison['baseline_execution_time']} s", f"{comparison['mitigated_execution_time']} s", imp_str)
    table.add_row("Max Partition Records", f"{comparison['baseline_max_partition_records']:,}", f"{comparison['mitigated_max_partition_records']:,}", "—")
    table.add_row("Partition Record Std Dev", f"{comparison['baseline_partition_std']}", f"{comparison['mitigated_partition_std']}", "—")

    console.print(table)
    console.print(f"[bold {WARNING}]Measured Runtime Improvement: [bold {GREEN}]{imp_str}[/bold {GREEN}]")


def print_final_report(summary: Dict[str, Any], results_path: str):
    """Prints executive summary report card at the end of run.py."""
    lines = [
        f"[bold {TEXT}]Dataset:[/bold {TEXT}]             {summary.get('rows', 100000):,} records",
        f"[bold {TEXT}]Skew Ratio:[/bold {TEXT}]          {summary.get('skew_ratio', 0.70)*100:.1f}%",
        f"[bold {TEXT}]Severity Class:[/bold {TEXT}]      [bold {ERROR if summary.get('predicted_class')=='HIGH_SKEW' else WARNING}]{summary.get('predicted_class', 'HIGH_SKEW')}[/bold {ERROR if summary.get('predicted_class')=='HIGH_SKEW' else WARNING}]",
        f"[bold {TEXT}]ML Model:[/bold {TEXT}]           {summary.get('ml_model', 'Random Forest')}",
        f"[bold {TEXT}]Mitigation Applied:[/bold {TEXT}] [bold {GREEN}]{summary.get('mitigation_strategy', 'SALTING')}[/bold {GREEN}]",
        "",
        f"[bold {TEXT}]Runtime Baseline:[/bold {TEXT}]   {summary.get('baseline_execution_time', 0.0):.2f} s",
        f"[bold {TEXT}]Runtime Mitigated:[/bold {TEXT}]  {summary.get('mitigated_execution_time', 0.0):.2f} s",
        f"[bold {TEXT}]Improvement:[/bold {TEXT}]        [bold {GREEN_2}]{summary.get('improvement_pct', 0.0):+.1f}%[/bold {GREEN_2}]",
        "",
        f"[bold {TEXT}]Tests Status:[/bold {TEXT}]       [bold {GREEN}]{summary.get('tests_passed', 0)} passed[/bold {GREEN}]"
    ]

    body = "\n".join(lines)
    panel = Panel(
        body,
        title=f"[bold {GREEN}]EXPERIMENT COMPLETE[/bold {GREEN}]",
        border_style=GREEN,
        expand=False,
        padding=(1, 4)
    )
    console.print()
    console.print(panel)
    console.print(f"[bold {TEXT}]Latest Results Available At:[/bold {TEXT}] [bold {WARNING}]{results_path}[/bold {WARNING}]")


def print_error(title: str, reason: str, log_path: str = "logs/error.log"):
    """Displays clean error report without dumping raw tracebacks into the CLI."""
    console.print()
    console.print(f"[bold {ERROR}]✗ {title.upper()}[/bold {ERROR}]")
    console.print(f"\n[bold {TEXT}]Reason:[/bold {TEXT}]\n{reason}")
    console.print(f"\n[dim {MUTED}]Detailed log saved to:[/dim {MUTED}] [yellow]{log_path}[/yellow]")

