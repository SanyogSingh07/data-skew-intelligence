from ml.features import extract_features_from_run, generate_synthetic_training_dataset
from ml.predict import predict_skew_severity
from ml.train import train_skew_classifiers
from spark.analyze_skew import analyze_data_skew
from spark.baseline import run_baseline_aggregation
from spark.generate_data import generate_skewed_dataset
from spark.mitigation import apply_salting_aggregation


def test_end_to_end_smoke(spark, tmp_path):
    # 1. Generate small dataset
    df, meta = generate_skewed_dataset(
        num_rows=500,
        skew_ratio=0.85,
        seed=42,
        spark=spark
    )
    assert df.count() == 500
    
    # 2. Run baseline aggregation & analyze telemetry
    _, telemetry = run_baseline_aggregation(df)
    analysis = analyze_data_skew(df)
    assert analysis["severity_class"] == "HIGH_SKEW"
    
    # 3. Extract ML features
    features = extract_features_from_run(analysis, telemetry)
    assert features["top1_concentration"] >= 0.80
    
    # 4. Train classifiers on small sample
    out_dir = str(tmp_path / "models")
    synth_df = generate_synthetic_training_dataset(n_samples=50, seed=42)
    train_res = train_skew_classifiers(df=synth_df, output_dir=out_dir)
    
    # 5. Predict severity & recommend mitigation
    pred_res = predict_skew_severity(features, model_path=train_res["saved_classifier_path"])
    assert pred_res["recommended_mitigation"] in ["SALTING", "REPARTITION", "NONE"]
    
    # 6. Execute mitigation
    if pred_res["recommended_mitigation"] == "SALTING":
        mit_df, mit_telemetry = apply_salting_aggregation(df, num_salts=4)
        total_mitigated = sum([row["record_count"] for row in mit_df.collect()])
        assert total_mitigated == df.count()
