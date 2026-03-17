# 🚀 MEGA-ORCHESTRATOR MIGRATION - SHORT TODO LIST

## 📊 PORT MAPPING - SKUTEČNÝ STAV HAS

| Service | External Port | Internal Port | Status |
|---------|---------------|---------------|---------|
| Mega-Orchestrator | 7000 | 8020 | ✅ Funguje |
| Filesystem MCP | 7001 | 8000 | ✅ Funguje |
| Git MCP | 7002 | 8000 | ✅ Funguje |
| Database MCP | 7004 | 8000 | ✅ Funguje |
| Memory MCP | 7005 | 8000 | ✅ Funguje |
| Network MCP | 7006 | 8000 | ❌ Potřebuje implementaci |
| System MCP | 7007 | 8000 | ❌ Potřebuje implementaci |
| Security MCP | 7008 | 8000 | ❌ Potřebuje implementaci |
| Config MCP | 7009 | 8000 | ✅ Funguje |
| Log MCP | 7010 | 8000 | ✅ Funguje |
| AI MCP | 7011 | 8000 | ❌ Potřebuje implementaci |
| Advanced Memory MCP | 7012 | 8000 | ✅ Funguje |
| Debug MCP | 7013 | 8000 | ❌ Potřebuje implementaci |
| Vision MCP | 7014 | 8000 | ❌ Potřebuje implementaci |
| Video Processing | 7015 | 8000 | ❌ Potřebuje implementaci |
| ZEN MCP Server | 7016 | 8000 | ❌ Potřebuje implementaci |
| Web MCP | 7017 | 8000 | ❌ Potřebuje implementaci |
| MQTT Broker | 7018 | 1883 | ✅ Funguje |
| MQTT WebSocket | 7019 | 9001 | ❌ Potřebuje implementaci |
| Redis | 7020 | 6379 | ✅ Funguje |
| Qdrant | 7021 | 6333 | ✅ Funguje |
| PostgreSQL | 7022 | 5432 | ✅ Funguje |
| Monitoring | 7023 | 9090 | ✅ Funguje |
| Backup MCP | 7024 | 8000 | ✅ Funguje |
| Message Queue | 7025 | 6379 | ✅ Funguje |

## 🖥️ HW SPECIFIKACE HAS

```
CPU: AMD E-300 APU (2 cores, 2 siblings)
RAM: 3.4G total, 1.7G used, 149.5M free, 1.5G available
Disk: 224G total, 34G used, 180G free (16% used)
OS: Alpine Linux (produkční)
```

## 📋 TODO LIST

### **FÁZE 1: VirtualBox Setup (Týden 1-2)**

#### **1.1 MX Linux VM**
- [ ] Vytvořit VirtualBox VM (2GB RAM, 50GB disk)
- [ ] Instalace MX Linux CLI (GUI na vyžádání)
- [ ] Konfigurace: `sudo systemctl set-default multi-user.target`
- [ ] GUI start: `startx` nebo `sudo systemctl start lightdm`

#### **1.2 Dev Tools**
- [ ] Oh My Zsh: `sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"`
- [ ] Essential tools: `sudo apt install -y tmux mc htop git curl wget vim nano tree jq docker.io docker-compose nodejs npm`
- [ ] GitHub CLI: `curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg`
- [ ] Node.js 22+: `curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs`
- [ ] Gemini CLI: `npm install -g @google/generative-ai-cli`
- [ ] Cursor Agent: podle dokumentace

#### **1.3 ZEN MCP Server**
- [ ] Clone: `git clone https://github.com/david-strejc/zen-mcp-server.git`
- [ ] Analýza: `ls -la && cat README.md && cat package.json`
- [ ] Testování současné funkcionality

### **FÁZE 2: Mega-Orchestrator Refactoring (Týden 3-4)**

#### **2.1 Backup & Analysis**
- [ ] Backup HAS: `tar -czf mega_orchestrator_backup_$(date +%Y%m%d_%H%M%S).tar.gz /home/orchestration/`
- [ ] Analýza mega-orchestrator kódu
- [ ] Identifikace komponent pro přejmenování

#### **2.2 Mega-Orchestrator Implementation**
- [ ] Refaktorování mega-orchestrator → Mega-Orchestrator
- [ ] Implementace Provider Registry
- [ ] SAGE Mode Router dokončení
- [ ] Conversation Memory v2
- [ ] File Storage v2

#### **2.3 ZEN MCP Server Integration**
- [ ] Adaptace pro Gemini/multi-model
- [ ] Integrace s Mega-Orchestrator
- [ ] LLM provider management

### **FÁZE 3: Missing MCP Services (Týden 5-6)**

#### **3.1 Network MCP (Port 7006)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/network-mcp/`
- [ ] Implementovat: Network scanning, Port monitoring, Connection testing
- [ ] Dockerfile a docker-compose.yml

#### **3.2 System MCP (Port 7007)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/system-mcp/`
- [ ] Implementovat: System monitoring, Process management, Resource monitoring
- [ ] Dockerfile a docker-compose.yml

#### **3.3 Security MCP (Port 7008)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/security-mcp/`
- [ ] Implementovat: Security scanning, Vulnerability assessment, Access control
- [ ] Dockerfile a docker-compose.yml

#### **3.4 AI MCP (Port 7011)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/ai-mcp/`
- [ ] Implementovat: AI model management, Inference routing, Model switching
- [ ] Dockerfile a docker-compose.yml

### **FÁZE 4: Advanced Services (Týden 7-8)**

#### **4.1 Vision MCP (Port 7014)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/vision-mcp/`
- [ ] Implementovat: Image analysis, OCR, Object detection
- [ ] Dockerfile a docker-compose.yml

#### **4.2 Video Processing MCP (Port 7015)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/video-processing/`
- [ ] Implementovat: Video analysis, Frame extraction, Audio extraction
- [ ] Dockerfile a docker-compose.yml

#### **4.3 Web MCP (Port 7017)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/web-mcp/`
- [ ] Implementovat: Web scraping, HTTP requests, API testing
- [ ] Dockerfile a docker-compose.yml

#### **4.4 Debug MCP (Port 7013)**
- [ ] Vytvořit `/home/orchestration/mcp-servers/debug-mcp/`
- [ ] Implementovat: Debugging tools, Log analysis, Performance profiling
- [ ] Dockerfile a docker-compose.yml

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

## 🚨 KRITICKÉ POŽADAVKY

- ✅ **HAS "No Touch" Policy** - současný HAS zůstává netknutý během vývoje
- ✅ **Port mapping**: 8xxx (internal) → 7xxx (external)
- ✅ **ZEN MCP Server**: Claude Code tool pro multi-model AI collaboration
- ✅ **MX Linux CLI**: CLI default s GUI na vyžádání

## 🔄 ROLLBACK PLAN

1. **VirtualBox**: Snapshot před každou fází
2. **HAS**: Kompletní backup před migrací
3. **Docker**: `docker-compose down && docker-compose up -d`
4. **Ports**: Revert na původní mapování
5. **Services**: Restart všech služeb

---

**Status**: ✅ Plán kompletní s reálnými daty z HAS  
**Next Step**: Implementace Fáze 1 - VirtualBox Setup
