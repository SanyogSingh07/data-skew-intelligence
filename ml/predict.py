"""Prediction / intelligent decision engine.

Loads the best trained classifier and predicts skew severity from live
execution telemetry, then hands that prediction to the deterministic
mitigation decision rule (spark/mitigation.py::choose_mitigation).
If the model is uninitialized or confidence is low, falls back to the
statistical detector.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from ml.features import FEATURE_COLUMNS
from spark.baseline import BaselineReport
from spark.config import get, resolve_path
from spark.mitigation import choose_mitigation


@dataclass
class PredictionResult:
    severity: str
    confidence: float
    probabilities: dict[str, float]
    recommended_mitigation: str


def load_best_model(model_path: str | Path | None = None) -> dict[str, Any]:
    if model_path is None:
        models_dir = resolve_path(get("paths", "results_models", default="results/models"))
        model_path = models_dir / "best_model.joblib"
        if not model_path.exists():
            model_path = models_dir / "skew_classifier.joblib"

    resolved = resolve_path(model_path)
    if not resolved.exists():
        raise FileNotFoundError(f"No trained model found at {resolved}.")

    loaded = joblib.load(resolved)
    if isinstance(loaded, dict) and "pipeline" in loaded:
        return loaded
    return {"pipeline": loaded, "labels": ["NORMAL", "LOW_SKEW", "HIGH_SKEW"], "feature_columns": FEATURE_COLUMNS}


def features_from_baseline(baseline: BaselineReport, top1_concentration: float, top5_concentration: float) -> dict[str, Any]:
    return {
        "skew_ratio": baseline.skew_ratio,
        "top1_concentration": top1_concentration,
        "top5_concentration": top5_concentration,
        "partition_count": baseline.result_partitions,
        "mean_partition_size": baseline.mean_partition_size,
        "max_partition_size": baseline.max_partition_size,
        "partition_std": baseline.partition_std,
        "execution_time_sec": baseline.execution_time_sec,
        "shuffle_read_bytes": baseline.shuffle_read_bytes or 0,
        "shuffle_write_bytes": baseline.shuffle_write_bytes or 0,
    }


def predict_severity(feature_row: dict[str, Any], bundle: dict[str, Any] | None = None) -> PredictionResult:
    try:
        bundle = bundle or load_best_model()
        pipeline = bundle["pipeline"]
        labels = bundle.get("labels", ["NORMAL", "LOW_SKEW", "HIGH_SKEW"])

        X_cols = bundle.get("feature_columns", FEATURE_COLUMNS)
        X = pd.DataFrame([{col: feature_row.get(col, 0.0) for col in X_cols}])

        pred_raw = pipeline.predict(X)[0]
        pred = str(pred_raw)
        if pred in ("0", "1", "2"):
            class_map = {"0": "NORMAL", "1": "LOW_SKEW", "2": "HIGH_SKEW"}
            pred = class_map.get(pred, "NORMAL")

        probabilities = {}
        confidence = 1.0
        if hasattr(pipeline, "predict_proba"):
            proba = pipeline.predict_proba(X)[0]
            classes = pipeline.classes_ if hasattr(pipeline, "classes_") else labels
            probabilities = {str(c): round(float(p), 4) for c, p in zip(classes, proba)}
            confidence = round(float(max(proba)), 4)

        if confidence < 0.50:
            pred = fallback_statistical_prediction_str(feature_row)

        mitigation = choose_mitigation(pred)

        return PredictionResult(
            severity=pred,
            confidence=confidence,
            probabilities=probabilities,
            recommended_mitigation=mitigation,
        )
    except FileNotFoundError:
        pred = fallback_statistical_prediction_str(feature_row)
        return PredictionResult(
            severity=pred,
            confidence=0.85,
            probabilities={},
            recommended_mitigation=choose_mitigation(pred),
        )


def fallback_statistical_prediction_str(feature_row: dict[str, Any]) -> str:
    skew_ratio = float(feature_row.get("skew_ratio", 1.0))
    top1_conc = float(feature_row.get("top1_concentration", 0.0))
    if top1_conc >= 0.50 or skew_ratio >= 2.5:
        return "HIGH_SKEW"
    elif top1_conc >= 0.20 or skew_ratio >= 1.4:
        return "LOW_SKEW"
    return "NORMAL"


def predict_skew_severity(
    feature_dict: dict[str, Any],
    model_path: str = "results/models/best_model.joblib",
) -> dict[str, Any]:
    """Legacy helper function for skew severity prediction."""
    res = predict_severity(feature_dict)
    class_id_map = {"NORMAL": 0, "LOW_SKEW": 1, "HIGH_SKEW": 2}
    return {
        "predicted_class_id": class_id_map.get(res.severity, 0),
        "predicted_class_name": res.severity,
        "confidence": res.confidence,
        "recommended_mitigation": res.recommended_mitigation,
    }


def fallback_statistical_prediction(feature_dict: dict[str, Any]) -> int:
    sev = fallback_statistical_prediction_str(feature_dict)
    return {"NORMAL": 0, "LOW_SKEW": 1, "HIGH_SKEW": 2}.get(sev, 0)


def recommend_mitigation(class_name: str) -> str:
    return choose_mitigation(class_name)
