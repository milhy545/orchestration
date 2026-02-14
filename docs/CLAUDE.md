# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## !!!DŮLEŽITÉ!!! 🚨 REMOTE REPOSITORY CONNECTION

### **SKUTEČNÝ LOKÁLNÍ REPOSITORY:**
```bash
📍 Pravý lokální repository: ssh root@192.168.0.58:/home/orchestration/
🌐 HAS Production Environment: 192.168.0.58
🔗 GitHub Repository: milhy545/orchestration (live sync'd)
📂 This folder je POUZE workspace proxy - NOT the real repository!
```

### **⚠️ CRITICAL WORKSPACE RULES:**

1. **REMOTE WORK ONLY:**
   - Všechny změny kódu, commits, pushes se dělají na HAS (192.168.0.58)
   - Claude spuštěný v této složce pracuje vzdáleně přes SSH
   - Lokální změny se automaticky synchronizují s `/home/orchestration/` na HAS

2. **ZAKÁZANÉ LOKÁLNÍ SOUBORY:**
   - ❌ ŽÁDNÉ git soubory (.git/, .gitignore, atd.)
   - ❌ ŽÁDNÉ produkční soubory (docker-compose.yml, zen_mcp_server.py, atd.)
   - ❌ ŽÁDNÉ konfigurace (.env, config/, atd.)
   - ❌ ŽÁDNÉ zdrojové kódy (Python, JavaScript, Docker files)

