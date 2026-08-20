"""Data Integrity Validation before Visualization.

Ensures underlying experimental and distribution data is non-empty, numerically
valid, and consistent before passing it to chart rendering routines. Never fabricates
or alters data.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Union

logger = logging.getLogger("SkewCTL.Visualization")


def validate_key_distribution(data: Dict[str, int]) -> Dict[str, int]:
    """Validates top key frequency mapping."""
    if not isinstance(data, dict) or not data:
        raise ValueError("No key distribution data available for plotting.")
    
    clean_data = {}
    for k, v in data.items():
        if not isinstance(v, (int, float)) or v < 0:
            raise ValueError(f"Invalid record count '{v}' for key '{k}'")
        # pyrefly: ignore [unnecessary-type-conversion]
        clean_data[k] = int(v)
        
    return clean_data


def validate_partition_distribution(sizes: List[int], name: str = "partition distribution") -> List[int]:
    """Validates physical partition row count array."""
    if not sizes or not isinstance(sizes, (list, tuple)):
        raise ValueError(f"No {name} data available for plotting.")
    
    int_sizes = []
    for val in sizes:
        if not isinstance(val, (int, float)) or val < 0:
            raise ValueError(f"Invalid partition size '{val}' in {name}.")
        # pyrefly: ignore [unnecessary-type-conversion]
        int_sizes.append(int(val))
        
    if len(set(int_sizes)) == 1 and len(int_sizes) > 1:
        logger.warning(
            f"WARNING: All measured {name} sizes are identical ({int_sizes[0]} records). "
            "No partition imbalance is visible in this run."
        )
        print(f"[WARNING] All measured {name} sizes are identical ({int_sizes[0]} records).")

    return int_sizes


def validate_experiment_series(experiments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validates multi-run experiment observation series."""
    if not experiments:
        raise ValueError("No experiment series observations available for plotting.")
    
    valid_series = []
    for idx, exp in enumerate(experiments):
        if not isinstance(exp, dict):
            continue
        skew = exp.get("skew") if exp.get("skew") is not None else exp.get("skew_ratio")
        runtime = exp.get("runtime") if exp.get("runtime") is not None else exp.get("baseline_execution_time", exp.get("execution_time_sec"))
        partition_cv = exp.get("partition_cv") if exp.get("partition_cv") is not None else exp.get("coefficient_of_variation")
        
        if skew is None or runtime is None:
            continue
            
        valid_series.append({
            "skew": float(skew),
            "runtime": float(runtime),
            "partition_cv": float(partition_cv) if partition_cv is not None else 0.0,
            "experiment_id": exp.get("experiment_id", f"EXP-{idx}")
        })
        
    if not valid_series:
        raise ValueError("Experiment series lacks valid numeric observation metrics.")
        
    return valid_series
