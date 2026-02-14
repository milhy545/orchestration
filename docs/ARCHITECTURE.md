# Architecture Documentation - Orchestration MCP Platform

## 🏗️ System Overview

The Orchestration MCP Platform is a microservices-based system that implements the **Model Context Protocol (MCP)** specification to provide a unified interface for AI agents and applications. The system is designed with security, scalability, and maintainability as core principles.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   External      │    │  ZEN            │    │   MCP           │
│   Clients       ├────┤  Coordinator    ├────┤   Services      │
│   (Port varies) │    │  (Port 7000)    │    │   (7001-7017)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              │
                    ┌─────────┴─────────┐
                    │   Infrastructure  │
                    │   Services        │
                    │   (DB, Cache,     │
                    │    Vector Store)  │
                    └───────────────────┘
```

## 🔒 Security Architecture

### Zero Trust Network Model

The platform implements a **Zero Trust** security model where:

1. **Single Entry Point**: Only ZEN Coordinator (port 7000) is exposed externally
2. **Internal Isolation**: MCP services (7001-7017) are not directly accessible
3. **Service Mesh**: All internal communication is controlled and monitored
4. **Authentication**: JWT-based authentication for API access
5. **Authorization**: Role-based access control for MCP tools

### Network Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL NETWORK                         │
│                         │                                   │
│               ┌─────────▼─────────┐                         │
│               │  ZEN Coordinator  │ ◄─ ONLY EXPOSED PORT   │
│               │    (Port 7000)    │                         │
│               └─────────┬─────────┘                         │
└─────────────────────────┼─────────────────────────────────────┘
                          │
┌─────────────────────────▼─────────────────────────────────────┐
│                 INTERNAL DOCKER NETWORK                       │
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │   MCP   │  │   MCP   │  │   MCP   │  │   MCP   │         │
│  │   7001  │  │   7002  │  │   7003  │  │   7004  │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
│                                                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐         │
│  │Database │  │  Redis  │  │ Qdrant  │  │Portainer│         │
│  │  7021   │  │  7022   │  │  6333   │  │  9001   │         │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘         │
└───────────────────────────────────────────────────────────────┘
```

### Port Allocation Strategy

| Port Range | Purpose | Security Level | Access |
|------------|---------|----------------|--------|
| 7000 | ZEN Coordinator | Public | External + Internal |
| 7001-7017 | MCP Services | Private | Internal Only |
| 7021-7022 | Databases | Private | Internal Only |
| 6333 | Vector Store | Private | Internal Only |
| 9001 | Management | Limited | Portainer Only |

## 🧩 Component Architecture

### ZEN Coordinator (Port 7000)

**Purpose**: Central orchestration hub and security gateway
**Technology**: Python FastAPI
**Key Features**:
- Request routing to appropriate MCP services
- Authentication and authorization
- Rate limiting and request validation
- Health monitoring and service discovery
- Protocol translation (HTTP → MCP JSON-RPC)

**Code Structure**:
```python
zen_mcp_server.py (408 lines, 16.4KB)
├── Authentication Layer
├── Request Router
├── Service Discovery
├── MCP Protocol Handler
├── Health Monitor
└── Error Handler
```

**Critical Responsibilities**:
1. **Security Gateway**: All external requests must pass through
2. **Service Discovery**: Maintains registry of available MCP services
3. **Protocol Translation**: Converts HTTP requests to MCP JSON-RPC
4. **Load Balancing**: Distributes requests across service instances
5. **Circuit Breaker**: Handles service failures gracefully

### MCP Services Layer

#### 1. Filesystem MCP (Port 7001)
**Container**: `mcp-filesystem`
**Purpose**: File system operations and management
**Tools**: 5 tools
- `file_read`: Read file contents
- `file_write`: Write/create files
- `file_list`: Directory listing
- `file_search`: Pattern-based file search
- `file_analyze`: File metadata analysis

**Technology Stack**:
- Language: Python 3.12+
- Framework: FastAPI
- File I/O: aiofiles for async operations
- Security: Path traversal protection

#### 2. Git MCP (Port 7002)
**Container**: `mcp-git`
**Purpose**: Version control operations
**Tools**: 5 tools
- `git_status`: Repository status
- `git_commit`: Create commits
- `git_push`: Push to remote
- `git_log`: Commit history
- `git_diff`: Show differences

**Technology Stack**:
- Language: Python 3.12+
- Git Library: GitPython
- Authentication: SSH key / token support
- Repository: Local git operations

#### 3. Terminal MCP (Port 7003)
**Container**: `mcp-terminal`
**Purpose**: System command execution
**Tools**: 3 tools
- `terminal_exec`: Command execution
- `shell_command`: Advanced shell operations
- `system_info`: System information

