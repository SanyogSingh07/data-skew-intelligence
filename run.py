"""SINGLE-ENTRYPOINT PROJECT RUNNER

Data Skew Intelligence — Antigravity One-Click Execution Runner

Usage:
    python run.py             # Standard full experiment execution
    python run.py --menu      # Directly launch interactive Results Console
    python run.py --no-menu   # Non-interactive mode (for CI and automation)
    python run.py --verbose   # Verbose diagnostic console output
    python run.py --check     # Verify environment & dependencies only
    python run.py --quick     # Quick mode with small dataset (10,000 rows)
    python run.py --clean     # Clean temporary files & run fresh pipeline
    python run.py --dashboard # Launch Streamlit UI
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root and .venv site-packages are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

VENV_SITE = PROJECT_ROOT / ".venv" / "Lib" / "site-packages"
if VENV_SITE.exists() and str(VENV_SITE) not in sys.path:
    sys.path.insert(0, str(VENV_SITE))

# Ensure UTF-8 output encoding on Windows consoles
for stream in (sys.stdout, sys.stderr):
    reconfig = getattr(stream, "reconfigure", None)
    if callable(reconfig):
        try:
            reconfig(encoding="utf-8", errors="replace")
        except Exception:
            pass

import warnings
warnings.filterwarnings("ignore")

from cli.menu import run_results_console
from core.pipeline import run_pipeline


def main():
    parser = argparse.ArgumentParser(
        description="⚡ SkewCTL: Single-Entrypoint Data Skew Intelligence Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run.py
  python run.py --menu
  python run.py --no-menu
  python run.py --verbose
  python run.py --check
  python run.py --quick
  python run.py --clean
  python run.py --dashboard
"""
    )
    parser.add_argument(
        "--menu",
        action="store_true",
        help="Launch the interactive Results Console directly"
    )
    parser.add_argument(
        "--no-menu",
        action="store_true",
        help="Bypass interactive menu prompts (for CI/automation)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed diagnostic logging output in terminal"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate Java JDK 17+, PySpark, Python packages, and environment readiness"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run fast smoke execution using a small dataset (10,000 rows)"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove old datasets, temporary Spark output, logs, and results before running"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Launch the Streamlit visualization dashboard"
    )
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Install project dependencies from requirements.txt"
    )
    parser.add_argument(
        "--export-site",
        action="store_true",
        help="Generate standalone static HTML/CSS/JS web dashboard for GitHub Pages hosting"
    )

    args = parser.parse_args()

    # Direct menu launch mode
    if args.menu:
        run_results_console()
        sys.exit(0)

    # Standalone site export mode (if requested independently)
    if args.export_site and not (args.quick or args.clean or args.setup):
        from visualization.site_generator import export_static_site
        site_dir = export_static_site()
        print(f"✓ Static site successfully generated at: {site_dir}")
        sys.exit(0)

    # Default execution: run quick pipeline if no specific mode selected
    is_default = not (args.check or args.quick or args.clean or args.dashboard or args.setup or args.export_site)
    if is_default:
        args.quick = True

    while True:
        exit_code = run_pipeline(
            quick=args.quick,
            clean=args.clean,
            dashboard=args.dashboard,
            check_only=args.check,
            setup=args.setup,
            verbose=args.verbose,
            export_site=args.export_site,
        )

        if exit_code != 0 or args.no_menu or args.check or args.setup or args.dashboard:
            sys.exit(exit_code)

        # Interactive menu prompt for standard terminal execution
        print()
        try:
            ans = input("Open Results Console? [Y/n]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            ans = "n"

        if ans in ("", "y", "yes"):
            rerun_requested = run_results_console()
            if rerun_requested:
                continue  # Loop again to re-run pipeline
        break

    sys.exit(0)


if __name__ == "__main__":
    main()

