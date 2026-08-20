"""EDA and statistical skew detection.

Computes key-frequency EDA statistics and a transparent, weighted
`SkewScore` that maps onto three severity classes (NORMAL / LOW_SKEW /
HIGH_SKEW) before any ML model gets involved — a statistical baseline the
classifier can be compared against.
"""
from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from typing import Any

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

from spark.config import get, resolve_path
from spark.metrics import PartitionStats, get_partition_metrics, shuffle_partition_stats


@dataclass
class KeyFrequencyStats:
    distinct_keys: int
    total_rows: int
    mean_frequency: float
    median_frequency: float
    std_frequency: float
    max_frequency: int
    min_frequency: int
    top1_concentration: float
    top5_concentration: float
    top_keys: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SkewAssessment:
    skew_score: float
    severity: str
    skew_ratio: float
    coefficient_of_variation_norm: float
    top1_concentration: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def key_frequency_stats(df: DataFrame, key_col: str = "key") -> KeyFrequencyStats:
    """EDA over the key column: frequency distribution and concentration."""
    counts_df = df.groupBy(key_col).count().orderBy(F.desc("count"))
    rows = counts_df.collect()
    counts = [r["count"] for r in rows]
    top_keys_map = {str(r[key_col]): int(r["count"]) for r in rows[:20]}
    total_rows = sum(counts)
    distinct_keys = len(counts)

    top1 = counts[0] if counts else 0
    top5 = sum(counts[:5]) if counts else 0

    return KeyFrequencyStats(
        distinct_keys=distinct_keys,
        total_rows=total_rows,
        mean_frequency=statistics.fmean(counts) if counts else 0.0,
        median_frequency=statistics.median(counts) if counts else 0.0,
        std_frequency=statistics.pstdev(counts) if len(counts) > 1 else 0.0,
        max_frequency=max(counts) if counts else 0,
        min_frequency=min(counts) if counts else 0,
        top1_concentration=(top1 / total_rows) if total_rows else 0.0,
        top5_concentration=(top5 / total_rows) if total_rows else 0.0,
        top_keys=top_keys_map,
    )


def _normalize(value: float, cap: float) -> float:
    """Clamp value/cap into [0, 1]."""
    if cap <= 0:
        return 0.0
    return max(0.0, min(1.0, value / cap))


def classify_severity(score: float) -> str:
    normal_max = get("skew_score", "thresholds", "normal_max", default=0.30)
    low_skew_max = get("skew_score", "thresholds", "low_skew_max", default=0.60)
    if score <= normal_max:
        return "NORMAL"
    if score <= low_skew_max:
        return "LOW_SKEW"
    return "HIGH_SKEW"


def compute_skew_score(
    key_stats: KeyFrequencyStats,
    part_stats: PartitionStats,
) -> SkewAssessment:
    """Composite, weighted SkewScore over three project-defined signals:

        SkewScore = w1 * norm(skew_ratio) + w2 * norm(coefficient_of_variation) + w3 * top1_concentration

    Coefficient of variation (std/mean of partition sizes) is used instead
    of raw partition-size variance because variance scales with dataset
    size — a fixed absolute cap on it would saturate for large datasets
    regardless of actual skew, while CV stays comparable across dataset
    sizes. Weights and normalization caps live in config.yaml so they stay
    documented and adjustable rather than being magic numbers in code.
    """
    w1 = get("skew_score", "w1", default=0.4)
    w2 = get("skew_score", "w2", default=0.3)
    w3 = get("skew_score", "w3", default=0.3)
    ratio_cap = get("skew_score", "skew_ratio_cap", default=10.0)
    cv_cap = get("skew_score", "cv_cap", default=1.5)

    ratio_norm = _normalize(part_stats.skew_ratio, ratio_cap)
    cv_norm = _normalize(part_stats.coefficient_of_variation, cv_cap)
    top1 = key_stats.top1_concentration

    score = w1 * ratio_norm + w2 * cv_norm + w3 * top1
    score = max(0.0, min(1.0, score))

    return SkewAssessment(
        skew_score=round(score, 4),
        severity=classify_severity(score),
        skew_ratio=round(part_stats.skew_ratio, 4),
        coefficient_of_variation_norm=round(cv_norm, 4),
        top1_concentration=round(top1, 4),
    )


def analyze(spark: SparkSession, input_path: str | Any) -> tuple[KeyFrequencyStats, SkewAssessment]:
    """Convenience entry point: load a parquet dataset and run full EDA + scoring."""
    resolved = resolve_path(input_path)
    df = spark.read.parquet(str(resolved))
    k_stats = key_frequency_stats(df)
    shuffle_partitions = int(spark.conf.get("spark.sql.shuffle.partitions") or "8")
    p_stats = shuffle_partition_stats(df, "key", shuffle_partitions)
    assessment = compute_skew_score(k_stats, p_stats)
    return k_stats, assessment


def analyze_data_skew(df: DataFrame, key_col: str = "key") -> dict[str, Any]:
    """Legacy helper for performing EDA and statistical skew detection on DataFrame."""
    k_stats = key_frequency_stats(df, key_col=key_col)
    p_stats = shuffle_partition_stats(df, key_col, 8)
    part_metrics = p_stats.to_dict()
    assessment = compute_skew_score(k_stats, p_stats)
    return {
        "total_records": k_stats.total_rows,
        "unique_keys": k_stats.distinct_keys,
        "top1_key_count": k_stats.max_frequency,
        "top1_concentration": k_stats.top1_concentration,
        "top5_concentration": k_stats.top5_concentration,
        "mean_key_frequency": k_stats.mean_frequency,
        "std_key_frequency": k_stats.std_frequency,
        "median_key_frequency": k_stats.median_frequency,
        "iqr_key_frequency": 0.0,
        "partition_metrics": part_metrics,
        "skew_score": assessment.skew_score,
        "severity_class": assessment.severity,
        "statistical_severity_score": assessment.skew_score,
        "statistical_class": assessment.severity,
    }
