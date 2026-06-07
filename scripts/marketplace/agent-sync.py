#!/usr/bin/env python3
"""
Agent Sync - Distributes skills from marketplace to all agents
Creates symlinks or copies skills to agent directories
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Set

# Agent skill target directories
AGENT_TARGETS = {
    "pi": Path.home() / ".pi" / "agent" / "skills",
    "codex": Path.home() / ".codex" / "skills",
    "gemini": Path.home() / ".gemini" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "agents": Path.home() / ".agents" / "skills",
}

# Skills to sync (from marketplace catalog)
SYNCED_SKILLS = [
    "update-all-agents",
    "mega-orchestrator-mcp",
    "archive-global-chat-memory",
    "core-rules",
]

# Source directories for each skill
SKILL_SOURCES = {
    "update-all-agents": Path.home() / ".pi" / "agent" / "skills" / "update-all-agents",
    "mega-orchestrator-mcp": Path.home() / ".pi" / "agent" / "skills" / "mega-orchestrator-mcp",
    "archive-global-chat-memory": Path.home() / ".pi" / "skills" / "archive-global-chat-memory",
    "core-rules": Path.home() / ".agents" / "skills" / "core-rules",
}


def sync_skill(skill_name: str, source: Path, targets: Dict[str, Path], dry_run: bool = False) -> List[str]:
    """Sync a skill to all agent targets using symlinks"""
    actions = []
    
    if not source.exists():
        print(f"  ⚠️  Source not found: {source}")
        return actions
    
    for agent, target_dir in targets.items():
        target = target_dir / skill_name
        
        # Skip if already a symlink to the same source
        if target.is_symlink():
            try:
                if target.resolve() == source.resolve():
                    actions.append(f"  ✓ {agent}: Already synced")
                    continue
            except OSError:
                pass
        
        # Create target directory if needed
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove existing directory/symlink
        if target.exists() or target.is_symlink():
            if dry_run:
                actions.append(f"  → {agent}: Would remove existing {target}")
            else:
                if target.is_dir() and not target.is_symlink():
                    shutil.rmtree(target)
                else:
                    target.unlink()
        
        # Create symlink
        if dry_run:
            actions.append(f"  → {agent}: Would create symlink {target} -> {source}")
        else:
            try:
                target.symlink_to(source)
                actions.append(f"  ✓ {agent}: Synced {skill_name}")
            except OSError as e:
                actions.append(f"  ✗ {agent}: Failed to create symlink: {e}")
    
    return actions


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Sync skills from marketplace to agents")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--skill", help="Sync specific skill only")
    parser.add_argument("--list", action="store_true", help="List syncable skills")
    args = parser.parse_args()
    
    if args.list:
        print("\n📦 Syncable Skills:")
        for skill in SYNCED_SKILLS:
            source = SKILL_SOURCES.get(skill)
            if source and source.exists():
                print(f"  ✓ {skill}")
            else:
                print(f"  ✗ {skill} (source not found)")
        return 0
    
    print("\n🔄 Agent Skill Sync")
    print("=" * 50)
    
    skills_to_sync = [args.skill] if args.skill else SYNCED_SKILLS
    
    for skill_name in skills_to_sync:
        print(f"\n📦 Syncing: {skill_name}")
        source = SKILL_SOURCES.get(skill_name)
        
        if not source:
            print(f"  ⚠️  No source defined for {skill_name}")
            continue
        
        actions = sync_skill(skill_name, source, AGENT_TARGETS, dry_run=args.dry_run)
        for action in actions:
            print(action)
    
    print("\n" + "=" * 50)
    
    if args.dry_run:
        print("🔍 Dry run complete. No changes made.")
    else:
        print("✅ Sync complete!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
