"""skewctl — Intelligent Data Skew Detection & Mitigation CLI.

Command tree:
    skewctl system check
    skewctl data generate|inspect
    skewctl spark baseline|analyze
    skewctl ml build-dataset|train|evaluate|predict
    skewctl mitigate repartition|salt|auto
    skewctl experiment run|compare
    skewctl dashboard launch
"""
from __future__ import annotations

import importlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

# Ensure project root and virtual environment site-packages are in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_VENV_SITE = _PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

# Reconfigure stdout/stderr to UTF-8 for Windows console compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from spark.config import get, resolve_path

console = Console()

app = typer.Typer(help="skewctl — Intelligent Data Skew Detection & Mitigation", add_completion=False)
data_app = typer.Typer(help="Generate and inspect controlled-skew datasets")
spark_app = typer.Typer(help="Run Spark baseline and skew analysis")
ml_app = typer.Typer(help="Build ML dataset, train, evaluate, predict")
mitigate_app = typer.Typer(help="Apply mitigation strategies")
experiment_app = typer.Typer(help="Run and compare end-to-end experiments")
dashboard_app = typer.Typer(help="Launch the Streamlit dashboard")

app.add_typer(data_app, name="data")
app.add_typer(spark_app, name="spark")
app.add_typer(ml_app, name="ml")
app.add_typer(mitigate_app, name="mitigate")
app.add_typer(experiment_app, name="experiment")
app.add_typer(dashboard_app, name="dashboard")


def _banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]S K E W C T L[/bold cyan]\n"
            "[dim]Intelligent Data Skew Detection & Mitigation[/dim]\n\n"
            "Spark Analytics Engine\nML Severity Classifier\nAdaptive Mitigation",
            border_style="cyan",
        )
    )


# ---------------------------------------------------------------- system ---
@app.command()
def system(action: str = typer.Argument("check", help="Only 'check' is supported")):
    """System readiness check: Python, Java, PySpark, CPU/memory."""
    if action != "check":
        console.print(f"[red]Unknown system action:[/red] {action}")
        raise typer.Exit(1)

    _banner()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_row("System", "[green]● READY[/green]")

    py_version = platform.python_version()
    table.add_row("Python", f"[green]●[/green] {py_version}")

    java_ok = shutil.which("java") is not None or "JAVA_HOME" in os.environ
    java_version = "not found"
    if java_ok:
        try:
            java_cmd = "java"
            if "JAVA_HOME" in os.environ:
                j_bin = os.path.join(os.environ["JAVA_HOME"], "bin", "java.exe" if sys.platform == "win32" else "java")
                if os.path.exists(j_bin):
                    java_cmd = j_bin
            out = subprocess.run([java_cmd, "-version"], capture_output=True, text=True, timeout=5)
            java_version = (out.stderr or out.stdout).splitlines()[0]
        except Exception:
            java_version = "detected"
    table.add_row("Java", f"[{'green' if java_ok else 'red'}]●[/] {java_version}")

    try:
        importlib.import_module("pyspark")
        spark_ok = True
    except ImportError:
        spark_ok = False
    table.add_row("PySpark", f"[{'green' if spark_ok else 'red'}]●[/] {'READY' if spark_ok else 'NOT INSTALLED'}")

    try:
        cpu_count = os.cpu_count() or 0
        table.add_row("CPU cores", f"[green]●[/green] {cpu_count}")
    except Exception:
        pass

    ml_dir = resolve_path(get("paths", "results_models", default="results/models"))
    ml_ready = (ml_dir / "best_model.joblib").exists() or (ml_dir / "skew_classifier.joblib").exists()
    table.add_row("ML Engine", f"[{'green' if ml_ready else 'yellow'}]●[/] {'READY' if ml_ready else 'NOT TRAINED YET'}")

    console.print(table)


