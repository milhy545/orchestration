# API Documentation - Orchestration MCP Platform

## 🌐 API Overview

The Orchestration platform provides a unified REST API through the **ZEN Coordinator** that orchestrates 28 MCP tools across 7 specialized services. All external communication goes through the ZEN Coordinator for security and unified interface.

### Base URL
```
Production: http://192.168.0.58:8020
Local Development: http://localhost:8020
```

### Authentication
```bash
# API Key Authentication (if enabled)
Authorization: Bearer your_api_token_here

# Or using X-API-Key header
X-API-Key: your_api_token_here
```

## 🛡️ Security Architecture

### Network Security Model
```
Internet → ZEN Coordinator (8020) → Internal MCP Services (8001-8013)
          ✅ Only exposed port       ❌ Not directly accessible
```

**Critical Security Rules:**
- **NEVER** expose MCP service ports (8001-8013) directly to internet
- **ALL** external access must go through ZEN Coordinator (8020)
- **Portainer Agent** required for container management (port 9001)

## 📋 Core API Endpoints

### Health & Discovery

#### GET /health
Check overall system health and coordinator status.

**Request:**
```bash
curl http://192.168.0.58:8020/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2025-08-17T03:24:38.371865",
  "coordinator": "running",
  "services_count": 7,
  "tools_count": 28
}
```

#### GET /services
List all available MCP services and their status.

**Request:**
```bash
curl http://192.168.0.58:8020/services
```

**Response:**
```json
{
  "services": [
    {
      "name": "filesystem",
      "port": 8001,
      "status": "running",
      "container": "mcp-filesystem",
      "uptime": "26h",
      "tools": ["file_read", "file_write", "file_list", "file_search", "file_analyze"]
    },
    {
      "name": "git",
      "port": 8002,
      "status": "running", 
      "container": "mcp-git",
      "uptime": "26h",
      "tools": ["git_status", "git_commit", "git_push", "git_log", "git_diff"]
    }
  ],
  "total_services": 7,
  "healthy_services": 6,
  "unhealthy_services": 1
}
```

#### GET /tools/list
List all available MCP tools across all services.

**Request:**
```bash
curl http://192.168.0.58:8020/tools/list
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "file_read",
        "service": "filesystem",
        "description": "file_read via Enhanced Filesystem MCP Server",
        "container": "mcp-filesystem"
      }
    ],
    "total_tools": 28,
    "architecture": "organized"
  }
}
```

### MCP Tool Execution

#### POST /mcp
Execute any MCP tool with specified arguments.

**Request Format:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "tool_name",
    "arguments": {
      "param1": "value1",
      "param2": "value2"
    }
  }'
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "data": "tool_specific_response",
    "service": "service_name",
    "execution_time": "0.045s"
  }
}
```

## 🗂️ Filesystem MCP API (Port 8001)

### file_read
Read contents of a file.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "arguments": {
      "path": "/home/orchestration/README.md"
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "content": "file contents here...",
    "size": 1024,
    "encoding": "utf-8",
    "last_modified": "2025-08-17T03:24:38Z"
  }
}
```

### file_write
Write or create a file.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_write",
    "arguments": {
      "path": "/tmp/test.txt",
      "content": "Hello World",
      "mode": "w"
    }
  }'
```

### file_list
List directory contents.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_list",
    "arguments": {
      "path": "/home/orchestration",
      "recursive": false,
      "include_hidden": false
    }
  }'
```

### file_search
Search for files by pattern.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_search",
    "arguments": {
      "path": "/home/orchestration",
      "pattern": "*.py",
      "recursive": true
    }
  }'
```

### file_analyze
Analyze file structure and metadata.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_analyze",
    "arguments": {
      "path": "/home/orchestration/zen_mcp_server.py"
    }
  }'
```

## 🔄 Git MCP API (Port 8002)

### git_status
Check repository status.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_status",
    "arguments": {
      "repository": "/home/orchestration"
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "branch": "master",
    "status": "clean",
    "modified_files": [],
    "untracked_files": [],
    "staged_files": []
  }
}
```

### git_commit
Create a git commit.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_commit",
    "arguments": {
      "repository": "/home/orchestration",
      "message": "Update documentation",
      "add_all": true
    }
  }'
```

