# 🚀 Migrace na Astral `uv`: Architektura a Průvodce (Verze 2.0)

Tento dokument detailně popisuje kompletní refaktoring infrastruktury Mega-Orchestratoru z tradičního `pip` na moderní ekosystém `uv` od Astral-sh. Účelem je dosáhnout 1000% optimalizace ve fázích buildování kontejnerů a správy prostředí.

## 🎯 Proč jsme opustili `pip`?
Klasický `pip` a `pip-tools` (včetně `poetry` či `pipenv`) trpí na starší architektuře pomalým rozlišováním závislostí a neefektivním cachováním. Na serveru s omezenými prostředky jako HAS to znamenalo zbytečně dlouhé desítky minut při `docker-compose build`.

1. **Rychlost:** `uv` je napsáno v jazyce Rust. Oproti `pip` je **10x až 100x rychlejší** při stahování a rozlišování balíčků.
2. **Čistota:** Umožňuje bezpečně spustit balíčky přes `uvx` bez jejich instalace do globálního systému, čímž odpadá nutnost řešit spletité virtuální prostředí (venv).
3. **Předvídatelnost:** Instalace v Docker kontejnerech je deterministická, nemění se a nenechává za sebou nepotřebná dočasná data.

## 🛠️ Architektonické změny v Dockerfilech

V rámci přechodu bylo upraveno všech 25 služeb (`mcp-servers/*/Dockerfile` a `config/Dockerfile`). 

### Stará (pip) verze
```dockerfile
# Pomalé stahování a instalace
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
```

### Nová (uv) verze
```dockerfile
# Převzetí pre-build binárky (žádná nutnost instalace závislostí pro samotný balíčkovací nástroj)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY requirements.txt .
# Ultra-rychlá paralelizovaná instalace přímo do sytému kontejneru
RUN uv pip install --system --no-cache -r requirements.txt
```

## 🧪 Postup při vývoji (Lokálně i na HAS)

S přechodem na `uv` se mění doporučené postupy (best practices) při přidávání nových závislostí:

1. **Přidání knihovny do kontejneru:**
   Pokud potřebuješ přidat knihovnu, přidej ji do `requirements.txt` příslušného kontejneru a spusť:
   `docker-compose build <jmeno_kontejneru>`
   *Build už nebude trvat minutu, ale několik málo sekund.*

2. **Testování MCP serveru bez Dockeru (Přes `uvx`):**
   Pokud si najdeš na GitHubu nějaký cizí užitečný MCP server (např. *Freshdesk*), už ho nemusíš balit do Dockeru nebo instalovat do systému HAS.
   Spustíš ho bezpečně, čistě a izolovaně jedním příkazem:
   ```bash
   uvx jmeno-balicku-z-pypi
   # Příklad:
   uvx freshdesk-mcp
   ```

## 🔍 Výsledky a E2E Ověření

Před nasazením do vývojové větve proběhly tyto validační testy:
- **Terminal MCP Build Test:** Sestavení kontejneru proběhlo úspěšně. Krok stahování závislostí zredukován na **4 sekundy**.
- **Kompatibilita:** Nástroj korektně zpracovává starší formáty `requirements.txt`, díky čemuž nebylo nutné přepisovat závislosti v žádném z 25 modulů.
- **Odstranění konfliktů NVM:** Jelikož Node verze pro určité CLI dělaly na Alpine problémy, instalace UV řeší pro Python naprostou flexibilitu bez ohledu na stáří podkladového OS (Alpine/Debian).

## 📊 Co dál? (Roadmap k 100% testům)
Větve `feature/uv-refactoring-and-optimization` slouží k dodělání posledního dílu skládačky:
- Implementace `pyproject.toml` ke každému modulu (náhrada za legacy `requirements.txt`).
- Napsání Unit a E2E testů pomocí `uv run pytest` napříč celou orchestrací. 
- Jakmile bude pokrytí kódu 100 %, budeme moci toto merge-ovat zpět do `masteru` a distribuovat na produkční HAS.
