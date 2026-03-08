"""Helpers for reading runtime settings and secrets."""

from __future__ import annotations

import os
from pathlib import Path


def load_env(name: str, default: str | None = None) -> str | None:
    """Load a setting from *_FILE first, then from the environment."""
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        value = Path(file_path).read_text(encoding="utf-8").strip()
        if value:
            return value
        return default

    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value
