import pytest

from spark.baseline import run_baseline_aggregation
from spark.generate_data import generate_skewed_dataset
from spark.session import get_spark_session


@pytest.fixture(scope="module")
def spark():
    session = get_spark_session(app_name="TestSparkSuite")
    yield session


def test_spark_session_creation(spark):
    assert spark is not None
    assert spark.sparkContext is not None


def test_spark_baseline_aggregation(spark):
    df, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.60, spark=spark)
    agg_df, telemetry = run_baseline_aggregation(df)
    assert agg_df is not None
    assert "execution_time_seconds" in telemetry
    assert "input_partition_metrics" in telemetry
    assert telemetry["input_records"] == 500
