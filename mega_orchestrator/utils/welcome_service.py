"""Welcome bootstrap service for agents connecting through Mega Orchestrator.

Supports hot-reload via:
- SIGHUP signal: kill -HUP <pid>
- MCP call: reload_welcome_service
- Python: importlib.reload(welcome_service)
"""

from __future__ import annotations

import importlib
import json
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_REGISTRY_ROOT = "/home/orchestration/data/welcome"

# Default paths - can be overridden via constructor or env vars
DEFAULT_MEMORY_PATHS = {
    "source_of_truth": "~/.gemini/GEMINI.md",
    "global_agents": "~/AGENTS.md",
    "standards": "~/.gemini/extensions/archive-gemini-chat-memory/MEMORY_STANDARDS.md",
    "full_archive": "HAS:/home/chat-transcripts",
    "exact_recall_tool": "search_chat_history",
    "semantic_layer": "Advanced-Memory MCP pointers",
    "raw_transcripts_in_semantic_memory": False,
}

# Environment variable mappings for paths
ENV_PATH_MAPPINGS = {
    "source_of_truth": "WELCOME_MEMORY_SOURCE_OF_TRUTH",
    "global_agents": "WELCOME_MEMORY_GLOBAL_AGENTS",
    "standards": "WELCOME_MEMORY_STANDARDS",
    "full_archive": "WELCOME_MEMORY_FULL_ARCHIVE",
    "exact_recall_tool": "WELCOME_MEMORY_EXACT_RECALL_TOOL",
    "semantic_layer": "WELCOME_MEMORY_SEMANTIC_LAYER",
}

# Hardware type constants
HW_TYPE_HAS = "has"
HW_TYPE_AGENT = "agent"


