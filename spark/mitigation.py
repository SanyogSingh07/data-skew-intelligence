"""Stage 8 — Mitigation: repartitioning and salting.

Two techniques for reducing partition imbalance caused by hot keys:

Repartitioning
    Increases the number of shuffle partitions for the grouping shuffle.
    This helps when skew is moderate: cold keys spread thinner, so fewer of
    them collide with the hot key's partition. It does **not** split a
    single hot key's records across partitions, so it has limited effect
    once one key dominates the dataset — which is exactly why the decision
    engine reserves it for LOW_SKEW and reaches for salting on HIGH_SKEW.

Salting
    Appends a random suffix (`key -> key_0, key_1, ... key_{B-1}`) to every
    key before the first aggregation, spreading a single hot key's records
    across B partitions. A second aggregation phase strips the salt and
    sums the partial counts back into the original logical keys, so the
    final result is identical to a plain `groupBy("key").count()`.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from spark.baseline import BaselineReport
from spark.config import get, resolve_path
from spark.metrics import (
    fetch_last_stage_shuffle_metrics,
    get_partition_metrics,
    shuffle_partition_stats,
    time_spark_action,
)
from spark.session import get_spark_session, stop_spark_session


def choose_mitigation(prediction: str) -> str:
    """Deterministic decision rule: severity -> mitigation strategy."""
    pred = prediction.upper()
    if pred == "NORMAL":
        return "NONE"
    if pred == "LOW_SKEW":
        return "REPARTITION"
    return "SALTING"


def apply_repartition(
    df: DataFrame,
    spark: SparkSession | int | None = None,
    multiplier: int = 2,
    key_col: Optional[str] = None,
    num_partitions: Optional[int] = None,
) -> tuple[DataFrame, dict[str, Any]] | DataFrame:
    """Widen the shuffle-partition count for the upcoming groupBy shuffle
    or repartition DataFrame directly.
    """
    if num_partitions is not None:
        spark = num_partitions

    # Overload support: if called with (df, num_partitions, key_col) -> tuple (legacy test interface)
    if isinstance(spark, int):
        num_parts = spark
        if key_col:
            repartitioned = df.repartition(num_parts, key_col)
        else:
            repartitioned = df.repartition(num_parts)
        part_metrics = get_partition_metrics(repartitioned)
        telemetry = {
            "mitigation": "REPARTITION",
            "num_partitions": num_parts,
            "partition_metrics": part_metrics,
        }
        return repartitioned, telemetry

    # New pipeline interface
    spark_sess = spark or get_spark_session()
    base = get("spark", "shuffle_partitions", default=8)
    spark_sess.conf.set("spark.sql.shuffle.partitions", str(base * multiplier))
    return df


def apply_salting_groupby(df: DataFrame, buckets: int | None = None) -> DataFrame:
    """Two-phase salted aggregation, logically equivalent to
    `df.groupBy("key").count()`.
    """
    buckets = buckets or get("mitigation", "salt_buckets", default=8)

    salted = df.withColumn("_salt", (F.rand() * buckets).cast("int"))
    partial = salted.groupBy("key", "_salt").count().withColumnRenamed("count", "partial_count")
    reconstructed = (
        partial.groupBy("key")
        .agg(F.sum("partial_count").alias("count"))
    )
    return reconstructed


@dataclass
class MitigationReport:
    dataset: str
    method: str
    rows: int
    execution_time_sec: float
    result_partitions: int
    max_partition_size: int
    min_partition_size: int
    mean_partition_size: float
    partition_std: float
    skew_ratio: float
    coefficient_of_variation: float
    shuffle_read_bytes: int | None
    shuffle_write_bytes: int | None
    partition_sizes: list[int] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def run_mitigation(
    input_path: str | Path,
    method: str,
    spark: SparkSession | None = None,
    save: bool = True,
) -> MitigationReport:
    """Run the groupBy workload with the given mitigation applied and
    collect the same telemetry `run_baseline` does, for apples-to-apples
    before/after comparison.
    """
    method = method.upper()
    resolved_path = resolve_path(input_path)
    active_before = SparkSession.getActiveSession() is not None
    owns_session = (spark is None) and (not active_before)
    spark = spark or get_spark_session()

    try:
        df = spark.read.parquet(str(resolved_path))
        rows = df.count()

        buckets = get("mitigation", "salt_buckets", default=8)

        start = time.perf_counter()
        if method == "SALTING":
            result = apply_salting_groupby(df, buckets)
        elif method == "REPARTITION":
            df_rep = apply_repartition(df, spark)
            if isinstance(df_rep, tuple):
                df_rep = df_rep[0]
            result = df_rep.groupBy("key").count()
        else:  # NONE
            result = df.groupBy("key").count()

        result.cache()
        result.count()
        elapsed = time.perf_counter() - start

        shuffle_partitions = int(spark.conf.get("spark.sql.shuffle.partitions") or "8")
        if method == "SALTING":
            salted = df.withColumn("_salt", (F.rand() * buckets).cast("int"))
            pstats = shuffle_partition_stats(salted, ["key", "_salt"], shuffle_partitions)
        else:
            pstats = shuffle_partition_stats(df, "key", shuffle_partitions)

        shuffle = fetch_last_stage_shuffle_metrics(spark)
        result.unpersist()

        report = MitigationReport(
            dataset=resolved_path.name,
            method=method,
            rows=rows,
            execution_time_sec=round(elapsed, 4),
            result_partitions=pstats.partition_count,
            max_partition_size=pstats.max_size,
            min_partition_size=pstats.min_size,
            mean_partition_size=round(pstats.mean_size, 4),
            partition_std=round(pstats.std_size, 4),
            skew_ratio=round(pstats.skew_ratio, 4),
            coefficient_of_variation=round(pstats.coefficient_of_variation, 4),
            shuffle_read_bytes=shuffle["shuffle_read_bytes"],
            shuffle_write_bytes=shuffle["shuffle_write_bytes"],
            partition_sizes=pstats.sizes,
        )

        if save:
            out_dir = resolve_path(get("paths", "results_experiments", default="results/experiments"))
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"mitigation_{method.lower()}_{resolved_path.stem}.json"
            with open(out_path, "w") as f:
                json.dump(report.to_dict(), f, indent=2)

        return report
    finally:
        if owns_session:
            stop_spark_session(spark)


def compare_before_after(before: BaselineReport, after: MitigationReport) -> dict[str, Any]:
    """Compute percentage improvement for each comparable metric."""

    def pct(b: float | int | None, a: float | int | None) -> float | None:
        if b in (None, 0):
            return None
        if a is None:
            return None
        return round(((b - a) / b) * 100, 2)

    return {
        "runtime_improvement_pct": pct(before.execution_time_sec, after.execution_time_sec),
        "max_partition_improvement_pct": pct(before.max_partition_size, after.max_partition_size),
        "partition_std_improvement_pct": pct(before.partition_std, after.partition_std),
        "shuffle_read_improvement_pct": pct(before.shuffle_read_bytes, after.shuffle_read_bytes),
        "shuffle_write_improvement_pct": pct(before.shuffle_write_bytes, after.shuffle_write_bytes),
    }


def apply_salting_aggregation(
    df: DataFrame,
    num_salts: int = 8,
    key_col: str = "key",
    val_col: str = "value",
) -> tuple[DataFrame, dict[str, Any]]:
    """Legacy helper for salted aggregations."""
    df_salted = df.withColumn("salt", F.floor(F.rand() * num_salts)) \
                  .withColumn("salted_key", F.concat(F.col(key_col), F.lit("_SALT_"), F.col("salt")))

    stage1_agg = df_salted.groupBy("salted_key", key_col).agg(
        F.count("*").alias("partial_count"),
        F.sum(val_col).alias("partial_sum")
    )

    final_agg = stage1_agg.groupBy(key_col).agg(
        F.sum("partial_count").alias("record_count"),
        F.sum("partial_sum").alias("total_value"),
        (F.sum("partial_sum") / F.sum("partial_count")).alias("avg_value")
    )

    result, duration = time_spark_action(lambda: final_agg.collect())

    telemetry = {
        "mitigation": "SALTING",
        "num_salts": num_salts,
        "execution_time_seconds": duration,
        "output_groups": len(result),
    }

    return final_agg, telemetry


def apply_salting_join(
    fact_df: DataFrame,
    dim_df: DataFrame,
    num_salts: int = 8,
    key_col: str = "key",
) -> tuple[DataFrame, dict[str, Any]]:
    """Legacy helper for salted joins."""
    salts_arr = F.array([F.lit(i) for i in range(num_salts)])
    dim_exploded = dim_df.withColumn("salt", F.explode(salts_arr))
    fact_salted = fact_df.withColumn("salt", F.floor(F.rand() * num_salts))

    joined_df = fact_salted.join(dim_exploded, on=[key_col, "salt"], how="inner").drop("salt")
    result_count, duration = time_spark_action(lambda: joined_df.count())

    telemetry = {
        "mitigation": "SALTING_JOIN",
        "num_salts": num_salts,
        "execution_time_seconds": duration,
        "joined_records": result_count,
    }

    return joined_df, telemetry
