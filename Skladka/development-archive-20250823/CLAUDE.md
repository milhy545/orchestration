# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an MCP (Model Context Protocol) orchestration system that provides a unified interface to multiple containerized services. The system consists of:

- **Zen Coordinator** (`config/zen_coordinator.py`) - Main HTTP coordinator service running on port 8020
- **Multiple MCP Services** - Containerized microservices (ports 8001-8011)
- **Shared Infrastructure** - PostgreSQL, Redis, Qdrant vector database

## Key Services Architecture

The system uses a service mesh pattern with Docker containers where all MCP services connect to shared infrastructure:
- **PostgreSQL**: Unified database (`mcp_unified`) on port 8021 (internal port 5432)
- **Redis**: Caching and sessions on port 8022 (internal port 6379)  
- **Qdrant**: Vector database on port 8023 (internal port 6333)
- **Zen Coordinator**: HTTP→MCP protocol bridge routes all requests

### Core MCP Services (Ports 8001-8010)
- `filesystem-mcp` (8001) - File operations with workspace mounting
- `git-mcp` (8002) - Git operations (status, log, diff) - read-only
- `terminal-mcp` (8003) - Command execution with privileged access
- `database-mcp` (8004) - Database operations and schema management
- `memory-mcp` (8005) - Simple memory/persistence (FastAPI)
- `network-mcp` (8006) - Network operations (placeholder)
- `system-mcp` (8007) - System information (placeholder)
- `security-mcp` (8008) - Security operations (placeholder)
- `config-mcp` (8009) - Configuration management (placeholder)
- `log-mcp` (8010) - Logging operations (placeholder)

### AI/Enhanced Services (Ports 8011+)
- `research-mcp` (8011) - Perplexity AI research integration
- `advanced-memory-mcp` (8012) - Vector-based memory with Qdrant
- `transcriber-mcp` (8013) - Audio transcription (WebM/MP3)
- `vision-mcp` (8014) - Vision processing (placeholder)
- `mqtt-broker` (8018) - Message queue broker
- `mqtt-mcp` (8019) - MQTT operations via MCP protocol

## Common Development Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Check service status
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep mcp

# View logs for specific service
docker logs mcp-<service-name>

# Health check all services
./scripts/health-check.sh
```

### Development and Testing
```bash
# Run orchestration workflow tests
./tests/unit/orchestration_workflow_test.sh

# Run memory CRUD tests
./tests/unit/memory_crud_test.sh

# Performance stress testing
./tests/performance/stress_load_test.sh

# Security assessment testing
./tests/security/security_assessment_test.sh

# Failure recovery testing
./tests/failure/failure_recovery_test.sh

# Monitor services
./scripts/monitor-services.sh
```

### Database Operations
```bash
# Backup databases
./scripts/backup-databases.sh

# Check database status
ls -la data/databases/

# PostgreSQL connection
psql -h localhost -p 5432 -U mcp_admin -d mcp_unified
```

## Tool Routing via Zen Coordinator

All tools are accessed through the Zen Coordinator at `http://localhost:8020/mcp`. Request format:
```json
{
  "tool": "tool_name",
  "arguments": {...}
}
```

### Tool Routing Map:
- `execute_command`, `terminal_exec`, `shell_command` → terminal-mcp
- `file_read`, `file_write`, `list_files`, `file_search` → filesystem-mcp  
- `git_status`, `git_log`, `git_diff` → git-mcp (read-only operations)
- `store_memory`, `search_memories`, `memory_stats` → memory-mcp
- `transcribe_webm`, `transcribe_url`, `audio_convert` → transcriber-mcp
- `research_query`, `perplexity_search` → research-mcp
- `db_query`, `db_connect`, `db_schema` → database-mcp

The Zen Coordinator uses prefix-based routing (e.g., `file_*` → filesystem) and direct tool name mapping.

## Data Persistence

- **SQLite Databases**: `data/databases/` (cldmemory.db, unified_memory_forai.db)
- **PostgreSQL**: `data/postgresql/` (unified database for all MCP services)
- **Redis**: `data/redis/` (caching and sessions)
- **Qdrant**: `data/qdrant/` (vector embeddings)
- **Workspaces**: `data/workspaces/` (filesystem operations)
- **Repositories**: `data/repositories/` (git operations)

## Service URLs for Direct Access
- **Zen Coordinator**: http://localhost:8020 (main entry point)
- **Core MCP Services**:
  - Filesystem MCP: http://localhost:8001
  - Git MCP: http://localhost:8002  
  - Terminal MCP: http://localhost:8003
  - Database MCP: http://localhost:8004
  - Memory MCP: http://localhost:8005 (FastAPI docs: /docs)
- **AI/Enhanced Services**:
  - Research MCP: http://localhost:8011
  - Advanced Memory: http://localhost:8012 (Node.js + Qdrant)
  - Transcriber MCP: http://localhost:8013
- **Infrastructure Services**:
  - PostgreSQL: localhost:8021 (internal: 5432)
  - Redis: localhost:8022 (internal: 6379)
  - Qdrant Vector DB: localhost:8023 (internal: 6333)
  - MQTT Broker: localhost:8018 (internal: 1883)
  - Monitoring: http://localhost:8028 (Prometheus)

## Environment Configuration

Each MCP service uses these environment variables:
- `MCP_DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- Service-specific keys (GEMINI_API_KEY, PERPLEXITY_API_KEY)

## Architecture Patterns

### Service Communication
- **Protocol Translation**: Zen Coordinator converts HTTP requests to MCP JSON-RPC 2.0
- **Service Discovery**: Container-based networking with service names (e.g., `mcp-filesystem`)
- **Shared Infrastructure**: All services connect to unified PostgreSQL, Redis, and Qdrant
- **Request Logging**: PostgreSQL stores all MCP request metrics with response times
- **Caching Layer**: Redis provides 5-minute caching for read operations (`tools/list`, `health`)

### Container Architecture
- **Multi-stage Builds**: Each MCP service has its own Dockerfile in `mcp-servers/`
- **Volume Mapping**: Selective mounts (workspaces, repositories, databases, temp files)
- **Network Isolation**: All services run on `mcp-network` bridge network
- **Privilege Management**: Terminal MCP runs privileged, others run as restricted users
- **Health Checks**: Socket-based connectivity tests with fallback mechanisms

### Development Workflow Integration
- **Comprehensive Testing**: Unit, performance, security, and failure recovery test suites
- **Monitoring**: Prometheus metrics on port 8028 with container status tracking
- **Backup Strategy**: Automated database backups to `data/backups/`
- **Log Management**: Centralized logging via `data/logs/` with service-specific subdirectories

### Production Considerations
- Environment-based configuration (no hardcoded credentials)
- Database connection pooling and Redis connection reuse
- Git operations limited to read-only for security
- MQTT integration for IoT and real-time communication patterns