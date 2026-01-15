# 🚀 MEGA-ORCHESTRATOR MIGRATION PLAN v2 - FINAL
**Datum**: 2025-10-16  
**Status**: Implementace s reálnými daty z HAS

## 📋 EXECUTIVE SUMMARY

Migrace současného systému na **Mega-Orchestrator** s integrací **ZEN MCP Server** (Claude Code tool) jako LLM Gateway. Vývoj probíhá ve VirtualBox (MX Linux), produkční nasazení na HAS až po dokončení.

---

## 🎯 KLÍČOVÉ ZMĚNY OD v1

### ✅ **Opravené chyby z v1:**
- **Port mapping**: 8xxx (internal) → 7xxx (external) ✅
- **HW requirements**: 2GB RAM místo 16GB (skutečné HAS specifikace)
- **MQTT porty**: 7018, 7019 přidány
- **Porty 10k+**: Portainer (10000), HomeAssistant (8123), AdGuard (3000)
- **ZEN MCP Server**: Claude Code tool pro multi-model AI collaboration
- **OS**: MX Linux pro VM (ne Alpine)
- **Dev tools**: oh-my-zsh, tmux, mc, htop, gh, node 22+, gemini-cli, cursor-agent

---

## 🏗️ ARCHITEKTURA SYSTÉMU

### **3-Machine Ecosystem:**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WORKSTATION   │    │   LLM SERVER    │    │      HAS        │
│                 │    │                 │    │                 │
│ • Development   │    │ • Ollama        │    │ • Mega-Orch.    │
│ • VirtualBox    │    │ • AI Models     │    │ • ZEN MCP       │
│ • MX Linux CLI  │    │ • Port 11434    │    │ • MCP Services  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Port Mapping (8xxx → 7xxx):**
```
# MEGA-ORCHESTRATOR (Centrální koordinátor)
7000: Mega-Orchestrator (Master) ← 8020
7001: Filesystem MCP ← 8000
7002: Git MCP ← 8001
7003: Terminal MCP ← 8002
7004: Memory MCP ← 8003
7005: Code MCP ← 8004
7006: Network MCP ← 8005
7007: System MCP ← 8006
7008: Security MCP ← 8007
7009: Database MCP ← 8008
7010: Web MCP ← 8009
7011: AI MCP ← 8010
7012: Docs MCP ← 8011
7013: Debug MCP ← 8012
7014: Vision MCP ← 8013
7015: Advanced Memory v2 ← 8014
7016: Video Processing ← 8015
7017: ZEN MCP Server ← 8016
7018: MQTT Broker ← 1883
7019: MQTT WebSocket ← 9001

# ZEN MCP SERVER (LLM Gateway - Claude Code tool)
8000: ZEN MCP Server (LLM Gateway) ← 8020
8001-8010: LLM Provider Adapters
8011-8020: Model Management
8021-8030: LLM Monitoring

# EXISTUJÍCÍ HAS SLUŽBY (10k+)
10000: Portainer
8123: HomeAssistant
3000: AdGuard
11434: Ollama (LLM Server)
```

---

## 📊 SKUTEČNÉ HW SPECIFIKACE HAS

### **Aktuální stav HAS:**
```
CPU: AMD E-300 APU (2 cores, 2 siblings)
RAM: 3.4G total, 1.7G used, 149.5M free, 1.5G available
Disk: 224G total, 34G used, 180G free (16% used)
OS: Alpine Linux (produkční)
```

### **Doporučené VM specifikace:**
```
CPU: 2 cores (AMD E-300 kompatibilní)
RAM: 2GB (dostatečné pro vývoj)
Disk: 50GB (dostatečné pro MX Linux + Docker)
OS: MX Linux CLI (GUI na vyžádání)
```

---

## 🔧 VIRTUALBOX SETUP (MX Linux)

### **1. MX Linux CLI Installation**
```bash
# 1. Stáhnout MX Linux ISO
# 2. Instalace s CLI default
# 3. Konfigurace pro CLI boot s GUI na vyžádání
sudo systemctl set-default multi-user.target  # CLI default
sudo systemctl enable lightdm.service         # GUI na vyžádání

# 4. Spuštění GUI manuálně
startx  # nebo
sudo systemctl start lightdm
```

