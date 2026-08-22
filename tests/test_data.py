from data.generator import generate_dataset
from data.profiler import profile_dataset, validate_dataset


def test_dataset_generation_and_validation(spark):
    df, meta = generate_dataset(num_rows=1000, skew_ratio=0.70, spark=spark, force_rebuild=True)
    assert df is not None
    assert meta["num_rows"] == 1000
    assert meta["skew_ratio"] == 0.70

    valid, errors = validate_dataset(df)
    assert valid, f"Validation errors: {errors}"


def test_dataset_profiling(spark):
    df, _ = generate_dataset(num_rows=1000, skew_ratio=0.70, spark=spark)
    profile = profile_dataset(df)
    assert profile["total_records"] == 1000
    assert profile["unique_keys"] > 0
    assert "skew_score" in profile
    assert profile["severity_class"] in ["NORMAL", "LOW_SKEW", "HIGH_SKEW"]
