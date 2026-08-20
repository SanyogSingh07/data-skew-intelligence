import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from pyspark.sql import DataFrame, SparkSession

from core.config import DEFAULT_NUM_KEYS, DEFAULT_PARQUET_PATH, DEFAULT_ROWS, DEFAULT_SEED, DEFAULT_SKEW_RATIO
from spark.generate_data import generate_skewed_dataset as _generate_skewed_dataset


def generate_dataset(
    num_rows: int = DEFAULT_ROWS,
    skew_ratio: float = DEFAULT_SKEW_RATIO,
    num_unique_keys: int = DEFAULT_NUM_KEYS,
    seed: int = DEFAULT_SEED,
    output_path: Optional[str | Path] = None,
    spark: Optional[SparkSession] = None,
    force_rebuild: bool = False
) -> Tuple[DataFrame, Dict[str, Any]]:
    """
    Generates or loads the synthetic skewed Parquet dataset.
    
    Args:
        num_rows: Total rows count.
        skew_ratio: Primary key concentration.
        num_unique_keys: Distinct keys count.
        seed: Random seed.
        output_path: Target Parquet file path (defaults to data/generated/skew_70.parquet).
        spark: Active SparkSession.
        force_rebuild: Force dataset regeneration.
        
    Returns:
        Tuple of (Spark DataFrame, metadata dict).
    """
    if output_path is None:
        target_path = DEFAULT_PARQUET_PATH
    else:
        target_path = Path(output_path)

    # Check if target dataset file already exists and rebuild is not forced
    if not force_rebuild and target_path.exists():
        if spark is None:
            from spark.session import get_spark_session
            spark = get_spark_session()
        try:
            clean_str_path = str(target_path.resolve()).replace("\\", "/")
            df = spark.read.parquet(clean_str_path)
            meta = {
                "num_rows": df.count(),
                "skew_ratio": skew_ratio,
                "output_path": str(target_path),
                "loaded_existing": True
            }
            return df, meta
        except Exception:
            pass  # Fall back to rebuilding if read fails

    # Generate new dataset
    return _generate_skewed_dataset(
        num_rows=num_rows,
        skew_ratio=skew_ratio,
        num_unique_keys=num_unique_keys,
        seed=seed,
        spark=spark,
        output_path=str(target_path)
    )