class WelcomeService:
    """Maintain agent and hardware registries and return a deterministic welcome pack."""

    def __init__(
        self,
        registry_root: Optional[str] = None,
        memory_paths: Optional[Dict[str, Any]] = None,
        has_hardware: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.registry_root = Path(
            registry_root or os.getenv("WELCOME_REGISTRY_ROOT", DEFAULT_REGISTRY_ROOT)
        )
        self.agent_registry_path = self.registry_root / "agent_registry.json"
        self.hw_registry_path = self.registry_root / "hw_registry.json"
        self.agent_hw_registry_path = self.registry_root / "agent_hw_registry.json"
        
        # Merge memory paths: defaults < env vars < constructor params
        self.memory_paths = self._build_memory_paths(memory_paths or {})
        
        # HAS hardware can be set at initialization (from Docker container)
        self.has_hardware = has_hardware or self._detect_has_hardware()

    def _build_memory_paths(self, override_paths: Dict[str, Any]) -> Dict[str, Any]:
        """Build memory paths by merging defaults, env vars, and overrides."""
        paths = DEFAULT_MEMORY_PATHS.copy()
        
        # Apply environment variable overrides
        for key, env_var in ENV_PATH_MAPPINGS.items():
            env_value = os.getenv(env_var)
            if env_value:
                paths[key] = env_value
        
        # Apply constructor overrides (highest priority)
        paths.update(override_paths)
        
        return paths

    def _detect_has_hardware(self) -> Dict[str, Any]:
        """Detect HAS server hardware from Docker container environment."""
        # Try to read from existing registry first
        if self.hw_registry_path.exists():
            registry = self._load_json(self.hw_registry_path, {})
            if registry.get("hardware"):
                return registry["hardware"]
        
        # Default HAS hardware detection (can be enhanced with psutil)
        return {
            "hostname": os.getenv("HOSTNAME", "unknown"),
            "os": os.getenv("OS", "unknown"),
            "cpu": "unknown",
            "ram_gb": 0,
            "type": HW_TYPE_HAS,
        }

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

        # Update registries
        has_hw_update = self._update_has_hw_registry(now)
        agent_hw_update = self._update_agent_hw_registry(current_hw_data or {}, agent_name, now)
        
        pack_json = {
            "agent": {
                "name": agent_name,
                "version": agent_version,
                "registry_path": str(self.agent_registry_path),
                "welcome_count": agent_record["welcome_count"],
            },
            "memory": self.memory_paths.copy(),
            "hardware": has_hw_update,  # Backwards compatible - HAS hardware
            "has_hardware": has_hw_update,  # Explicit HAS hardware
            "agent_hardware": agent_hw_update,  # Agent-specific hardware
            "semantic_context": semantic_context,
            "marketplace": {
                "enabled": True,
                "endpoint": "Mega-Orchestrator (port 7000)",
                "tools": ["skills_list", "skills_resolve", "registry_search", "registry_get_server", "catalog_validate"],
                "description": "Unified skill marketplace with 92+ skills from all agents",
            },
        }
        return {
            "welcome_markdown": self._render_markdown(pack_json),
            "welcome_json": pack_json,
        }

    def _update_has_hw_registry(self, now: str) -> Dict[str, Any]:
        """Update HAS hardware registry (read-only, never overwritten by agents)."""
        registry = self._load_json(
            self.hw_registry_path,
            {
                "version": 1,
                "updated_at": None,
                "hardware": {},
                "history": [],
            },
        )
        
        # HAS hardware is set at initialization, not by agents
        current = self.has_hardware
        previous = registry.get("hardware", {})
        changes = self._diff_dict(previous, current)
        
        if changes:
            registry["hardware"] = current
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

    def _update_agent_hw_registry(
        self, current_hw_data: Dict[str, Any], agent_name: str, now: str
    ) -> Dict[str, Any]:
        """Update agent-specific hardware registry."""
        registry = self._load_json(
            self.agent_hw_registry_path,
            {
                "version": 1,
                "updated_at": None,
                "agents": {},
                "history": [],
            },
        )
        
        # Ensure hardware data has type
        if "type" not in current_hw_data:
            current_hw_data["type"] = HW_TYPE_AGENT
        
        # Get previous state for this agent
        agents = registry.setdefault("agents", {})
        previous = agents.get(agent_name, {})
        changes = self._diff_dict(previous, current_hw_data)
        
        if changes:
            agents[agent_name] = current_hw_data
            registry["updated_at"] = now
            registry.setdefault("history", []).append({
                "updated_at": now,
                "agent": agent_name,
                "changes": changes,
            })
            registry["history"] = registry["history"][-100:]  # Keep more history for agents
            self._save_json(self.agent_hw_registry_path, registry)
        elif not self.agent_hw_registry_path.exists():
            self._save_json(self.agent_hw_registry_path, registry)
        
        return {
            "registry_path": str(self.agent_hw_registry_path),
            "updated": bool(changes),
            "changes": changes,
            "current": agents.get(agent_name, {}),
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
        marketplace = pack.get("marketplace", {})
        
        lines = [
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
        
        if marketplace.get("enabled"):
            lines.extend([
                "",
                "## Skills Marketplace",
                f"- Access via: {marketplace['endpoint']}",
                f"- Available tools: {', '.join(marketplace['tools'])}",
                f"- {marketplace['description']}",
                "- Use `skills_list` to browse available skills",
                "- Use `skills_resolve` to get skill details",
            ])
        
        return "\n".join(lines)

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


# =============================================================================
# HOT-RELOAD SUPPORT
# =============================================================================

# Module-level singleton for hot-reload
default_service: Optional[WelcomeService] = None


def get_service() -> WelcomeService:
    """Get or create the default WelcomeService instance."""
    global default_service
    if default_service is None:
        default_service = WelcomeService()
    return default_service


def reload_service() -> Dict[str, Any]:
    """Reload the WelcomeService module and create fresh instance.
    
    This function can be called via:
    - MCP tool: reload_welcome_service
    - Signal: kill -HUP <pid>
    - Python: from welcome_service import reload_service; reload_service()
    
    Returns:
        Status dict with reload result.
    """
    global default_service
    
    # Get current module
    current_module = sys.modules.get(__name__)
    if current_module is None:
        return {"success": False, "error": "Module not found in sys.modules"}
    
    try:
        # Reload the module
        importlib.reload(current_module)
        
        # Create fresh instance
        default_service = WelcomeService()
        
        return {
            "success": True,
            "message": "WelcomeService reloaded successfully",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "service_id": id(default_service),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }


def reload_welcome_service() -> Dict[str, Any]:
    """MCP-compatible wrapper for reload_service().
    
    This function can be registered as an MCP tool.
    """
    return reload_service()


# Signal handler for hot-reload
def _handle_sighup(signum: int, frame: Any) -> None:
    """Handle SIGHUP signal for hot-reload."""
    print(f"[WelcomeService] Received SIGHUP (signal {signum}), reloading...")
    result = reload_service()
    if result["success"]:
        print(f"[WelcomeService] Reload successful, new service ID: {result['service_id']}")
    else:
        print(f"[WelcomeService] Reload failed: {result.get('error')}")


# Register SIGHUP handler if available
if hasattr(signal, "SIGHUP"):
    signal.signal(signal.SIGHUP, _handle_sighup)


# Auto-initialize on import
default_service = WelcomeService()
