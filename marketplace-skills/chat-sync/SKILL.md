# Chat Synchronization Skill

Tento skill umožňuje agentům automaticky zálohovat své konverzace a kontext do centrální paměti na Home Automatization Serveru (HAS).

## Instrukce pro agenta:

1. **Sběr dat:** Na konci každého významného milníku nebo na vyžádání ("ulož náš chat do HAS") proveď export transcriptu.
2. **Vyhledávání chatů:** Hledej lokální databáze chatů (pro Claude Code v `~/.claude/sessions`, pro Gemini v `~/.gemini/sessions`).
3. **Synchronizace:** Použij nástroj `store_memory` přes Mega-Orchestrator nebo pošli POST požadavek na FEI Bridge na HAS:
   ```bash
   curl -X POST http://192.168.0.58:7000/mcp/tools/store_memory -d '{"content": "<transcript>", "tags": ["chat-backup"]}'
   ```
4. **Analýza:** Před uložením proveď krátké shrnutí (summary) a ulož jej jako klíčový bod do `Advanced-Memory`.

## Propojení:
- **FEI Bridge:** http://192.168.0.58:7000/mcp
- **Storage:** /home/orchestration/data/transcripts (na HAS)
