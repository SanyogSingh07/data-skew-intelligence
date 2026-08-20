import math

from spark.analyze_skew import analyze_data_skew
from spark.generate_data import generate_skewed_dataset
from spark.metrics import get_partition_metrics


def test_skew_ratio_increases_with_skew(spark):
    normal_df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.10, seed=42, spark=spark)
    skewed_df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.90, seed=42, spark=spark)
    
    normal_metrics = analyze_data_skew(normal_df)
    skewed_metrics = analyze_data_skew(skewed_df)
    
    assert skewed_metrics["top1_concentration"] > normal_metrics["top1_concentration"]
    assert skewed_metrics["skew_score"] > normal_metrics["skew_score"]


def test_top1_and_top5_concentration(spark):
    df, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.60, spark=spark)
    metrics = analyze_data_skew(df)
    
    assert 0.0 <= metrics["top1_concentration"] <= 1.0
    assert 0.0 <= metrics["top5_concentration"] <= 1.0
    assert metrics["top1_concentration"] <= metrics["top5_concentration"]


def test_metrics_are_finite(spark):
    df, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.50, spark=spark)
    metrics = analyze_data_skew(df)
    
    for _k, v in metrics.items():
        if isinstance(v, (int, float)):
            assert not math.isnan(v)
            assert not math.isinf(v)


def test_severity_score_classification(spark):
    df_normal, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.10, spark=spark)
    df_high, _ = generate_skewed_dataset(num_rows=1000, skew_ratio=0.90, spark=spark)
    
    analysis_normal = analyze_data_skew(df_normal)
    analysis_high = analyze_data_skew(df_high)
    
    assert analysis_normal["severity_class"] in ["NORMAL", "LOW_SKEW"]
    assert analysis_high["severity_class"] == "HIGH_SKEW"


def test_partition_metrics_calculation(spark):
    data = [("KEY_00", 1.0), ("KEY_00", 2.0), ("KEY_01", 3.0)]
    df = spark.createDataFrame(data, ["key", "value"])
    
    p_metrics = get_partition_metrics(df)
    assert p_metrics["partition_count"] > 0
    assert p_metrics["total_records"] == 3
    assert p_metrics["skew_ratio"] >= 1.0

