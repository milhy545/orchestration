# 🌟 MCP Orchestration System

> **Advanced Model Context Protocol (MCP) orchestration platform with unified HTTP interface to multiple containerized microservices**

[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![Node.js](https://img.shields.io/badge/Node.js-18+-339933?style=flat&logo=node.js&logoColor=white)](https://nodejs.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_DB-FF6B6B?style=flat&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAwIiBoZWlnaHQ9IjEwMCIgdmlld0JveD0iMCAwIDEwMCAxMDAiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxyZWN0IHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIiBmaWxsPSIjRkY2QjZCIi8+Cjx0ZXh0IHg9IjUwIiB5PSI1NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0id2hpdGUiIGZvbnQtc2l6ZT0iMTQiIGZvbnQtZmFtaWx5PSJBcmlhbCI+UTwvdGV4dD4KPHN2Zz4K&logoColor=white)](https://qdrant.tech)

## ✨ What Makes This Special

This is a **production-ready MCP orchestration system** that demonstrates enterprise-level architecture patterns with:

- 🎯 **Unified HTTP Interface** - Single endpoint for all MCP services
- 🏗️ **Service Mesh Architecture** - Containerized microservices with shared infrastructure
- 🔄 **Automatic Health Monitoring** - Built-in service discovery and health checks
- 🔐 **Security-First Design** - Environment-based secrets, no hardcoded credentials
- 📊 **Vector Database Integration** - Advanced AI memory with semantic search
- 🧪 **Comprehensive Testing** - Unit, performance, security, and failure recovery tests
- 📈 **Production Monitoring** - Redis caching, PostgreSQL persistence, logging

## 🏛️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────────────────────────┐
│   HTTP Client   │────│           Zen Coordinator            │
└─────────────────┘    │         (Port 8020)                 │
                       │    HTTP ↔ MCP Protocol Bridge        │
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
                       │        Shared Infrastructure        │
                       │  PostgreSQL │ Redis │ Qdrant Vector │
                       │   (5432)    │ (6379)│    (6333)     │
                       └─────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 4GB+ RAM recommended
- Linux/macOS/WSL2

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

## 🛠️ MCP Services

| Service | Port | Purpose | Key Features |
|---------|------|---------|--------------|
| **Zen Coordinator** | 8020 | HTTP ↔ MCP Bridge | Request routing, protocol translation |
| **Filesystem MCP** | 8001 | File Operations | Read, write, search, analysis |
| **Git MCP** | 8002 | Version Control | Status, log, diff, history |
| **Terminal MCP** | 8003 | Command Execution | System commands, process management |
| **Database MCP** | 8004 | Data Operations | Query, schema, backup, connections |
| **Memory MCP** | 8005 | Context Storage | Simple key-value, FastAPI interface |
| **Advanced Memory** | 8006 | AI Memory | Vector search, semantic similarity |
| **Qdrant Vector** | 8007 | Vector Database | Embeddings, similarity search |
| **Transcriber** | 8008 | Audio Processing | WebM transcription, audio analysis |
| **Research MCP** | 8011 | AI Research | Perplexity integration, data gathering |

## 🔧 Development Workflow

### Service Management
```bash
# Monitor all services
./scripts/monitor-services.sh

# Check specific service logs
docker logs mcp-filesystem

# Restart individual service
docker-compose restart memory-mcp
```

### Testing Suite
```bash
# Unit tests
./tests/unit/memory_crud_test.sh
./tests/unit/orchestration_workflow_test.sh

# Performance testing
./tests/performance/stress_load_test.sh

# Security assessment
./tests/security/security_assessment_test.sh

# Failure recovery
./tests/failure/failure_recovery_test.sh
```

### Database Operations
```bash
# Backup all databases
./scripts/backup-databases.sh

# Connect to PostgreSQL
psql -h localhost -p 5432 -U mcp_admin -d mcp_unified

# Check data directories
ls -la data/
```

## 📡 API Usage

### Making Requests
```bash
# Execute terminal command
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "execute_command",
    "arguments": {"command": "ls -la"}
  }'

# Store memory
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "key": "project_status",
      "content": "System is running perfectly"
    }
  }'

# Search memories
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_memories",
    "arguments": {"query": "project status"}
  }'
```

## 🔐 Security Features

- **Environment-based Configuration** - No hardcoded secrets
- **Container Isolation** - Services run in isolated containers
- **Network Segmentation** - Internal Docker network
- **Credential Management** - PostgreSQL authentication
- **API Key Protection** - External service keys via environment
- **Data Persistence Security** - Separate data volumes

## 📊 Monitoring & Observability

### Health Monitoring
```bash
# System health check
./scripts/health-check.sh

# Service status monitoring
docker ps --format 'table {{.Names}}\t{{.Status}}'

# Resource monitoring
docker stats
```

### Data Persistence
- **PostgreSQL**: `data/postgresql/` - Unified database for all MCP services
- **Redis**: `data/redis/` - Caching and session management  
- **Qdrant**: `data/qdrant/` - Vector embeddings and similarity search
- **SQLite**: `data/databases/` - Local database files
- **Workspaces**: `data/workspaces/` - Filesystem operations
- **Repositories**: `data/repositories/` - Git operations

## 🌍 Use Cases

### AI Development
- **Context Management** - Store and retrieve AI conversation context
- **Code Analysis** - Analyze codebases with filesystem and git integration
- **Research Automation** - Gather information with Perplexity integration

### DevOps & Automation
- **System Monitoring** - Execute commands and collect system information
- **Database Operations** - Manage multiple database connections
- **File Processing** - Handle file operations across different environments

### Data Processing
- **Audio Transcription** - Process WebM audio files
- **Vector Search** - Semantic similarity search with Qdrant
- **Memory Management** - Persistent storage with retrieval capabilities

## 🤝 Contributing

We welcome contributions! This project demonstrates production-ready patterns for:
- Microservices architecture
- Container orchestration
- API design
- Testing strategies
- Security practices

## 📄 License

MIT License - feel free to use this as a foundation for your own MCP orchestration systems.

## 🎯 Why This Matters

This isn't just another container setup - it's a **complete enterprise architecture** that shows:

✅ **Scalable Design Patterns**  
✅ **Security Best Practices**  
✅ **Comprehensive Testing**  
✅ **Production Monitoring**  
✅ **Service Mesh Architecture**  
✅ **AI Integration Patterns**  

Perfect for learning, extending, or using as a foundation for production systems.

---

<p align="center">
  <strong>🚀 Ready to orchestrate your MCP services? Star this repo and let's build something amazing! 🚀</strong>
</p>