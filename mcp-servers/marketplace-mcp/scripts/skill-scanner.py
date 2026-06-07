#!/usr/bin/env python3
"""
Skill Scanner - Discovers all agent skills across the PC
Scans: Pi, Codex, Gemini, Claude, Antigravity, and skills.sh ecosystem
Outputs: Unified catalog for marketplace-mcp
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Agent skill directories
AGENT_SKILL_DIRS = {
    "pi": [
        Path.home() / ".pi" / "agent" / "skills",
        Path.home() / ".pi" / "skills",
    ],
    "codex": [
        Path.home() / ".codex" / "skills",
    ],
    "gemini": [
        Path.home() / ".gemini" / "skills",
    ],
    "claude": [
        Path.home() / ".claude" / "skills",
        Path.home() / ".claude" / "projects" / "skills",
    ],
    "agents": [
        Path.home() / ".agents" / "skills",
    ],
    "antigravity": [
        Path.home() / ".antigravity" / "skills",
    ],
}

# Marketplace catalog path
CATALOG_PATH = Path(__file__).parent.parent / "catalog"
SKILLS_INDEX = CATALOG_PATH / "skills-index.json"


def scan_skill_dir(skill_dir: Path, agent: str) -> List[Dict[str, Any]]:
    """Scan a directory for skills (SKILL.md or skill.md)"""
    skills = []
    
    if not skill_dir.exists():
        return skills
    
    for item in skill_dir.iterdir():
        if not item.is_dir():
            continue
        
        # Skip hidden directories and symlinks to avoid duplicates
        if item.name.startswith(".") or item.is_symlink():
            continue
        
        skill_md = item / "SKILL.md"
        if not skill_md.exists():
            skill_md = item / "skill.md"
        
        if skill_md.exists():
            skill_info = parse_skill_md(skill_md, agent, item)
            if skill_info:
                skills.append(skill_info)
    
    return skills


def parse_skill_md(path: Path, agent: str, skill_dir: Path) -> Optional[Dict[str, Any]]:
    """Parse SKILL.md frontmatter and content"""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"  Warning: Cannot read {path}: {e}", file=sys.stderr)
        return None
    
    # Extract frontmatter (simple YAML-like parser)
    frontmatter = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            try:
                # Simple key: value parsing for frontmatter
                for line in parts[1].strip().split("\n"):
                    if ":" in line:
                        key, _, value = line.partition(":")
                        key = key.strip().strip('"')
                        value = value.strip().strip('"')
                        if value:
                            frontmatter[key] = value
            except Exception:
                pass
    
    # Extract description from frontmatter or first paragraph
    description = frontmatter.get("description", "")
    if not description:
        # Get first non-empty paragraph
        lines = content.split("\n")
        in_frontmatter = content.startswith("---")
        for line in lines:
            if in_frontmatter:
                if line.strip() == "---":
                    in_frontmatter = False
                continue
            if line.strip() and not line.startswith("#"):
                description = line.strip()[:200]
                break
    
    # Calculate content hash for deduplication
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
    
    # Determine tags from path and frontmatter
    tags = frontmatter.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    
    # Auto-tag based on agent and directory name
    tags.append(agent)
    if "mcp" in skill_dir.name.lower():
        tags.append("mcp")
    if "update" in skill_dir.name.lower():
        tags.append("maintenance")
    
    # Generate archive URL (local path for now)
    archive_url = f"skills/{skill_dir.name}-{frontmatter.get('version', '1.0.0')}.tar.gz"
    
    return {
        "name": skill_dir.name,
        "version": frontmatter.get("version", "1.0.0"),
        "description": description[:500],
        "archive_url": archive_url,
        "agent": agent,
        "path": str(skill_dir),
        "content_hash": content_hash,
        "tags": list(set(tags)),
        "source": "local",
        "compat": {
            "clients": [agent],
            "min_version": "0.0.0"
        }
    }


def scan_all_agents() -> List[Dict[str, Any]]:
    """Scan all configured agent directories"""
    all_skills = []
    seen_hashes: Set[str] = set()
    
    for agent, dirs in AGENT_SKILL_DIRS.items():
        print(f"\n Scanning {agent}...")
        for skill_dir in dirs:
            if not skill_dir.exists():
                print(f"  Skipping {skill_dir} (not found)")
                continue
            
            print(f"  Scanning {skill_dir}...")
            skills = scan_skill_dir(skill_dir, agent)
            
            for skill in skills:
                # Deduplicate by content hash
                if skill["content_hash"] in seen_hashes:
                    print(f"  Skipping {skill['name']} (duplicate)")
                    continue
                
                seen_hashes.add(skill["content_hash"])
                all_skills.append(skill)
                print(f"  Found: {skill['name']} ({skill['description'][:50]}...)")
    
    return all_skills


def scan_skills_sh_cache() -> List[Dict[str, Any]]:
    """Scan skills.sh cache for installed skills"""
    cache_dir = Path.home() / ".cache" / "skills"
    if not cache_dir.exists():
        return []
    
    skills = []
    for item in cache_dir.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            # Check for SKILL.md
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                content = skill_md.read_text(encoding="utf-8")
                content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                
                skills.append({
                    "name": item.name,
                    "version": "1.0.0",
                    "description": f"Skills.sh cached skill: {item.name}",
                    "archive_url": f"skills/{item.name}-1.0.0.tar.gz",
                    "agent": "skills.sh",
                    "path": str(item),
                    "content_hash": content_hash,
                    "tags": ["skills.sh", "cached"],
                    "source": "skills.sh",
                    "compat": {
                        "clients": ["all"],
                        "min_version": "0.0.0"
                    }
                })
    
    return skills


def build_catalog(skills: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build the marketplace catalog from discovered skills"""
    return {
        "skills": skills,
        "metadata": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_skills": len(skills),
            "agents_scanned": list(AGENT_SKILL_DIRS.keys()),
            "scanner_version": "1.0.0"
        }
    }


def save_catalog(catalog: Dict[str, Any]) -> None:
    """Save catalog to JSON"""
    CATALOG_PATH.mkdir(parents=True, exist_ok=True)
    
    # Save full catalog
    with open(SKILLS_INDEX, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Catalog saved to {SKILLS_INDEX}")
    print(f"   Total skills: {catalog['metadata']['total_skills']}")


def print_summary(skills: List[Dict[str, Any]]) -> None:
    """Print summary of discovered skills"""
    by_agent: Dict[str, int] = {}
    for skill in skills:
        agent = skill["agent"]
        by_agent[agent] = by_agent.get(agent, 0) + 1
    
    print("\n" + "=" * 60)
    print("📊 SKILL SCAN SUMMARY")
    print("=" * 60)
    print(f"\nTotal unique skills: {len(skills)}")
    print("\nBy agent:")
    for agent, count in sorted(by_agent.items()):
        print(f"  {agent}: {count}")
    print("\n" + "=" * 60)


def main():
    """Main entry point"""
    print("🔍 Starting skill scanner...")
    print(f"   Scanning directories: {list(AGENT_SKILL_DIRS.keys())}")
    
    # Scan all agents
    skills = scan_all_agents()
    
    # Scan skills.sh cache
    skills_sh = scan_skills_sh_cache()
    skills.extend(skills_sh)
    
    # Build and save catalog
    catalog = build_catalog(skills)
    save_catalog(catalog)
    
    # Print summary
    print_summary(skills)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