# -------------------------------------------------------------------- data ---
@data_app.command("generate")
def data_generate(
    rows: int = typer.Option(None, help="Row count (defaults to config)"),
    skew: float = typer.Option(0.10, help="Skew fraction in [0, 1)"),
    output: str = typer.Option(None, help="Output parquet path"),
    num_keys: int = typer.Option(None, help="Distinct key cardinality"),
    seed: int = typer.Option(None, help="RNG seed"),
):
    """Generate a controlled-skew synthetic dataset."""
    from spark.generate_data import generate_dataset

    with console.status("[cyan]Generating dataset..."):
        result = generate_dataset(rows=rows, skew=skew, output=output, num_keys=num_keys, seed=seed)

    console.print(f"[green]✓[/green] Dataset generated: [bold]{result.output_path}[/bold]")
    table = Table(show_header=False, box=None)
    table.add_row("Rows", f"{result.rows:,}")
    table.add_row("Skew", f"{result.skew:.0%}")
    table.add_row("Total keys", str(result.num_keys))
    table.add_row("Hot keys", str(result.num_hot_keys))
    console.print(table)


@data_app.command("inspect")
def data_inspect(
    input_path: str = typer.Argument(None, help="Parquet dataset to inspect"),
    input: str = typer.Option(None, "--input", "-i", help="Parquet dataset to inspect"),
):
    """EDA and key-distribution profile for a dataset."""
    from spark.analyze_skew import analyze
    from spark.session import get_spark_session, stop_spark_session

    target_path = input or input_path
    if not target_path:
        console.print("[red]Error: missing dataset path. Specify as positional argument or via --input[/red]")
        raise typer.Exit(1)

    spark = get_spark_session()
    try:
        with console.status("[cyan]Running EDA..."):
            key_stats, assessment = analyze(spark, target_path)

        table = Table(title=f"EDA — {Path(target_path).name}")
        table.add_column("Metric")
        table.add_column("Value", justify="right")
        for k, v in key_stats.to_dict().items():
            label = "Unique Keys" if k == "distinct_keys" else k.replace("_", " ").title()
            table.add_row(label, f"{v:,.4f}" if isinstance(v, float) else str(v))
        console.print(table)

        severity_color = {"NORMAL": "green", "LOW_SKEW": "yellow", "HIGH_SKEW": "red"}.get(
            assessment.severity, "white"
        )
        console.print(
            Panel.fit(
                f"SkewScore: [bold]{assessment.skew_score}[/bold]\n"
                f"Severity: [bold {severity_color}]{assessment.severity}[/bold {severity_color}]",
                title="Statistical Skew Assessment",
            )
        )
    finally:
        stop_spark_session(spark)


# ------------------------------------------------------------------- spark ---
@spark_app.command("baseline")
def spark_baseline(input: str = typer.Option(..., "--input", help="Parquet dataset")):
    """Run the groupBy baseline workload and print telemetry."""
    from spark.baseline import run_baseline
    from spark.session import get_spark_session, stop_spark_session

    spark = get_spark_session()
    try:
        with console.status("[cyan]Running Spark baseline..."):
            report = run_baseline(input, spark=spark)
        _print_metrics_table("Baseline Report", report.to_dict())
    finally:
        stop_spark_session(spark)


@spark_app.command("analyze")
def spark_analyze(input: str = typer.Option(..., "--input", help="Parquet dataset")):
    """Alias for `data inspect` under the spark namespace."""
    data_inspect(input)


# ---------------------------------------------------------------------- ml ---
@ml_app.command("build-dataset")
def ml_build_dataset(
    repeats: int = typer.Option(3, help="Repeats per skew level for label balance"),
    rows: int = typer.Option(None, help="Rows per generated run"),
):
    """Generate the experiment feature dataset used to train the classifier."""
    from ml.features import build_feature_dataset

    with console.status("[cyan]Building ML feature dataset (running Spark jobs)..."):
        df = build_feature_dataset(rows_per_run=rows, repeats=repeats)

    console.print(f"[green]✓[/green] Built feature dataset with [bold]{len(df)}[/bold] rows")
    console.print(df[["dataset", "skew_level", "skew_score", "severity"]].to_string(index=False))