### git_push
Push commits to remote repository.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_push",
    "arguments": {
      "repository": "/home/orchestration",
      "remote": "origin",
      "branch": "master"
    }
  }'
```

### git_log
View commit history.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_log",
    "arguments": {
      "repository": "/home/orchestration",
      "limit": 10,
      "format": "oneline"
    }
  }'
```

### git_diff
Show differences between commits/files.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_diff",
    "arguments": {
      "repository": "/home/orchestration",
      "file": "README.md",
      "staged": false
    }
  }'
```

## 💻 Terminal MCP API (Port 8003)

### terminal_exec
Execute terminal commands.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "terminal_exec",
    "arguments": {
      "command": "ls -la /home/orchestration",
      "working_dir": "/home/orchestration",
      "timeout": 30
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "stdout": "total 64\ndrwxr-xr-x 8 root root 4096 Aug 17 03:24 .\n...",
    "stderr": "",
    "exit_code": 0,
    "execution_time": "0.023s"
  }
}
```

### shell_command
Run shell commands with advanced options.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "shell_command",
    "arguments": {
      "command": "docker ps",
      "capture_output": true,
      "shell": "/bin/bash"
    }
  }'
```

### system_info
Get system information.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "system_info",
    "arguments": {
      "details": ["cpu", "memory", "disk", "network"]
    }
  }'
```

## 🗃️ Database MCP API (Port 8004)

### db_query
Execute database queries.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_query",
    "arguments": {
      "connection": "postgresql://mcp_admin:password@localhost:5432/mcp_unified",
      "query": "SELECT * FROM memories LIMIT 10",
      "parameters": []
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "rows": [
      {"id": 1, "content": "memory content", "created_at": "2025-08-17T03:24:38Z"}
    ],
    "row_count": 1,
    "columns": ["id", "content", "created_at"],
    "execution_time": "0.012s"
  }
}
```

### db_connect
Test database connection.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_connect",
    "arguments": {
      "connection_string": "postgresql://mcp_admin:password@localhost:5432/mcp_unified"
    }
  }'
```

### db_schema
Get database schema information.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_schema",
    "arguments": {
      "connection": "postgresql://mcp_admin:password@localhost:5432/mcp_unified",
      "table": "memories"
    }
  }'
```

### db_backup
Create database backup.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_backup",
    "arguments": {
      "connection": "postgresql://mcp_admin:password@localhost:5432/mcp_unified",
      "output_path": "/tmp/backup.sql",
      "format": "sql"
    }
  }'
```

## 🧠 Memory MCP API (Port 8005, 8012)

### store_memory
Store information in memory system.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "content": "Important information to remember",
      "tags": ["important", "documentation"],
      "context": "API documentation update",
      "importance": 0.8
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "memory_id": "mem_12345",
    "status": "stored",
    "embedding_generated": true,
    "timestamp": "2025-08-17T03:24:38Z"
  }
}
```

### search_memories
Search stored memories.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_memories",
    "arguments": {
      "query": "API documentation",
      "limit": 10,
      "similarity_threshold": 0.7,
      "tags": ["documentation"]
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "memories": [
      {
        "id": "mem_12345",
        "content": "Important information to remember",
        "similarity": 0.92,
        "tags": ["important", "documentation"],
        "created_at": "2025-08-17T03:24:38Z"
      }
    ],
    "total_found": 1,
    "search_time": "0.034s"
  }
}
```

### get_context
Retrieve context information.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "get_context",
    "arguments": {
      "context_id": "ctx_12345",
      "include_related": true
    }
  }'
```

### memory_stats
Get memory system statistics.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "memory_stats",
    "arguments": {
      "include_details": true
    }
  }'
```

### list_memories
List all stored memories.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_memories",
    "arguments": {
      "limit": 50,
      "offset": 0,
      "sort_by": "created_at",
      "order": "desc"
    }
  }'
