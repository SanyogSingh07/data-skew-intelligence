from ml.features import extract_features_from_run
from ml.predict import predict_skew_severity
from ml.train import train_skew_classifiers


def test_ml_feature_extraction_and_prediction():
    mock_eda = {
        "total_records": 100000,
        "unique_keys": 20,
        "top1_concentration": 0.70,
        "top5_concentration": 0.85,
        "std_key_frequency": 1500.0,
        "skew_score": 0.75,
        "severity_class": "HIGH_SKEW"
    }
    mock_telemetry = {
        "execution_time_seconds": 12.5,
        "input_partition_metrics": {
            "partition_count": 8,
            "max_partition_records": 70000,
            "mean_partition_records": 12500,
            "partition_std": 20000.0,
            "skew_ratio": 5.6
        }
    }

    feats = extract_features_from_run(mock_eda, mock_telemetry)
    assert "top1_concentration" in feats
    assert feats["top1_concentration"] == 0.70

    pred = predict_skew_severity(feats)
    assert "predicted_class_name" in pred
    assert pred["predicted_class_name"] in ["NORMAL", "LOW_SKEW", "HIGH_SKEW"]
    assert "recommended_mitigation" in pred


def test_ml_model_training():
    res = train_skew_classifiers()
    assert "best_model" in res
    assert "best_f1_score" in res
    assert res["best_f1_score"] >= 0.0
