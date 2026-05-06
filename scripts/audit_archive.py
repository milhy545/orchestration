#!/usr/bin/env python3
"""Audit script for the Mega-Orchestrator chat archive and welcome registry.

Checks:
  1. Chat transcript archive on HAS (/home/chat-transcripts)
  2. Agent registry — which agents received a welcome pack and when
  3. HW registry — is hardware data present and how old is it?
  4. MEMORY_STANDARDS.md — is the canonical standards file in place?

Usage:
    python scripts/audit_archive.py [--registry-root PATH] [--archive-root PATH]

Exit codes:
    0  — all checks passed
    1  — one or more warnings / missing items
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# Defaults (can be overridden via env or CLI)
# ---------------------------------------------------------------------------

DEFAULT_REGISTRY_ROOT = os.getenv(
    "WELCOME_REGISTRY_ROOT", "/home/orchestration/data/welcome"
)
DEFAULT_ARCHIVE_ROOT = os.getenv("CHAT_TRANSCRIPTS_ROOT", "/home/chat-transcripts")
MEMORY_STANDARDS_PATH = Path(
    os.getenv(
        "MEMORY_STANDARDS_PATH",
        os.path.expanduser(
            "~/.gemini/extensions/archive-gemini-chat-memory/MEMORY_STANDARDS.md"
        ),
    )
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"_load_error": str(exc)}


def _fmt_age(ts_str: str | None) -> str:
    """Return human-readable age from an ISO-8601 timestamp string."""
    if not ts_str:
        return "never"
    try:
        import datetime

        ts = datetime.datetime.fromisoformat(ts_str.rstrip("Z"))
        delta = datetime.datetime.utcnow() - ts
        hours = int(delta.total_seconds() // 3600)
        if hours < 1:
            return f"{int(delta.total_seconds() // 60)}m ago"
        if hours < 48:
            return f"{hours}h ago"
        return f"{hours // 24}d ago"
    except Exception:
        return ts_str


# ---------------------------------------------------------------------------
# Individual audit checks
# ---------------------------------------------------------------------------


def check_archive(archive_root: str) -> Dict[str, Any]:
    """Count transcript directories and manifests in the HAS archive root."""
    root = Path(archive_root)
    result: Dict[str, Any] = {"root": str(root), "accessible": root.is_dir()}
    if not result["accessible"]:
        result["warning"] = "Archive root is not accessible from this host."
        return result

    dirs = [p for p in root.iterdir() if p.is_dir()]
    manifests = list(root.rglob("manifest.json"))
    result["session_dirs"] = len(dirs)
    result["manifest_files"] = len(manifests)
    result["missing_manifests"] = len(dirs) - len(manifests)
    if result["missing_manifests"] > 0:
        result["warning"] = (
            f"{result['missing_manifests']} session dirs lack a manifest.json"
        )
    return result


def check_agent_registry(registry_root: str) -> Dict[str, Any]:
    """Report which agents have received a welcome pack."""
    path = Path(registry_root) / "agent_registry.json"
    result: Dict[str, Any] = {"path": str(path), "exists": path.is_file()}
    if not result["exists"]:
        result["warning"] = (
            "agent_registry.json not found — no agent has been welcomed yet."
        )
        return result

    data = _load_json(path)
    if "_load_error" in data:
        result["error"] = data["_load_error"]
        return result

    agents: Dict[str, Any] = data.get("agents", {})
    result["agent_count"] = len(agents)
    rows: List[Dict[str, Any]] = []
    for name, info in sorted(agents.items()):
        rows.append(
            {
                "agent": name,
                "welcome_count": info.get("welcome_count", 0),
                "last_seen": _fmt_age(info.get("last_seen")),
                "version": info.get("agent_version") or "unknown",
            }
        )
    result["agents"] = rows
    if not rows:
        result["warning"] = "Registry exists but no agents are recorded."
    return result


def check_hw_registry(registry_root: str) -> Dict[str, Any]:
    """Report whether hardware data is present and how stale it is."""
    path = Path(registry_root) / "hw_registry.json"
    result: Dict[str, Any] = {"path": str(path), "exists": path.is_file()}
    if not result["exists"]:
        result["warning"] = (
            "hw_registry.json not found — call agent_welcome to auto-populate it."
        )
        return result

    data = _load_json(path)
    if "_load_error" in data:
        result["error"] = data["_load_error"]
        return result

    hw = data.get("hardware", {})
    updated_at = data.get("updated_at")
    result["hardware_keys"] = sorted(hw.keys())
    result["updated_at"] = updated_at
    result["age"] = _fmt_age(updated_at)
    result["history_entries"] = len(data.get("history", []))

    if not hw:
        result["warning"] = "hw_registry.json exists but hardware section is empty."
    elif not updated_at:
        result["warning"] = "hw_registry.json has no updated_at — data may be stale."
    return result


def check_memory_standards(path: Path) -> Dict[str, Any]:
    """Verify that MEMORY_STANDARDS.md exists at the expected location."""
    result: Dict[str, Any] = {"path": str(path), "exists": path.is_file()}
    if result["exists"]:
        result["size_bytes"] = path.stat().st_size
    else:
        result["warning"] = "MEMORY_STANDARDS.md not found. Expected at: " + str(path)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print("=" * 60)


def _print_result(label: str, data: Dict[str, Any]) -> bool:
    """Print one check result. Returns True if there is a warning/error."""
    has_issue = "warning" in data or "error" in data
    status = "⚠️ " if has_issue else "✅"
    print(f"\n{status} {label}")
    for key, val in data.items():
        if key in {"agents"}:
            for row in val:
                print(
                    f"     • {row['agent']}  (seen {row['welcome_count']}x,"
                    f" last: {row['last_seen']}, v{row['version']})"
                )
        elif key not in {"_load_error"}:
            print(f"   {key}: {val}")
    return has_issue


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--registry-root",
        default=DEFAULT_REGISTRY_ROOT,
        help="Welcome registry directory (default: %(default)s)",
    )
    parser.add_argument(
        "--archive-root",
        default=DEFAULT_ARCHIVE_ROOT,
        help="Chat transcript archive root (default: %(default)s)",
    )
    parser.add_argument(
        "--memory-standards",
        default=str(MEMORY_STANDARDS_PATH),
        help="Path to MEMORY_STANDARDS.md (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    issues = 0

    _section("1. Chat Transcript Archive")
    issues += _print_result("Archive root", check_archive(args.archive_root))

    _section("2. Agent Welcome Registry")
    issues += _print_result("Agent registry", check_agent_registry(args.registry_root))

    _section("3. Hardware Registry")
    issues += _print_result("HW registry", check_hw_registry(args.registry_root))

    _section("4. Memory Standards Document")
    issues += _print_result(
        "MEMORY_STANDARDS.md", check_memory_standards(Path(args.memory_standards))
    )

    print(f"\n{'=' * 60}")
    if issues:
        print(f"  Result: {issues} issue(s) found — review warnings above.")
    else:
        print("  Result: all checks passed ✅")
    print("=" * 60)

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