```

## 🎵 Transcriber MCP API (Port 8013)

⚠️ **Status**: Currently unhealthy - debugging required

### transcribe_webm
Transcribe WebM audio files.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "transcribe_webm",
    "arguments": {
      "file_path": "/path/to/audio.webm",
      "language": "en",
      "output_format": "text"
    }
  }'
```

### transcribe_url
Transcribe audio from URL.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "transcribe_url",
    "arguments": {
      "url": "https://example.com/audio.mp3",
      "language": "auto",
      "timestamps": true
    }
  }'
```

### audio_convert
Convert audio formats.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "audio_convert",
    "arguments": {
      "input_path": "/path/to/input.mp3",
      "output_path": "/path/to/output.wav",
      "format": "wav"
    }
  }'
```

## 🔍 Research MCP API (Port 8011)

### research_query
Execute research queries.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "research_query",
    "arguments": {
      "query": "MCP protocol implementation best practices",
      "sources": ["web", "academic", "documentation"],
      "depth": "detailed"
    }
  }'
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "results": [
      {
        "title": "MCP Protocol Implementation Guide",
        "url": "https://example.com/mcp-guide",
        "summary": "Comprehensive guide on MCP implementation...",
        "relevance": 0.95
      }
    ],
    "total_results": 12,
    "search_time": "1.234s"
  }
}
```

### perplexity_search
Search using Perplexity AI.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "perplexity_search",
    "arguments": {
      "query": "Latest Docker orchestration patterns 2025",
      "mode": "precise",
      "include_citations": true
    }
  }'
```

### web_search
General web search functionality.

**Request:**
```bash
curl -X POST http://192.168.0.58:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "web_search",
    "arguments": {
      "query": "Portainer API deployment examples",
      "limit": 20,
      "filter_domains": ["docs.portainer.io", "github.com"]
    }
  }'
```

## 🐳 Portainer Integration API

### Portainer Agent Requirements

For Portainer management of the orchestration platform, you **MUST** install Portainer Agent:

#### Agent Installation
```bash
# Install Portainer Agent (REQUIRED)
docker run -d \
  --name portainer_agent \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /var/lib/docker/volumes:/var/lib/docker/volumes \
  -p 9001:9001 \
  portainer/agent:latest
```

#### Agent Health Check
```bash
# Verify agent is running
curl http://192.168.0.58:9001/ping

# Expected response:
# {"status":"ok","agent_version":"2.19.1"}
```

#### Adding Environment to Portainer

1. **In Portainer UI:**
   - Go to "Environments" → "Add environment"
   - Select "Docker" → "Agent"
   - Enter Environment details:
     - Name: `Orchestration-HAS`
     - Environment URL: `192.168.0.58:9001`

2. **Via Portainer API:**
```bash
curl -X POST "https://your-portainer.com/api/endpoints" \
  -H "X-API-Key: your_api_token" \
  -H "Content-Type: application/json" \
  -d '{
    "Name": "Orchestration-HAS",
    "EndpointCreationType": 1,
    "URL": "192.168.0.58:9001",
    "GroupID": 1,
    "TLS": false
  }'
```

### Stack Deployment via Portainer API

#### Get API Token
```bash
# Login and get token
curl -X POST "https://your-portainer.com/api/auth" \
  -H "Content-Type: application/json" \
  -d '{
    "Username": "admin",
    "Password": "your_password"
  }'

# Response includes: {"jwt": "your_token_here"}
```

#### Deploy Stack
```bash
export PORTAINER_URL="https://your-portainer.com"
export PORTAINER_TOKEN="your_jwt_token"
export ENDPOINT_ID="2"  # Your environment ID

curl -X POST "$PORTAINER_URL/api/stacks" \
  -H "X-API-Key: $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "orchestration-mcp",
    "swarmID": "",
    "endpointId": '$ENDPOINT_ID',
    "repositoryURL": "https://github.com/milhy545/orchestration",
    "repositoryReferenceName": "refs/heads/master",
    "repositoryAuthentication": false,
    "composeFile": "docker-compose.yml",
    "env": [
      {
        "name": "POSTGRES_PASSWORD",
        "value": "your_secure_password"
      },
      {
        "name": "REDIS_PASSWORD", 
        "value": "your_redis_password"
      }
    ]
  }'
```

