# Repository Guidelines

## Struktura projektu a organizace modulů
- `mcp-servers/`: jednotlivé MCP mikroservisy (každý má vlastní `requirements.txt` a `Dockerfile`).
- `mega_orchestrator/`, `claude-agent/`, `claude-agent-env/`: core orchestrace a agentní komponenty.
- `config/`: sdílená konfigurace (včetně `config/requirements.txt` a `config/Dockerfile`).
- `monitoring/`: konfigurace Prometheus, Grafana, Loki, Promtail.
- `docs/`: dokumentace (viz `docs/MONITORING.md`).
- `scripts/`: údržbové a health‑check skripty.
- `tests/`: cross‑service testy a utilitky.

## Build, test a vývojové příkazy
- `docker-compose up -d`: spustí celý stack na pozadí.
- `docker-compose down`: zastaví všechny služby.
- `docker-compose logs -f <service>`: sleduje logy jedné služby.
- `./scripts/monitoring-health-check.sh`: ověří nastavení monitoringu.
- `bash tests/docker-compose-monitoring-test.sh`: zkontroluje monitoring části `docker-compose.yml`.
- `pytest`: spustí Python testy v `tests/` a `mcp-servers/*/tests`.

## Styl kódu a pojmenování
- Respektuj existující konvence v dané službě. Pro Python používej 4 mezery a PEP 8.
- V YAML (např. `docker-compose.yml`) drž 2‑mezerné odsazení a pokud jde, řaď bloky služeb konzistentně.
- Testy musí být pojmenované `test_*.py` a třídy/funkce `Test*`/`test_*` (viz `pytest.ini`).

## Testovací pravidla
- Pytest je konfigurovaný v `pytest.ini` a používá markery `unit`, `integration`, `security`, `performance`, `slow`.
- Při použití `pytest-cov` je minimum pokrytí `fail_under = 70`.
- Přidávej testy ke službě, kterou upravuješ (např. `mcp-servers/<service>/tests/`).

## Commity a Pull Requesty
- Nedávné commity jsou krátké a popisné, občas se scope prefixem (např. `docs:`). Drž se tohoto stylu.
- PR by měl mít jasné shrnutí, důvod změn a seznam spuštěných příkazů.
- Při změnách monitoringu nebo Dockeru uveď dotčené služby a případné nové proměnné prostředí.

## Bezpečnost a konfigurace
- Před spuštěním zkopíruj `.env.example` na `.env`.
- Nikdy necommituj tajné údaje; používej `.env` nebo externí bezpečné úložiště.