### **2. Essential Dev Tools**
```bash
# Oh My Zsh
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"

# Essential tools
sudo apt update && sudo apt install -y \
    tmux \
    mc \
    htop \
    git \
    curl \
    wget \
    vim \
    nano \
    tree \
    jq \
    docker.io \
    docker-compose \
    nodejs \
    npm

# GitHub CLI
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update && sudo apt install gh

# Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Gemini CLI
npm install -g @google/generative-ai-cli

# Cursor Agent (pokud dostupný)
# Instalace podle dokumentace Cursor
```

---

## 🏛️ MEGA-ORCHESTRATOR ARCHITEKTURA

### **Současný stav (HAS):**
```
✅ Fungující služby:
- zen-coordinator (port 7000→8020) - bude přejmenován na Mega-Orchestrator
- filesystem-mcp (port 7001→8000)
- git-mcp (port 7002→8001)
- terminal-mcp (port 7003→8002)
- memory-mcp (port 7004→8003)
- code-mcp (port 7005→8004)
- web-mcp (port 7010→8009)
- ai-mcp (port 7011→8010)
- docs-mcp (port 7012→8011)
- debug-mcp (port 7013→8012)
- mqtt-broker (port 7018→1883)
- postgres (port 7019→5432)
- redis (port 7020→6379)
- qdrant (port 7021→6333)

❌ Placeholder služby (potřebují implementaci):
- network-mcp (port 7006→8005)
- system-mcp (port 7007→8006)
- security-mcp (port 7008→8007)
- database-mcp (port 7009→8008)
- vision-mcp (port 7014→8013)
- advanced-memory-v2 (port 7015→8014)
- video-processing (port 7016→8015)
```

### **ZEN MCP Server Integration:**
```bash
# Stažení ZEN MCP Server (Claude Code tool)
cd /home/orchestration
git clone https://github.com/david-strejc/zen-mcp-server.git
cd zen-mcp-server

# Analýza struktury
ls -la
cat README.md
cat package.json
```

---

## 📋 DETAILNÍ IMPLEMENTAČNÍ PLÁN

### **FÁZE 1: VirtualBox Setup & ZEN MCP Server (Týden 1-2)**

#### **1.1 VirtualBox Environment**
- [ ] Vytvořit VM s MX Linux CLI
- [ ] Instalace všech dev tools (oh-my-zsh, tmux, mc, htop, gh, node 22+, gemini-cli, cursor-agent)
- [ ] Docker & Docker Compose setup
- [ ] Git konfigurace s SSH klíči

#### **1.2 ZEN MCP Server Analysis**
- [ ] Clone ZEN MCP Server repository
- [ ] Analýza kódu a architektury
- [ ] Identifikace adaptačních bodů pro Gemini/multi-model
- [ ] Testování současné funkcionality

#### **1.3 Port Mapping Setup**
- [ ] Konfigurace port forwarding (8xxx→7xxx)
- [ ] Testování síťové konektivity
- [ ] MQTT broker setup

### **FÁZE 2: Mega-Orchestrator Refactoring (Týden 3-4)**

#### **2.1 Current System Analysis**
- [ ] Backup současné konfigurace
- [ ] Analýza současného zen-coordinator kódu
- [ ] Identifikace komponent pro přejmenování na Mega-Orchestrator
- [ ] Dokumentace současných MCP služeb

#### **2.2 Mega-Orchestrator Implementation**
- [ ] Refaktorování zen-coordinator → Mega-Orchestrator
- [ ] Implementace Provider Registry
- [ ] SAGE Mode Router dokončení
- [ ] Conversation Memory v2
- [ ] File Storage v2

#### **2.3 ZEN MCP Server Adaptation**
- [ ] Adaptace pro práci s Gemini/multi-model
- [ ] Integrace s Mega-Orchestrator
- [ ] LLM provider management
- [ ] Model selection logic

### **FÁZE 3: Missing MCP Services (Týden 5-6)**

