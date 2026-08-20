import os

from ml.evaluate import evaluate_model_artifact
from ml.features import extract_features_from_run, generate_synthetic_training_dataset
from ml.predict import predict_skew_severity, recommend_mitigation
from ml.train import train_skew_classifiers
from spark.analyze_skew import analyze_data_skew
from spark.baseline import run_baseline_aggregation
from spark.generate_data import generate_skewed_dataset


def test_feature_extraction(spark):
    df, _ = generate_skewed_dataset(num_rows=500, skew_ratio=0.70, spark=spark)
    _, telemetry = run_baseline_aggregation(df)
    analysis = analyze_data_skew(df)
    
    feats = extract_features_from_run(analysis, telemetry)
    for col in ["skew_ratio", "top1_concentration", "partition_count", "target_class", "class_name"]:
        assert col in feats


def test_model_training_and_artifacts(tmp_path):
    out_dir = str(tmp_path / "models")
    synth_df = generate_synthetic_training_dataset(n_samples=100, seed=42)
    res = train_skew_classifiers(df=synth_df, output_dir=out_dir)
    
    assert "logistic_regression" in res["models"]
    assert "random_forest" in res["models"]
    assert os.path.exists(res["saved_classifier_path"])


def test_model_predictions(tmp_path):
    out_dir = str(tmp_path / "models")
    synth_df = generate_synthetic_training_dataset(n_samples=100, seed=42)
    res = train_skew_classifiers(df=synth_df, output_dir=out_dir)
    
    sample_feat = {
        "skew_ratio": 3.5,
        "top1_concentration": 0.85,
        "top5_concentration": 0.90,
        "partition_count": 8,
        "mean_partition_size": 1000.0,
        "max_partition_size": 3500.0,
        "partition_std": 800.0,
        "cv": 0.8,
        "execution_time_seconds": 1.5
    }
    
    pred = predict_skew_severity(sample_feat, model_path=res["saved_classifier_path"])
    assert pred["predicted_class_name"] in ["NORMAL", "LOW_SKEW", "HIGH_SKEW"]
    assert pred["recommended_mitigation"] in ["NONE", "REPARTITION", "SALTING"]


def test_model_evaluation_metrics(tmp_path):
    out_dir = str(tmp_path / "models")
    report_path = str(tmp_path / "report.json")
    synth_df = generate_synthetic_training_dataset(n_samples=100, seed=42)
    res = train_skew_classifiers(df=synth_df, output_dir=out_dir)
    
    eval_res = evaluate_model_artifact(model_path=res["saved_classifier_path"], output_report_path=report_path)
    assert 0.0 <= eval_res["overall_accuracy"] <= 1.0
    assert os.path.exists(report_path)


def test_mitigation_decision_policy():
    assert recommend_mitigation("NORMAL") == "NONE"
    assert recommend_mitigation("LOW_SKEW") == "REPARTITION"
    assert recommend_mitigation("HIGH_SKEW") == "SALTING"
