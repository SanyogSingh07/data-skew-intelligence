import sys
from pathlib import Path

# Ensure project root and .venv site-packages are in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_VENV_SITE = _PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))

import pytest

from spark.session import _init_spark_env, get_spark_session, stop_spark_session

# Guarantee environment paths are initialized before SparkSession creation
_init_spark_env()


@pytest.fixture(scope="session")
def spark():
    """
    Session-scoped PySpark SparkSession fixture for fast, lightweight testing.
    """
    session = get_spark_session(
        app_name="DataSkewIntelligenceTests",
        master="local[2]",
        shuffle_partitions=4,
        adaptive_execution=False,
        driver_memory="1g",
        log_level="ERROR"
    )
    yield session
    stop_spark_session(session, force=True)