#### **3.1 Network MCP (Port 7006→8005)**
```python
# /home/orchestration/mcp-servers/network-mcp/
# Funkce:
# - Network scanning
# - Port monitoring
# - Connection testing
# - Bandwidth monitoring
```

#### **3.2 System MCP (Port 7007→8006)**
```python
# /home/orchestration/mcp-servers/system-mcp/
# Funkce:
# - System monitoring
# - Process management
# - Resource monitoring
# - Log analysis
```

#### **3.3 Security MCP (Port 7008→8007)**
```python
# /home/orchestration/mcp-servers/security-mcp/
# Funkce:
# - Security scanning
# - Vulnerability assessment
# - Access control
# - Audit logging
```

#### **3.4 Database MCP (Port 7009→8008)**
```python
# /home/orchestration/mcp-servers/database-mcp/
# Funkce:
# - Database management
# - Query execution
# - Schema management
# - Backup/restore
```

### **FÁZE 4: Advanced Services (Týden 7-8)**

#### **4.1 Vision MCP (Port 7014→8013)**
```python
# /home/orchestration/mcp-servers/vision-mcp/
# Funkce:
# - Image analysis
# - OCR
# - Object detection
# - Image processing
```

#### **4.2 Advanced Memory v2 (Port 7015→8014)**
```python
# /home/orchestration/mcp-servers/advanced-memory-v2/
# Funkce:
# - Vector search
# - Semantic similarity
# - Conversation threading
# - File deduplication
# - Cross-tool memory
```

#### **4.3 Video Processing MCP (Port 7016→8015)**
```python
# /home/orchestration/mcp-servers/video-processing/
# Funkce:
# - Video analysis
# - Frame extraction
# - Audio extraction
# - Format conversion
# - Metadata extraction
```

### **FÁZE 5: Integration & Testing (Týden 9-10)**

#### **5.1 System Integration**
- [ ] Mega-Orchestrator + ZEN MCP Server integrace
- [ ] Všechny MCP služby testování
- [ ] Port mapping validace
- [ ] MQTT komunikace testování

#### **5.2 Performance Testing**
- [ ] Load testing
- [ ] Memory usage monitoring
- [ ] Response time testing
- [ ] Error handling testing

#### **5.3 Documentation**
- [ ] API dokumentace
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] User manual

### **FÁZE 6: Production Migration (Týden 11-12)**

#### **6.1 HAS Preparation**
- [ ] Backup současného HAS systému
- [ ] Příprava migračních skriptů
- [ ] Rollback plán

#### **6.2 Production Deployment**
- [ ] Migrace z VirtualBox na HAS
- [ ] Port mapping aktualizace
- [ ] Service monitoring setup
- [ ] Performance monitoring

#### **6.3 Post-Migration**
- [ ] Funkční testování
- [ ] Performance monitoring
- [ ] User training
- [ ] Documentation update

---

## 🔍 TECHNICKÉ DETAILY

### **Mega-Orchestrator Core Components:**
```python
class MegaOrchestrator:
    def __init__(self, port: int = 7000, backup_mode: bool = False):
        self.port = port
        self.backup_mode = backup_mode
        self.services = self._init_mcp_services()
        self.provider_registry = ModelProviderRegistry()
        self.conversation_memory = ConversationMemory()
        self.file_storage = FileStorage()
        self.sage_router = SAGEModeRouter()
        self.zen_mcp_client = ZENMCPClient()  # Nový
```

### **ZEN MCP Server Integration:**
```python
class ZENMCPClient:
    def __init__(self, zen_server_url: str = "http://localhost:8000"):
        self.zen_server_url = zen_server_url
        self.providers = self._init_providers()
    
    def route_request(self, request: dict, mode: SAGEMode) -> dict:
        # Routování na správný LLM provider
        # Claude Code + Gemini + další modely
        pass
```