3. **POVOLENÉ LOKÁLNÍ SOUBORY:**
   - ✅ Claude interní soubory (/.claude/, claude-*.json)
   - ✅ Dokumentace a poznámky (*.md soubory)
   - ✅ Temporary workspace files
   - ✅ AI Agents (claude's agents) interní soubory

4. **DEPLOYMENT WORKFLOW:**
   ```bash
   # Práce s dokumentací lokálně
   vim notes.md, documentation.md, analysis.md
   
   # Transfer na HAS a push na GitHub
   scp *.md root@192.168.0.58:/home/orchestration/docs/
   ssh root@192.168.0.58 "cd /home/orchestration && git add docs/ && git commit && git push"
   ```

---

## 🏗️ ORCHESTRATION PROJECT INFO

### **Project Overview:**
- **Repository**: `milhy545/orchestration` (GitHub)
- **Production**: HAS 192.168.0.58:/home/orchestration/
- **Architecture**: MCP (Model Context Protocol) microservices orchestration
- **Core Component**: ZEN MCP Server (408 lines, 16,454 bytes)

### **Live Production Services (HAS):**
```
Port 7001: Filesystem MCP    (Up 26h)
Port 7002: Git MCP           (Up 26h)  
Port 7003: Terminal MCP      (Up 26h)
Port 7004: Database MCP      (Up 26h)
Port 7005: Memory MCP        (Up 26h)
Port 7011: Research MCP      (Up 26h)
Port 7012: Advanced Memory   (Up 26h) 🆕
Port 7013: Transcriber MCP   (Up 26h, unhealthy) ⚠️
Port 7021: PostgreSQL        (Up 26h)
Port 7022: Redis             (Up 26h)
```

### **Development Stack:**
- **Languages**: Python 3.12+, Node.js 18+
- **Infrastructure**: Docker Compose, PostgreSQL, Redis, Qdrant
- **Architecture**: Microservices with unified HTTP interface
- **Protocol**: JSON-RPC 2.0 for MCP communication

### **Key Components:**
- **ZEN MCP Server**: Central orchestration hub with 30+ tools
- **Docker Infrastructure**: Complete containerized microservices
- **Vector Database**: Qdrant for AI embeddings and semantic search  
- **Memory System**: Advanced memory with Gemini AI integration
- **Monitoring**: Comprehensive health checks and service discovery

### **Common Development Commands (Remote HAS):**
```bash
# Connect to HAS
ssh root@192.168.0.58

# Navigate to repository
cd /home/orchestration

# Service management
docker ps                           # Check service status
docker-compose ps                   # View all orchestration services
docker logs mcp-transcriber         # View specific service logs
docker-compose restart [service]    # Restart specific service

# Development setup
cp .env.example .env                # Configure environment
docker-compose up -d                # Start all services
docker-compose down                 # Stop all services

# Health monitoring
./scripts/health-check.sh           # Check all service health
./scripts/monitor-services.sh       # Continuous monitoring
curl http://localhost:7000/health   # Test ZEN coordinator

# Testing
./tests/unit/orchestration_workflow_test.sh    # Unit tests
./tests/performance/stress_load_test.sh        # Performance tests
./tests/security/security_assessment_test.sh   # Security tests

# Git operations (always on HAS)
git status
git add .
git commit -m "Update message"
git push origin master

# ZEN Coordinator testing
curl http://192.168.0.58:7000/services         # List MCP services
curl http://192.168.0.58:7000/tools/list       # List available tools
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool":"store_memory","arguments":{"content":"test"}}'
```

### **Project Status:**
- ✅ Live production environment (26h uptime)
- ✅ GitHub synchronized
- ✅ 10+ microservices running
- ⚠️ Transcriber service needs debugging
- 📈 Active development since July 2025

---

## 🏗️ ARCHITECTURE & CODE STRUCTURE

### **ZEN MCP Server (Core Component):**
- **Location**: `/home/orchestration/zen_mcp_server.py`
- **Size**: 408 lines, 16,454 bytes
- **Protocol**: JSON-RPC 2.0 over stdin/stdout
- **Tools**: 30+ specialized tools for orchestration

### **MCP Microservices Architecture:**
```
Internet → ZEN Coordinator (7000) → MCP Services (7001-7017)
          ✅ Security Gateway      ❌ Not directly accessible
```

### **Available MCP Tools via ZEN Coordinator:**
```python
# Memory operations (ports 7005, 7012)
"store_memory", "search_memories", "get_context", "memory_stats"

# Filesystem operations (port 7001)  
"file_read", "file_write", "file_list", "file_search"

# Git operations (port 7002)
"git_status", "git_commit", "git_push", "git_log", "git_diff"

# Terminal operations (port 7003)
"execute_command", "shell_command", "system_info"

# Database operations (port 7004)
"database_query", "database_execute", "database_schema"

# Research operations (port 7011)
"research_query", "perplexity_search", "web_search"

# Audio/transcription (port 7013 - currently unhealthy)
"transcribe_webm", "transcribe_url", "audio_convert"
```

### **Infrastructure Stack:**
- **Docker Compose**: Complete microservices orchestration
- **PostgreSQL** (port 7021): Primary database for MCP services
- **Redis** (port 7022): Caching and session management
- **Qdrant** (port 6333): Vector database for AI embeddings
- **Health Monitoring**: Comprehensive service discovery and health checks

### **Code Patterns:**
- **JSON-RPC 2.0**: Standard MCP protocol implementation
- **Async/await**: Python asyncio for concurrent operations
- **Error Handling**: Granular error codes and graceful degradation
- **Service Discovery**: Dynamic routing based on tool names
- **Security**: All external access through ZEN Coordinator only

---

## 🔧 DEVELOPMENT WORKFLOW

### **Local Workspace Management:**
This directory serves as a **LOCAL PROXY** for remote repository work:
- Documentation and analysis files only
- No source code or configuration files
- All development happens on HAS (192.168.0.58)

### **Typical Development Cycle:**
1. **Analysis/Documentation** - Work locally in this directory
2. **Remote Development** - SSH to HAS for code changes
3. **Testing** - Run tests on HAS production environment
4. **Git Operations** - Always commit/push from HAS

### **Environment Variables (HAS only):**
```bash
# PostgreSQL connection
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mcp_unified
POSTGRES_USER=mcp_admin

# Redis connection
REDIS_HOST=localhost
REDIS_PORT=6379

# Qdrant vector database
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### **Debugging Common Issues:**
```bash
# Transcriber service troubleshooting
docker logs mcp-transcriber
docker restart mcp-transcriber

# Memory service diagnostics  
curl http://192.168.0.58:7005/health
curl http://192.168.0.58:7012/health

# ZEN Coordinator health check
curl http://192.168.0.58:7000/health
```

---

## ⚠️ CRITICAL REMINDERS

1. **NEVER create source code files locally** - Only documentation/analysis
2. **ALL git operations on HAS** - This workspace has no .git directory
3. **Production environment is live** - Changes affect running services
4. **Security model**: Services only accessible through ZEN Coordinator
5. **Multi-environment sync**: GitHub ↔ HAS ↔ Local documentation

---
!!!Nenahrazuj timto CLAUDE.md souborem hlavni ~/Develop/CLAUDE.md ktery obsahuje celkove obecnou memory!!! 
---
*This workspace serves as a LOCAL PROXY for remote HAS repository work.*  
*Always remember: Real work happens on 192.168.0.58:/home/orchestration/*