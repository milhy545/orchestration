#!/usr/bin/env python3
"""
Rychlá demonstrace ElevenLabs MCP serveru
Zobrazí dostupné nástroje a jejich parametry
"""

import os
import sys


def require_api_key() -> None:
    if os.getenv("ELEVENLABS_API_KEY", "").strip():
        return
    print("❌ ELEVENLABS_API_KEY není nastavený v prostředí.")
    print("   Nastavte ho před spuštěním demonstrace, například:")
    print("   export ELEVENLABS_API_KEY='your-api-key'")
    sys.exit(1)


require_api_key()

print("\n" + "="*70)
print("🎙️  ELEVENLABS MCP SERVER - RYCHLÁ DEMONSTRACE")
print("="*70)

print("\n📦 Ověřuji instalaci...")

try:
    import elevenlabs_mcp
    print("✅ Balíček elevenlabs-mcp je nainstalován")
    print(f"   Verze: {elevenlabs_mcp.__version__ if hasattr(elevenlabs_mcp, '__version__') else 'N/A'}")
except ImportError as e:
    print(f"❌ Chyba: {e}")
    sys.exit(1)

print("\n🔧 Dostupné nástroje serveru:")
print("-" * 70)

tools = [
    {
        "name": "elevenlabs_text_to_speech",
        "description": "Převod textu na řeč s výběrem hlasu a modelu",
        "params": ["text", "voice_id", "model_id", "output_path"]
    },
    {
        "name": "elevenlabs_list_voices",
        "description": "Seznam všech dostupných hlasů",
        "params": []
    },
    {
        "name": "elevenlabs_get_voice",
        "description": "Získání detailů o konkrétním hlasu",
        "params": ["voice_id"]
    },
    {
        "name": "elevenlabs_add_voice",
        "description": "Přidání vlastního hlasu (klonování)",
        "params": ["name", "files", "description"]
    },
    {
        "name": "elevenlabs_delete_voice",
        "description": "Smazání hlasu z knihovny",
        "params": ["voice_id"]
    },
    {
        "name": "elevenlabs_speech_to_speech",
        "description": "Převod řeči na jinou řeč",
        "params": ["audio_path", "voice_id", "model_id"]
    },
    {
        "name": "elevenlabs_generate_sound_effect",
        "description": "Generování zvukových efektů z textového popisu",
        "params": ["text", "duration_seconds", "prompt_influence"]
    },
    {
        "name": "elevenlabs_isolate_audio",
        "description": "Izolace hlasu z audio nahrávky",
        "params": ["audio_path"]
    },
    {
        "name": "elevenlabs_transcribe_audio",
        "description": "Přepis audio nahrávky na text",
        "params": ["audio_path", "language"]
    },
    {
        "name": "elevenlabs_design_voice",
        "description": "Návrh AI hlasu s vlastními charakteristikami",
        "params": ["text", "gender", "age", "accent"]
    }
]

for i, tool in enumerate(tools, 1):
    print(f"\n{i}. 📌 {tool['name']}")
    print(f"   📝 {tool['description']}")
    if tool['params']:
        print(f"   🔑 Parametry: {', '.join(tool['params'])}")

print("\n" + "="*70)
print("📊 STATISTIKY")
print("="*70)
print(f"✅ Celkem nástrojů: {len(tools)}")
print(f"📁 Výstupní adresář: /home/orchestration/mcp-servers/elevenlabs-mcp/outputs/")
print(f"⚙️  Konfigurační soubor: /home/orchestration/blackbox_mcp_settings.json")
print("🔑 API klíč: Načten z prostředí")

print("\n" + "="*70)
print("💡 PŘÍKLADY POUŽITÍ")
print("="*70)

print("\n1️⃣  Text-to-Speech:")
print("   python -c \"")
print("   import asyncio, os")
print("   os.environ['ELEVENLABS_API_KEY'] = 'your-key'")
print("   from elevenlabs_mcp.server import mcp")
print("   asyncio.run(mcp.call_tool('elevenlabs_text_to_speech', {")
print("       'text': 'Hello world',")
print("       'voice_id': '21m00Tcm4TlvDq8ikWAM',")
print("       'output_path': 'output.mp3'")
print("   }))")
print("   \"")

print("\n2️⃣  Seznam hlasů:")
print("   python -c \"")
print("   import asyncio, os")
print("   os.environ['ELEVENLABS_API_KEY'] = 'your-key'")
print("   from elevenlabs_mcp.server import mcp")
print("   asyncio.run(mcp.call_tool('elevenlabs_list_voices', {}))")
print("   \"")

print("\n3️⃣  Zvukové efekty:")
print("   python -c \"")
print("   import asyncio, os")
print("   os.environ['ELEVENLABS_API_KEY'] = 'your-key'")
print("   from elevenlabs_mcp.server import mcp")
print("   asyncio.run(mcp.call_tool('elevenlabs_generate_sound_effect', {")
print("       'text': 'thunder and rain',")
print("       'duration_seconds': 5.0")
print("   }))")
print("   \"")

print("\n" + "="*70)
print("🚀 SPUŠTĚNÍ SERVERU")
print("="*70)
print("\nPro spuštění MCP serveru použijte:")
print("   export ELEVENLABS_API_KEY='your-key'")
print("   python -m elevenlabs_mcp")

print("\n" + "="*70)
print("✅ DEMONSTRACE DOKONČENA")
print("="*70)
print("\n📚 Další informace:")
print("   • README: /home/orchestration/mcp-servers/elevenlabs-mcp/README.md")
print("   • Souhrn: /home/orchestration/mcp-servers/elevenlabs-mcp/INSTALLATION_SUMMARY.md")
print("   • GitHub: https://github.com/elevenlabs/elevenlabs-mcp")
print()