### **Port Mapping Table:**
| Service | External Port | Internal Port | Status |
|---------|---------------|---------------|---------|
| Mega-Orchestrator | 7000 | 8020 | ✅ Funguje |
| Filesystem MCP | 7001 | 8000 | ✅ Funguje |
| Git MCP | 7002 | 8001 | ✅ Funguje |
| Terminal MCP | 7003 | 8002 | ✅ Funguje |
| Memory MCP | 7004 | 8003 | ✅ Funguje |
| Code MCP | 7005 | 8004 | ✅ Funguje |
| Network MCP | 7006 | 8005 | ❌ Potřebuje implementaci |
| System MCP | 7007 | 8006 | ❌ Potřebuje implementaci |
| Security MCP | 7008 | 8007 | ❌ Potřebuje implementaci |
| Database MCP | 7009 | 8008 | ❌ Potřebuje implementaci |
| Web MCP | 7010 | 8009 | ✅ Funguje |
| AI MCP | 7011 | 8010 | ✅ Funguje |
| Docs MCP | 7012 | 8011 | ✅ Funguje |
| Debug MCP | 7013 | 8012 | ✅ Funguje |
| Vision MCP | 7014 | 8013 | ❌ Potřebuje implementaci |
| Advanced Memory v2 | 7015 | 8014 | ❌ Potřebuje implementaci |
| Video Processing | 7016 | 8015 | ❌ Potřebuje implementaci |
| ZEN MCP Server | 7017 | 8016 | ❌ Potřebuje implementaci |
| MQTT Broker | 7018 | 1883 | ✅ Funguje |
| MQTT WebSocket | 7019 | 9001 | ❌ Potřebuje implementaci |
| PostgreSQL | 7019 | 5432 | ✅ Funguje |
| Redis | 7020 | 6379 | ✅ Funguje |
| Qdrant | 7021 | 6333 | ✅ Funguje |

### **MQTT Integration:**
```yaml
# MQTT Broker
mqtt-broker:
  image: eclipse-mosquitto:2
  container_name: mqtt-broker
  ports:
    - "7018:1883"    # MQTT
    - "7019:9001"    # WebSocket
  volumes:
    - ./mqtt/config:/mosquitto/config
    - ./mqtt/data:/mosquitto/data
    - ./mqtt/log:/mosquitto/log
```

---

## 🚨 KRITICKÉ POŽADAVKY

### **1. HAS "No Touch" Policy**
- ✅ Současný HAS zůstává netknutý během vývoje
- ✅ Všechny změny se testují ve VirtualBox
- ✅ Migrace na HAS až po dokončení a testování

### **2. Port Mapping Direction**
- ✅ **8xxx (internal) → 7xxx (external)** - OVĚŘENO
- ✅ Všechny služby používají správný směr mapování

### **3. ZEN MCP Server Context**
- ✅ Claude Code tool pro multi-model AI collaboration
- ✅ Adaptace pro práci s Gemini/multi-model
- ✅ Integrace s Mega-Orchestrator jako LLM Gateway

### **4. MX Linux CLI Focus**
- ✅ CLI default s GUI na vyžádání
- ✅ Všechny dev tools předinstalovány
- ✅ Docker & Docker Compose ready

---

## 📈 SUCCESS METRICS

### **Funkční metriky:**
- [ ] Všechny MCP služby fungují
- [ ] Port mapping správně nakonfigurován
- [ ] ZEN MCP Server integrován
- [ ] MQTT komunikace funkční
- [ ] Performance < 2s response time

### **Vývojové metriky:**
- [ ] VirtualBox environment ready
- [ ] Všechny dev tools nainstalovány
- [ ] Git workflow nastaven
- [ ] Testing pipeline funkční

### **Produkční metriky:**
- [ ] Migrace na HAS úspěšná
- [ ] Zero downtime deployment
- [ ] Monitoring a alerting funkční
- [ ] Dokumentace kompletní

---

## 🔄 ROLLBACK PLAN

### **V případě problémů:**
1. **VirtualBox**: Snapshot před každou fází
2. **HAS**: Kompletní backup před migrací
3. **Docker**: `docker-compose down && docker-compose up -d`
4. **Ports**: Revert na původní mapování
5. **Services**: Restart všech služeb

---

**Status**: ✅ Plán kompletní s reálnými daty z HAS  
**Next Step**: Implementace Fáze 1 - VirtualBox Setup
