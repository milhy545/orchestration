# 🌟 MCP Orchestrační Systém

> **Pokročilá Model Context Protocol (MCP) orchestrační platforma s jednotným HTTP rozhraním pro více kontejnerizovaných mikroservisů**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)

## ✨ Co Dělá Tento Projekt Výjimečným

Toto je **produkční MCP orchestrační systém**, který demonstruje enterprise-level architektonické vzory s:

- 🎯 **Jednotné HTTP Rozhraní** - Jediný endpoint pro všechny MCP služby
- 🏗️ **Service Mesh Architektura** - Kontejnerizované mikroservisy se sdílenou infrastrukturou
- 🔄 **Automatické Monitorování** - Vestavěné zjišťování služeb a health checky
- 🔐 **Security-First Design** - Environment-based tajnosti, žádné hardcoded kredenciály
- 📊 **Integrace Vektorové Databáze** - Pokročilá AI paměť se sémantickým vyhledáváním
- 🧪 **Komprehenzivní Testování** - Unit, výkonnostní, bezpečnostní a failure recovery testy
- 📈 **Produkční Monitoring** - Redis caching, PostgreSQL persistence, logování

## 🏛️ Přehled Architektury

```
┌─────────────────┐    ┌──────────────────────────────────────┐
│   HTTP Klient   │────│           Zen Koordinátor            │
└─────────────────┘    │         (Port 8020)                 │
                       │    HTTP ↔ MCP Protokol Most         │
                       └──────────────────────────────────────┘
                                          │
                       ┌──────────────────┼──────────────────┐
                       │                  │                  │
            ┌──────────▼────┐  ┌─────────▼────┐  ┌─────────▼────┐
            │ Filesystem MCP │  │ Memory MCP   │  │ Terminal MCP │
            │   (8001)       │  │   (8005)     │  │   (8003)     │
            └───────────────┘  └──────────────┘  └──────────────┘
                       │                  │                  │
                       └──────────────────┼──────────────────┘
                                          │
                       ┌──────────────────▼──────────────────┐
                       │        Sdílená Infrastruktura       │
                       │  PostgreSQL │ Redis │ Qdrant Vector │
                       │   (5432)    │ (6379)│    (6333)     │
                       └─────────────────────────────────────┘
```

## 🚀 Rychlý Start

### Předpoklady
- Docker & Docker Compose
- Doporučeno 4GB+ RAM
- Linux/macOS/WSL2

### 1. Klonování & Konfigurace
```bash
git clone https://github.com/milhy545/orchestration.git
cd orchestration

# Kopírování environment šablony
cp .env.example .env

# Úprava .env s vašimi API klíči
nano .env
```

### 2. Spuštění Všeho
```bash
# Spuštění všech služeb
docker-compose up -d

# Ověření zdraví systému
./scripts/health-check.sh
```

### 3. Testování Systému
```bash
# Spuštění komprehenzivních testů
./tests/unit/orchestration_workflow_test.sh

# Výkonnostní benchmarking
./tests/performance/stress_load_test.sh
```

## 🛠️ MCP Služby

| Služba | Port | Účel | Klíčové Funkce |
|--------|------|------|----------------|
| **Zen Koordinátor** | 8020 | HTTP ↔ MCP Most | Směrování požadavků, překlad protokolu |
| **Filesystem MCP** | 8001 | Souborové Operace | Čtení, zápis, vyhledávání, analýza |
| **Git MCP** | 8002 | Správa Verzí | Status, log, diff, historie |
| **Terminal MCP** | 8003 | Spouštění Příkazů | Systémové příkazy, správa procesů |
| **Database MCP** | 8004 | Databázové Operace | Dotazy, schéma, zálohy, připojení |
| **Memory MCP** | 8005 | Úložiště Kontextu | Jednoduchý key-value, FastAPI interface |
| **Pokročilá Paměť** | 8006 | AI Paměť | Vektorové vyhledávání, sémantická podobnost |
| **Qdrant Vector** | 8007 | Vektorová Databáze | Embeddingy, vyhledávání podobnosti |
| **Transcriber** | 8008 | Zpracování Audia | WebM transkripce, analýza audia |
| **Research MCP** | 8011 | AI Výzkum | Perplexity integrace, shromažďování dat |

## 🔧 Vývojářský Workflow

### Správa Služeb
```bash
# Monitoring všech služeb
./scripts/monitor-services.sh

# Kontrola logů konkrétní služby
docker logs mcp-filesystem

# Restart individuální služby
docker-compose restart memory-mcp
```

### Testovací Suite
```bash
# Unit testy
./tests/unit/memory_crud_test.sh
./tests/unit/orchestration_workflow_test.sh

# Výkonnostní testování
./tests/performance/stress_load_test.sh

# Bezpečnostní hodnocení
./tests/security/security_assessment_test.sh

# Failure recovery
./tests/failure/failure_recovery_test.sh
```

## 📡 Použití API

### Vytváření Požadavků
```bash
# Spuštění terminálového příkazu
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "execute_command",
    "arguments": {"command": "ls -la"}
  }'

# Uložení paměti
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "key": "stav_projektu",
      "content": "Systém běží perfektně"
    }
  }'
```

## 🔐 Bezpečnostní Funkce

- **Environment-based Konfigurace** - Žádné hardcoded tajnosti
- **Kontejnerová Izolace** - Služby běží v izolovaných kontejnerech
- **Síťová Segmentace** - Interní Docker síť
- **Správa Kredenciálů** - PostgreSQL autentifikace
- **Ochrana API Klíčů** - Externí service klíče přes environment
- **Bezpečnost Persistentních Dat** - Separátní data volumes

## 🎯 Proč To Má Význam

Toto není jen další kontejnerový setup - je to **kompletní enterprise architektura**, která ukazuje:

✅ **Škálovatelné Designové Vzory**  
✅ **Bezpečnostní Best Practices**  
✅ **Komprehenzivní Testování**  
✅ **Produkční Monitoring**  
✅ **Service Mesh Architekturu**  
✅ **AI Integration Patterns**  

Perfektní pro učení, rozšiřování, nebo použití jako základ pro produkční systémy.

## 📄 Licence

MIT License - klidně použijte jako základ pro vaše vlastní MCP orchestrační systémy.

---

<p align="center">
  <strong>🚀 Připraveni orchestrovat vaše MCP služby? Označte tento repo hvězdičkou! 🚀</strong>
</p>