#### Stack Management
```bash
# List stacks
curl -X GET "$PORTAINER_URL/api/stacks" \
  -H "X-API-Key: $PORTAINER_TOKEN"

# Update stack
curl -X PUT "$PORTAINER_URL/api/stacks/{stack_id}" \
  -H "X-API-Key: $PORTAINER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "env": [
      {
        "name": "POSTGRES_PASSWORD",
        "value": "new_password"
      }
    ]
  }'

# Delete stack
curl -X DELETE "$PORTAINER_URL/api/stacks/{stack_id}" \
  -H "X-API-Key: $PORTAINER_TOKEN"
```

## 🔧 Error Handling

### Standard Error Response Format
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32603,
    "message": "Internal error",
    "data": {
      "service": "filesystem",
      "container": "mcp-filesystem",
      "details": "File not found: /path/to/file"
    }
  }
}
```

### Common Error Codes
- **-32700**: Parse error (Invalid JSON)
- **-32600**: Invalid Request (Malformed request)
- **-32601**: Method not found (Unknown tool)
- **-32602**: Invalid params (Bad arguments)
- **-32603**: Internal error (Service error)
- **502**: Service unavailable (MCP service down)

### Rate Limiting
```json
{
  "error": {
    "code": 429,
    "message": "Rate limit exceeded",
    "data": {
      "limit": 100,
      "window": "60s",
      "retry_after": 30
    }
  }
}
```

## 📊 API Usage Examples

### Complete Workflow Example
```bash
#!/bin/bash

BASE_URL="http://192.168.0.58:8020"

# 1. Check system health
echo "Checking system health..."
curl "$BASE_URL/health"

# 2. List available services
echo "Listing services..."
curl "$BASE_URL/services"

# 3. Store some information in memory
echo "Storing memory..."
curl -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "content": "API integration test completed successfully",
      "tags": ["test", "api", "integration"],
      "importance": 0.7
    }
  }'

# 4. Search for the stored memory
echo "Searching memories..."
curl -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_memories",
    "arguments": {
      "query": "API integration test",
      "limit": 5
    }
  }'

# 5. Get system information
echo "Getting system info..."
curl -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "system_info",
    "arguments": {
      "details": ["cpu", "memory", "disk"]
    }
  }'
```

### Python SDK Example
```python
import requests
import json

class OrchestrationAPI:
    def __init__(self, base_url="http://192.168.0.58:8020", api_key=None):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json"
        }
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    def health_check(self):
        """Check system health"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def list_services(self):
        """List all MCP services"""
        response = requests.get(f"{self.base_url}/services")
        return response.json()
    
    def call_tool(self, tool_name, arguments=None):
        """Execute MCP tool"""
        payload = {
            "tool": tool_name,
            "arguments": arguments or {}
        }
        response = requests.post(
            f"{self.base_url}/mcp",
            headers=self.headers,
            data=json.dumps(payload)
        )
        return response.json()
    
    def store_memory(self, content, tags=None, importance=0.5):
        """Store information in memory"""
        return self.call_tool("store_memory", {
            "content": content,
            "tags": tags or [],
            "importance": importance
        })
    
    def search_memories(self, query, limit=10):
        """Search stored memories"""
        return self.call_tool("search_memories", {
            "query": query,
            "limit": limit
        })

# Usage example
api = OrchestrationAPI()

# Check health
health = api.health_check()
print(f"System status: {health['status']}")

# Store and search memory
api.store_memory("Python API integration working", ["python", "api"])
results = api.search_memories("Python API")
print(f"Found {len(results['result']['memories'])} memories")
```

---

## 📝 Notes

1. **Portainer Agent is MANDATORY** for Portainer management - the platform will NOT work without it
2. **Security**: Never expose MCP service ports directly - always use ZEN Coordinator
3. **Performance**: MCP tools are optimized for concurrent execution
4. **Monitoring**: Use `/health` and `/services` endpoints for monitoring
5. **Backup**: Regular database backups via `db_backup` tool recommended

For additional support, see the [troubleshooting guide](TROUBLESHOOTING.md) or [GitHub issues](https://github.com/milhy545/orchestration/issues).