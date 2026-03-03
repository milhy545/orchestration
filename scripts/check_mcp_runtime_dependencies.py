#!/usr/bin/env python3
"""Validate MCP runtime dependency policy for critical packages."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MCP_DIR = ROOT / "mcp-servers"

CRITICAL_BASELINE = {
    "fastapi": "fastapi>=0.121.0,<0.122.0",
    "uvicorn": "uvicorn>=0.24.0,<0.25.0",
    "uvicorn[standard]": "uvicorn[standard]>=0.24.0,<0.25.0",
    "pydantic": "pydantic>=2.5.0,<3.0.0",
    "starlette": "starlette>=0.49.1,<0.50.0",
    "prometheus-fastapi-instrumentator": "prometheus-fastapi-instrumentator>=6.1.0,<6.2.0",
}

BOUNDED_RANGE_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+(?:\[[^\]]+\])?>=[^,\s]+,<[^,\s]+$")


def normalize_req_line(line: str) -> str:
    return line.split("#", 1)[0].strip()


def package_name(requirement: str) -> str:
    match = re.match(r"^([A-Za-z0-9_.-]+(?:\[[^\]]+\])?)", requirement)
    return match.group(1) if match else requirement


def main() -> int:
    errors: list[str] = []

    for req_file in sorted(MCP_DIR.glob("*/requirements.txt")):
        lines = [normalize_req_line(line) for line in req_file.read_text().splitlines()]
        requirements = [line for line in lines if line]
        req_map = {package_name(req): req for req in requirements}

        if "fastapi" not in req_map:
            continue

        service = req_file.parent.name

        required = ["fastapi", "pydantic", "starlette", "prometheus-fastapi-instrumentator"]
        has_uvicorn = "uvicorn" in req_map or "uvicorn[standard]" in req_map

        if not has_uvicorn:
            errors.append(f"{service}: missing uvicorn/uvicorn[standard] pin")

        for pkg in required:
            if pkg not in req_map:
                errors.append(f"{service}: missing required critical dependency '{pkg}'")

        for pkg in required:
            req = req_map.get(pkg)
            if req and not BOUNDED_RANGE_PATTERN.match(req):
                errors.append(f"{service}: '{req}' must be a bounded range (>=...,<...)")

        for uv_pkg in ("uvicorn", "uvicorn[standard]"):
            uv_req = req_map.get(uv_pkg)
            if uv_req and not BOUNDED_RANGE_PATTERN.match(uv_req):
                errors.append(f"{service}: '{uv_req}' must be a bounded range (>=...,<...)")

    if errors:
        print("Dependency policy violations found:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("All MCP runtime dependency policies passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
