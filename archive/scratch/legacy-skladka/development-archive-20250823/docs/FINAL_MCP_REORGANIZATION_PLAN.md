# 🎯 KOMPLETNÍ REORGANIZACE MCP ORCHESTRACE - FINÁLNÍ PLÁN

*Datum vytvoření: 16. srpna 2025*  
*Autor: Claude Code AI Assistant*  
*Prostředí: HAS 192.168.0.58 + GitHub milhy545/orchestration*  

---

## 📊 AKTUALIZOVANÁ TABULKA PORTŮ 8001-8030

| Port | Služba | Původní stav | Nový plán | Status | Akce |
|------|--------|--------------|-----------|---------|------|
| **8001** | Filesystem MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8002** | Git MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **8003** | Terminal MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8004** | Database MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **8005** | Memory MCP | ❌ Unhealthy | 🔧 Opravit | ❌ Fix | Database fix |
| **8006** | Network MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **8007** | System MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **8008** | Security MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **8009** | Config MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **8010** | **Perun Performance** | ❌ Chybí | 🚀 **Implementovat** | 🆕 **New** | **Vytvořit z todo** |
| **8011** | Research MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **8012** | **Contextual AI** | ✅ Advanced Memory | 🔄 **Správné označení** | 🔄 **Rename** | **Přejmenovat** |
| **8013** | Transcriber MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8014** | **Vision Processing** | 🔄 MQTT Broker | 🚀 **Nová služba** | 🆕 **New** | **Obrazy/OCR/Vision** |
| **8015** | **Advanced Memory** | ❌ Neexistuje | 🔄 **Přesun z 8012** | 🔄 **Move** | **Memory orchestrace** |
| **8016** | **Video Processing** | ❌ Volný | 🚀 **Nová služba** | 🆕 **New** | **Video/ffmpeg** |
| **8017** | **VOLNÝ** | ❌ Volný | ✅ Rezerva | ✅ Free | Budoucí expanze |
| **8018** | **MQTT Broker** | ❌ Volný | 🔄 **Přesun z 8014** | 🔄 **Move** | **Mosquitto** |
| **8019** | **MQTT MCP Server** | ❌ Volný | 🔄 **Přesun z 8015** | 🔄 **Move** | **MQTT tools** |
| **8020** | ZEN Coordinator | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8021** | PostgreSQL | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8022** | Redis | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8023** | Qdrant Vector | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8024** | PostgreSQL Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **8025** | Redis Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **8026** | Qdrant Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **8027** | Qdrant UI | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **8028** | Monitoring (Prometheus) | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Deploy monitoring |
| **8029** | Backup Service | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Automated backups |
| **8030** | Message Queue | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Task queuing |

## 🎯 IMPLEMENTAČNÍ FÁZE

### Fáze 1: Reorganizace MQTT služeb (8018-8019)
1. **Přesunout MQTT Broker** z portu 8014 na 8018
2. **Přesunout MQTT MCP Server** z portu 8015 na 8019  
3. **Dokončit build MQTT MCP Serveru** na novém portu
4. **Otestovat MQTT funkčnost** na nových portech

### Fáze 2: Memory služby reorganizace (8012, 8015)
1. **Přejmenovat Advanced Memory na Contextual AI** (port 8012)
2. **Vytvořit novou Advanced Memory službu** na portu 8015
3. **Aktualizovat docker-compose** pro správné port mapping
4. **Otestovat oba memory systémy** samostatně

### Fáze 3: Vision & Video Processing (8014, 8016)
1. **Vytvořit Vision Processing MCP** (port 8014)
   - Image analysis, OCR, computer vision
   - Integration s Gemini Vision API
2. **Vytvořit Video Processing MCP** (port 8016)  
   - Video transcoding, frame extraction, analysis
   - Integration s ffmpeg a video AI models

### Fáze 4: Dokončení chybějících služeb
1. **Implementovat Perun Performance Monitor** (port 8010)
2. **Implementovat placeholder services** (8006-8009)
3. **Spustit Wrapper services** (8024-8026)
4. **Aktivovat Management services** (8028-8030)

### Fáze 5: Oprava problémových služeb  
1. **Debug Git MCP** (8002) - routing fix
2. **Debug Database MCP** (8004) - connection fix
3. **Fix Memory MCP** (8005) - database error
4. **Debug Research MCP** (8011) - service fix

### Fáze 6: Testing & Production finalizace
1. **Kompletní testing** všech 30 portů
2. **ZEN Coordinator integration** pro všechny nové služby
3. **Portainer stack verification** - všechny v orchestration stacku
4. **Performance testing** a optimalizace
5. **Final commit & GitHub push** + dokumentace

## 📈 VÝSLEDEK

- **30/30 portů aktivních** (100% využití)
- **MQTT správně umístěno** (8018-8019)
- **Vision/Video processing** implementováno
- **Memory services logicky rozděleno**
- **Kompletní MCP orchestrace** ready for production
- **Vše v Portainer orchestration stacku**

## 🛠️ TECHNICKÉ SPECIFIKACE

### MQTT Services (8018-8019)
- **8018**: Eclipse Mosquitto 2.0 broker s authentication
- **8019**: Python MCP Server s gmqtt, JSON-RPC 2.0 compliant

### Vision/Video Processing (8014, 8016)
- **8014**: Vision Processing - Gemini Vision API, OCR, image analysis
- **8016**: Video Processing - ffmpeg, frame extraction, video AI

### Memory Architecture (8012, 8015)
- **8012**: Contextual AI - AI conversation context management
- **8015**: Advanced Memory - Vector search, semantic similarity

### Performance & Monitoring (8010, 8028)
- **8010**: Perun Performance Monitor - System metrics, optimization
- **8028**: Prometheus Monitoring - Health checks, alerting

## 📄 IMPLEMENTATION STATUS

- [x] Plán vytvořen a schválen
- [x] Dokumentace uložena
- [ ] MQTT reorganizace (Fáze 1)
- [ ] Memory reorganizace (Fáze 2) 
- [ ] Vision/Video implementace (Fáze 3)
- [ ] Chybějící služby (Fáze 4)
- [ ] Debug problémových služeb (Fáze 5)
- [ ] Testing & finalizace (Fáze 6)

---

*Tento dokument představuje kompletní strategii pro dokončení MCP orchestrace s využitím všech portů 8001-8030 a vytvořením enterprise-ready AI infrastructure.*