#!/usr/bin/env python3
"""
Minimální OAuth setup pro Anthropic na HAS
"""
import os

def setup_oauth():
    print("🔐 Anthropic OAuth Setup pro HAS")
    print("=" * 40)
    
    print("Otevři v browseru: https://console.anthropic.com/settings/keys")
    print("Vytvoř nový API klíč a zkopíruj ho sem.")
    print()
    
    api_key = input("Vlož API key (sk-ant-api03-...): ").strip()
    
    if not api_key.startswith("sk-ant-api03-"):
        print("❌ Nesprávný formát API key")
        return False
    
    # Prefer OS keyring for secure storage
    stored_in_keyring = False
    try:
        import keyring  # type: ignore

        keyring.set_password("anthropic", "api_key", api_key)
        stored_in_keyring = True
    except Exception:
        stored_in_keyring = False

    # Set environment variable for current process
    os.environ["ANTHROPIC_API_KEY"] = api_key

    print("✅ API key nastaven!")
    if stored_in_keyring:
        print("   Uloženo bezpečně do OS keyring.")
    else:
        print("   Keyring není dostupný. API key je nastaven pouze pro tuto session.")
        print("   Pro trvalé použití nastav ANTHROPIC_API_KEY ručně ve svém shellu.")
    
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
