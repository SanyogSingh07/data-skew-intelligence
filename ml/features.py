"""Feature engineering.

Builds the experiment-level ML dataset: one row per Spark run, with
execution-telemetry features (partition/shuffle/runtime statistics) and a
severity label. Labels come from the transparent statistical `SkewScore`
(spark/analyze_skew.py).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pyspark.sql import SparkSession

from spark.analyze_skew import analyze
from spark.baseline import run_baseline
from spark.config import get, resolve_path
from spark.generate_data import generate_dataset
from spark.session import get_spark_session, stop_spark_session

FEATURE_COLUMNS = [
    "skew_ratio",
    "top1_concentration",
    "top5_concentration",
    "partition_count",
    "mean_partition_size",
    "max_partition_size",
    "partition_std",
    "execution_time_sec",
    "shuffle_read_bytes",
    "shuffle_write_bytes",
]
LABEL_COLUMN = "severity"


def _row_for_dataset(spark: SparkSession, dataset_path: Path) -> dict[str, Any]:
    baseline = run_baseline(dataset_path, spark=spark, save=False)
    key_stats, assessment = analyze(spark, dataset_path)

    return {
        "dataset": dataset_path.name,
        "skew_ratio": baseline.skew_ratio,
        "top1_concentration": key_stats.top1_concentration,
        "top5_concentration": key_stats.top5_concentration,
        "partition_count": baseline.result_partitions,
        "mean_partition_size": baseline.mean_partition_size,
        "max_partition_size": baseline.max_partition_size,
        "partition_std": baseline.partition_std,
        "execution_time_sec": baseline.execution_time_sec,
        "shuffle_read_bytes": baseline.shuffle_read_bytes or 0,
        "shuffle_write_bytes": baseline.shuffle_write_bytes or 0,
        "skew_score": assessment.skew_score,
        LABEL_COLUMN: assessment.severity,
    }


def build_feature_dataset(
    skew_levels: list[float] | None = None,
    rows_per_run: int | None = None,
    repeats: int = 3,
    spark: SparkSession | None = None,
    save: bool = True,
) -> pd.DataFrame:
    """Generate datasets across skew levels, benchmark each, and assemble
    the experiment feature table.
    """
    skew_levels = skew_levels or get("experiment", "skew_levels", default=[0.10, 0.30, 0.50, 0.70, 0.90])
    rows_per_run = rows_per_run or get("experiment", "rows", default=50_000)

    active_before = SparkSession.getActiveSession() is not None
    owns_session = (spark is None) and (not active_before)
    spark = spark or get_spark_session()

    records = []
    try:
        for level in skew_levels:
            for i in range(repeats):
                gen = generate_dataset(
                    rows=rows_per_run,
                    skew=level,
                    seed=get("experiment", "seed", default=42) + i,
                    output=resolve_path("data/generated") / f"train_skew_{int(level*100)}_{i}.parquet",
                )
                row = _row_for_dataset(spark, gen.output_path)
                row["skew_level"] = level
                records.append(row)
    finally:
        if owns_session:
            stop_spark_session(spark)

    df = pd.DataFrame(records)

    if save:
        out_path = resolve_path(get("paths", "experiment_dataset", default="results/metrics/experiment_dataset.csv"))
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_path, index=False)

    return df


def extract_features_from_run(analysis: dict[str, Any], telemetry: dict[str, Any]) -> dict[str, Any]:
    """Legacy helper function for extracting features from run outputs."""
    p_metrics = analysis.get("partition_metrics", {})
    skew_score = analysis.get("skew_score", 0.0)
    if skew_score < 0.30:
        target_class = 0
        class_name = "NORMAL"
    elif skew_score < 0.60:
        target_class = 1
        class_name = "LOW_SKEW"
    else:
        target_class = 2
        class_name = "HIGH_SKEW"

    return {
        "skew_ratio": float(p_metrics.get("skew_ratio", 1.0)),
        "top1_concentration": float(analysis.get("top1_concentration", 0.0)),
        "top5_concentration": float(analysis.get("top5_concentration", 0.0)),
        "partition_count": int(p_metrics.get("partition_count", 8)),
        "mean_partition_size": float(p_metrics.get("mean_partition_records", 0.0)),
        "max_partition_size": float(p_metrics.get("max_partition_records", 0.0)),
        "partition_std": float(p_metrics.get("partition_std", 0.0)),
        "cv": float(p_metrics.get("cv", 0.0)),
        "execution_time_seconds": float(telemetry.get("execution_time_seconds", 0.0)),
        "target_class": target_class,
        "class_name": class_name,
    }


def generate_synthetic_training_dataset(n_samples: int = 300, seed: int = 42) -> pd.DataFrame:
    """Legacy helper function to generate synthetic dataset for ML tests."""
    np.random.seed(seed)
    data = []

    for _ in range(n_samples):
        skew_level = str(np.random.choice(["NORMAL", "LOW_SKEW", "HIGH_SKEW"], p=[0.35, 0.35, 0.30]))
        num_rows = int(np.random.choice([50000, 100000, 500000, 1000000]))
        partitions = int(np.random.choice([4, 8, 16, 32]))
        mean_part = num_rows / float(partitions)

        if skew_level == "NORMAL":
            top1_conc = np.random.uniform(0.01, 0.20)
            top5_conc = top1_conc + np.random.uniform(0.05, 0.25)
            skew_ratio = np.random.uniform(1.0, 1.4)
            cv = np.random.uniform(0.05, 0.3)
            exec_time = (num_rows / 200000.0) * np.random.uniform(0.8, 1.2)
            target = 0
            severity = "NORMAL"
        elif skew_level == "LOW_SKEW":
            top1_conc = np.random.uniform(0.20, 0.50)
            top5_conc = top1_conc + np.random.uniform(0.05, 0.25)
            skew_ratio = np.random.uniform(1.4, 2.5)
            cv = np.random.uniform(0.3, 0.8)
            exec_time = (num_rows / 200000.0) * np.random.uniform(1.3, 2.0)
            target = 1
            severity = "LOW_SKEW"
        else:
            top1_conc = np.random.uniform(0.50, 0.95)
            top5_conc = top1_conc + np.random.uniform(0.01, 0.05)
            skew_ratio = np.random.uniform(2.5, 8.0)
            cv = np.random.uniform(0.8, 3.5)
            exec_time = (num_rows / 200000.0) * np.random.uniform(2.2, 5.5)
            target = 2
            severity = "HIGH_SKEW"

        max_part = mean_part * skew_ratio
        part_std = cv * mean_part

        data.append({
            "skew_ratio": round(skew_ratio, 4),
            "top1_concentration": round(top1_conc, 4),
            "top5_concentration": round(min(1.0, top5_conc), 4),
            "partition_count": partitions,
            "mean_partition_size": round(mean_part, 2),
            "max_partition_size": round(max_part, 2),
            "partition_std": round(part_std, 2),
            "execution_time_sec": round(exec_time, 4),
            "execution_time_seconds": round(exec_time, 4),
            "shuffle_read_bytes": 1024,
            "shuffle_write_bytes": 1024,
            "cv": round(cv, 4),
            "target_class": target,
            "class_name": skew_level,
            "severity": severity,
        })

    return pd.DataFrame(data)
