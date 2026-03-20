---
name: gemini-speak
description: Read the last agent reply aloud using ElevenLabs TTS. Triggered by /speak or requests to "read that".
---

# Gemini Speak Skill

Tento skill umožňuje Gemini CLI číst své odpovědi nahlas pomocí špičkové technologie ElevenLabs.

## Workflow

1. **Trigger:** Skill se aktivuje, pokud uživatel napíše `/speak` nebo požádá o přečtení předchozí zprávy.
2. **Context:** Skill automaticky získá text poslední odpovědi z proměnné prostředí `GEMINI_LAST_REPLY`.
3. **Action:** Spustí se přibalený skript `scripts/speak.py`, který:
   - Vyčistí text od Markdownu.
   - Odešle jej do ElevenLabs.
   - Přehraje výsledné audio na lokálním systému.

## Requirements

- **ELEVENLABS_API_KEY**: Musí být nastaven v prostředí (např. v `.zshrc` nebo `.bashrc` jako `export ELEVENLABS_API_KEY="..."`).
- **Audio Player**: Vyžaduje nainstalovaný `ffplay` (součást ffmpeg) nebo `mpv`.

## Usage

Jednoduše napiš:
`/speak`
nebo
`přečti mi to`
