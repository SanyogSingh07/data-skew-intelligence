"""Central configuration loader.

Every module reads settings from `config.yaml` at the project root through
this module instead of hard-coding constants, so experiments stay
reproducible and tunable from one place.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped,import]

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config.yaml"


@functools.lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    """Load and cache config.yaml as a plain dict."""
    if not CONFIG_PATH.exists():
        return {}
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f) or {}


def get(*keys: str, default: Any = None) -> Any:
    """Fetch a nested config value, e.g. get('spark', 'shuffle_partitions')."""
    cfg = load_config()
    node = cfg
    for key in keys:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def resolve_path(relative: str | Path) -> Path:
    """Resolve a path relative to the project root."""
    p = Path(relative)
    return p if p.is_absolute() else PROJECT_ROOT / p