@ml_app.command("train")
def ml_train(input: str = typer.Option(None, "--input", help="Experiment dataset CSV")):
    """Train Logistic Regression, Decision Tree, and Random Forest; keep the best by F1."""
    from ml.train import train_and_select

    with console.status("[cyan]Training classifiers..."):
        outcome = train_and_select(dataset_path=input)

    table = Table(title="Model Comparison")
    table.add_column("Model")
    table.add_column("Accuracy", justify="right")
    table.add_column("Precision", justify="right")
    table.add_column("Recall", justify="right")
    table.add_column("F1", justify="right")
    for r in outcome.results:
        style = "bold green" if r.model_name == outcome.best_model_name else ""
        table.add_row(
            r.model_name, f"{r.accuracy:.4f}", f"{r.precision_macro:.4f}",
            f"{r.recall_macro:.4f}", f"{r.f1_macro:.4f}", style=style,
        )
    console.print(table)
    console.print(f"[green]✓[/green] Training complete! Best model: [bold]{outcome.best_model_name}[/bold] saved to {outcome.best_model_path.parent / 'best_model.joblib'}")


@ml_app.command("evaluate")
def ml_evaluate(model: str = typer.Option(None, "--model", help="Path to model joblib")):
    """Print model evaluation report."""
    from ml.evaluate import evaluate_model_artifact
    model_path = model or "results/models/best_model.joblib"
    report = evaluate_model_artifact(model_path=model_path)
    console.print(Panel.fit(f"Overall Accuracy: [bold]{report['overall_accuracy']:.2%}[/bold]\nF1-Score: [bold]{report['macro_avg']['f1_score']:.4f}[/bold]"))


@ml_app.command("predict")
def ml_predict(input: str = typer.Option(..., "--input", help="Parquet dataset to score")):
    """Run baseline + predict skew severity + recommend mitigation."""
    from ml.predict import features_from_baseline, predict_severity
    from spark.analyze_skew import key_frequency_stats
    from spark.baseline import run_baseline
    from spark.session import get_spark_session, stop_spark_session

    spark = get_spark_session()
    try:
        with console.status("[cyan]Scoring dataset..."):
            baseline = run_baseline(input, spark=spark, save=False)
            df = spark.read.parquet(str(resolve_path(input)))
            k_stats = key_frequency_stats(df)
            features = features_from_baseline(baseline, k_stats.top1_concentration, k_stats.top5_concentration)
            result = predict_severity(features)

        severity_color = {"NORMAL": "green", "LOW_SKEW": "yellow", "HIGH_SKEW": "red"}.get(result.severity, "white")
        console.print(
            Panel.fit(
                f"Severity: [bold {severity_color}]{result.severity}[/bold {severity_color}] "
                f"(confidence {result.confidence:.0%})\n"
                f"Recommended mitigation: [bold]{result.recommended_mitigation}[/bold]",
                title="ML Prediction",
            )
        )
    finally:
        stop_spark_session(spark)


# ----------------------------------------------------------------- mitigate ---
@mitigate_app.command("repartition")
def mitigate_repartition(input: str = typer.Option(..., "--input")):
    _run_mitigation_cmd(input, "REPARTITION")


@mitigate_app.command("salt")
def mitigate_salt(input: str = typer.Option(..., "--input")):
    _run_mitigation_cmd(input, "SALTING")


