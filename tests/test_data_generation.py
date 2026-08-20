from pyspark.sql import functions as F

from spark.generate_data import generate_skewed_dataset


def test_generated_dataset_has_requested_size(spark):
    rows = 1000
    skew = 0.70
    df, meta = generate_skewed_dataset(num_rows=rows, skew_ratio=skew, spark=spark)
    
    assert df.count() == rows
    assert meta["num_rows"] == rows
    assert meta["skew_ratio"] == skew
    for col in ["record_id", "key", "value", "category", "timestamp"]:
        assert col in df.columns


def test_generated_dataset_no_null_keys(spark):
    df, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.80, spark=spark)
    null_count = df.filter(F.col("key").isNull()).count()
    assert null_count == 0


def test_generator_is_reproducible(spark):
    df1, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.70, seed=42, spark=spark)
    df2, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.70, seed=42, spark=spark)
    
    counts1 = {row["key"]: row["count"] for row in df1.groupBy("key").count().collect()}
    counts2 = {row["key"]: row["count"] for row in df2.groupBy("key").count().collect()}
    
    assert counts1 == counts2


def test_skew_concentration_levels(spark):
    rows = 1000
    for target_skew in [0.10, 0.50, 0.90]:
        df, meta = generate_skewed_dataset(num_rows=rows, skew_ratio=target_skew, spark=spark)
        top1_count = df.filter(F.col("key") == "KEY_00000").count()
        actual_ratio = top1_count / float(rows)
        assert abs(actual_ratio - target_skew) <= 0.05
