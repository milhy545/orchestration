#!/usr/bin/env python3
"""
Demonstrace Text-to-Speech funkce ElevenLabs MCP serveru
"""

import asyncio
import os
from pathlib import Path

# Nastavení API klíče
os.environ['ELEVENLABS_API_KEY'] = 'sk_3acc58a81525e79c89124add46a3df6d8eb0f6cd6b4845ff'
os.environ['ELEVENLABS_MCP_BASE_PATH'] = '/home/orchestration/mcp-servers/elevenlabs-mcp/outputs'

from elevenlabs_mcp.server import mcp

async def demo_text_to_speech():
    """Demonstrace převodu textu na řeč"""
    print("\n" + "="*70)
    print("🎙️  DEMONSTRACE TEXT-TO-SPEECH")
    print("="*70)
    
    # Text k převodu
    text = "Ahoj! Jsem ElevenLabs AI hlas. Toto je demonstrace MCP serveru pro převod textu na řeč."
    
    print(f"\n📝 Text k převodu:")
    print(f"   '{text}'")
    print(f"\n⏳ Generuji audio...")
    
    try:
        # Zavoláme nástroj pro text-to-speech
        result = await mcp.call_tool(
            "elevenlabs_text_to_speech",
            {
                "text": text,
                "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel - výchozí hlas
                "model_id": "eleven_multilingual_v2",
                "output_path": "demo_output.mp3"
            }
        )
        
        print(f"\n✅ Audio úspěšně vygenerováno!")
        
        if result and hasattr(result, 'content'):
            for content in result.content:
                if hasattr(content, 'text'):
                    print(f"\n📄 Výsledek:")
                    print(content.text)
        
        # Zkontrolujeme, jestli byl soubor vytvořen
        output_dir = Path("/home/orchestration/mcp-servers/elevenlabs-mcp/outputs")
        if output_dir.exists():
            files = list(output_dir.glob("*.mp3"))
            if files:
                print(f"\n📁 Vygenerované soubory:")
                for file in files:
                    size = file.stat().st_size
                    print(f"   • {file.name} ({size:,} bytů)")
        
    except Exception as e:
        print(f"\n❌ Chyba při generování audia: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*70}\n")

async def list_available_voices():
    """Vypíše dostupné hlasy"""
    print("\n" + "="*70)
    print("🎤 DOSTUPNÉ HLASY")
    print("="*70)
    
    try:
        result = await mcp.call_tool("elevenlabs_list_voices", {})
        
        if result and hasattr(result, 'content'):
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
        
    except Exception as e:
        print(f"\n❌ Chyba: {e}")
    
    print(f"\n{'='*70}\n")

async def main():
    """Hlavní funkce"""
    print("\n" + "🎵 "*20)
    print("ELEVENLABS MCP SERVER - TEXT-TO-SPEECH DEMO")
    print("🎵 "*20)
    
    # Nejprve vypíšeme dostupné hlasy
    print("\n1️⃣  Získávám seznam dostupných hlasů...")
    await list_available_voices()
    
    # Pak vygenerujeme demo audio
    print("\n2️⃣  Generuji demo audio soubor...")
    await demo_text_to_speech()
    
    print("\n✅ Demonstrace dokončena!")
    print("\n💡 Tip: Audio soubory najdete v:")
    print("   /home/orchestration/mcp-servers/elevenlabs-mcp/outputs/\n")

if __name__ == "__main__":
    asyncio.run(main())
