# Gemini Project Memory

This file stores information about the project to help Gemini assist you better.

## Language Preference

**Primary language for communication: Czech (česky)**
- Use Czech for all explanations, discussions, and documentation
- Code comments and technical documentation can remain in English where appropriate
- Error messages and logs should be explained in Czech

## Architecture Overview

This is an MCP (Model Context Protocol) orchestration system that provides a unified interface to multiple containerized services. The system consists of:

- **Zen Coordinator** (`config/zen_coordinator.py`) - Main HTTP coordinator service running on port 8020
- **Multiple MCP Services** - Containerized microservices (ports 8001-8011)
- **Shared Infrastructure** - PostgreSQL, Redis, Qdrant vector database

## Key Services Architecture

The system uses a service mesh pattern where all MCP services connect to:
- PostgreSQL database (`mcp_unified` database, port 5432)
- Redis cache (port 8009 mapped to 6379)
- Zen Coordinator routes requests between services

### MCP Services
- `filesystem-mcp` (port 8001) - File system operations
- `git-mcp` (port 8002) - Git operations (status, log, diff)
- `terminal-mcp` (port 8003) - Command execution
- `database-mcp` (port 8004) - Database operations
- `memory-mcp` (port 8005) - Memory/persistence (FastAPI)
- `cldmemory-api` (port 8006) - Advanced memory with vector search
- `qdrant-vector` (port 8007) - Vector database
- `webm-transcriber` (port 8008) - Audio transcription
- `research-mcp` (port 8011) - Research operations

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

### Available Tools:
- `execute_command` → terminal-mcp
- `list_files`, `read_file` → filesystem-mcp
- `git_execute` → git-mcp (supports: status, log, diff)
- `store_memory`, `search_memories` → memory-mcp
- `transcribe_audio`, `transcribe_url` → webm-transcriber
- Email tools → gmail (stdio)

## Data Persistence

- **SQLite Databases**: `data/databases/` (cldmemory.db, unified_memory_forai.db)
- **PostgreSQL**: `data/postgresql/` (unified database for all MCP services)
- **Redis**: `data/redis/` (caching and sessions)
- **Qdrant**: `data/qdrant/` (vector embeddings)
- **Workspaces**: `data/workspaces/` (filesystem operations)
- **Repositories**: `data/repositories/` (git operations)

## Service URLs for Direct Access
- Zen Coordinator: http://localhost:8020
- Memory MCP API docs: http://localhost:8005/docs
- Qdrant UI: http://localhost:8007 (6333)
- PostgreSQL: localhost:5432
- Redis: localhost:8009

## Environment Configuration

Each MCP service uses these environment variables:
- `MCP_DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- Service-specific keys (GEMINI_API_KEY, PERPLEXITY_API_KEY)``

## Development Notes

- All MCP servers are containerized with individual Dockerfiles
- Services communicate through the shared PostgreSQL database and Redis cache
- The Zen Coordinator provides HTTP→MCP protocol translation
- Memory services support both simple storage and vector-based search
- Git operations are limited to read-only commands (status, log, diff)
- Testing includes workflow chains, performance benchmarks, and concurrent operations

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
EVERYTIME proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.