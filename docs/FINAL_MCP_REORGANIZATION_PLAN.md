# 🎯 KOMPLETNÍ REORGANIZACE MCP ORCHESTRACE - FINÁLNÍ PLÁN

*Datum vytvoření: 16. srpna 2025*  
*Autor: Claude Code AI Assistant*  
*Prostředí: HAS 192.168.0.58 + GitHub milhy545/orchestration*  

---

## 📊 AKTUALIZOVANÁ TABULKA PORTŮ 7001-7030

| Port | Služba | Původní stav | Nový plán | Status | Akce |
|------|--------|--------------|-----------|---------|------|
| **7001** | Filesystem MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7002** | Git MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **7003** | Terminal MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7004** | Database MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **7005** | Memory MCP | ❌ Unhealthy | 🔧 Opravit | ❌ Fix | Database fix |
| **7006** | Network MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **7007** | System MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **7008** | Security MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **7009** | Config MCP | ❌ Placeholder | 🚀 Implementovat | 🆕 New | Vytvořit |
| **7010** | **Perun Performance** | ❌ Chybí | 🚀 **Implementovat** | 🆕 **New** | **Vytvořit z todo** |
| **7011** | Research MCP | ⚠️ HTTP 404 | 🔧 Opravit | ⚠️ Fix | Debug & fix |
| **7012** | **Contextual AI** | ✅ Advanced Memory | 🔄 **Správné označení** | 🔄 **Rename** | **Přejmenovat** |
| **7013** | Transcriber MCP | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7014** | **Vision Processing** | 🔄 MQTT Broker | 🚀 **Nová služba** | 🆕 **New** | **Obrazy/OCR/Vision** |
| **7015** | **Advanced Memory** | ❌ Neexistuje | 🔄 **Přesun z 7012** | 🔄 **Move** | **Memory orchestrace** |
| **7016** | **Video Processing** | ❌ Volný | 🚀 **Nová služba** | 🆕 **New** | **Video/ffmpeg** |
| **7017** | **VOLNÝ** | ❌ Volný | ✅ Rezerva | ✅ Free | Budoucí expanze |
| **7018** | **MQTT Broker** | ❌ Volný | 🔄 **Přesun z 7014** | 🔄 **Move** | **Mosquitto** |
| **7019** | **MQTT MCP Server** | ❌ Volný | 🔄 **Přesun z 7015** | 🔄 **Move** | **MQTT tools** |
| **7000** | ZEN Coordinator | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7021** | PostgreSQL | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7022** | Redis | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7023** | Qdrant Vector | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7024** | PostgreSQL Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **7025** | Redis Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **7026** | Qdrant Wrapper | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Build & deploy |
| **7027** | Qdrant UI | ✅ Funguje | ✅ Zachovat | ✅ OK | - |
| **7028** | Monitoring (Prometheus) | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Deploy monitoring |
| **7029** | Backup Service | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Automated backups |
| **7030** | Message Queue | ❌ Nespuštěno | 🚀 Spustit | 🔄 Start | Task queuing |

## 🎯 IMPLEMENTAČNÍ FÁZE

### Fáze 1: Reorganizace MQTT služeb (7018-7019)
1. **Přesunout MQTT Broker** z portu 7014 na 7018
2. **Přesunout MQTT MCP Server** z portu 7015 na 7019  
3. **Dokončit build MQTT MCP Serveru** na novém portu
4. **Otestovat MQTT funkčnost** na nových portech

### Fáze 2: Memory služby reorganizace (7012, 7015)
1. **Přejmenovat Advanced Memory na Contextual AI** (port 7012)
2. **Vytvořit novou Advanced Memory službu** na portu 7015
3. **Aktualizovat docker-compose** pro správné port mapping
4. **Otestovat oba memory systémy** samostatně

### Fáze 3: Vision & Video Processing (7014, 7016)
1. **Vytvořit Vision Processing MCP** (port 7014)
   - Image analysis, OCR, computer vision
   - Integration s Gemini Vision API
2. **Vytvořit Video Processing MCP** (port 7016)  
   - Video transcoding, frame extraction, analysis
   - Integration s ffmpeg a video AI models

### Fáze 4: Dokončení chybějících služeb
1. **Implementovat Perun Performance Monitor** (port 7010)
2. **Implementovat placeholder services** (7006-7009)
3. **Spustit Wrapper services** (7024-7026)
4. **Aktivovat Management services** (7028-7030)

### Fáze 5: Oprava problémových služeb  
1. **Debug Git MCP** (7002) - routing fix
2. **Debug Database MCP** (7004) - connection fix
3. **Fix Memory MCP** (7005) - database error
4. **Debug Research MCP** (7011) - service fix

### Fáze 6: Testing & Production finalizace
1. **Kompletní testing** všech 30 portů
2. **ZEN Coordinator integration** pro všechny nové služby
3. **Portainer stack verification** - všechny v orchestration stacku
4. **Performance testing** a optimalizace
5. **Final commit & GitHub push** + dokumentace

## 📈 VÝSLEDEK

- **30/30 portů aktivních** (100% využití)
- **MQTT správně umístěno** (7018-7019)
- **Vision/Video processing** implementováno
- **Memory services logicky rozděleno**
- **Kompletní MCP orchestrace** ready for production
- **Vše v Portainer orchestration stacku**

## 🛠️ TECHNICKÉ SPECIFIKACE

### MQTT Services (7018-7019)
- **7018**: Eclipse Mosquitto 2.0 broker s authentication
- **7019**: Python MCP Server s gmqtt, JSON-RPC 2.0 compliant

### Vision/Video Processing (7014, 7016)
- **7014**: Vision Processing - Gemini Vision API, OCR, image analysis
- **7016**: Video Processing - ffmpeg, frame extraction, video AI

### Memory Architecture (7012, 7015)
- **7012**: Contextual AI - AI conversation context management
- **7015**: Advanced Memory - Vector search, semantic similarity

### Performance & Monitoring (7010, 7028)
- **7010**: Perun Performance Monitor - System metrics, optimization
- **7028**: Prometheus Monitoring - Health checks, alerting

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

*Tento dokument představuje kompletní strategii pro dokončení MCP orchestrace s využitím všech portů 7001-7030 a vytvořením enterprise-ready AI infrastructure.*