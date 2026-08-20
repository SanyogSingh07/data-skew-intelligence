from typing import Any, Dict, List, Tuple
from pyspark.sql import DataFrame
from spark.analyze_skew import analyze_data_skew


def validate_dataset(df: DataFrame, required_cols: List[str] | None = None) -> Tuple[bool, List[str]]:
    """
    Validates dataset integrity before Spark analysis:
    - Non-empty check
    - Required columns exist
    - Null check on primary keys
    """
    if required_cols is None:
        required_cols = ["record_id", "key", "value"]

    errors = []
    
    # Check count
    count = df.count()
    if count == 0:
        errors.append("Dataset is empty (0 records).")

    # Check columns
    existing_cols = df.columns
    for col in required_cols:
        if col not in existing_cols:
            errors.append(f"Required column '{col}' is missing.")

    # Check nulls on key column if present
    if "key" in existing_cols:
        null_keys = df.filter(df["key"].isNull()).count()
        if null_keys > 0:
            errors.append(f"Key column contains {null_keys} null values.")

    return len(errors) == 0, errors


def profile_dataset(df: DataFrame, key_col: str = "key") -> Dict[str, Any]:
    """
    Profiles key frequency distribution and physical partition metrics.
    """
    return analyze_data_skew(df, key_col=key_col)
