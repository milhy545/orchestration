# MCP Orchestration Production Status

## Architecture Overview
- **ZEN Coordinator**: HTTP ↔ MCP Protocol Bridge (Port 8020)
- **Core Services**: 24 MCP microservices
- **Infrastructure**: PostgreSQL, Redis, Qdrant
- **AI Coordination**: Dual agent system (HAS + LLMS)

## Service Categories
### Core MCP Services (8001-8010)
- Filesystem, Git, Terminal, Database, Memory, etc.

### Extended Services (8011-8020)
- Research, Transcriber, Advanced Memory, etc.

### Infrastructure Services
- PostgreSQL (8021), Redis (8022), Qdrant (6333)

## Health Monitoring
- ZEN Coordinator: http://192.168.0.58:8020/health
- Services List: http://192.168.0.58:8020/services
- Tools Count: http://192.168.0.58:8020/tools/list

## AI Agent Coordination
- **HAS-System-Admin**: Alpine Linux orchestration management
- **LLMS Advanced Bot**: Ubuntu AI model coordination (192.168.0.10)

## Production Commands
```bash
# Health check
./production_monitor.sh

# Service restart
docker-compose restart [service-name]

# Full orchestration restart
docker-compose down && docker-compose up -d
```
