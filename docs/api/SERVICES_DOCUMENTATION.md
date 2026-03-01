# Services Documentation - Orchestration MCP Platform

## 🎯 Services Overview

The Orchestration MCP Platform consists of **8 MCP services** providing **28 specialized tools** for AI agents and applications, plus a ZEN MCP gateway for orchestration. Each service is containerized and communicates through the MCP (Model Context Protocol) standard.

### Service Architecture Summary

| Service | Port | Container | Tools | Status | Purpose |
|---------|------|-----------|-------|--------|---------|
| [Filesystem MCP](#filesystem-mcp-port-7001) | 7001 | `mcp-filesystem` | 5 | ✅ Running | File operations |
| [Git MCP](#git-mcp-port-7002) | 7002 | `mcp-git` | 5 | ✅ Running | Version control |
| [Terminal MCP](#terminal-mcp-port-7003) | 7003 | `mcp-terminal` | 3 | ✅ Running | System commands |
| [Database MCP](#database-mcp-port-7004) | 7004 | `mcp-database` | 4 | ✅ Running | Database operations |
| [Memory MCP](#memory-mcp-port-7005) | 7005 | `mcp-memory` | 5 | ✅ Running | Information storage |
| [Research MCP](#research-mcp-port-7011) | 7011 | `mcp-research` | 3 | ✅ Running | Web search & research |
| [Advanced Memory MCP](#advanced-memory-mcp-port-7012) | 7012 | `mcp-advanced-memory` | 0 | ✅ Running | Enhanced AI memory |
| [Transcriber MCP](#transcriber-mcp-port-7013) | 7013 | `mcp-transcriber` | 3 | ⚠️ Debugging | Audio/video processing |
| [ZEN MCP Server](#zen-mcp-server-port-7017) | 7017 | `zen-mcp-server` | N/A | ✅ Running | MCP tool orchestration gateway |

**Total: 28 MCP Tools across 9 Services**

---

## 🗄️ Filesystem MCP (Port 7001)

**Container**: `mcp-filesystem`  
**Purpose**: Comprehensive file system operations and management  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, FastAPI, aiofiles

### Tools (5 total)

#### 1. file_read
**Description**: Read contents of files with support for multiple encodings  
**Use Cases**: Reading configuration files, logs, source code, documentation

**Parameters**:
```json
{
  "path": "/home/orchestration/README.md",
  "encoding": "utf-8",          // Optional: file encoding
  "max_size": 10485760         // Optional: max file size (10MB default)
}
```

**Response**:
```json
{
  "content": "file contents here...",
  "size": 1024,
  "encoding": "utf-8",
  "last_modified": "2025-08-17T03:24:38Z",
  "mime_type": "text/markdown"
}
```

**Example**:
```bash
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "arguments": {
      "path": "/home/orchestration/zen_mcp_server.py"
    }
  }'
```

#### 2. file_write
**Description**: Write or create files with atomic operations  
**Use Cases**: Creating configuration files, saving data, updating source code

**Parameters**:
```json
{
  "path": "/tmp/output.txt",
  "content": "Hello World",
  "mode": "w",                 // w=write, a=append, x=exclusive create
  "encoding": "utf-8",         // Optional: file encoding
  "create_dirs": true          // Optional: create parent directories
}
```

**Response**:
```json
{
  "status": "success",
  "bytes_written": 11,
  "file_created": true,
  "timestamp": "2025-08-17T03:24:38Z"
}
```

#### 3. file_list
**Description**: List directory contents with detailed metadata  
**Use Cases**: Directory exploration, file discovery, system auditing

**Parameters**:
```json
{
  "path": "/home/orchestration",
  "recursive": false,          // Optional: recursive listing
  "include_hidden": false,     // Optional: show hidden files
  "pattern": "*.py",           // Optional: file pattern filter
  "sort_by": "name"            // Optional: name, size, modified
}
```

**Response**:
```json
{
  "files": [
    {
      "name": "zen_mcp_server.py",
      "path": "/home/orchestration/zen_mcp_server.py",
      "type": "file",
      "size": 16454,
      "modified": "2025-08-17T03:24:38Z",
      "permissions": "644",
      "owner": "root"
    }
  ],
  "total_files": 12,
  "total_size": 245760
}
```

#### 4. file_search
**Description**: Search for files using patterns and content  
**Use Cases**: Finding configuration files, searching source code, locating logs

**Parameters**:
```json
{
  "path": "/home/orchestration",
  "pattern": "*.py",           // File name pattern
  "content_pattern": "async",  // Optional: search file contents
  "recursive": true,
  "case_sensitive": false,
  "max_results": 100
}
```

**Response**:
```json
{
  "matches": [
    {
      "file": "/home/orchestration/zen_mcp_server.py",
      "line_matches": [
        {
          "line_number": 45,
          "content": "async def handle_request(request):",
          "context": "Function definition"
        }
      ]
    }
  ],
  "total_matches": 23,
  "search_time": "0.156s"
}
```

#### 5. file_analyze
**Description**: Analyze file structure, metadata, and content statistics  
**Use Cases**: Code analysis, file type detection, content summarization

**Parameters**:
```json
{
  "path": "/home/orchestration/zen_mcp_server.py",
  "include_content_stats": true,  // Optional: analyze content
  "detect_language": true,        // Optional: programming language detection
  "calculate_complexity": true    // Optional: code complexity metrics
}
```

**Response**:
```json
{
  "file_info": {
    "size": 16454,
    "lines": 408,
    "language": "python",
    "encoding": "utf-8"
  },
  "content_stats": {
    "functions": 12,
    "classes": 3,
    "imports": 8,
    "complexity_score": 15.7
  },
  "security_analysis": {
    "potential_issues": [],
    "confidence": "high"
  }
}
```

### Security Features
- **Path Traversal Protection**: Prevents access outside allowed directories
- **File Size Limits**: Configurable maximum file sizes
- **Permission Checking**: Validates read/write permissions
- **Content Sanitization**: Filters dangerous file content

---

## 🔄 Git MCP (Port 7002)

**Container**: `mcp-git`  
**Purpose**: Version control operations and repository management  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, GitPython, SSH/HTTPS authentication

### Tools (5 total)

#### 1. git_status
**Description**: Check repository status including changes, branches, and remote info  
**Use Cases**: Repository health checks, change detection, branch monitoring

**Parameters**:
```json
{
  "repository": "/home/orchestration",
  "include_untracked": true,      // Optional: show untracked files
  "include_ignored": false,       // Optional: show ignored files
  "verbose": true                 // Optional: detailed output
}
```

**Response**:
```json
{
  "branch": "master",
  "remote_branch": "origin/master",
  "ahead": 0,
  "behind": 0,
  "status": "clean",
  "modified_files": [],
  "untracked_files": [],
  "staged_files": [],
  "last_commit": {
    "hash": "a1b2c3d4e5f6",
    "message": "Update documentation",
    "author": "System",
    "date": "2025-08-17T03:24:38Z"
  }
}
```

#### 2. git_commit
**Description**: Create commits with proper authoring and validation  
**Use Cases**: Automated commits, documentation updates, configuration changes

**Parameters**:
```json
{
  "repository": "/home/orchestration",
  "message": "Update MCP service configuration",
  "add_all": true,                // Optional: git add . before commit
  "author_name": "Orchestration Bot",  // Optional: custom author
  "author_email": "bot@orchestration.local",
  "files": ["specific_file.py"]   // Optional: commit specific files only
}
```

**Response**:
```json
{
  "status": "success",
  "commit_hash": "a1b2c3d4e5f6789",
  "message": "Update MCP service configuration",
  "files_changed": 3,
  "insertions": 45,
  "deletions": 12,
  "timestamp": "2025-08-17T03:24:38Z"
}
```

#### 3. git_push
**Description**: Push commits to remote repositories with authentication  
**Use Cases**: Deploying changes, synchronizing repositories, backup

**Parameters**:
```json
{
  "repository": "/home/orchestration",
  "remote": "origin",             // Optional: remote name (default: origin)
  "branch": "master",             // Optional: branch name (default: current)
  "force": false,                 // Optional: force push
  "set_upstream": true            // Optional: set upstream branch
}
```

**Response**:
```json
{
  "status": "success",
  "remote": "origin",
  "branch": "master",
  "commits_pushed": 2,
  "bytes_transferred": 4096,
  "remote_url": "https://github.com/milhy545/orchestration.git"
}
```

#### 4. git_log
**Description**: View commit history with filtering and formatting options  
**Use Cases**: Audit trails, change tracking, release notes generation

**Parameters**:
```json
{
  "repository": "/home/orchestration",
  "limit": 10,                    // Optional: number of commits
  "since": "2025-08-01",         // Optional: date filter
  "author": "System",            // Optional: author filter
  "format": "detailed",          // Optional: oneline, short, detailed
  "file_path": "zen_mcp_server.py"  // Optional: commits affecting specific file
}
```

**Response**:
```json
{
  "commits": [
    {
      "hash": "a1b2c3d4e5f6",
      "short_hash": "a1b2c3d",
      "message": "Update documentation",
      "author": "System",
      "email": "system@orchestration.local",
      "date": "2025-08-17T03:24:38Z",
      "files_changed": ["README.md", "API_DOCUMENTATION.md"]
    }
  ],
  "total_commits": 156,
  "repository_age": "45 days"
}
```

#### 5. git_diff
**Description**: Show differences between commits, files, or working directory  
**Use Cases**: Code review, change analysis, conflict resolution

**Parameters**:
```json
{
  "repository": "/home/orchestration",
  "file": "zen_mcp_server.py",   // Optional: specific file
  "staged": false,                // Optional: show staged changes
  "commit1": "HEAD~1",           // Optional: compare commits
  "commit2": "HEAD",
  "context_lines": 3             // Optional: lines of context
}
```

**Response**:
```json
{
  "diff": "@@ -45,7 +45,7 @@ async def handle_request(request):\n-    old_line\n+    new_line",
  "files_changed": 1,
  "insertions": 12,
  "deletions": 8,
  "binary_files": false
}
```

### Authentication Support
- **SSH Keys**: Support for SSH key authentication
- **HTTPS Tokens**: Personal access tokens for HTTPS
- **Git Credentials**: Stored credentials management
- **Multi-Remote**: Support for multiple remote repositories

---

## 💻 Terminal MCP (Port 7003)

**Container**: `mcp-terminal`  
**Purpose**: System command execution and system information  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, asyncio subprocess, security sandboxing

### Tools (3 total)

#### 1. terminal_exec
**Description**: Execute terminal commands with timeout and output capture  
**Use Cases**: System administration, service management, diagnostics

**Parameters**:
```json
{
  "command": "docker ps --format 'table {{.Names}}\\t{{.Status}}'",
  "working_dir": "/home/orchestration",  // Optional: working directory
  "timeout": 30,                         // Optional: timeout in seconds
  "capture_output": true,                // Optional: capture stdout/stderr
  "shell": "/bin/bash",                  // Optional: shell to use
  "env": {"VAR": "value"}               // Optional: environment variables
}
```

**Response**:
```json
{
  "stdout": "zen-coordinator\\tUp 26 hours\\nmcp-filesystem\\tUp 26 hours",
  "stderr": "",
  "exit_code": 0,
  "execution_time": "0.234s",
  "command": "docker ps --format 'table {{.Names}}\\t{{.Status}}'",
  "working_dir": "/home/orchestration"
}
```

**Security Features**:
- Command whitelist/blacklist
- Execution timeout limits
- Working directory restrictions
- Output size limits

#### 2. shell_command
**Description**: Advanced shell command execution with enhanced features  
**Use Cases**: Complex scripting, pipeline operations, system monitoring

**Parameters**:
```json
{
  "command": "ps aux | grep python | head -5",
  "capture_output": true,
  "shell": "/bin/bash",
  "interactive": false,           // Optional: interactive mode
  "background": false,            // Optional: run in background
  "input_data": "yes\\n"         // Optional: stdin input
}
```

**Response**:
```json
{
  "stdout": "root  1234  0.1  2.3  python zen_mcp_server.py",
  "stderr": "",
  "exit_code": 0,
  "process_id": 5678,
  "execution_time": "0.045s"
}
```

#### 3. system_info
**Description**: Comprehensive system information and resource monitoring  
**Use Cases**: Health monitoring, capacity planning, troubleshooting

**Parameters**:
```json
{
  "details": ["cpu", "memory", "disk", "network", "processes"],  // Optional: specific info types
  "include_docker": true,         // Optional: include Docker info
  "include_services": true,       // Optional: include systemd services
  "format": "detailed"            // Optional: brief, detailed, json
}
```

**Response**:
```json
{
  "system": {
    "hostname": "orchestration-server",
    "os": "Alpine Linux 3.18",
    "kernel": "6.1.105-antix.1-amd64-smp",
    "uptime": "26 hours 34 minutes",
    "load_average": [0.15, 0.12, 0.08]
  },
  "cpu": {
    "cores": 4,
    "usage": 12.5,
    "frequency": "2.83GHz"
  },
  "memory": {
    "total": "8.0GB",
    "used": "2.6GB",
    "free": "5.4GB",
    "usage_percent": 32.5
  },
  "disk": {
    "total": "100GB",
    "used": "45GB",
    "free": "55GB",
    "usage_percent": 45.0
  },
  "docker": {
    "version": "24.0.7",
    "containers_running": 10,
    "images": 25
  }
}
```

### Command Security
- **Restricted Commands**: Dangerous commands are blocked
- **Sandboxed Execution**: Commands run in isolated environment
- **Resource Limits**: CPU and memory limits per command
- **Audit Logging**: All commands are logged for security

---

## 🗃️ Database MCP (Port 7004)

**Container**: `mcp-database`  
**Purpose**: Multi-database operations and management  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, asyncpg, aioredis, connection pooling

### Supported Databases
- **PostgreSQL** (Primary): Full SQL operations
- **Redis**: Key-value operations and caching
- **SQLite**: File-based database operations
- **Future**: MySQL, MongoDB support planned

### Tools (4 total)

#### 1. db_query
**Description**: Execute SQL queries with parameter binding and result formatting  
**Use Cases**: Data retrieval, analysis, reporting, admin operations

**Parameters**:
```json
{
  "connection": "postgresql://mcp_admin:password@mcp-postgresql:5432/mcp_unified",
  "query": "SELECT id, content, created_at FROM memories WHERE tags && $1 LIMIT $2",
  "parameters": [["documentation"], 10],  // Optional: query parameters
  "fetch_mode": "all",                    // Optional: all, one, many
  "timeout": 30                           // Optional: query timeout
}
```

**Response**:
```json
{
  "rows": [
    {
      "id": 1,
      "content": "API documentation updated",
      "created_at": "2025-08-17T03:24:38Z"
    }
  ],
  "row_count": 1,
  "columns": ["id", "content", "created_at"],
  "execution_time": "0.012s",
  "query_plan": "Seq Scan on memories"  // Optional: if explain enabled
}
```

**Redis Example**:
```json
{
  "connection": "redis://mcp-redis:6379/0",
  "query": "GET search_cache:api_docs",
  "parameters": []
}
```

#### 2. db_connect
**Description**: Test database connections and retrieve connection info  
**Use Cases**: Health checks, connection validation, troubleshooting

**Parameters**:
```json
{
  "connection_string": "postgresql://mcp_admin:password@mcp-postgresql:5432/mcp_unified",
  "test_query": "SELECT 1",            // Optional: custom test query
  "timeout": 10                        // Optional: connection timeout
}
```

**Response**:
```json
{
  "status": "connected",
  "database_type": "postgresql",
  "server_version": "13.12",
  "database_name": "mcp_unified",
  "connection_info": {
    "host": "mcp-postgresql",
    "port": 5432,
    "ssl_mode": "prefer"
  },
  "test_result": "success",
  "response_time": "0.003s"
}
```

#### 3. db_schema
**Description**: Retrieve database schema information and metadata  
**Use Cases**: Database documentation, migration planning, analysis

**Parameters**:
```json
{
  "connection": "postgresql://mcp_admin:password@mcp-postgresql:5432/mcp_unified",
  "table": "memories",                 // Optional: specific table
  "include_indexes": true,             // Optional: include index info
  "include_constraints": true,         // Optional: include constraints
  "include_statistics": true           // Optional: include table statistics
}
```

**Response**:
```json
{
  "tables": [
    {
      "name": "memories",
      "schema": "public",
      "columns": [
        {
          "name": "id",
          "type": "integer",
          "nullable": false,
          "primary_key": true,
          "default": "nextval('memories_id_seq'::regclass)"
        },
        {
          "name": "content",
          "type": "text",
          "nullable": false
        }
      ],
      "indexes": [
        {
          "name": "memories_pkey",
          "type": "btree",
          "unique": true,
          "columns": ["id"]
        }
      ],
      "row_count": 1247,
      "size": "256KB"
    }
  ]
}
```

#### 4. db_backup
**Description**: Create database backups with multiple format options  
**Use Cases**: Data protection, migration preparation, disaster recovery

**Parameters**:
```json
{
  "connection": "postgresql://mcp_admin:password@mcp-postgresql:5432/mcp_unified",
  "output_path": "/tmp/backup_20250817.sql",
  "format": "sql",                     // Optional: sql, json, csv
  "tables": ["memories", "contexts"],  // Optional: specific tables
  "compression": true,                 // Optional: compress output
  "include_data": true                 // Optional: schema only or with data
}
```

**Response**:
```json
{
  "status": "success",
  "backup_file": "/tmp/backup_20250817.sql.gz",
  "file_size": "2.4MB",
  "tables_backed_up": ["memories", "contexts", "service_logs"],
  "rows_backed_up": 15673,
  "backup_time": "4.567s",
  "compression_ratio": "73%"
}
```

### Connection Management
- **Connection Pooling**: Automatic connection pool management
- **Health Monitoring**: Continuous connection health checks
- **Failover Support**: Automatic failover for read replicas
- **Security**: Encrypted connections and credential management

---

## 🧠 Memory MCP (Port 7005)

**Container**: `mcp-memory`  
**Purpose**: Information storage and retrieval with semantic search  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, PostgreSQL, Qdrant, sentence-transformers

### Storage Architecture
- **Text Storage**: PostgreSQL for structured data
- **Vector Storage**: Qdrant for semantic embeddings
- **Caching**: Redis for frequently accessed memories
- **Indexing**: Full-text search and semantic similarity

### Tools (5 total)

#### 1. store_memory
**Description**: Store information with automatic embedding generation  
**Use Cases**: Knowledge base building, context preservation, learning systems

**Parameters**:
```json
{
  "content": "The ZEN Coordinator handles all external API requests and routes them to appropriate MCP services",
  "tags": ["architecture", "zen-coordinator", "api"],  // Optional: categorization tags
  "context": "Documentation about system architecture",  // Optional: context information
  "importance": 0.8,                    // Optional: importance score (0.0-1.0)
  "metadata": {                         // Optional: additional metadata
    "source": "documentation",
    "author": "system",
    "version": "1.0"
  }
}
```

**Response**:
```json
{
  "memory_id": "mem_20250817_001234",
  "status": "stored",
  "embedding_generated": true,
  "vector_id": "vec_001234",
  "tags_processed": 3,
  "timestamp": "2025-08-17T03:24:38Z",
  "storage_info": {
    "content_length": 156,
    "embedding_dimension": 384,
    "processing_time": "0.234s"
  }
}
```

#### 2. search_memories
**Description**: Semantic search through stored memories with ranking  
**Use Cases**: Knowledge retrieval, context finding, intelligent assistance

**Parameters**:
```json
{
  "query": "How does the ZEN Coordinator work?",
  "limit": 10,                          // Optional: max results
  "similarity_threshold": 0.7,          // Optional: minimum similarity
  "tags": ["architecture"],             // Optional: filter by tags
  "include_metadata": true,             // Optional: include metadata
  "date_range": {                       // Optional: date filtering
    "start": "2025-08-01",
    "end": "2025-08-17"
  }
}
```

**Response**:
```json
{
  "memories": [
    {
      "id": "mem_20250817_001234",
      "content": "The ZEN Coordinator handles all external API requests...",
      "similarity": 0.92,
      "tags": ["architecture", "zen-coordinator", "api"],
      "metadata": {
        "source": "documentation",
        "author": "system"
      },
      "created_at": "2025-08-17T03:24:38Z",
      "importance": 0.8
    }
  ],
  "total_found": 1,
  "search_time": "0.034s",
  "query_embedding_time": "0.012s"
}
```

#### 3. get_context
**Description**: Retrieve related context and memory networks  
**Use Cases**: Context building, knowledge graphs, related information discovery

**Parameters**:
```json
{
  "context_id": "ctx_architecture_001",  // Optional: specific context ID
  "memory_ids": ["mem_20250817_001234"], // Optional: specific memories
  "depth": 2,                           // Optional: context depth
  "include_related": true,              // Optional: include related memories
  "relationship_types": ["similar", "referenced"]  // Optional: relationship filters
}
```

**Response**:
```json
{
  "context": {
    "id": "ctx_architecture_001",
    "primary_memories": [
      {
        "id": "mem_20250817_001234",
        "content": "The ZEN Coordinator handles...",
        "relevance": 1.0
      }
    ],
    "related_memories": [
      {
        "id": "mem_20250817_001235",
        "content": "MCP services communicate via JSON-RPC...",
        "relevance": 0.85,
        "relationship": "similar"
      }
    ],
    "context_summary": "Information about system architecture and communication patterns",
    "total_memories": 12,
    "context_strength": 0.87
  }
}
```

#### 4. memory_stats
**Description**: Statistics and analytics about the memory system  
**Use Cases**: System monitoring, usage analysis, optimization

**Parameters**:
```json
{
  "include_details": true,              // Optional: detailed statistics
  "group_by": "tags",                   // Optional: group statistics by field
  "time_range": "7d"                   // Optional: time range for stats
}
```

**Response**:
```json
{
  "total_memories": 1247,
  "total_size": "45.2MB",
  "average_similarity": 0.73,
  "storage_distribution": {
    "text_storage": "12.3MB",
    "vector_storage": "32.9MB"
  },
  "tag_distribution": {
    "documentation": 456,
    "api": 234,
    "architecture": 123
  },
  "daily_growth": {
    "memories_added": 23,
    "average_importance": 0.68
  },
  "performance_metrics": {
    "avg_search_time": "0.034s",
    "avg_storage_time": "0.156s",
    "cache_hit_rate": "78%"
  }
}
```

#### 5. list_memories
**Description**: List and browse stored memories with filtering and pagination  
**Use Cases**: Memory management, browsing, administration

**Parameters**:
```json
{
  "limit": 50,                         // Optional: results per page
  "offset": 0,                         // Optional: pagination offset
  "sort_by": "created_at",            // Optional: created_at, importance, similarity
  "order": "desc",                    // Optional: asc, desc
  "tags": ["documentation"],          // Optional: filter by tags
  "importance_min": 0.5,              // Optional: minimum importance
  "search_filter": "coordinator"      // Optional: text filter
}
```

**Response**:
```json
{
  "memories": [
    {
      "id": "mem_20250817_001234",
      "content": "The ZEN Coordinator handles all external API requests...",
      "tags": ["architecture", "zen-coordinator", "api"],
      "importance": 0.8,
      "created_at": "2025-08-17T03:24:38Z",
      "size": 156
    }
  ],
  "pagination": {
    "total": 1247,
    "limit": 50,
    "offset": 0,
    "has_more": true
  }
}
```

### AI Integration Features
- **Automatic Embedding**: Uses sentence-transformers for semantic embeddings
- **Context Linking**: Automatic relationship detection between memories
- **Smart Tagging**: AI-assisted tag suggestion and categorization
- **Importance Scoring**: Automatic importance calculation based on content

---

## 🔍 Research MCP (Port 7011)

**Container**: `mcp-research`  
**Purpose**: Web search, research, and information gathering  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, Perplexity AI, web search APIs, caching

### API Integrations
- **Perplexity AI**: Advanced AI-powered search
- **Web Search APIs**: Google, Bing, DuckDuckGo
- **Academic Sources**: ArXiv, PubMed integration
- **Documentation**: GitHub, official docs search

### Tools (3 total)

#### 1. research_query
**Description**: Comprehensive research with multiple sources and AI analysis  
**Use Cases**: Technical research, documentation gathering, problem solving

**Parameters**:
```json
{
  "query": "MCP protocol implementation best practices 2025",
  "sources": ["web", "academic", "documentation", "github"],  // Optional: source types
  "depth": "detailed",                  // Optional: brief, detailed, comprehensive
  "max_results": 20,                   // Optional: maximum results
  "time_filter": "recent",             // Optional: recent, year, all
  "language": "en"                     // Optional: search language
}
```

**Response**:
```json
{
  "research_summary": "MCP (Model Context Protocol) implementation best practices include...",
  "sources": [
    {
      "title": "MCP Protocol Implementation Guide",
      "url": "https://modelcontextprotocol.io/docs/implementation",
      "snippet": "The Model Context Protocol (MCP) is a standard for...",
      "relevance": 0.95,
      "source_type": "documentation",
      "date": "2025-08-15"
    },
    {
      "title": "Building MCP Servers: A Practical Guide",
      "url": "https://github.com/example/mcp-guide",
      "snippet": "This guide covers practical implementation details...",
      "relevance": 0.88,
      "source_type": "github",
      "stars": 1247
    }
  ],
  "total_results": 67,
  "search_time": "2.456s",
  "ai_analysis": {
    "key_concepts": ["JSON-RPC", "tool calling", "security"],
    "recommendations": ["Use proper error handling", "Implement rate limiting"],
    "confidence": 0.87
  }
}
```

#### 2. perplexity_search
**Description**: AI-powered search using Perplexity with citations  
**Use Cases**: Complex questions, current events, technical explanations

**Parameters**:
```json
{
  "query": "What are the latest developments in container orchestration for 2025?",
  "mode": "precise",                   // Optional: precise, balanced, creative
  "include_citations": true,           // Optional: include source citations
  "focus": "technical",               // Optional: technical, general, news
  "recency": "recent"                 // Optional: recent, all
}
```

**Response**:
```json
{
  "answer": "The latest developments in container orchestration for 2025 include enhanced security features in Kubernetes 1.31, improved multi-cloud management with service mesh integration, and the rise of edge computing orchestration platforms...",
  "citations": [
    {
      "id": 1,
      "title": "Kubernetes 1.31 Release Notes",
      "url": "https://kubernetes.io/blog/2025/08/kubernetes-1-31-release/",
      "relevance": "high"
    },
    {
      "id": 2,
      "title": "Cloud Native Computing Foundation Annual Report 2025",
      "url": "https://cncf.io/reports/annual-report-2025",
      "relevance": "medium"
    }
  ],
  "confidence": 0.91,
  "processing_time": "3.234s",
  "tokens_used": 1456
}
```

#### 3. web_search
**Description**: General web search with result filtering and ranking  
**Use Cases**: Quick searches, fact checking, current information

**Parameters**:
```json
{
  "query": "Docker Compose health check configuration examples",
  "limit": 15,                        // Optional: max results
  "filter_domains": ["docs.docker.com", "stackoverflow.com"],  // Optional: domain filter
  "exclude_domains": ["spam-site.com"],  // Optional: domain exclusion
  "safe_search": true,                // Optional: safe search filter
  "region": "US"                      // Optional: search region
}
```

**Response**:
```json
{
  "results": [
    {
      "title": "Docker Compose Health Check Configuration",
      "url": "https://docs.docker.com/compose/compose-file/compose-file-v3/#healthcheck",
      "snippet": "Health checks can be configured in Docker Compose files using the healthcheck key...",
      "domain": "docs.docker.com",
      "rank": 1,
      "date": "2025-08-10"
    },
    {
      "title": "Advanced Docker Health Check Examples",
      "url": "https://stackoverflow.com/questions/docker-health-checks",
      "snippet": "Here are several practical examples of Docker health checks...",
      "domain": "stackoverflow.com",
      "rank": 2,
      "votes": 245
    }
  ],
  "total_results": 15673,
  "search_time": "0.567s",
  "spelling_suggestion": null
}
```

### Search Features
- **Result Caching**: Redis-based caching for performance
- **Rate Limiting**: API quota management and throttling
- **Content Filtering**: Safe search and quality filtering
- **Multi-Source**: Aggregation from multiple search providers

---

## 🧠+ Advanced Memory MCP (Port 7012)

**Container**: `mcp-advanced-memory`  
**Purpose**: Enhanced memory capabilities with AI integration  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Python 3.12+, Gemini AI, advanced embeddings, context management

### Enhanced Features
- **Multi-Model Embeddings**: Support for multiple embedding models
- **AI-Enhanced Context**: Gemini AI for context understanding
- **Advanced Relationships**: Complex relationship modeling
- **Dynamic Context Windows**: Adaptive context size management

### Tools (Currently under development)
This service is running but tools are still being integrated. Expected tools include:

- `enhanced_store`: Store with AI-enhanced categorization
- `contextual_search`: Search with dynamic context understanding
- `relationship_analysis`: Advanced relationship mapping
- `knowledge_synthesis`: AI-powered knowledge synthesis
- `adaptive_learning`: Learning from usage patterns

### Current Status
The service is healthy and running, with basic memory operations delegated to the standard Memory MCP. Enhanced features are being gradually rolled out.

---

## 🎵 Transcriber MCP (Port 7013)

**Container**: `mcp-transcriber`  
**Purpose**: Audio and video transcription services  
**Status**: ⚠️ Currently unhealthy - debugging required  
**Technology**: Python 3.12+, Whisper, FFmpeg, Gemini AI

### Known Issues
- Service container is running but health checks are failing
- Audio processing dependencies may need reconfiguration
- GPU acceleration not properly configured

### Tools (3 total - currently not functioning)

#### 1. transcribe_webm
**Description**: Transcribe WebM audio/video files  
**Use Cases**: Meeting recordings, video content, voice notes

**Parameters** (when functional):
```json
{
  "file_path": "/tmp/audio.webm",
  "language": "en",                    // Optional: auto-detect or specific language
  "output_format": "text",            // Optional: text, srt, vtt, json
  "include_timestamps": true,         // Optional: include time markers
  "speaker_detection": false          // Optional: detect different speakers
}
```

#### 2. transcribe_url
**Description**: Transcribe audio/video from URL  
**Use Cases**: YouTube videos, podcasts, online meetings

**Parameters** (when functional):
```json
{
  "url": "https://example.com/audio.mp3",
  "language": "auto",
  "format": "text",
  "max_duration": 3600               // Optional: max duration in seconds
}
```

#### 3. audio_convert
**Description**: Convert between audio formats  
**Use Cases**: Format compatibility, compression, preprocessing

**Parameters** (when functional):
```json
{
  "input_path": "/tmp/input.mp3",
  "output_path": "/tmp/output.wav",
  "format": "wav",
  "quality": "high"                  // Optional: low, medium, high
}
```

### Debugging Steps Required
1. Check FFmpeg installation and GPU support
2. Verify Whisper model downloads
3. Test audio processing pipeline
4. Review container resource allocation
5. Update dependencies if needed

---

## 🤖 ZEN MCP Server (Port 7017)

**Container**: `zen-mcp-server`  
**Purpose**: MCP tool orchestration gateway for multi-model providers  
**Status**: ✅ Running  
**Technology**: Python 3.12+, FastAPI (runtime target)

### Notes
- Exposes MCP tool orchestration endpoints for LLM routing.
- Health check: `GET /health`

---

## 🔧 Infrastructure Services

### PostgreSQL Database (Port 7021)

**Container**: `mcp-postgresql`  
**Purpose**: Primary relational database for all MCP services  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: PostgreSQL 13, with vector extensions

**Databases**:
- `mcp_unified`: Main application database
- `postgres`: System database

**Key Tables**:
- `memories`: Memory storage with vector embeddings
- `contexts`: Context information and relationships
- `service_logs`: Audit logs for all MCP operations
- `user_sessions`: Session management data

### Redis Cache (Port 7022)

**Container**: `mcp-redis`  
**Purpose**: Caching, session storage, and temporary data  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Redis 6 Alpine

**Usage Patterns**:
- API rate limiting: `api_limit:{user_id}`
- Search caching: `search_cache:{hash}`
- Session storage: `session:{session_id}`
- Service health: `health:{service_name}`

### Qdrant Vector Database (Port 6333)

**Container**: `mcp-qdrant`  
**Purpose**: Vector embeddings and semantic search  
**Status**: ✅ Running (26h+ uptime)  
**Technology**: Qdrant latest

**Collections**:
- `memories`: Memory embeddings (384 dimensions)
- `documents`: Document embeddings
- `contexts`: Context embeddings

---

## 📊 Service Health Monitoring

### Health Check Endpoints

All services expose standard health endpoints:

```bash
# Individual service health
curl http://192.168.0.58:7001/health  # Filesystem MCP
curl http://192.168.0.58:7002/health  # Git MCP
curl http://192.168.0.58:7003/health  # Terminal MCP
curl http://192.168.0.58:7004/health  # Database MCP
curl http://192.168.0.58:7005/health  # Memory MCP
curl http://192.168.0.58:7011/health  # Research MCP
curl http://192.168.0.58:7012/health  # Advanced Memory MCP
curl http://192.168.0.58:7013/health  # Transcriber MCP (unhealthy)

# Unified health via ZEN Coordinator
curl http://192.168.0.58:7000/health
curl http://192.168.0.58:7000/services
```

### Service Dependencies

```
ZEN Coordinator (7000)
├── Depends on all MCP services (7001-7017)
├── PostgreSQL (7021) ← Required for Database MCP
├── Redis (7022) ← Required for caching
└── Qdrant (6333) ← Required for Memory MCP

MCP Services (7001-7017)
├── Independent of each other
├── May use PostgreSQL for data storage
├── May use Redis for caching
└── Report to ZEN Coordinator
```

### Performance Metrics

Current performance benchmarks:
- **Average Response Time**: 45ms per MCP tool call
- **Throughput**: 100+ requests per second
- **Memory Usage**: 2.6GB total across all services
- **CPU Usage**: 12-15% average system load
- **Uptime**: 26+ hours continuous operation

---

## 🔄 Service Integration Examples

### Multi-Service Workflow Example

```bash
# 1. Search for information using Research MCP
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "research_query",
    "arguments": {
      "query": "Docker health check best practices",
      "sources": ["documentation", "github"]
    }
  }'

# 2. Store the research results in Memory MCP
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "content": "Docker health checks should include timeout, interval, and retries parameters...",
      "tags": ["docker", "health-checks", "research"],
      "importance": 0.8
    }
  }'

# 3. Create a configuration file using Filesystem MCP
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_write",
    "arguments": {
      "path": "/tmp/docker-compose-healthcheck.yml",
      "content": "version: \"3.8\"\nservices:\n  app:\n    healthcheck:\n      test: [\"CMD\", \"curl\", \"-f\", \"http://localhost:8080/health\"]\n      interval: 30s\n      timeout: 10s\n      retries: 3"
    }
  }'

# 4. Commit the changes using Git MCP
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_commit",
    "arguments": {
      "repository": "/home/orchestration",
      "message": "Add Docker health check configuration example",
      "add_all": true
    }
  }'
```

---

## 🎯 Service Usage Recommendations

### For AI Agents
- **Start with Memory MCP**: Store and retrieve context information
- **Use Research MCP**: Gather current information and documentation
- **Leverage Filesystem MCP**: Read configurations and create files
- **Git MCP for Version Control**: Track changes and collaborate
- **Database MCP for Persistence**: Store structured data

### For Applications
- **API Integration**: Use ZEN Coordinator as single entry point
- **Batch Operations**: Combine multiple MCP tools for complex workflows
- **Caching Strategy**: Leverage Redis through Database MCP
- **Error Handling**: Implement proper error handling for service failures

### For System Administration
- **Terminal MCP**: System monitoring and administration
- **Database MCP**: Backup and maintenance operations
- **Health Monitoring**: Regular health checks across all services
- **Performance Tuning**: Monitor and optimize based on usage patterns

---

This comprehensive services documentation provides detailed information about all 28 MCP tools across 8 services in the Orchestration platform. Each service is designed to work independently while providing seamless integration through the unified ZEN Coordinator interface.
