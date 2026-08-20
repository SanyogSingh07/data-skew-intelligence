import ctypes
import os
import sys
from pathlib import Path

# Ensure project root and .venv site-packages are in sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_VENV_SITE = _PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if _VENV_SITE.exists() and str(_VENV_SITE) not in sys.path:
    sys.path.insert(0, str(_VENV_SITE))


def _to_short_path(path: str) -> str:
    """Converts Windows long path with spaces to 8.3 short path representation."""
    if not path or sys.platform != "win32":
        return path
    try:
        from ctypes import wintypes
        GetShortPathNameW = ctypes.windll.kernel32.GetShortPathNameW
        GetShortPathNameW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.DWORD]
        GetShortPathNameW.restype = wintypes.DWORD
        buf = ctypes.create_unicode_buffer(500)
        GetShortPathNameW(path, buf, 500)
        return buf.value if buf.value else path
    except Exception:
        return path

def _get_valid_java_home() -> str | None:
    """Finds a valid JDK installation directory containing bin/java.exe on Windows."""
    current = os.environ.get("JAVA_HOME")
    if current and os.path.exists(os.path.join(current, "bin", "java.exe")):
        return current

    search_dirs = [
        r"C:\Program Files\Eclipse Adoptium",
        r"C:\Program Files\Java",
        r"C:\Program Files (x86)\Java",
    ]
    for top in search_dirs:
        if os.path.exists(top):
            for entry in os.listdir(top):
                candidate = os.path.join(top, entry)
                if os.path.exists(os.path.join(candidate, "bin", "java.exe")):
                    return candidate
    return current


def _init_spark_env():
    """Initializes SPARK_HOME and JAVA_HOME environment variables safely on Windows."""
    venv_python = _PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    py_exec = str(venv_python) if venv_python.exists() else sys.executable
    py_exec = _to_short_path(py_exec)

    os.environ["PYSPARK_PYTHON"] = py_exec
    os.environ["PYSPARK_DRIVER_PYTHON"] = py_exec
    if sys.platform == "win32":
        java_home = _get_valid_java_home()
        if java_home:
            os.environ["JAVA_HOME"] = _to_short_path(java_home)
        try:
            import pyspark
            pyspark_dir = os.path.dirname(pyspark.__file__)
            os.environ["SPARK_HOME"] = _to_short_path(pyspark_dir)
        except ImportError:
            pass

_init_spark_env()

import contextlib

from pyspark.sql import SparkSession


@contextlib.contextmanager
def _silence_stderr_fd():
    """Temporarily suppresses low-level C stderr noise (Java JVM startup warnings)."""
    try:
        stderr_fd = sys.stderr.fileno()
        saved_fd = os.dup(stderr_fd)
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)
        try:
            yield
        finally:
            os.dup2(saved_fd, stderr_fd)
            os.close(saved_fd)
    except Exception:
        yield


def get_spark_session(
    app_name: str | None = None,
    master: str | None = None,
    shuffle_partitions: int | None = None,
    adaptive_execution: bool | None = None,
    driver_memory: str = "2g",
    log_level: str = "ERROR"
) -> SparkSession:
    """
    Creates or retrieves a configured PySpark SparkSession.
    """
    from spark import config as cfg_module

    app_name = app_name or cfg_module.get("spark", "app_name", default="data-skew-intelligence")
    master = master or cfg_module.get("spark", "master", default="local[*]")
    if shuffle_partitions is None:
        shuffle_partitions = cfg_module.get("spark", "shuffle_partitions", default=8)
    if adaptive_execution is None:
        adaptive_execution = cfg_module.get("spark", "adaptive_query_execution", default=False)

    # Java 17/21/25 module export flags to ensure clean execution on modern JDKs
    java_opts = (
        "--add-opens=java.base/java.lang=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.invoke=ALL-UNNAMED "
        "--add-opens=java.base/java.lang.reflect=ALL-UNNAMED "
        "--add-opens=java.base/java.io=ALL-UNNAMED "
        "--add-opens=java.base/java.net=ALL-UNNAMED "
        "--add-opens=java.base/java.nio=ALL-UNNAMED "
        "--add-opens=java.base/java.util=ALL-UNNAMED "
        "--add-opens=java.base/java.util.concurrent=ALL-UNNAMED "
        "--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED "
        "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED "
        "-Djdk.reflect.useDirectMethodHandle=false "
        "-Dorg.apache.commons.logging.Log=org.apache.commons.logging.impl.NoOpLog"
    )

    builder = (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.shuffle.partitions", str(shuffle_partitions))
        .config("spark.sql.adaptive.enabled", "true" if adaptive_execution else "false")
        .config("spark.driver.memory", driver_memory)
        .config("spark.driver.extraJavaOptions", java_opts)
        .config("spark.executor.extraJavaOptions", java_opts)
        .config("spark.ui.enabled", "true")
        .config("spark.ui.port", "4040")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.hadoop.native.lib", "false")
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
        .config("spark.sql.parquet.int96RebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.int96RebaseModeInWrite", "CORRECTED")
        .config("spark.sql.parquet.nanosAsLong", "true")
    )

    active = SparkSession.getActiveSession()
    if active is not None:
        try:
            if active.sparkContext is None or active.sparkContext._jsc is None:
                active.stop()
                SparkSession._instantiatedSession = None
                SparkSession._activeSession = None
        except Exception:
            SparkSession._instantiatedSession = None
            SparkSession._activeSession = None

    if log_level != "INFO":
        with _silence_stderr_fd():
            spark = builder.getOrCreate()
    else:
        spark = builder.getOrCreate()
    try:
        sc = getattr(spark, "sparkContext", None)
        if sc:
            sc.setLogLevel(log_level if log_level else "ERROR")
            jvm = getattr(sc, "_jvm", None)
            if jvm and hasattr(jvm, "org"):
                log4j = jvm.org.apache.log4j
                log4j.LogManager.getRootLogger().setLevel(log4j.Level.ERROR)
                log4j.LogManager.getLogger("org").setLevel(log4j.Level.ERROR)
                log4j.LogManager.getLogger("akka").setLevel(log4j.Level.ERROR)
    except Exception:
        pass
    return spark


def stop_spark_session(spark: SparkSession | None = None, force: bool = False) -> None:
    """Stops the active SparkSession if present."""
    if os.environ.get("PYTEST_CURRENT_TEST") and not force:
        return
    if spark is not None:
        try:
            spark.stop()
        except Exception:
            pass
    else:
        active = SparkSession.getActiveSession()
        if active:
            try:
                active.stop()
            except Exception:
                pass
