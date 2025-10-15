#!/usr/bin/env python3
"""
Test skript pro ElevenLabs MCP server
Demonstruje základní funkčnost serveru
"""

import asyncio
import os
from elevenlabs_mcp.server import mcp

async def test_list_tools():
    """Vypíše všechny dostupné nástroje"""
    print("\n" + "="*70)
    print("🔧 DOSTUPNÉ NÁSTROJE ELEVENLABS MCP SERVERU")
    print("="*70)
    
    try:
        tools = await mcp.list_tools()
        
        for i, tool in enumerate(tools.tools, 1):
            print(f"\n{i}. 📌 {tool.name}")
            print(f"   📝 Popis: {tool.description}")
            
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                properties = tool.inputSchema.get('properties', {})
                if properties:
                    print(f"   🔑 Parametry:")
                    for param_name, param_info in properties.items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', 'Bez popisu')
                        required = '(povinný)' if param_name in tool.inputSchema.get('required', []) else '(volitelný)'
                        print(f"      • {param_name} [{param_type}] {required}")
                        print(f"        {param_desc}")
        
        print(f"\n{'='*70}")
        print(f"✅ Celkem nalezeno {len(tools.tools)} nástrojů")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Chyba při získávání nástrojů: {e}")
        import traceback
        traceback.print_exc()

async def test_list_voices():
    """Vypíše dostupné hlasy"""
    print("\n" + "="*70)
    print("🎤 DOSTUPNÉ HLASY")
    print("="*70)
    
    try:
        # Zavoláme nástroj pro získání hlasů
        result = await mcp.call_tool("elevenlabs_list_voices", {})
        
        if result and hasattr(result, 'content'):
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
        
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"❌ Chyba při získávání hlasů: {e}")
        print("ℹ️  Poznámka: Pro získání hlasů je potřeba platný API klíč\n")

async def main():
    """Hlavní funkce"""
    print("\n" + "🚀 "*20)
    print("ELEVENLABS MCP SERVER - TESTOVACÍ SKRIPT")
    print("🚀 "*20)
    
    # Test 1: Výpis nástrojů
    await test_list_tools()
    
    # Test 2: Výpis hlasů (vyžaduje API klíč)
    print("\n📋 Pokus o získání seznamu hlasů...")
    await test_list_voices()
    
    print("\n✅ Testování dokončeno!")
    print("\n💡 Pro použití nástrojů spusťte server pomocí:")
    print("   python -m elevenlabs_mcp")
    print("\n📚 Dokumentace: /home/orchestration/mcp-servers/elevenlabs-mcp/README.md\n")

if __name__ == "__main__":
    asyncio.run(main())
