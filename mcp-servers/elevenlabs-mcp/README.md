# ElevenLabs MCP Server

Oficiální ElevenLabs Model Context Protocol (MCP) server pro interakci s pokročilými Text-to-Speech a audio zpracovacími API.

## Instalace

Server byl nainstalován pomocí:
```bash
pip install elevenlabs-mcp
```

## Konfigurace

Konfigurační soubor: `/home/orchestration/blackbox_mcp_settings.json`

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
      }
    }
  }
}
```

## Proměnné prostředí

- **ELEVENLABS_API_KEY**: API klíč z ElevenLabs (povinné)
- **ELEVENLABS_MCP_OUTPUT_MODE**: Režim výstupu souborů
  - `files` (výchozí): Ukládá soubory na disk
  - `resources`: Vrací soubory jako MCP resources (base64)
  - `both`: Ukládá na disk A vrací jako resources
- **ELEVENLABS_MCP_BASE_PATH**: Základní cesta pro operace se soubory (výchozí: ~/Desktop)

## Dostupné funkce

Server poskytuje následující nástroje:

1. **Text-to-Speech**: Generování řeči z textu
2. **Klonování hlasů**: Vytváření vlastních hlasových profilů
3. **Přepis audia**: Převod řeči na text
4. **Návrh hlasů**: Vytváření AI hlasů s různými charakteristikami
5. **Zvukové efekty**: Generování zvukových efektů a soundscapů

## Spuštění serveru

### Manuální spuštění
```bash
cd /home/orchestration
source claude-agent-env/bin/activate
python -m elevenlabs_mcp
```

### Získání konfigurace
```bash
python -m elevenlabs_mcp --api-key=YOUR_API_KEY --print
```

## Výstupní adresář

Všechny generované audio soubory jsou ukládány do:
```
/home/orchestration/mcp-servers/elevenlabs-mcp/outputs/
```

## Příklady použití

### Text-to-Speech
Převod textu na řeč s výběrem hlasu a nastavení.

### Klonování hlasu
Nahrání vzorku hlasu a vytvoření vlastního hlasového profilu.

### Přepis audia
Převod audio nahrávky na text s identifikací mluvčích.

## Řešení problémů

### Logy
Logy serveru lze najít v terminálu při spuštění.

### Timeouty
Některé operace (návrh hlasu, izolace audia) mohou trvat dlouho. To je normální chování.

## Odkazy

- GitHub: https://github.com/elevenlabs/elevenlabs-mcp
- ElevenLabs API: https://elevenlabs.io/docs
- API klíče: https://elevenlabs.io/app/settings/api-keys

## Poznámky

- Free tier poskytuje 10 000 kreditů měsíčně
- Pro použití nástrojů jsou potřeba ElevenLabs kredity
- Data residency je enterprise funkce
