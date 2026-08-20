"""Controlled synthetic data generation.

Generates a dataset with a deliberately controlled key-concentration level
so that Spark execution behavior can be studied as a function of
*distribution* (skew) rather than dataset size, which is held constant.

Skew model
----------
A small "hot" subset of keys holds `skew` fraction of all rows. The remaining
rows are spread uniformly across the remaining keys. `skew=0.10` is therefore
close to uniform, and `skew=0.90` means a handful of keys dominate the
dataset — the classic "hot key" scenario that causes Spark stragglers during
groupBy/shuffle.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from pyspark.sql import DataFrame, SparkSession

from spark.config import get, resolve_path
from spark.session import get_spark_session


@dataclass
class GenerationResult:
    output_path: Path
    rows: int
    skew: float
    num_keys: int
    num_hot_keys: int


def generate_dataset(
    rows: int | None = None,
    skew: float = 0.10,
    output: str | Path | None = None,
    num_keys: int | None = None,
    seed: int | None = None,
) -> GenerationResult:
    """Generate a parquet dataset with the requested key-concentration level.

    Args:
        rows: total number of records. Defaults to config `experiment.rows`.
        skew: fraction of rows funneled into the hot-key subset, in [0, 1).
        output: destination parquet path. Auto-derived if not given.
        num_keys: total distinct key cardinality. Defaults to config value.
        seed: RNG seed for reproducibility. Defaults to config value.

    Returns:
        GenerationResult describing what was written.
    """
    if not (0.0 <= skew < 1.0):
        raise ValueError(f"skew must be in [0, 1), got {skew}")

    rows = rows or get("experiment", "rows", default=100_000)
    num_keys = num_keys or get("experiment", "num_keys", default=200)
    seed = seed if seed is not None else get("experiment", "seed", default=42)
    categories = get("experiment", "categories", default=["A", "B", "C", "D", "E"])

    rng = np.random.default_rng(seed)

    num_hot_keys = 1  # classic "hot key" scenario: one dominant key concentrates the load
    all_keys = np.array([f"KEY_{i:05d}" for i in range(num_keys)])
    hot_keys = all_keys[:num_hot_keys]
    cold_keys = all_keys[num_hot_keys:]

    num_hot_rows = round(rows * skew)
    num_cold_rows = rows - num_hot_rows

    hot_assignments = rng.choice(hot_keys, size=num_hot_rows) if num_hot_rows > 0 else np.array([])
    cold_assignments = (
        rng.choice(cold_keys, size=num_cold_rows) if num_cold_rows > 0 else np.array([])
    )

    key_column = np.concatenate([hot_assignments, cold_assignments])
    rng.shuffle(key_column)

    record_ids = np.array([f"rec_{i:08d}" for i in range(rows)])
    values = rng.normal(loc=100.0, scale=25.0, size=rows).round(2)
    category_column = rng.choice(categories, size=rows)
    start = pd.Timestamp("2026-01-01")
    timestamps = start + pd.to_timedelta(rng.integers(0, 60 * 60 * 24 * 180, size=rows), unit="s")

    df = pd.DataFrame(
        {
            "record_id": record_ids,
            "key": key_column,
            "value": values,
            "category": category_column,
            "timestamp": pd.to_datetime(timestamps).floor("ms"),
        }
    )

    if output is None:
        skew_pct = round(skew * 100)
        out_dir = resolve_path(get("paths", "data_generated", default="data/generated"))
        output = out_dir / f"skew_{skew_pct}.parquet"
    output = resolve_path(output) if not isinstance(output, Path) else output
    output.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(output, index=False, engine="pyarrow", coerce_timestamps="ms")

    return GenerationResult(
        output_path=output,
        rows=rows,
        skew=skew,
        num_keys=num_keys,
        num_hot_keys=num_hot_keys,
    )


def generate_matrix(
    skew_levels: list[float] | None = None,
    rows: int | None = None,
    seed: int | None = None,
) -> list[GenerationResult]:
    """Generate the full standard set of datasets (normal_10 ... skew_90)."""
    skew_levels = skew_levels or get("experiment", "skew_levels", default=[0.10, 0.30, 0.50, 0.70, 0.90])
    return [generate_dataset(rows=rows, skew=level, seed=seed) for level in skew_levels]


def generate_skewed_dataset(
    num_rows: int = 100000,
    skew_ratio: float = 0.70,
    num_unique_keys: int = 100,
    seed: int = 42,
    spark: SparkSession | None = None,
    output_path: str | None = None,
) -> tuple[DataFrame, dict[str, Any]]:
    """Legacy helper for generating a synthetic skewed dataset."""
    spark = spark or get_spark_session()
    res = generate_dataset(
        rows=num_rows,
        skew=skew_ratio,
        output=output_path,
        num_keys=num_unique_keys,
        seed=seed,
    )
    df_spark = spark.read.parquet(str(res.output_path))
    metadata = {
        "num_rows": res.rows,
        "skew_ratio": res.skew,
        "hot_key_count": round(res.rows * res.skew),
        "num_unique_keys": res.num_keys,
        "seed": seed,
        "output_path": str(res.output_path),
    }
    return df_spark, metadata


if __name__ == "__main__":
    spark = get_spark_session()
    res = generate_dataset(rows=100000, skew=0.70)
    print("Generated dataset result:", res)
