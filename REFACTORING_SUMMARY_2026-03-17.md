# Refaktoring a stabilizace systému: Shrnutí změn (17. 3. 2026)

Tento dokument slouží jako záznam provedených oprav, optimalizací a bezpečnostních vylepšení na serveru HAS a v hlavním repozitáři.

## 1. 🚀 Extrémní odlehčení HAS serveru
*   **Akce:** Úplné vypnutí a odinstalace **Trae Serveru** a **CKG Serveru** na HAS.
*   **Důvod:** Kritické vytížení CPU (Load 11+) a extrémní spotřeba RAM (desítky GB) kvůli indexaci v Remote-SSH módu.
*   **Nové workflow:** Implementováno v `TRAE_SETUP.md`. HAS nyní slouží pouze jako pasivní úložiště souborů přes **SSHFS**, zatímco veškerý výpočetní výkon pro AI funkce IDE běží na lokálním stroji.

## 2. 🧠 Stabilizace sémantické paměti (`advanced-memory-mcp`)
*   **Oprava:** Vyřešení chyby `SIGILL 132` (Illegal Instruction).
*   **Technické řešení:** 
    *   Odstranění binárních závislostí `numpy`, `torch` a `sentence-transformers`, které vyžadovaly instrukce AVX (nepodporované procesorem HAS).
    *   Přepis na **Ultra-Light REST architekturu**. Vektory (embeddings) jsou nyní počítány externě přes **Gemini API** pomocí `httpx`.
    *   Přímá komunikace s Qdrantem přes REST API místo gRPC klienta.
*   **Výsledek:** 100% stabilní služba s minimálními nároky na HW.

## 3. 🛡️ Bezpečnostní integrace (Vault)
*   **Změna:** Propojení s **HashiCorp Vault** pro správu citlivých údajů.
*   **Implementace:** Služba `advanced-memory-mcp` byla upravena tak, aby přednostně načítala API klíče z bezpečných souborů v `/vault/runtime/` spravovaných Vault agentem.
*   **Stav:** API klíče již nejsou pevně zapsány v `.env` ani v kódu.

## 4. 🛰️ Oprava směrování v `mega-orchestrator`
*   **Hostnames:** Sjednocení názvů hostitelů v konfiguraci koordinátora se skutečnými názvy Docker kontejnerů (např. `mcp-filesystem`, `mcp-advanced-memory`).
*   **Porty:** Přechod na vnitřní Docker porty (**8000**) pro veškerou inter-container komunikaci.
*   **Aliasy:** Přidání nástrojů `semantic_search` a `store_semantic_memory` do globálního mapování.
*   **SAGE Router:** Oprava chyb v SAGE módech (odstranění neexistujícího módu `RESEARCH`) a vynucení správného směrování paměťových nástrojů bez ohledu na detekovaný kontext.

## 5. 🧹 Úklid a standardizace
*   **Přejmenování:** Hromadná náhrada starého názvu `zen-coordinator` za nový **`mega-orchestrator`** v celém repozitáři (kód i dokumentace).
*   **Dependency Cleanup:** Odstranění omylem přidaných balíčků `24` a `node` z `package.json` a smazání `node_modules` na HAS.
*   **Vypnutí služeb:** Služby `mcp-vision` a `mcp-transcriber` byly trvale deaktivovány v `docker-compose.yml` (nastaveny na `disabled` profily).

## 🛠️ Nové nástroje na HAS
*   **`uv` / `uvx`**: Nainstalován moderní Python manažer pro bleskové spouštění MCP serverů.
*   **Node.js**: Nastavena stabilní systémová verze (v20.15.1), která nativně podporuje Alpine/BusyBox prostředí serveru HAS.

---
**Aktuální Load HAS:** ~3.0 (Stabilní)
**Status:** Systém je připraven na import produkčních dat a historií chatu.
