"""ML training pipeline.

Raw experiment table -> validation -> feature selection -> train/test split
-> train three candidate models -> evaluate -> select the best by F1.

Trains models in increasing complexity order (Logistic Regression ->
Decision Tree -> Random Forest) and picks a winner by measured
performance rather than assuming Random Forest wins by default.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

from ml.evaluate import EvaluationResult, evaluate_model, rank_models
from ml.features import FEATURE_COLUMNS, LABEL_COLUMN, generate_synthetic_training_dataset
from spark.config import get, resolve_path


@dataclass
class TrainingOutcome:
    best_model_name: str
    best_model_path: Path
    results: list[EvaluationResult]


def _validate(df: pd.DataFrame) -> pd.DataFrame:
    missing_cols = [c for c in FEATURE_COLUMNS + [LABEL_COLUMN] if c not in df.columns]
    if missing_cols:
        # Fallback if legacy dataset format
        if "severity" not in df.columns and "class_name" in df.columns:
            df["severity"] = df["class_name"]
        elif "severity" not in df.columns and "target_class" in df.columns:
            class_map = {0: "NORMAL", 1: "LOW_SKEW", 2: "HIGH_SKEW"}
            df["severity"] = df["target_class"].map(class_map)
        if "execution_time_sec" not in df.columns and "execution_time_seconds" in df.columns:
            df["execution_time_sec"] = df["execution_time_seconds"]
        if "shuffle_read_bytes" not in df.columns:
            df["shuffle_read_bytes"] = 0
        if "shuffle_write_bytes" not in df.columns:
            df["shuffle_write_bytes"] = 0

    missing_cols = [c for c in FEATURE_COLUMNS + [LABEL_COLUMN] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Experiment dataset missing required columns: {missing_cols}")

    before = len(df)
    df = df.dropna(subset=FEATURE_COLUMNS + [LABEL_COLUMN]).reset_index(drop=True)
    dropped = before - len(df)
    if dropped:
        print(f"[ml.train] Dropped {dropped} row(s) with missing values.")
    return df


def _candidate_models() -> dict[str, Pipeline]:
    random_state = get("ml", "random_state", default=42)
    return {
        "logistic_regression": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, random_state=random_state)),
            ]
        ),
        "decision_tree": Pipeline(
            [("clf", DecisionTreeClassifier(max_depth=6, random_state=random_state))]
        ),
        "random_forest": Pipeline(
            [("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=random_state, n_jobs=-1))]
        ),
    }


def train_and_select(
    dataset_path: str | Path | None = None,
    save: bool = True,
    spark: Any = None,
) -> TrainingOutcome:
    if dataset_path is None:
        dataset_path = resolve_path(
            get("paths", "experiment_dataset", default="results/metrics/experiment_dataset.csv")
        )

    resolved_path = resolve_path(dataset_path)
    if not resolved_path.exists():
        # Fallback to generating dataset if file doesn't exist yet
        from ml.features import build_feature_dataset
        df = build_feature_dataset(save=save, spark=spark)
    else:
        df = pd.read_csv(resolved_path)

    df = _validate(df)

    X = df[FEATURE_COLUMNS]
    y = df[LABEL_COLUMN]
    labels = sorted(y.unique().tolist())

    test_size = get("ml", "test_size", default=0.20)
    random_state = get("ml", "random_state", default=42)
    cv_folds = get("ml", "cv_folds", default=5)

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    results = []
    fitted_models = {}
    for name, pipeline in _candidate_models().items():
        pipeline.fit(X_train, y_train)
        preds = pipeline.predict(X_test)
        result = evaluate_model(name, y_test, preds, labels)

        min_class_count = y_train.value_counts().min()
        if min_class_count >= cv_folds:
            cv_scores = cross_val_score(pipeline, X, y, cv=cv_folds, scoring="f1_macro")
            result_dict = result.to_dict()
            result_dict["cv_f1_macro_mean"] = round(float(cv_scores.mean()), 4)
            result_dict["cv_f1_macro_std"] = round(float(cv_scores.std()), 4)
        else:
            result_dict = result.to_dict()
            result_dict["cv_f1_macro_mean"] = None
            result_dict["cv_f1_macro_std"] = None

        results.append((result, result_dict))
        fitted_models[name] = pipeline

    ranked = rank_models([r for r, _ in results])
    best_name = ranked[0].model_name
    best_pipeline = fitted_models[best_name]

    outcome = TrainingOutcome(
        best_model_name=best_name,
        best_model_path=resolve_path(get("paths", "results_models", default="results/models")) / f"{best_name}.joblib",
        results=[r for r, _ in results],
    )

    if save:
        models_dir = resolve_path(get("paths", "results_models", default="results/models"))
        models_dir.mkdir(parents=True, exist_ok=True)
        for name, pipeline in fitted_models.items():
            joblib.dump(pipeline, models_dir / f"{name}.joblib")

        best_bundle = {"pipeline": best_pipeline, "labels": labels, "feature_columns": FEATURE_COLUMNS}
        joblib.dump(best_bundle, models_dir / "best_model.joblib")
        joblib.dump(best_pipeline, models_dir / "skew_classifier.joblib")

        reports_dir = resolve_path(get("paths", "results_reports", default="results/reports"))
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_payload = {
            "best_model": best_name,
            "labels": labels,
            "results": [d for _, d in results],
        }
        with open(reports_dir / "ml_comparison.json", "w") as f:
            json.dump(report_payload, f, indent=2)

    return outcome


def train_skew_classifiers(
    df: pd.DataFrame | None = None,
    output_dir: str = "results/models",
    test_size: float = 0.20,
    random_state: int = 42,
) -> dict[str, Any]:
    """Legacy helper for training models."""
    if df is None:
        df = generate_synthetic_training_dataset(n_samples=500, seed=random_state)

    df_val = _validate(df.copy())
    X = df_val[FEATURE_COLUMNS]
    y = df_val[LABEL_COLUMN]

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=stratify
    )

    models = {
        "logistic_regression": Pipeline([("scaler", StandardScaler()), ("clf", LogisticRegression(max_iter=500, random_state=random_state))]),
        "decision_tree": Pipeline([("clf", DecisionTreeClassifier(max_depth=6, random_state=random_state))]),
        "random_forest": Pipeline([("clf", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=random_state, n_jobs=-1))]),
    }

    results = {}
    best_f1 = -1.0
    best_model_name = "random_forest"
    best_model_obj = None

    os.makedirs(output_dir, exist_ok=True)

    for name, model in models.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        result = evaluate_model(name, y_test, preds)

        model_path = os.path.join(output_dir, f"{name}.joblib")
        joblib.dump(model, model_path)

        results[name] = {
            "accuracy": result.accuracy,
            "precision": result.precision_macro,
            "recall": result.recall_macro,
            "f1_score": result.f1_macro,
            "confusion_matrix": result.confusion_matrix,
            "artifact_path": model_path,
        }

        if result.f1_macro > best_f1:
            best_f1 = result.f1_macro
            best_model_name = name
            best_model_obj = model

    default_best_path = os.path.join(output_dir, "skew_classifier.joblib")
    joblib.dump(best_model_obj, default_best_path)

    best_bundle = {"pipeline": best_model_obj, "labels": sorted(y.unique().tolist()), "feature_columns": FEATURE_COLUMNS}
    joblib.dump(best_bundle, os.path.join(output_dir, "best_model.joblib"))

    return {
        "models": results,
        "best_model": best_model_name,
        "best_f1_score": round(best_f1, 4),
        "saved_classifier_path": default_best_path,
    }


if __name__ == "__main__":
    outcome = train_and_select()
    print("Training Complete! Best model:", outcome.best_model_name)
