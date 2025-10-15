# ElevenLabs MCP Server - Souhrn instalace

## ✅ Dokončené kroky

### 1. Vytvoření adresářové struktury
```
/home/orchestration/mcp-servers/elevenlabs-mcp/
├── outputs/          # Adresář pro generované audio soubory
├── README.md         # Dokumentace
├── test_server.py    # Testovací skript
└── demo_text_to_speech.py  # Demonstrační skript
```

### 2. Instalace balíčku
```bash
pip install elevenlabs-mcp
```

**Nainstalované závislosti:**
- elevenlabs-mcp (0.9.0)
- mcp (1.12.4)
- elevenlabs (2.18.0)
- fastapi (0.109.2)
- uvicorn (0.27.1)
- sounddevice (0.5.1)
- soundfile (0.13.1)
- a další...

### 3. Konfigurace

**Konfigurační soubor:** `/home/orchestration/blackbox_mcp_settings.json`

```json
{
  "mcpServers": {
    "github.com/elevenlabs/elevenlabs-mcp": {
      "command": "python",
      "args": ["-m", "elevenlabs_mcp"],
      "env": {
        "ELEVENLABS_API_KEY": "sk_3acc58a81525e79c89124add46a3df6d8eb0f6cd6b4845ff",
        "ELEVENLABS_MCP_OUTPUT_MODE": "files",
        "ELEVENLABS_MCP_BASE_PATH": "/home/orchestration/mcp-servers/elevenlabs-mcp/outputs"
      },
      "description": "ElevenLabs MCP server pro text-to-speech, klonování hlasů a zpracování audia",
      "capabilities": [
        "text-to-speech",
        "voice-cloning",
        "audio-transcription",
        "voice-design",
        "sound-effects"
      ]
    }
  }
}
```

### 4. Proměnné prostředí

- **ELEVENLABS_API_KEY**: `sk_3acc58a81525e79c89124add46a3df6d8eb0f6cd6b4845ff`
- **ELEVENLABS_MCP_OUTPUT_MODE**: `files`
- **ELEVENLABS_MCP_BASE_PATH**: `/home/orchestration/mcp-servers/elevenlabs-mcp/outputs`

## 🎯 Dostupné nástroje

ElevenLabs MCP server poskytuje následující nástroje:

1. **elevenlabs_text_to_speech** - Převod textu na řeč
2. **elevenlabs_list_voices** - Seznam dostupných hlasů
3. **elevenlabs_get_voice** - Získání informací o konkrétním hlasu
4. **elevenlabs_add_voice** - Přidání vlastního hlasu (klonování)
5. **elevenlabs_delete_voice** - Smazání hlasu
6. **elevenlabs_speech_to_speech** - Převod řeči na jinou řeč
7. **elevenlabs_generate_sound_effect** - Generování zvukových efektů
8. **elevenlabs_isolate_audio** - Izolace hlasu z audia
9. **elevenlabs_transcribe_audio** - Přepis audia na text
10. **elevenlabs_design_voice** - Návrh AI hlasu

## 🚀 Spuštění serveru

### Manuální spuštění
```bash
cd /home/orchestration
source claude-agent-env/bin/activate
export ELEVENLABS_API_KEY="sk_3acc58a81525e79c89124add46a3df6d8eb0f6cd6b4845ff"
python -m elevenlabs_mcp
```

### Testování
```bash
# Test seznamu nástrojů
python mcp-servers/elevenlabs-mcp/test_server.py

# Demo text-to-speech
python mcp-servers/elevenlabs-mcp/demo_text_to_speech.py
```

## 📝 Příklady použití

### Text-to-Speech
```python
import os
os.environ['ELEVENLABS_API_KEY'] = 'your-api-key'

from elevenlabs_mcp.server import mcp

result = await mcp.call_tool(
    "elevenlabs_text_to_speech",
    {
        "text": "Hello, world!",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",
        "model_id": "eleven_multilingual_v2",
        "output_path": "output.mp3"
    }
)
```

### Seznam hlasů
```python
result = await mcp.call_tool("elevenlabs_list_voices", {})
```

### Generování zvukových efektů
```python
result = await mcp.call_tool(
    "elevenlabs_generate_sound_effect",
    {
        "text": "thunder and rain in a forest",
        "duration_seconds": 5.0,
        "prompt_influence": 0.5
    }
)
```

## 📁 Výstupní soubory

Všechny generované audio soubory jsou ukládány do:
```
/home/orchestration/mcp-servers/elevenlabs-mcp/outputs/
```

## 🔗 Odkazy

- **GitHub**: https://github.com/elevenlabs/elevenlabs-mcp
- **ElevenLabs API**: https://elevenlabs.io/docs
- **API klíče**: https://elevenlabs.io/app/settings/api-keys
- **MCP dokumentace**: https://github.com/modelcontextprotocol

## 💡 Poznámky

- Free tier: 10 000 kreditů měsíčně
- Pro použití nástrojů jsou potřeba ElevenLabs kredity
- Některé operace mohou trvat déle (voice design, audio isolation)
- Server podporuje více výstupních režimů (files, resources, both)

## ✅ Status

- ✅ Server nainstalován
- ✅ Konfigurace vytvořena
- ✅ API klíč nastaven
- ✅ Výstupní adresář vytvořen
- ✅ Dokumentace připravena
- ✅ Testovací skripty vytvořeny
- 🔄 Demonstrace funkčnosti probíhá...

## 🎓 Další kroky

1. Spustit demo skript pro ověření funkčnosti
2. Vyzkoušet různé hlasy a nastavení
3. Integrovat server s vašimi aplikacemi
4. Prozkoumat pokročilé funkce (voice cloning, sound effects)

---

**Datum instalace**: 2025-01-XX
**Verze**: elevenlabs-mcp 0.9.0
**Python prostředí**: /home/orchestration/claude-agent-env
