from __future__ import annotations

import os
from pathlib import Path


def load_secret(name: str) -> str | None:
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        value = Path(file_path).read_text(encoding="utf-8").strip()
        return value or None

    value = os.getenv(name, "").strip()
    return value or None
