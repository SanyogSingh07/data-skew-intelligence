import json
import os
import shutil
import time
from typing import Any, Dict

from core.config import EXPERIMENTS_RESULTS_DIR, LATEST_RESULTS_DIR, RESULTS_DIR


def compare_results(baseline_telemetry: Dict[str, Any], mitigated_telemetry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compares baseline and post-mitigation execution telemetry.
    
    Returns:
        Dictionary of comparison metrics (improvements, before/after values).
    """
    b_tel = baseline_telemetry or {}
    m_tel = mitigated_telemetry or {}

    before_raw = b_tel.get("execution_time_sec") or b_tel.get("execution_time_seconds") or 0.0
    after_raw = m_tel.get("execution_time_sec") or m_tel.get("execution_time_seconds") or 0.0

    before_time = float(before_raw)
    after_time = float(after_raw)
    
    if before_time > 0:
        pct_imp = round(((before_time - after_time) / before_time) * 100.0, 2)
    else:
        pct_imp = 0.0
        
    base_part = b_tel.get("partition_metrics") or b_tel.get("input_partition_metrics") or {}
    mit_part = m_tel.get("partition_metrics") or m_tel.get("input_partition_metrics") or {}
    
    base_max = b_tel.get("max_partition_size") or base_part.get("max_partition_records") or 0
    mit_max = m_tel.get("max_partition_size") or mit_part.get("max_partition_records") or 0

    base_std = b_tel.get("partition_std") or base_part.get("partition_std") or 0.0
    mit_std = m_tel.get("partition_std") or mit_part.get("partition_std") or 0.0

    return {
        "baseline_execution_time": round(before_time, 2),
        "mitigated_execution_time": round(after_time, 2),
        "improvement_pct": pct_imp,
        "baseline_max_partition_records": int(base_max),
        "mitigated_max_partition_records": int(mit_max),
        "baseline_partition_std": round(float(base_std), 2),
        "mitigated_partition_std": round(float(mit_std), 2),
    }


def save_run_results(
    config_dict: Dict[str, Any],
    profile_dict: Dict[str, Any],
    baseline_dict: Dict[str, Any],
    mitigated_dict: Dict[str, Any],
    ml_metrics_dict: Dict[str, Any],
    predictions_records: Any,
    summary_dict: Dict[str, Any]
) -> str:
    """
    Persists all experiment metrics to a timestamped directory and updates results/latest.
    
    Returns:
        Path string to the created timestamped directory.
    """
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    run_dir = RESULTS_DIR / timestamp
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Save manifest.json according to specification
    exp_id = summary_dict.get("experiment_id", f"EXP-{int(time.time())}")
    manifest = {
        "experiment_id": exp_id,
        "status": "success",
        "rows": summary_dict.get("rows", config_dict.get("rows", 0)),
        "skew_ratio": summary_dict.get("skew_ratio", config_dict.get("skew_ratio", 0.0)),
        "severity": summary_dict.get("predicted_class", "NORMAL"),
        "model": summary_dict.get("ml_model", ml_metrics_dict.get("best_model", "N/A")),
        "mitigation": summary_dict.get("mitigation", "NONE"),
        "timestamp": summary_dict.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S")),
    }
    with open(run_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, default=str)

    # Save individual JSON artifacts
    artifacts = {
        "config.json": config_dict,
        "dataset_profile.json": profile_dict,
        "baseline_metrics.json": baseline_dict,
        "mitigated_metrics.json": mitigated_dict,
        "ml_metrics.json": ml_metrics_dict,
        "summary.json": summary_dict
    }
    
    for filename, content in artifacts.items():
        with open(run_dir / filename, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, default=str)
            
    # Save predictions.csv if present
    if predictions_records is not None:
        try:
            import pandas as pd
            if isinstance(predictions_records, pd.DataFrame):
                predictions_records.to_csv(run_dir / "predictions.csv", index=False)
            elif isinstance(predictions_records, list):
                pd.DataFrame(predictions_records).to_csv(run_dir / "predictions.csv", index=False)
        except Exception:
            pass

    # Generate raw CSV data and PNG charts using the visualization exporter
    try:
        from visualization.exporter import export_experiment_visualizations
        export_experiment_visualizations(
            run_dir=run_dir,
            profile_dict=profile_dict,
            baseline_dict=baseline_dict,
            mitigated_dict=mitigated_dict,
        )
    except Exception as ex:
        import logging
        logging.getLogger("SkewCTL").warning(f"Chart export failed: {ex}")

    # Save experiment summary in results/experiments/ for historical UI
    EXPERIMENTS_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXPERIMENTS_RESULTS_DIR / f"{exp_id}.json", "w", encoding="utf-8") as f:
        json.dump(summary_dict, f, indent=2, default=str)

    # Sync to results/latest/
    if LATEST_RESULTS_DIR.exists():
        shutil.rmtree(LATEST_RESULTS_DIR, ignore_errors=True)
    shutil.copytree(run_dir, LATEST_RESULTS_DIR)
    
    return str(run_dir)
