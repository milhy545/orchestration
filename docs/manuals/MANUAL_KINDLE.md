# MCP Orchestration Platform - Kompletní Manuál

> Model Context Protocol (MCP) microservices orchestration platform s unified HTTP interface

---

## Obsah

1. [Úvod a přehled](#úvod-a-přehled)
2. [Architektura systému](#architektura-systému)
3. [Rychlý start](#rychlý-start)
4. [Konfigurace](#konfigurace)
5. [MCP služby](#mcp-služby)
6. [API dokumentace](#api-dokumentace)
7. [Testování](#testování)
8. [Bezpečnost](#bezpečnost)
9. [Monitoring a diagnostika](#monitoring-a-diagnostika)
10. [Claude AI Agent](#claude-ai-agent)
11. [Deployment](#deployment)
12. [Troubleshooting](#troubleshooting)
13. [Výkonnost a škálování](#výkonnost-a-škálování)
14. [Vývoj a přispívání](#vývoj-a-přispívání)

---

## Úvod a přehled

### Co je MCP Orchestration Platform?

MCP Orchestration Platform je enterprise-level microservices systém implementující Model Context Protocol (MCP) specifikaci. Poskytuje unified HTTP interface pro AI agenty a aplikace s 28+ specializovanými nástroji napříč 7 core službami.

### Klíčové vlastnosti

- **Unified HTTP Interface** - Jediný endpoint pro všechny MCP služby
- **Service Mesh Architecture** - Containerized microservices se shared infrastructure
- **Automatic Health Monitoring** - Built-in service discovery a health checks
- **Security-First Design** - Environment-based secrets, žádné hardcoded credentials
- **Vector Database Integration** - Advanced AI memory s semantic search
- **Comprehensive Testing** - Unit, performance, security, a failure recovery testy
- **Production Monitoring** - Redis caching, PostgreSQL persistence, logging

### Proč tento systém?

Tento projekt demonstruje production-ready patterns pro:
- Microservices architecture
- Container orchestration
- API design
- Testing strategies
- Security practices
- AI integration patterns

---

## Architektura systému

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────────────────────────┐
│   HTTP Client   │────│           ZEN Coordinator            │
└─────────────────┘    │         (Port 7000)                 │
                       │    HTTP ↔ MCP Protocol Bridge        │
                       └──────────────────────────────────────┘
                                          │
                       ┌──────────────────┼──────────────────┐
                       │                  │                  │
            ┌──────────▼────┐  ┌─────────▼────┐  ┌─────────▼────┐
            │ Filesystem MCP │  │ Memory MCP   │  │ Terminal MCP │
            │   (7001)       │  │   (7005)     │  │   (7003)     │
            └───────────────┘  └──────────────┘  └──────────────┘
                       │                  │                  │
                       └──────────────────┼──────────────────┘
                                          │
                       ┌──────────────────▼──────────────────┐
                       │        Shared Infrastructure        │
                       │  PostgreSQL │ Redis │ Qdrant Vector │
                       │   (5432)    │ (6379)│    (6333)     │
                       └─────────────────────────────────────┘
```

### Security Architecture

#### Zero Trust Network Model

Platforma implementuje Zero Trust security model:

1. **Single Entry Point**: Pouze ZEN Coordinator (port 7000) je exposed externally
2. **Internal Isolation**: MCP služby (7001-7017) nejsou přímo dostupné
3. **Service Mesh**: Všechna internal komunikace je kontrolována a monitorována
4. **Authentication**: JWT-based authentication pro API access
5. **Authorization**: Role-based access control pro MCP tools

### Service Categories

#### Core MCP Services (7001-7010)
- **Filesystem MCP** (7001) - File operations
- **Git MCP** (7002) - Version control
- **Terminal MCP** (7003) - Command execution
- **Database MCP** (7004) - Data operations
- **Memory MCP** (7005) - Simple storage
- **Network MCP** (7006) - Network operations
- **System MCP** (7007) - System info
- **Security MCP** (7008) - Security operations
- **Config MCP** (7009) - Configuration management
- **Log MCP** (7010) - Logging operations

#### Extended Services (7011-7017, 7024-7026)
- **Research MCP** (7011) - AI research
- **Advanced Memory MCP** (7012) - AI memory
- **Transcriber MCP** (7013) - Audio processing
- **Vision MCP** (7014) - Image processing
- **ZEN MCP Server** (7017) - MCP tool orchestration gateway
- **PostgreSQL MCP Wrapper** (7024) - Database operations API
- **Redis MCP Wrapper** (7025) - Cache management API
- **Qdrant MCP Wrapper** (7026) - Vector database API

#### Infrastructure Services
- **PostgreSQL** (7021) - Primary database
- **Redis** (7022) - Cache/sessions
- **Qdrant Vector DB** (7023) - Vector storage
- **Monitoring** (7028) - Health checks & metrics
- **Backup Service** (7029) - Automated backups
- **Message Queue** (7030) - Task queuing

---

## Rychlý start

### Prerequisites

- **Docker & Docker Compose** (20.10+)
- **Python 3.12+**
- **Node.js 18+**
- **PostgreSQL 13+**
- **Redis 6+**
- **4GB+ RAM** (doporučeno)
- **Linux/macOS/WSL2**

### 1. Clone & Configure

```bash
git clone https://github.com/milhy545/orchestration.git
cd orchestration

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

### 2. Launch Everything

```bash
# Start all services
docker-compose up -d

# Verify health
./scripts/health-check.sh
```

### 3. Test the System

```bash
# Run comprehensive tests
./tests/unit/orchestration_workflow_test.sh

# Performance benchmarking
./tests/performance/stress_load_test.sh
```

### 4. Access the System

- **ZEN Coordinator**: http://localhost:7000
- **Health Check**: http://localhost:7000/health
- **Services List**: http://localhost:7000/services
- **Tools List**: http://localhost:7000/tools/list

---

## Konfigurace

### Environment Variables

Vytvořte .env soubor s následujícími proměnnými:

```bash
# Database Configuration
MCP_DATABASE_URL=postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified
POSTGRES_DB=mcp_unified
POSTGRES_USER=mcp_admin
POSTGRES_PASSWORD=change_me_in_production

# Redis Configuration
REDIS_URL=redis://redis:6379

# Qdrant Vector Database
QDRANT_URL=http://qdrant-vector:6333

# API Keys
PERPLEXITY_API_KEY=your_perplexity_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Security
JWT_SECRET_KEY=your_jwt_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

### Docker Compose Configuration

Hlavní konfigurace je v docker-compose.yml:

```yaml
version: "3.8"

services:
  # ZEN Coordinator - Master Controller
  zen-coordinator:
    build: ./config
    container_name: zen-coordinator
    ports:
      - "7000:8020"
    environment:
      - MCP_DATABASE_URL=${MCP_DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgresql
      - redis
    restart: unless-stopped
    networks:
      - mcp-network
```

---

## MCP služby

### Core Services

#### Filesystem MCP (Port 7001)
**Účel**: File operations a filesystem management

**Nástroje**:
- file_read - Čtení souborů
- file_write - Zápis souborů
- file_list - Listování adresářů
- file_search - Vyhledávání souborů
- file_analyze - Analýza souborů

**Použití**:
```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "arguments": {"path": "/path/to/file.txt"}
  }'
```

#### Git MCP (Port 7002)
**Účel**: Version control operations

**Nástroje**:
- git_status - Git status
- git_commit - Git commit
- git_push - Git push
- git_pull - Git pull
- git_log - Git log

#### Terminal MCP (Port 7003)
**Účel**: Command execution a system operations

**Nástroje**:
- execute_command - Spuštění příkazů
- system_info - System information
- process_list - Seznam procesů
- disk_usage - Disk usage

#### Memory MCP (Port 7005)
**Účel**: Simple key-value storage

**Nástroje**:
- store_memory - Uložení paměti
- search_memories - Vyhledávání paměti
- retrieve_memory - Načtení paměti
- delete_memory - Smazání paměti

#### Advanced Memory MCP (Port 7012)
**Účel**: AI-enhanced memory s vector search

**Nástroje**:
- semantic_store - Semantic storage
- vector_search - Vector search
- memory_analytics - Memory analytics
- similarity_search - Similarity search

### Extended Services

#### Research MCP (Port 7011)
**Účel**: AI research a data gathering

**Nástroje**:
- web_search - Web search
- perplexity_query - Perplexity AI queries
- research_compile - Research compilation

#### Transcriber MCP (Port 7013)
**Účel**: Audio processing a transcription

**Nástroje**:
- transcribe_audio - Audio transcription
- transcribe_video - Video transcription
- audio_analysis - Audio analysis

---

## API dokumentace

### ZEN Coordinator API

#### Health Check
```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "postgresql": "healthy",
    "redis": "healthy",
    "qdrant": "healthy"
  }
}
```

#### Services List
```http
GET /services
```

**Response**:
```json
{
  "services": [
    {
      "name": "filesystem-mcp",
      "port": 7001,
      "status": "healthy",
      "tools": ["file_read", "file_write", "file_list"]
    }
  ]
}
```

#### MCP Tool Execution
```http
POST /mcp
Content-Type: application/json

{
  "tool": "file_read",
  "arguments": {
    "path": "/path/to/file.txt"
  }
}
```

### Error Handling

Všechny API responses obsahují standardizované error handling:

```json
{
  "success": false,
  "error": {
    "code": "TOOL_NOT_FOUND",
    "message": "Tool 'invalid_tool' not found",
    "details": "Available tools: file_read, file_write, ..."
  }
}
```

---

## Testování

### Test Suite Structure

```
tests/
├── unit/                    # Unit testy
│   ├── memory_crud_test.sh
│   └── orchestration_workflow_test.sh
├── performance/             # Performance testy
│   └── stress_load_test.sh
├── security/               # Security testy
│   └── security_assessment_test.sh
└── failure/                # Failure recovery testy
    └── failure_recovery_test.sh
```

### Spuštění testů

```bash
# Všechny testy
./tests/run_all_tests.sh

# Unit testy
./tests/unit/orchestration_workflow_test.sh

# Performance testy
./tests/performance/stress_load_test.sh

# Security testy
./tests/security/security_assessment_test.sh

# Failure recovery testy
./tests/failure/failure_recovery_test.sh
```

### Test Results

Testy generují detailní reporty:

```bash
# Test report
cat test_results.json

# Performance metrics
cat performance_metrics.json

# Security assessment
cat security_report.json
```

---

## Bezpečnost

### Security Features

- **Environment-based Configuration** - Žádné hardcoded secrets
- **Container Isolation** - Služby běží v izolovaných kontejnerech
- **Network Segmentation** - Internal Docker network
- **Credential Management** - PostgreSQL authentication
- **API Key Protection** - External service keys via environment
- **Data Persistence Security** - Separate data volumes

### Authentication & Authorization

```python
# JWT Token validation
def validate_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
```

### Network Security

```yaml
# Docker network configuration
networks:
  mcp-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

---

## Monitoring a diagnostika

### Health Monitoring

```bash
# System health check
./scripts/health-check.sh

# Service status monitoring
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Resource monitoring
docker stats
```

### Logging

```bash
# ZEN Coordinator logs
docker logs zen-coordinator

# Specific service logs
docker logs mcp-filesystem

# All services logs
docker-compose logs
```

### Metrics

- **Response Times**: Sub-100ms pro direct MCP calls
- **Memory Storage**: ~50ms average PostgreSQL write time
- **Service Discovery**: 11+ services auto-detected
- **Container Health**: 7+ services s health monitoring

---

## Claude AI Agent

### Claude Agent System

Claude Agent je pokročilý AI systém pro koordinaci MCP služeb:

#### Komponenty

- haiku_agent.py - Hlavní Claude agent
- claude_session_bridge.py - Session management
- anthropic_oauth_setup.py - OAuth setup
- claude_agent_start.sh - Spouštěcí skript

#### Konfigurace

```yaml
# claude-agent/config/agent_config.yaml
anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-3-5-sonnet-20241022
  
mcp_services:
  zen_coordinator: "http://localhost:7000"
  direct_bridge: "http://localhost:7001"
```

#### Spuštění

```bash
# Start Claude Agent
cd claude-agent
./claude_agent_start.sh

# Test agent
python test_agent.py
```

---

## Deployment

### Production Deployment

#### 1. Environment Setup

```bash
# Production environment
export NODE_ENV=production
export LOG_LEVEL=info
export ENABLE_METRICS=true
```

#### 2. Docker Compose Production

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  zen-coordinator:
    build: ./config
    restart: always
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

#### 3. Database Migration

```bash
# Run migrations
./scripts/migrate-to-postgresql.py

# Backup before migration
./scripts/backup-databases.sh
```

### Portainer Deployment

Pro GUI deployment použijte Portainer:

1. Import docs/PORTAINER_DEPLOYMENT.md návod
2. Upload docker-compose.yml
3. Configure environment variables
4. Deploy stack

---

## Troubleshooting

### Common Issues

#### 1. Service Not Starting

```bash
# Check logs
docker logs [service-name]

# Check health
curl http://localhost:7000/health

# Restart service
docker-compose restart [service-name]
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL
docker exec -it mcp-postgresql psql -U mcp_admin -d mcp_unified

# Check Redis
docker exec -it mcp-redis redis-cli ping
```

#### 3. Memory Issues

```bash
# Check memory usage
docker stats

# Clean up unused containers
docker system prune -a
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=debug
docker-compose up -d

# Debug specific service
docker exec -it [service-name] /bin/bash
```

---

## Výkonnost a škálování

### Performance Optimization

#### 1. Caching Strategy

```python
# Redis caching
@cache.memoize(timeout=300)
def expensive_operation():
    # Expensive computation
    pass
```

#### 2. Database Optimization

```sql
-- Index optimization
CREATE INDEX idx_memory_type ON memories(memory_type);
CREATE INDEX idx_importance ON memories(importance);
```

#### 3. Load Balancing

```yaml
# Multiple ZEN Coordinator instances
zen-coordinator-1:
  ports:
    - "7000:8020"
zen-coordinator-2:
  ports:
    - "7051:8020"
```

### Scaling Guidelines

- **Horizontal Scaling**: Multiple ZEN Coordinator instances
- **Vertical Scaling**: Increase container resources
- **Database Scaling**: Read replicas, connection pooling
- **Cache Scaling**: Redis Cluster

---

## Vývoj a přispívání

### Development Setup

```bash
# Development environment
git clone https://github.com/milhy545/orchestration.git
cd orchestration

# Install dependencies
pip install -r requirements.txt
npm install

# Start development services
docker-compose -f docker-compose.dev.yml up -d
```

### Adding New MCP Service

1. **Create Service Directory**:
```bash
mkdir mcp-servers/new-service
cd mcp-servers/new-service
```

2. **Create Dockerfile**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

3. **Add to docker-compose.yml**:
```yaml
new-service:
  build: ./mcp-servers/new-service
  container_name: mcp-new-service
  ports:
    - "80XX:8000"
  networks:
    - mcp-network
```

4. **Register in ZEN Coordinator**:
```python
self.services['new-service'] = {
    'port': 80XX,
    'methods': ['method1', 'method2']
}
```

### Testing New Features

```bash
# Run tests
./tests/unit/your_new_test.sh

# Performance test
./tests/performance/stress_load_test.sh

# Security test
./tests/security/security_assessment_test.sh
```

---

## Podpora a komunita

### Dokumentace

- **GitHub Repository**: https://github.com/milhy545/orchestration
- **Issues**: https://github.com/milhy545/orchestration/issues
- **Discussions**: https://github.com/milhy545/orchestration/discussions

### Kontakt

- **Email**: [váš-email@example.com]
- **Discord**: [váš-discord]
- **Telegram**: [váš-telegram]

---

## License

MIT License - feel free to use this as a foundation for your own MCP orchestration systems.

---

## Závěr

MCP Orchestration Platform je kompletní enterprise architecture která demonstruje:

✅ **Scalable Design Patterns**  
✅ **Security Best Practices**  
✅ **Comprehensive Testing**  
✅ **Production Monitoring**  
✅ **Service Mesh Architecture**  
✅ **AI Integration Patterns**  

Perfektní pro learning, extending, nebo použití jako foundation pro production systems.

---

**Ready to orchestrate your MCP services? Star this repo and let's build something amazing!**

---

*Tento manuál byl vytvořen automaticky z kompletní dokumentace projektu. Pro nejnovější informace navštivte GitHub repository.*