@mitigate_app.command("auto")
def mitigate_auto(input: str = typer.Option(..., "--input")):
    """Predict severity with ML, then apply the recommended mitigation."""
    from ml.predict import features_from_baseline, predict_severity
    from spark.analyze_skew import key_frequency_stats
    from spark.baseline import run_baseline
    from spark.mitigation import run_mitigation
    from spark.session import get_spark_session, stop_spark_session

    spark = get_spark_session()
    try:
        with console.status("[cyan]Predicting severity..."):
            baseline = run_baseline(input, spark=spark, save=False)
            df = spark.read.parquet(str(resolve_path(input)))
            k_stats = key_frequency_stats(df)
            features = features_from_baseline(baseline, k_stats.top1_concentration, k_stats.top5_concentration)
            prediction = predict_severity(features)

        console.print(f"[cyan]✓[/cyan] ML prediction: [bold]{prediction.severity}[/bold] ({prediction.confidence:.0%})")
        console.print(f"[cyan]✓[/cyan] Mitigation selected: [bold]{prediction.recommended_mitigation}[/bold]")

        if prediction.recommended_mitigation == "NONE":
            console.print("[green]No mitigation required.[/green]")
            return

        with console.status(f"[cyan]Applying {prediction.recommended_mitigation}..."):
            after = run_mitigation(input, prediction.recommended_mitigation, spark=spark)

        _print_before_after(baseline, after)
    finally:
        stop_spark_session(spark)


def _run_mitigation_cmd(input: str, method: str) -> None:
    from spark.baseline import run_baseline
    from spark.mitigation import run_mitigation
    from spark.session import get_spark_session, stop_spark_session

    spark = get_spark_session()
    try:
        with console.status(f"[cyan]Running baseline then {method}..."):
            before = run_baseline(input, spark=spark)
            after = run_mitigation(input, method, spark=spark)
        _print_before_after(before, after)
    finally:
        stop_spark_session(spark)


def _print_before_after(before, after) -> None:
    from spark.mitigation import compare_before_after

    improvements = compare_before_after(before, after)
    table = Table(title="PERFORMANCE")
    table.add_column("Metric")
    table.add_column("Before", justify="right")
    table.add_column("After", justify="right")
    table.add_row("Runtime (s)", f"{before.execution_time_sec}", f"{after.execution_time_sec}")
    table.add_row("Max Partition", f"{before.max_partition_size}", f"{after.max_partition_size}")
    table.add_row("Partition Std", f"{before.partition_std}", f"{after.partition_std}")
    table.add_row("Shuffle Read", f"{before.shuffle_read_bytes}", f"{after.shuffle_read_bytes}")
    table.add_row("Shuffle Write", f"{before.shuffle_write_bytes}", f"{after.shuffle_write_bytes}")
    console.print(table)

    rt = improvements.get("runtime_improvement_pct")
    if rt is not None:
        console.print(f"[bold]Improvement (runtime):[/bold] {rt}%")


def _print_metrics_table(title: str, metrics: dict) -> None:
    table = Table(title=title)
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    for k, v in metrics.items():
        label = "Execution Time" if k == "execution_time_sec" else str(k).replace("_", " ").title()
        table.add_row(label, str(v))
    console.print(table)


