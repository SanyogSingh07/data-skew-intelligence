"""Physical partition imbalance and shuffle telemetry.

Two families of metrics live here:

1. Partition-size statistics, computed directly from the RDD (`glom`) or Spark
   partition IDs — this works everywhere and needs no extra infrastructure.
2. Shuffle read/write byte counts, pulled from the Spark UI's REST API
   (`http://<driver>:4040/api/v1/...`). This is best-effort: if the UI is
   disabled or unreachable (e.g. some CI sandboxes), those fields come back
   as `None` rather than failing the run.
"""
from __future__ import annotations

import json
import statistics
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pyspark.sql import DataFrame, SparkSession


@dataclass
class PartitionStats:
    partition_count: int
    sizes: list[int] = field(repr=False)
    max_size: int
    min_size: int
    mean_size: float
    std_size: float

    @property
    def skew_ratio(self) -> float:
        """max_partition_size / mean_partition_size — 1.0 means perfectly even."""
        return (self.max_size / self.mean_size) if self.mean_size else 0.0

    @property
    def coefficient_of_variation(self) -> float:
        """std_size / mean_size — scale-invariant partition variation."""
        return (self.std_size / self.mean_size) if self.mean_size else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "partition_count": self.partition_count,
            "max_partition_size": self.max_size,
            "min_partition_size": self.min_size,
            "mean_partition_size": round(self.mean_size, 4),
            "partition_std": round(self.std_size, 4),
            "skew_ratio": round(self.skew_ratio, 4),
            "coefficient_of_variation": round(self.coefficient_of_variation, 4),
        }


def partition_stats(df: DataFrame) -> PartitionStats:
    """Compute per-partition row counts for a DataFrame's current physical layout."""
    sizes = df.rdd.glom().map(len).collect()
    if not sizes:
        sizes = [0]
    return PartitionStats(
        partition_count=len(sizes),
        sizes=sizes,
        max_size=max(sizes),
        min_size=min(sizes),
        mean_size=statistics.fmean(sizes),
        std_size=statistics.pstdev(sizes) if len(sizes) > 1 else 0.0,
    )


def shuffle_partition_stats(df: DataFrame, key_cols: str | list[str], num_partitions: int) -> PartitionStats:
    """Partition-size statistics for the *pre-aggregation* hash-partitioned
    layout a `groupBy(key_cols)` shuffle would actually produce.
    """
    if isinstance(key_cols, str):
        keyed = df.repartition(num_partitions, key_cols)
    else:
        keyed = df.repartition(num_partitions, *key_cols)
    return partition_stats(keyed)


def _spark_ui_base_url(spark: SparkSession) -> str | None:
    try:
        sc = spark.sparkContext
        return sc.uiWebUrl
    except Exception:
        return None


def fetch_last_stage_shuffle_metrics(spark: SparkSession, timeout: float = 2.0) -> dict[str, Any]:
    """Best-effort fetch of shuffle read/write bytes for the most recently
    completed stage via the Spark UI REST API.
    """
    result = {"shuffle_read_bytes": None, "shuffle_write_bytes": None}
    base = _spark_ui_base_url(spark)
    if not base:
        return result
    try:
        app_id = spark.sparkContext.applicationId
        url = f"{base}/api/v1/applications/{app_id}/stages"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            stages = json.loads(resp.read().decode("utf-8"))
        completed = [s for s in stages if isinstance(s, dict) and s.get("status") == "COMPLETE"]
        if not completed:
            return result
        completed.sort(key=lambda s: s.get("stageId", 0), reverse=True)
        latest = completed[0]
        result["shuffle_read_bytes"] = latest.get("shuffleReadBytes")
        result["shuffle_write_bytes"] = latest.get("shuffleWriteBytes")
    except Exception:
        pass
    return result


def get_partition_metrics(df: DataFrame) -> dict[str, Any]:
    """Legacy helper: computes distribution metrics across physical Spark partitions."""
    pstats = partition_stats(df)
    return {
        "partition_count": pstats.partition_count,
        "total_records": sum(pstats.sizes),
        "min_partition_records": pstats.min_size,
        "max_partition_records": pstats.max_size,
        "mean_partition_records": round(pstats.mean_size, 2),
        "partition_std": round(pstats.std_size, 2),
        "skew_ratio": round(pstats.skew_ratio, 4),
        "cv": round(pstats.coefficient_of_variation, 4),
        "counts": pstats.sizes,
    }


def time_spark_action(action_func: Callable[[], Any]) -> tuple[Any, float]:
    """Executes a Spark action function and measures wall-clock execution time."""
    start = time.perf_counter()
    result = action_func()
    end = time.perf_counter()
    duration = end - start
    return result, round(duration, 4)