**Technology Stack**:
- Language: Python 3.12+
- Process Management: asyncio subprocess
- Security: Command sanitization
- Isolation: Containerized execution

#### 4. Database MCP (Port 7004)
**Container**: `mcp-database`
**Purpose**: Database operations and management
**Tools**: 4 tools
- `db_query`: Execute queries
- `db_connect`: Connection management
- `db_schema`: Schema introspection
- `db_backup`: Database backup

**Technology Stack**:
- Language: Python 3.12+
- Drivers: asyncpg (PostgreSQL), aioredis (Redis)
- Connection Pooling: Built-in pool management
- Security: Parameterized queries

#### 5. Memory MCP (Port 7005)
**Container**: `mcp-memory`
**Purpose**: Information storage and retrieval
**Tools**: 5 tools
- `store_memory`: Store information
- `search_memories`: Semantic search
- `get_context`: Context retrieval
- `memory_stats`: Statistics
- `list_memories`: List all memories

**Technology Stack**:
- Language: Python 3.12+
- Vector Store: Qdrant integration
- Embeddings: sentence-transformers
- Database: PostgreSQL for metadata

#### 6. Research MCP (Port 7011)
**Container**: `mcp-research`
**Purpose**: Research and web search operations
**Tools**: 3 tools
- `research_query`: Research queries
- `perplexity_search`: Perplexity AI integration
- `web_search`: General web search

**Technology Stack**:
- Language: Python 3.12+
- APIs: Perplexity AI, web search APIs
- Caching: Redis for search results
- Rate Limiting: API quota management

#### 7. Advanced Memory MCP (Port 7012)
**Container**: `mcp-advanced-memory`
**Purpose**: Enhanced memory with AI capabilities
**Technology Stack**:
- Language: Python 3.12+
- AI Integration: Gemini API
- Enhanced Embeddings: Multi-model support
- Context Management: Advanced context windows

#### 8. Transcriber MCP (Port 7013) ⚠️
**Container**: `mcp-transcriber`
**Purpose**: Audio/video transcription
**Status**: Currently unhealthy - requires debugging
**Tools**: 3 tools
- `transcribe_webm`: WebM transcription
- `transcribe_url`: URL-based transcription
- `audio_convert`: Format conversion

**Technology Stack**:
- Language: Python 3.12+
- Audio Processing: FFmpeg, Whisper
- AI Models: OpenAI Whisper, Gemini
- Format Support: WebM, MP3, WAV, MP4

## 🗄️ Data Architecture

### Database Layer

#### PostgreSQL (Port 7021)
**Container**: `mcp-postgresql`
**Purpose**: Primary relational database
**Databases**:
- `mcp_unified`: Main application database
- User: `mcp_admin`

**Schema Overview**:
```sql
-- Memory storage
CREATE TABLE memories (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding VECTOR(384),
    tags TEXT[],
    created_at TIMESTAMP DEFAULT NOW(),
    importance FLOAT DEFAULT 0.5
);

-- Context information
CREATE TABLE contexts (
    id SERIAL PRIMARY KEY,
    context_data JSONB,
    related_memories INTEGER[],
    created_at TIMESTAMP DEFAULT NOW()
);

-- Service logs
CREATE TABLE service_logs (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(50),
    tool_name VARCHAR(50),
    request_data JSONB,
    response_data JSONB,
    execution_time INTERVAL,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

#### Redis (Port 7022)
**Container**: `mcp-redis`
**Purpose**: Caching and session management
**Usage**:
- API rate limiting counters
- Search result caching
- Session storage
- Temporary data storage

**Key Patterns**:
```
api_limit:{user_id} → request count
search_cache:{query_hash} → search results
session:{session_id} → user session data
service_health:{service} → health status
```

#### Qdrant Vector Database (Port 6333)
**Container**: `mcp-qdrant`
**Purpose**: Vector embeddings and semantic search
**Collections**:
- `memories`: Memory embeddings
- `documents`: Document embeddings
- `contexts`: Context embeddings

**Configuration**:
```yaml
collections:
  memories:
    vectors:
      size: 384  # sentence-transformers model
      distance: Cosine
    storage_type: InMemory
```

### Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │    │    ZEN      │    │    MCP      │
│   Request   ├────┤ Coordinator ├────┤   Service   │
└─────────────┘    └─────┬───────┘    └──────┬──────┘
                         │                   │
                         ▼                   ▼
                  ┌─────────────┐    ┌─────────────┐
                  │   Redis     │    │ PostgreSQL │
                  │  (Cache)    │    │ (Primary)   │
                  └─────────────┘    └─────────────┘
                         │                   │
                         └─────────┬─────────┘
                                   ▼
                            ┌─────────────┐
                            │   Qdrant    │
                            │  (Vector)   │
                            └─────────────┘
```

