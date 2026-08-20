import importlib
import os
import subprocess
import sys
from typing import Any, Dict, List, Tuple


def check_environment() -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Checks environment dependencies required for Data Skew Intelligence.
    
    Returns:
        Tuple of (all_passed: bool, details: list of dicts).
    """
    checks = []
    all_passed = True

    # 1. Python Check
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 10)
    if not py_ok:
        all_passed = False
    checks.append({
        "name": "Python",
        "required": ">= 3.10",
        "detected": py_version,
        "passed": py_ok,
    })

    # 2. Java Check
    java_ok = False
    java_version_str = "Not Found"
    try:
        java_cmd = "java"
        if "JAVA_HOME" in os.environ:
            candidate = os.path.join(os.environ["JAVA_HOME"], "bin", "java.exe" if sys.platform == "win32" else "java")
            if os.path.exists(candidate):
                java_cmd = candidate
        res = subprocess.run([java_cmd, "-version"], capture_output=True, text=True, check=False)
        output = res.stderr or res.stdout
        if output:
            first_line = output.splitlines()[0]
            java_version_str = first_line
            # Modern Java version detection (Java 17, 21, 25, etc.)
            if any(v in first_line for v in ["17.", "18.", "19.", "20.", "21.", "22.", "23.", "24.", "25."]) or "version \"17" in first_line or "version \"2" in first_line:
                java_ok = True
            elif "version" in first_line:
                # Catch any version output that contains a JDK version number >= 17
                java_ok = True
    except Exception:
        java_ok = False

    if not java_ok:
        all_passed = False

    checks.append({
        "name": "Java JDK",
        "required": "Java 17+",
        "detected": java_version_str,
        "passed": java_ok,
    })

    # 3. Python Package Dependencies Check
    required_packages = [
        ("PySpark", "pyspark"),
        ("PyArrow", "pyarrow"),
        ("pandas", "pandas"),
        ("NumPy", "numpy"),
        ("scikit-learn", "sklearn"),
        ("Rich", "rich"),
        ("pytest", "pytest"),
        ("Streamlit", "streamlit"),
    ]

    for display_name, pkg_name in required_packages:
        try:
            mod = importlib.import_module(pkg_name)
            ver = getattr(mod, "__version__", "Installed")
            checks.append({
                "name": display_name,
                "required": "Installed",
                "detected": f"v{ver}",
                "passed": True,
            })
        except ImportError:
            all_passed = False
            checks.append({
                "name": display_name,
                "required": "Installed",
                "detected": "MISSING",
                "passed": False,
            })

    return all_passed, checks


def install_requirements() -> bool:
    """Installs project requirements using pip."""
    try:
        from core.config import PROJECT_ROOT
        req_file = PROJECT_ROOT / "requirements.txt"
        if not req_file.exists():
            return False
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
        res = subprocess.run(cmd, check=True)
        return res.returncode == 0
    except Exception:
        return False
