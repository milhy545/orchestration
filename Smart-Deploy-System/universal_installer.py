#!/usr/bin/env python3
"""
Smart Universal Installer - Smart Deploy System
Handles dynamic registration of skills for various AI agents.
"""
import os
import json
import argparse
import shutil
from pathlib import Path

# Mock database of agent configurations (simulating dynamic web updates)
AGENT_KNOWLEDGE = {
    "codex": {
        "config_home": "~/.codex",
        "skills_dir": "skills",
        "registration_file": "config.toml",
        "method": "toml_append"
    },
    "gemini": {
        "config_home": "~/.gemini",
        "extensions_dir": "extensions",
        "method": "symlink"
    },
    "claude": {
        "config_home": "~/.claude",
        "method": "mcp_config"
    }
}

class UniversalInstaller:
    def __init__(self, hub_path):
        self.hub_path = Path(hub_path).expanduser()

    def deploy(self, skill_name, target_agent):
        skill_dir = self.hub_path / skill_name
        manifest_path = skill_dir / "manifest.json"
        
        if not manifest_path.exists():
            print(f"Error: Manifest for {skill_name} not found in HUB.")
            return False

        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        print(f"Deploying {skill_name} v{manifest['version']} to {target_agent}...")
        
        agent_info = AGENT_KNOWLEDGE.get(target_agent)
        if not agent_info:
            print(f"Error: Unknown agent {target_agent}")
            return False

        # Specific deployment logic based on agent type
        if target_agent == "gemini":
            return self._deploy_to_gemini(skill_dir, manifest, agent_info)
        elif target_agent == "codex":
            return self._deploy_to_codex(skill_dir, manifest, agent_info)
        else:
            print(f"Deployment logic for {target_agent} not yet implemented.")
            return False

    def _deploy_to_gemini(self, skill_dir, manifest, info):
        dest_base = Path(info['config_home']).expanduser() / info['extensions_dir']
        dest_dir = dest_base / manifest['name']
        
        print(f"  Target directory: {dest_dir}")
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        
        shutil.copytree(skill_dir, dest_dir)
        print("  Gemini extension deployed successfully.")
        return True

    def _deploy_to_codex(self, skill_dir, manifest, info):
        # Codex likes files in ~/.codex/skills/
        dest_base = Path(info['config_home']).expanduser() / info['skills_dir']
        dest_dir = dest_base / manifest['name']
        
        print(f"  Target directory: {dest_dir}")
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
            
        shutil.copytree(skill_dir, dest_dir)
        # Note: In real scenario, would also parse and update config.toml
        print("  Codex skill deployed. (Config registration manual check required in alpha)")
        return True

def main():
    parser = argparse.ArgumentParser(description="Smart Deploy Universal Installer")
    parser.add_argument("skill", help="Name of the skill in HUB")
    parser.add_argument("--target", required=True, choices=["codex", "gemini", "claude"], help="Target AI agent")
    
    args = parser.parse_args()
    
    hub = "/home/milhy777/Develop/Smart-Deploy-System/skill-hub"
    installer = UniversalInstaller(hub)
    installer.deploy(args.skill, args.target)

if __name__ == "__main__":
    main()
