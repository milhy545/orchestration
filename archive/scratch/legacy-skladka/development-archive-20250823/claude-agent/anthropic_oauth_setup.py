#!/usr/bin/env python3
"""
Minimální OAuth setup pro Anthropic na HAS
"""
import json
import os
from pathlib import Path

def setup_oauth():
    print("🔐 Anthropic OAuth Setup pro HAS")
    print("=" * 40)
    
    # Create .anthropic directory
    anthropic_dir = Path.home() / ".anthropic"
    anthropic_dir.mkdir(exist_ok=True)
    
    print("Otevři v browseru: https://console.anthropic.com/settings/keys")
    print("Vytvoř nový API klíč a zkopíruj ho sem.")
    print()
    
    api_key = input("Vlož API key (sk-ant-api03-...): ").strip()
    
    if not api_key.startswith("sk-ant-api03-"):
        print("❌ Nesprávný formát API key")
        return False
    
    # Save to config file
    config = {
        "api_key": api_key
    }
    
    config_file = anthropic_dir / "config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Also set environment variable
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    # Add to profile
    profile_line = f'export ANTHROPIC_API_KEY="{api_key}"'
    with open(Path.home() / ".profile", "a") as f:
        f.write(f"\n# Anthropic API Key\n{profile_line}\n")
    
    print("✅ API key nastaven!")
    print(f"   Config: {config_file}")
    print(f"   Profile: ~/.profile")
    
    # Test the API key
    print("\n🧪 Testování API key...")
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=20,
            messages=[{"role": "user", "content": "Test"}]
        )
        print("✅ API key funguje!")
        print(f"   Response: {response.content[0].text}")
        return True
    except Exception as e:
        print(f"❌ Test selhal: {e}")
        return False

if __name__ == "__main__":
    setup_oauth()