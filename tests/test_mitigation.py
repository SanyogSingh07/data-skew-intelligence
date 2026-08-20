from spark.baseline import run_baseline_aggregation
from spark.generate_data import generate_skewed_dataset
from spark.mitigation import (
    apply_repartition,
    apply_salting_aggregation,
    apply_salting_groupby,
    apply_salting_join,
)


def test_repartition_preserves_record_count(spark):
    df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.80, spark=spark)
    rep_df, _ = apply_repartition(df, num_partitions=8)

    assert rep_df.count() == df.count()


def test_salting_preserves_records(spark):
    df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.80, spark=spark)
    salt_agg, telemetry = apply_salting_aggregation(df, num_salts=4)

    total_records = sum([row["record_count"] for row in salt_agg.collect()])
    assert total_records == df.count()


def test_salting_aggregation_mathematical_equivalence(spark):
    df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.75, seed=123, spark=spark)

    base_agg, _ = run_baseline_aggregation(df)
    base_results = {row["key"]: row["record_count"] for row in base_agg.collect()}

    salt_agg, _ = apply_salting_aggregation(df, num_salts=4)
    salt_results = {row["key"]: row["record_count"] for row in salt_agg.collect()}

    assert base_results == salt_results


def test_salting_groupby_equivalence(spark):
    df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.75, seed=123, spark=spark)

    base_grouped = df.groupBy("key").count()
    base_map = {row["key"]: row["count"] for row in base_grouped.collect()}

    salted_grouped = apply_salting_groupby(df, buckets=4)
    salted_map = {row["key"]: row["count"] for row in salted_grouped.collect()}

    assert base_map == salted_map


def test_salting_join_correctness(spark):
    fact_df, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.70, seed=42, spark=spark)
    unique_keys = [row["key"] for row in fact_df.select("key").distinct().collect()]
    dim_data = [(k, f"Category_Desc_{k}") for k in unique_keys]
    dim_df = spark.createDataFrame(dim_data, ["key", "description"])

    joined_df, telemetry = apply_salting_join(fact_df, dim_df, num_salts=4)
    assert joined_df.count() == fact_df.count()