## 🔄 Communication Protocols

### MCP Protocol Implementation

The platform implements **Model Context Protocol (MCP)** for tool communication:

#### JSON-RPC 2.0 Format
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "file_read",
    "arguments": {
      "path": "/home/orchestration/README.md"
    }
  },
  "id": "request_123"
}
```

#### Response Format
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "File contents here..."
      }
    ]
  },
  "id": "request_123"
}
```

### Internal Service Communication

#### HTTP Health Checks
All services expose `/health` endpoint:
```json
{
  "status": "ok",
  "timestamp": "2025-08-17T03:24:38.371865",
  "version": "1.0.0",
  "uptime": "26h"
}
```

#### Service Discovery Protocol
ZEN Coordinator maintains service registry:
```json
{
  "services": [
    {
      "name": "filesystem",
      "host": "mcp-filesystem",
      "port": 7001,
      "status": "healthy",
      "tools": ["file_read", "file_write", ...]
    }
  ]
}
```

## 🚀 Deployment Architecture

### Container Orchestration

The platform uses **Docker Compose** for orchestration:

```yaml
version: '3.8'

networks:
  orchestration_network:
    driver: bridge
    internal: true  # Internal network for security

services:
  # Infrastructure Services
  mcp-postgresql:
    image: postgres:13
    networks: [orchestration_network]
    
  mcp-redis:
    image: redis:6-alpine
    networks: [orchestration_network]
    
  mcp-qdrant:
    image: qdrant/qdrant:latest
    networks: [orchestration_network]
  
  # MCP Services
  mcp-filesystem:
    build: ./services/filesystem
    networks: [orchestration_network]
    depends_on: [mcp-postgresql]
    
  # Coordinator (Only service with external port)
  zen-coordinator:
    build: ./coordinator
    ports: ["7000:8020"]
    networks: [orchestration_network]
    depends_on: [all_mcp_services]
```

### Scaling Strategy

#### Horizontal Scaling
```yaml
# Scale MCP services based on load
services:
  mcp-filesystem:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: 0.5
          
  zen-coordinator:
    deploy:
      replicas: 2  # Load balanced
      resources:
        limits:
          memory: 1G
          cpus: 1.0
```

#### Vertical Scaling
- **Memory**: Increase container memory limits
- **CPU**: Adjust CPU allocation based on tool usage
- **Storage**: Expand volumes for databases

### Resource Requirements

| Component | Min RAM | Min CPU | Storage | Scaling |
|-----------|---------|---------|---------|---------|
| ZEN Coordinator | 512MB | 0.5 CPU | 1GB | Horizontal |
| Filesystem MCP | 256MB | 0.25 CPU | 500MB | Horizontal |
| Git MCP | 256MB | 0.25 CPU | 500MB | Horizontal |
| Terminal MCP | 512MB | 0.5 CPU | 500MB | Limited |
| Database MCP | 512MB | 0.5 CPU | 500MB | Horizontal |
| Memory MCP | 1GB | 0.5 CPU | 2GB | Vertical |
| Research MCP | 512MB | 0.5 CPU | 1GB | Horizontal |
| Transcriber MCP | 2GB | 1.0 CPU | 3GB | Vertical |
| PostgreSQL | 1GB | 0.5 CPU | 10GB | Vertical |
| Redis | 512MB | 0.25 CPU | 2GB | Horizontal |
| Qdrant | 2GB | 1.0 CPU | 20GB | Vertical |

## 🔧 Configuration Management

### Environment Variables

#### Global Configuration
```bash
# Network Configuration
ZEN_COORDINATOR_HOST=0.0.0.0
ZEN_COORDINATOR_PORT=7000
INTERNAL_NETWORK=orchestration_network

# Security Configuration
ENABLE_AUTH=true
JWT_SECRET=your_jwt_secret_here
API_RATE_LIMIT=100
CORS_ORIGINS=*

# Database Configuration
POSTGRES_HOST=mcp-postgresql
POSTGRES_PORT=5432
POSTGRES_DB=mcp_unified
POSTGRES_USER=mcp_admin
POSTGRES_PASSWORD=secure_password

# Cache Configuration
REDIS_HOST=mcp-redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password

# Vector Database
QDRANT_HOST=mcp-qdrant
QDRANT_PORT=6333
QDRANT_API_KEY=qdrant_api_key
```