# --------------------------------------------------------------- experiment ---
@experiment_app.command("run")
def experiment_run(
    rows: int = typer.Option(None, help="Row count"),
    skew: float = typer.Option(0.90, help="Skew fraction"),
    mitigation: str = typer.Option("auto", help="none | repartition | salting | auto"),
):
    """End-to-end: generate -> baseline -> ML predict -> mitigate -> compare -> save."""
    import time

    from ml.predict import features_from_baseline, predict_severity
    from spark.analyze_skew import key_frequency_stats
    from spark.baseline import run_baseline
    from spark.generate_data import generate_dataset
    from spark.mitigation import run_mitigation
    from spark.session import get_spark_session, stop_spark_session

    exp_id = f"EXP-{int(time.time()) % 100000:05d}"
    console.print(
        Panel.fit(
            f"ID              {exp_id}\n"
            f"Records         {rows or get('experiment', 'rows'):,}\n"
            f"Skew            {skew:.0%}\n"
            f"Mitigation      {mitigation}",
            title="Experiment",
        )
    )

    spark = get_spark_session()
    try:
        with console.status("[cyan]Generating dataset..."):
            gen = generate_dataset(rows=rows, skew=skew)
        console.print("[green]✓[/green] Dataset generated")

        with console.status("[cyan]Running Spark baseline..."):
            baseline = run_baseline(gen.output_path, spark=spark)
        console.print("[green]✓[/green] Baseline completed")

        method = mitigation.upper()
        if method == "AUTO":
            df = spark.read.parquet(str(gen.output_path))
            k_stats = key_frequency_stats(df)
            features = features_from_baseline(baseline, k_stats.top1_concentration, k_stats.top5_concentration)
            try:
                prediction = predict_severity(features)
                method = prediction.recommended_mitigation
                console.print(f"[green]✓[/green] ML prediction: [bold]{prediction.severity}[/bold] ({prediction.confidence:.0%})")
            except FileNotFoundError:
                from spark.analyze_skew import compute_skew_score
                from spark.metrics import partition_stats

                grouped = spark.read.parquet(str(gen.output_path)).groupBy("key").count()
                assessment = compute_skew_score(k_stats, partition_stats(grouped))
                from spark.mitigation import choose_mitigation

                method = choose_mitigation(assessment.severity)

        console.print(f"[green]✓[/green] Mitigation selected: [bold]{method}[/bold]")

        if method == "NONE":
            console.print("[green]No mitigation required — dataset is not meaningfully skewed.[/green]")
            return

        with console.status(f"[cyan]Running mitigated job ({method})..."):
            after = run_mitigation(gen.output_path, method, spark=spark)
        console.print("[green]✓[/green] Mitigated run completed")

        _print_before_after(baseline, after)

        exp_dir = resolve_path(get("paths", "results_experiments", default="results/experiments"))
        exp_dir.mkdir(parents=True, exist_ok=True)
        with open(exp_dir / f"{exp_id}.json", "w") as f:
            json.dump(
                {
                    "experiment_id": exp_id,
                    "dataset": gen.output_path.name,
                    "skew": skew,
                    "rows": gen.rows,
                    "mitigation": method,
                    "before": baseline.to_dict(),
                    "after": after.to_dict(),
                },
                f,
                indent=2,
            )
        console.print(f"[green]✓[/green] Results saved to {exp_dir / f'{exp_id}.json'}")
    finally:
        stop_spark_session(spark)


@experiment_app.command("compare")
def experiment_compare(runs: str = typer.Option("results/experiments/", "--runs")):
    """Summarize all saved experiment JSON files."""
    runs_dir = resolve_path(runs)
    files = sorted(runs_dir.glob("EXP-*.json"))
    if not files:
        console.print(f"[yellow]No experiment files found under {runs_dir}[/yellow]")
        raise typer.Exit(0)

    table = Table(title="Experiment Comparison")
    table.add_column("Experiment")
    table.add_column("Skew", justify="right")
    table.add_column("Mitigation")
    table.add_column("Runtime Before", justify="right")
    table.add_column("Runtime After", justify="right")
    table.add_column("Improvement %", justify="right")

    for path in files:
        with open(path) as f:
            payload = json.load(f)
        before_rt = payload["before"]["execution_time_sec"]
        after_rt = payload["after"]["execution_time_sec"]
        improvement = round(((before_rt - after_rt) / before_rt) * 100, 2) if before_rt else None
        table.add_row(
            payload["experiment_id"],
            f"{payload['skew']:.0%}",
            payload["mitigation"],
            f"{before_rt}s",
            f"{after_rt}s",
            f"{improvement}%" if improvement is not None else "—",
        )
    console.print(table)


# --------------------------------------------------------------- dashboard ---
@dashboard_app.command("launch")
def dashboard_launch(port: int = typer.Option(8501, help="Streamlit port")):
    """Launch the Streamlit results dashboard."""
    dashboard_path = resolve_path("dashboard/app.py")
    console.print(f"[cyan]Launching dashboard from {dashboard_path} on port {port}...[/cyan]")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", str(dashboard_path), "--server.port", str(port)]
    )


if __name__ == "__main__":
    app()
