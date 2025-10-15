# Orchestration Project - MCP Microservices Platform

## 🏗️ Overview

This is a comprehensive **MCP (Model Context Protocol)** microservices orchestration platform that provides a unified interface for AI agents and applications. The system consists of 28 specialized tools across 7 core services, all orchestrated through a central ZEN Coordinator.

### Production Environment
- **GitHub Repository**: [milhy545/orchestration](https://github.com/milhy545/orchestration)
- **Production Server**: `192.168.0.58` (Home Automation Server - HAS)
- **Live Status**: 26+ hours uptime, 10+ microservices running
- **Architecture**: Secure containerized microservices with unified HTTP interface

## 🌟 Key Features

- **28 MCP Tools** across 7 specialized services
- **Security-First Architecture** - All services accessed through ZEN Coordinator only
- **Production-Ready** - Docker Compose orchestration with health monitoring
- **Multi-Database Support** - PostgreSQL, Redis, Qdrant vector database
- **AI-Enhanced Memory** - Advanced memory system with semantic search
- **Real-time Monitoring** - Comprehensive health checks and service discovery

## 🎯 Quick Start

### Prerequisites

- **Docker & Docker Compose** (20.10+)
- **Python 3.11+** 
- **Node.js 18+**
- **PostgreSQL 13+**
- **Redis 6+**
- **Portainer Agent** (for Portainer deployment)

### Installation

1. **Clone the repository** (on production server):
```bash
ssh root@192.168.0.58
cd /home
git clone https://github.com/milhy545/orchestration.git
cd orchestration
```

2. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start all services**:
```bash
docker-compose up -d
```

4. **Verify deployment**:
```bash
curl http://localhost:8020/health
curl http://localhost:8020/services
```

## 🏛️ Architecture Overview

### Core Components

```
Internet → ZEN Coordinator (8020) → MCP Services (8001-8013)
          ✅ Security Gateway      ❌ Not directly accessible
```

### Service Ports

| Port | Service | Status | Description |
|------|---------|--------|-------------|
| 8001 | Filesystem MCP | ✅ Running | File operations, search, analysis |
| 8002 | Git MCP | ✅ Running | Git operations, version control |
| 8003 | Terminal MCP | ✅ Running | Shell commands, system info |
| 8004 | Database MCP | ✅ Running | Database queries, schema management |
| 8005 | Memory MCP | ✅ Running | Memory storage, context management |
| 8011 | Research MCP | ✅ Running | Web search, Perplexity integration |
| 8012 | Advanced Memory | ✅ Running | Enhanced memory with AI |
| 8013 | Transcriber MCP | ⚠️ Needs Debug | Audio/video transcription |
| 8020 | **ZEN Coordinator** | ✅ Running | **Central orchestration hub** |
| 8021 | PostgreSQL | ✅ Running | Primary database |
| 8022 | Redis | ✅ Running | Caching, sessions |
| 6333 | Qdrant | ✅ Running | Vector database |

### Available MCP Tools (28 total)

#### 🗄️ Filesystem Operations (Port 8001)
- `file_read` - Read file contents
- `file_write` - Write/create files  
- `file_list` - List directory contents
- `file_search` - Search files by pattern
- `file_analyze` - Analyze file structure

#### 🔄 Git Operations (Port 8002)
- `git_status` - Check repository status
- `git_commit` - Create commits
- `git_push` - Push to remote repository
- `git_log` - View commit history
- `git_diff` - Show differences

#### 💻 Terminal Operations (Port 8003)
- `terminal_exec` - Execute commands
- `shell_command` - Run shell commands
- `system_info` - Get system information

#### 🗃️ Database Operations (Port 8004)
- `db_query` - Execute database queries
- `db_connect` - Connect to databases
- `db_schema` - Get database schema
- `db_backup` - Backup databases

#### 🧠 Memory Operations (Port 8005, 8012)
- `store_memory` - Store information in memory
- `search_memories` - Search stored memories
- `get_context` - Retrieve context information
- `memory_stats` - Get memory statistics
- `list_memories` - List all memories

#### 🎵 Audio/Transcription (Port 8013)
- `transcribe_webm` - Transcribe WebM audio
- `transcribe_url` - Transcribe from URL
- `audio_convert` - Convert audio formats

#### 🔍 Research Operations (Port 8011)
- `research_query` - Research queries
- `perplexity_search` - Perplexity AI search
- `web_search` - Web search functionality

## 🚀 Deployment Guide

### Standard Docker Deployment

1. **Environment Setup**:
```bash
# Copy and configure environment
cp .env.example .env

# Required environment variables:
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mcp_unified
POSTGRES_USER=mcp_admin
POSTGRES_PASSWORD=your_secure_password

REDIS_HOST=localhost
REDIS_PORT=6379

QDRANT_HOST=localhost
QDRANT_PORT=6333
```

2. **Start Services**:
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f zen-coordinator
```

3. **Health Verification**:
```bash
# Check ZEN Coordinator
curl http://localhost:8020/health

# List all services
curl http://localhost:8020/services

# List available tools
curl http://localhost:8020/tools/list
```

### Portainer Deployment

#### Prerequisites for Portainer

1. **Install Portainer Agent** on target server:
```bash
# Install Portainer Agent
docker run -d \
  --name portainer_agent \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -p 9001:9001 \
  portainer/agent:latest
```

2. **Verify Agent Installation**:
```bash
# Check if agent is running
docker ps | grep portainer_agent

# Test agent connectivity
curl http://localhost:9001/ping
```

#### Portainer Stack Deployment

1. **Prepare API Token**:
   - Login to Portainer UI
   - Go to User Settings → Access tokens
   - Create new token with appropriate permissions
   - Save token securely

2. **Deploy using API**:
```bash
# Set your Portainer details
export PORTAINER_URL="https://your-portainer-instance.com"
export PORTAINER_TOKEN="your_api_token_here"
export ENDPOINT_ID="your_endpoint_id"

# Deploy stack
curl -X POST "$PORTAINER_URL/api/stacks" \
  -H "X-API-Key: $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d @portainer_stack_config.json
```

3. **Stack Configuration** (portainer_stack_config.json):
```json
{
  "name": "orchestration-mcp",
  "swarmID": "",
  "endpointId": 1,
  "repositoryURL": "https://github.com/milhy545/orchestration",
  "repositoryReferenceName": "refs/heads/master",
  "repositoryAuthentication": false,
  "composeFile": "docker-compose.yml",
  "env": [
    {
      "name": "POSTGRES_PASSWORD",
      "value": "your_secure_password"
    }
  ]
}
```

#### Portainer Agent Troubleshooting

**Common Issues:**

1. **Agent Not Accessible**:
```bash
# Check agent status
docker logs portainer_agent

# Verify port binding
netstat -tlnp | grep 9001

# Test connectivity
telnet localhost 9001
```

2. **Permission Issues**:
```bash
# Ensure Docker socket access
ls -la /var/run/docker.sock

# Fix permissions if needed
sudo chmod 666 /var/run/docker.sock
```

3. **Network Connectivity**:
```bash
# Check if port is open
sudo ufw status
sudo ufw allow 9001

# Test from Portainer server
curl http://target-server-ip:9001/ping
```

## 🔧 Configuration

### Environment Variables

Create `.env` file with the following variables:

```bash
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=mcp_unified
POSTGRES_USER=mcp_admin
POSTGRES_PASSWORD=your_secure_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# Qdrant Vector Database
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_qdrant_key

# AI Services (Optional)
ANTHROPIC_API_KEY=your_anthropic_key
PERPLEXITY_API_KEY=your_perplexity_key
GEMINI_API_KEY=your_gemini_key

# ZEN Coordinator
ZEN_COORDINATOR_HOST=0.0.0.0
ZEN_COORDINATOR_PORT=8020
ZEN_COORDINATOR_DEBUG=false

# Security
ENABLE_AUTH=true
JWT_SECRET=your_jwt_secret
API_RATE_LIMIT=100
```

### Service Dependencies

The services have the following startup dependencies:

```yaml
# Dependency Order:
1. PostgreSQL (8021)
2. Redis (8022) 
3. Qdrant (6333)
4. MCP Services (8001-8013)
5. ZEN Coordinator (8020)
```

### Port Mapping Strategy

```bash
# Core Infrastructure
8020: ZEN Coordinator (main entry point)
8021: PostgreSQL 
8022: Redis
6333: Qdrant Vector DB

# MCP Services (isolated)
8001: Filesystem MCP
8002: Git MCP  
8003: Terminal MCP
8004: Database MCP
8005: Memory MCP
8011: Research MCP
8012: Advanced Memory MCP
8013: Transcriber MCP (debugging needed)

# Reserved for future expansion
8006-8010: Available for new MCP services
8014-8030: Reserved for specialized services
```

## 🐛 Troubleshooting

### Service Health Checks

```bash
# Check all service health
./scripts/health-check.sh

# Individual service checks
curl http://localhost:8020/health  # ZEN Coordinator
curl http://localhost:8001/health  # Filesystem MCP
curl http://localhost:8002/health  # Git MCP
curl http://localhost:8003/health  # Terminal MCP
curl http://localhost:8004/health  # Database MCP
curl http://localhost:8005/health  # Memory MCP
```

### Common Issues

#### 1. Transcriber Service Unhealthy

```bash
# Check transcriber logs
docker logs mcp-transcriber

# Restart transcriber service
docker-compose restart mcp-transcriber

# Debug transcriber connectivity
curl http://localhost:8013/health
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
docker logs mcp-postgresql

# Test database connection
psql -h localhost -U mcp_admin -d mcp_unified

# Reset database if needed
docker-compose down
docker volume rm orchestration_postgres_data
docker-compose up -d
```

#### 3. MCP Protocol Errors

```bash
# Check ZEN Coordinator logs
docker logs zen-coordinator

# Test MCP tool directly
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool":"system_info","arguments":{}}'

# Restart coordinator if needed
docker-compose restart zen-coordinator
```

#### 4. Memory/Performance Issues

```bash
# Check system resources
docker stats

# Memory optimization
echo 3 > /proc/sys/vm/drop_caches

# Restart heavy services
docker-compose restart mcp-memory mcp-database
```

#### 5. Network Connectivity

```bash
# Check port binding
netstat -tlnp | grep 802

# Test service connectivity
telnet localhost 8020

# Check Docker network
docker network ls
docker network inspect orchestration_default
```

### Performance Monitoring

```bash
# Continuous service monitoring
./scripts/monitor-services.sh

# Resource usage monitoring
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Log monitoring
docker-compose logs -f --tail=100
```

### Recovery Procedures

#### Emergency Service Restart
```bash
# Complete system restart
docker-compose down
docker-compose up -d

# Wait for services to stabilize
sleep 30

# Verify all services
curl http://localhost:8020/services
```

#### Database Recovery
```bash
# Backup current state
docker exec mcp-postgresql pg_dump -U mcp_admin mcp_unified > backup.sql

# Reset and restore
docker-compose down
docker volume rm orchestration_postgres_data
docker-compose up -d mcp-postgresql

# Wait for PostgreSQL to start
sleep 10

# Restore data
docker exec -i mcp-postgresql psql -U mcp_admin mcp_unified < backup.sql
```

## 🧪 Testing

### Unit Tests
```bash
# Run unit tests
./tests/unit/orchestration_workflow_test.sh

# Test individual services
./tests/unit/filesystem_mcp_test.sh
./tests/unit/memory_mcp_test.sh
```

### Integration Tests
```bash
# Full integration test suite
./tests/integration/full_stack_test.sh

# API endpoint tests
./tests/integration/api_test.sh
```

### Performance Tests
```bash
# Load testing
./tests/performance/stress_load_test.sh

# Benchmark MCP tools
./tests/performance/mcp_benchmark.sh
```

### Security Tests
```bash
# Security assessment
./tests/security/security_assessment_test.sh

# Vulnerability scanning
./tests/security/vulnerability_scan.sh
```

## 📊 Monitoring & Observability

### Health Monitoring
- Comprehensive health checks for all services
- Automatic service discovery and registration
- Real-time status monitoring via ZEN Coordinator

### Logging
- Centralized logging through Docker Compose
- Structured JSON logging for all MCP services
- Log rotation and retention policies

### Metrics
- Service uptime tracking
- Request/response metrics for MCP tools
- Database performance metrics
- Memory usage and optimization metrics

## 🔐 Security

### Network Security
- **Zero External Access**: Only ZEN Coordinator (8020) exposed
- **Internal Service Isolation**: MCP services accessible only within Docker network
- **Secure Transport**: All internal communication over secure channels

### Authentication & Authorization
- JWT-based authentication for API access
- Role-based access control for MCP tools
- API rate limiting and request validation

### Data Security
- Encrypted database connections
- Secure memory storage with encryption at rest
- Audit logging for all operations

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Run tests locally
4. Submit pull request

### Code Standards
- **Python**: PEP 8, type hints, comprehensive docstrings
- **JavaScript/TypeScript**: ESLint, Prettier formatting
- **Docker**: Multi-stage builds, security scanning

### Testing Requirements
- Unit tests for all new features
- Integration tests for MCP tools
- Performance benchmarks for critical paths

## 📚 Additional Resources

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Qdrant Vector Database](https://qdrant.tech/documentation/)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For issues and questions:
- **GitHub Issues**: [orchestration/issues](https://github.com/milhy545/orchestration/issues)
- **Documentation**: See [docs/](docs/) directory
- **Production Support**: Contact system administrator

---

**Current Status**: Production Ready ✅ | 26h+ Uptime | 28 MCP Tools | 10+ Microservices