#### Service-Specific Configuration
```bash
# Filesystem MCP
FILESYSTEM_ROOT=/home/orchestration
FILESYSTEM_MAX_FILE_SIZE=100MB
FILESYSTEM_ALLOWED_EXTENSIONS=.txt,.md,.py,.js,.json,.yml,.yaml

# Git MCP
GIT_DEFAULT_BRANCH=master
GIT_MAX_REPO_SIZE=1GB
GIT_SSH_KEY_PATH=/root/.ssh/id_rsa

# Terminal MCP
TERMINAL_TIMEOUT=300
TERMINAL_MAX_OUTPUT_SIZE=10MB
TERMINAL_ALLOWED_COMMANDS=ls,cat,grep,find,ps,top,df,free

# Memory MCP
MEMORY_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
MEMORY_MAX_CONTEXT_SIZE=4096
MEMORY_SIMILARITY_THRESHOLD=0.7

# Research MCP
PERPLEXITY_API_KEY=your_perplexity_key
WEB_SEARCH_ENGINE=google
SEARCH_RESULT_LIMIT=20

# Transcriber MCP
WHISPER_MODEL=base
TRANSCRIPTION_LANGUAGE=auto
MAX_AUDIO_SIZE=500MB
```

### Configuration Precedence
1. Environment variables (highest priority)
2. `.env` file
3. Docker Compose defaults
4. Application defaults (lowest priority)

## 🔍 Monitoring & Observability

### Health Monitoring Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  External       │    │  ZEN Health     │    │  Service        │
│  Monitors       ├────┤  Monitor        ├────┤  Health         │
│                 │    │                 │    │  Endpoints      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Metrics Collection

#### Application Metrics
- Request count per tool
- Response time per service
- Error rate per endpoint
- Memory usage per container
- CPU utilization trends

#### Infrastructure Metrics
- Database connection count
- Cache hit/miss ratio
- Disk usage trends
- Network I/O patterns
- Container restart count

### Logging Architecture

#### Structured Logging Format
```json
{
  "timestamp": "2025-08-17T03:24:38.371865Z",
  "level": "INFO",
  "service": "zen-coordinator",
  "tool": "file_read",
  "request_id": "req_123456",
  "execution_time": "0.045s",
  "status": "success",
  "user_id": "user_789",
  "message": "File read operation completed"
}
```

#### Log Aggregation
- Container logs collected via Docker logging driver
- Centralized logging with structured JSON format
- Log rotation and retention policies
- Search and filtering capabilities

## 🛡️ Security Considerations

### Threat Model

#### External Threats
1. **API Abuse**: Rate limiting, authentication required
2. **Data Breach**: Encryption at rest and in transit
3. **Service Disruption**: Circuit breakers, graceful degradation
4. **Unauthorized Access**: JWT authentication, RBAC

#### Internal Threats
1. **Service Compromise**: Network segmentation, least privilege
2. **Data Leakage**: Audit logging, access controls
3. **Privilege Escalation**: Container isolation, security contexts

### Security Controls

#### Network Security
- **Zero Trust Model**: No service directly accessible externally
- **Network Segmentation**: Internal Docker network isolation
- **TLS Encryption**: All external communication encrypted
- **Firewall Rules**: Strict port access controls

#### Application Security
- **Input Validation**: All inputs sanitized and validated
- **Output Encoding**: Prevent injection attacks
- **Authentication**: JWT-based API authentication
- **Authorization**: Role-based access control

#### Data Security
- **Encryption at Rest**: Database encryption enabled
- **Encryption in Transit**: TLS for all communication
- **Key Management**: Secure key storage and rotation
- **Backup Security**: Encrypted backups with access controls

## 🔄 Disaster Recovery

### Backup Strategy

#### Database Backups
```bash
# Automated daily backup
docker exec mcp-postgresql pg_dump -U mcp_admin mcp_unified > backup_$(date +%Y%m%d).sql

# Vector database backup
curl -X POST "http://mcp-qdrant:6333/collections/memories/snapshots"
```

#### Configuration Backups
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml
```

### Recovery Procedures

#### Service Recovery
1. **Single Service Failure**: `docker-compose restart service_name`
2. **Multiple Service Failure**: `docker-compose down && docker-compose up -d`
3. **Complete System Failure**: Full restoration from backups

#### Data Recovery
1. **Database Corruption**: Restore from latest backup
2. **Vector Database Loss**: Rebuild embeddings from source data
3. **Configuration Loss**: Restore from configuration backup

### High Availability

#### Load Balancing
- Multiple ZEN Coordinator instances
- Database read replicas
- Service instance scaling

#### Failover Mechanisms
- Health check-based failover
- Circuit breaker patterns
- Graceful degradation modes

---

This architecture provides a robust, secure, and scalable foundation for the MCP orchestration platform. The design emphasizes security through isolation, scalability through microservices, and maintainability through clear separation of concerns.
