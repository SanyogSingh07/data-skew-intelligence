"""Model evaluation and metrics collection.

Computes accuracy, macro precision, macro recall, macro F1, and confusion
matrices for classification candidate models.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Sequence

import joblib
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support

from ml.features import FEATURE_COLUMNS, generate_synthetic_training_dataset


@dataclass
class EvaluationResult:
    model_name: str
    accuracy: float
    precision_macro: float
    recall_macro: float
    f1_macro: float
    confusion_matrix: list[list[int]]
    labels: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate_model(
    model_name: str,
    y_true: Sequence,
    y_pred: Sequence,
    labels: list[str] | None = None,
) -> EvaluationResult:
    """Compute standard metrics and confusion matrix for a model's predictions."""
    labels = labels or sorted(list(set(y_true) | set(y_pred)))
    acc = float(accuracy_score(y_true, y_pred))
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=labels).tolist()

    return EvaluationResult(
        model_name=model_name,
        accuracy=round(acc, 4),
        precision_macro=round(float(p), 4),
        recall_macro=round(float(r), 4),
        f1_macro=round(float(f1), 4),
        confusion_matrix=cm,
        labels=labels,
    )


def rank_models(results: list[EvaluationResult]) -> list[EvaluationResult]:
    """Rank evaluation results descending by F1 macro score."""
    return sorted(results, key=lambda r: (r.f1_macro, r.accuracy), reverse=True)


def evaluate_model_artifact(
    model_path: str = "results/models/best_model.joblib",
    test_df: pd.DataFrame | None = None,
    output_report_path: str = "results/reports/model_evaluation_report.json",
) -> dict[str, Any]:
    """Legacy helper function for evaluating model artifact."""
    if not os.path.exists(model_path):
        alt_path = "results/models/skew_classifier.joblib"
        if os.path.exists(alt_path):
            model_path = alt_path
        else:
            raise FileNotFoundError(f"Model file not found at {model_path}.")

    if test_df is None:
        test_df = generate_synthetic_training_dataset(n_samples=200, seed=123)

    loaded = joblib.load(model_path)
    model = loaded["pipeline"] if isinstance(loaded, dict) and "pipeline" in loaded else loaded

    feature_cols = [c for c in FEATURE_COLUMNS if c in test_df.columns]
    X_test = test_df[feature_cols]
    if "severity" in test_df.columns:
        y_test = test_df["severity"]
    elif "class_name" in test_df.columns:
        y_test = test_df["class_name"]
    else:
        y_test = test_df["target_class"]

    preds = model.predict(X_test)
    labels = sorted(list(set(y_test.dropna()) | set(preds)))

    report_dict: dict[str, Any] = classification_report(  # type: ignore[assignment]
        y_test, preds, output_dict=True, zero_division=0
    )
    cm = confusion_matrix(y_test, preds, labels=labels).tolist()

    macro_raw = report_dict.get("macro avg")
    macro: dict[str, Any] = macro_raw if isinstance(macro_raw, dict) else {"precision": 0, "recall": 0, "f1-score": 0}
    accuracy_val = float(report_dict.get("accuracy", 0.0)) if isinstance(report_dict.get("accuracy"), (int, float)) else 0.0

    evaluation_results = {
        "model_path": model_path,
        "test_samples": len(test_df),
        "overall_accuracy": round(accuracy_val, 4),
        "macro_avg": {
            "precision": round(float(macro.get("precision", 0.0)), 4),
            "recall": round(float(macro.get("recall", 0.0)), 4),
            "f1_score": round(float(macro.get("f1-score", 0.0)), 4),
        },
        "confusion_matrix": cm,
        "labels": [str(lbl) for lbl in labels],
    }

    os.makedirs(os.path.dirname(os.path.abspath(output_report_path)), exist_ok=True)
    with open(output_report_path, "w") as f:
        json.dump(evaluation_results, f, indent=2)

    return evaluation_results
