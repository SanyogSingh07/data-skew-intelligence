import os
from pathlib import Path

# Base Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
GENERATED_DATA_DIR = DATA_DIR / "generated"
RESULTS_DIR = PROJECT_ROOT / "results"
LATEST_RESULTS_DIR = RESULTS_DIR / "latest"
EXPERIMENTS_RESULTS_DIR = RESULTS_DIR / "experiments"
MODELS_DIR = PROJECT_ROOT / "models"
LOGS_DIR = PROJECT_ROOT / "logs"

# Default Dataset File Paths
DEFAULT_PARQUET_PATH = GENERATED_DATA_DIR / "skew_70.parquet"
QUICK_PARQUET_PATH = GENERATED_DATA_DIR / "skew_quick.parquet"

# Experiment Configuration Defaults
DEFAULT_ROWS = 100_000
QUICK_ROWS = 10_000
DEFAULT_SKEW_RATIO = 0.70
DEFAULT_SEED = 42
DEFAULT_NUM_KEYS = 20
DEFAULT_NUM_PARTITIONS = 8

# Execution Flags
RUN_ML = True
RUN_TESTS = True
RUN_DASHBOARD = False


def ensure_directories():
    """Ensures all essential directory structures exist."""
    for d in [DATA_DIR, GENERATED_DATA_DIR, RESULTS_DIR, LATEST_RESULTS_DIR, EXPERIMENTS_RESULTS_DIR, MODELS_DIR, LOGS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
