"""Spark baseline execution.

Runs the canonical `groupBy("key").count()` workload against a dataset and
records the execution telemetry (runtime, partition imbalance, shuffle
volume) that everything downstream — EDA, feature engineering, the ML
classifier, and mitigation — is built on top of.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from spark.config import get, resolve_path
from spark.metrics import (
    fetch_last_stage_shuffle_metrics,
    get_partition_metrics,
    shuffle_partition_stats,
    time_spark_action,
)
from spark.session import get_spark_session, stop_spark_session


@dataclass
class BaselineReport:
    dataset: str
    rows: int
    input_partitions: int
    result_partitions: int
    execution_time_sec: float
    max_partition_size: int
    min_partition_size: int
    mean_partition_size: float
    partition_std: float
    skew_ratio: float
    coefficient_of_variation: float
    shuffle_read_bytes: int | None
    shuffle_write_bytes: int | None
    distinct_keys: int
    partition_sizes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _load(spark: SparkSession, input_path: Path) -> DataFrame:
    return spark.read.parquet(str(input_path))


def run_baseline(
    input_path: str | Path,
    spark: SparkSession | None = None,
    save: bool = True,
) -> BaselineReport:
    """Run the groupBy baseline workload and collect telemetry.

    Args:
        input_path: parquet dataset to benchmark.
        spark: an existing SparkSession to reuse; a new one is created (and
            stopped) if not provided.
        save: whether to persist the report as JSON under results/experiments.
    """
    resolved_path = resolve_path(input_path)
    active_before = SparkSession.getActiveSession() is not None
    owns_session = (spark is None) and (not active_before)
    spark = spark or get_spark_session()

    try:
        df = _load(spark, resolved_path)
        rows = df.count()
        input_partitions = df.rdd.getNumPartitions()

        start = time.perf_counter()
        grouped = df.groupBy("key").count()
        grouped.cache()
        result_row_count = grouped.count()  # action: triggers the shuffle
        elapsed = time.perf_counter() - start

        shuffle_partitions = int(spark.conf.get("spark.sql.shuffle.partitions") or "8")
        pstats = shuffle_partition_stats(df, "key", shuffle_partitions)
        shuffle = fetch_last_stage_shuffle_metrics(spark)
        grouped.unpersist()

        report = BaselineReport(
            dataset=resolved_path.name,
            rows=rows,
            input_partitions=input_partitions,
            result_partitions=pstats.partition_count,
            execution_time_sec=round(elapsed, 4),
            max_partition_size=pstats.max_size,
            min_partition_size=pstats.min_size,
            mean_partition_size=round(pstats.mean_size, 4),
            partition_std=round(pstats.std_size, 4),
            skew_ratio=round(pstats.skew_ratio, 4),
            coefficient_of_variation=round(pstats.coefficient_of_variation, 4),
            shuffle_read_bytes=shuffle["shuffle_read_bytes"],
            shuffle_write_bytes=shuffle["shuffle_write_bytes"],
            distinct_keys=result_row_count,
            partition_sizes=pstats.sizes,
        )

        if save:
            out_dir = resolve_path(get("paths", "results_experiments", default="results/experiments"))
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"baseline_{resolved_path.stem}.json"
            with open(out_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2)

        return report
    finally:
        if owns_session:
            stop_spark_session(spark)


def run_baseline_aggregation(df: DataFrame, key_col: str = "key") -> tuple[DataFrame, dict[str, Any]]:
    """Legacy helper for baseline grouped aggregation."""
    input_records = df.count()
    before_part_metrics = get_partition_metrics(df)

    agg_df = df.groupBy(key_col).agg(
        F.count("*").alias("record_count"),
        F.sum("value").alias("total_value"),
        F.avg("value").alias("avg_value"),
    )

    result, duration = time_spark_action(lambda: agg_df.collect())

    telemetry = {
        "input_records": input_records,
        "execution_time_seconds": duration,
        "input_partition_metrics": before_part_metrics,
        "output_groups": len(result),
        "agg_type": "groupBy",
    }

    return agg_df, telemetry


def run_baseline_join(df: DataFrame, dim_df: DataFrame, key_col: str = "key") -> tuple[DataFrame, dict[str, Any]]:
    """Legacy helper for baseline join workload."""
    joined_df = df.join(dim_df, on=key_col, how="inner")
    result, duration = time_spark_action(lambda: joined_df.count())

    telemetry = {
        "joined_records": result,
        "execution_time_seconds": duration,
        "agg_type": "join",
    }

    return joined_df, telemetry
