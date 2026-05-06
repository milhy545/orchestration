"""Welcome bootstrap service for agents connecting through Mega Orchestrator."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_REGISTRY_ROOT = "/home/orchestration/data/welcome"
MEMORY_STANDARDS_PATH = (
    "/home/milhy777/.gemini/extensions/archive-gemini-chat-memory/MEMORY_STANDARDS.md"
)


class WelcomeService:
    """Maintain agent and hardware registries and return a deterministic welcome pack."""

    def __init__(self, registry_root: Optional[str] = None) -> None:
        self.registry_root = Path(
            registry_root or os.getenv("WELCOME_REGISTRY_ROOT", DEFAULT_REGISTRY_ROOT)
        )
        self.agent_registry_path = self.registry_root / "agent_registry.json"
        self.hw_registry_path = self.registry_root / "hw_registry.json"

    def welcome(
        self,
        *,
        agent_name: str,
        agent_version: Optional[str] = None,
        current_hw_data: Optional[Dict[str, Any]] = None,
        semantic_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        agent_name = agent_name.strip()
        if not agent_name:
            return {"error": "agent_name is required"}

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        self.registry_root.mkdir(parents=True, exist_ok=True)

        agent_registry = self._load_json(self.agent_registry_path, {"version": 1, "agents": {}})
        agent_record = agent_registry.setdefault("agents", {}).setdefault(
            agent_name,
            {"first_seen": now, "welcome_count": 0},
        )
        agent_record["last_seen"] = now
        agent_record["agent_version"] = agent_version or agent_record.get("agent_version")
        agent_record["welcome_count"] = int(agent_record.get("welcome_count", 0)) + 1
        self._save_json(self.agent_registry_path, agent_registry)

        hw_update = self._update_hw_registry(current_hw_data or {}, now)
        pack_json = {
            "agent": {
                "name": agent_name,
                "version": agent_version,
                "registry_path": str(self.agent_registry_path),
                "welcome_count": agent_record["welcome_count"],
            },
            "memory": {
                "source_of_truth": "~/.gemini/GEMINI.md",
                "global_agents": "~/AGENTS.md",
                "standards": MEMORY_STANDARDS_PATH,
                "full_archive": "HAS:/home/chat-transcripts",
                "exact_recall_tool": "search_chat_history",
                "semantic_layer": "Advanced-Memory MCP pointers",
                "raw_transcripts_in_semantic_memory": False,
            },
            "hardware": hw_update,
            "semantic_context": semantic_context,
        }
        return {
            "welcome_markdown": self._render_markdown(pack_json),
            "welcome_json": pack_json,
        }

    def _update_hw_registry(self, current_hw_data: Dict[str, Any], now: str) -> Dict[str, Any]:
        registry = self._load_json(
            self.hw_registry_path,
            {
                "version": 1,
                "updated_at": None,
                "hardware": {},
                "history": [],
            },
        )
        previous = registry.get("hardware", {})
        changes = self._diff_dict(previous, current_hw_data)
        if changes:
            registry["hardware"] = current_hw_data
            registry["updated_at"] = now
            registry.setdefault("history", []).append({"updated_at": now, "changes": changes})
            registry["history"] = registry["history"][-50:]
            self._save_json(self.hw_registry_path, registry)
        elif not self.hw_registry_path.exists():
            self._save_json(self.hw_registry_path, registry)
        return {
            "registry_path": str(self.hw_registry_path),
            "updated": bool(changes),
            "changes": changes,
            "current": registry.get("hardware", {}),
        }

    def _diff_dict(self, previous: Dict[str, Any], current: Dict[str, Any]) -> List[Dict[str, Any]]:
        changes: List[Dict[str, Any]] = []
        keys = sorted(set(previous) | set(current))
        for key in keys:
            old_value = previous.get(key)
            new_value = current.get(key)
            if old_value != new_value:
                changes.append({"field": key, "old": old_value, "new": new_value})
        return changes

    def _render_markdown(self, pack: Dict[str, Any]) -> str:
        agent = pack["agent"]
        memory = pack["memory"]
        hardware = pack["hardware"]
        return "\n".join(
            [
                f"# Welcome, {agent['name']}",
                "",
                f"- Agent version: {agent.get('version') or 'unknown'}",
                f"- Source of truth: `{memory['source_of_truth']}`",
                f"- Global agent rules: `{memory['global_agents']}`",
                f"- Memory standards: `{memory['standards']}`",
                f"- Full transcript archive: `{memory['full_archive']}`",
                f"- Exact recall MCP tool: `{memory['exact_recall_tool']}`",
                f"- Semantic layer: {memory['semantic_layer']}",
                "- Do not store raw transcripts in semantic memory; store HAS pointers only.",
                f"- HW registry updated: {hardware['updated']}",
            ]
        )

    def _load_json(self, path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
        if not path.is_file():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def _save_json(self, path: Path, payload: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
