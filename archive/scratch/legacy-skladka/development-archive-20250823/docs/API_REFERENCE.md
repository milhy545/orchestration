# 📡 API Reference

## Base URL
```
http://localhost:8020/mcp
```

## Request Format
All requests use POST method with JSON payload:

```json
{
  "tool": "tool_name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

## Response Format
```json
{
  "success": true,
  "result": "response_data",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "service_name"
}
```

---

## 📁 Filesystem MCP (Port 8001)

### `file_read`
Read file contents
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "arguments": {
      "path": "/path/to/file.txt"
    }
  }'
```

### `file_write`
Write content to file
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_write",
    "arguments": {
      "path": "/path/to/file.txt",
      "content": "Hello, World!"
    }
  }'
```

### `file_list`
List directory contents
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_list",
    "arguments": {
      "path": "/path/to/directory"
    }
  }'
```

---

## 🗃️ Git MCP (Port 8002)

### `git_status`
Get repository status
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_status",
    "arguments": {
      "repository": "/path/to/repo"
    }
  }'
```

### `git_log`
Get commit history
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_log",
    "arguments": {
      "repository": "/path/to/repo",
      "limit": 10
    }
  }'
```

### `git_diff`
Show changes between commits
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_diff",
    "arguments": {
      "repository": "/path/to/repo",
      "commit1": "abc123",
      "commit2": "def456"
    }
  }'
```

---

## 💻 Terminal MCP (Port 8003)

### `execute_command`
Execute system command
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "execute_command",
    "arguments": {
      "command": "ls -la /tmp"
    }
  }'
```

### `system_info`
Get system information
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "system_info",
    "arguments": {}
  }'
```

---

## 🗄️ Database MCP (Port 8004)

### `db_query`
Execute database query
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_query",
    "arguments": {
      "query": "SELECT * FROM users LIMIT 10",
      "database": "mcp_unified"
    }
  }'
```

### `db_schema`
Get database schema
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "db_schema",
    "arguments": {
      "database": "mcp_unified"
    }
  }'
```

---

## 🧠 Memory MCP (Port 8005)

### `store_memory`
Store key-value memory
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "store_memory",
    "arguments": {
      "key": "user_preference",
      "content": "Dark mode enabled"
    }
  }'
```

### `search_memories`
Search stored memories
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "search_memories",
    "arguments": {
      "query": "user preference"
    }
  }'
```

### `list_memories`
List all stored memories
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "list_memories",
    "arguments": {}
  }'
```

### `memory_stats`
Get memory usage statistics
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "memory_stats",
    "arguments": {}
  }'
```

---

## 🎧 WebM Transcriber MCP (Port 8008)

### `transcribe_audio`
Transcribe audio file
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "transcribe_audio",
    "arguments": {
      "file_path": "/path/to/audio.webm"
    }
  }'
```

### `transcribe_url`
Transcribe audio from URL
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "transcribe_url",
    "arguments": {
      "url": "https://example.com/audio.webm"
    }
  }'
```

---

## 🔍 Research MCP (Port 8011)

### `research_query`
Perform research using Perplexity API
```bash
curl -X POST http://localhost:8020/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "research_query",
    "arguments": {
      "query": "Latest developments in AI",
      "sources": 5
    }
  }'
```

---

## 📊 Advanced Memory (Port 8006)

### Direct FastAPI Interface
Access advanced memory features directly:

```bash
# Store with vector embedding
curl -X POST http://localhost:8006/memories \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning project notes",
    "metadata": {"project": "ai-research"}
  }'

# Semantic search
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "AI project information",
    "limit": 5,
    "threshold": 0.7
  }'
```

---

## 🗂️ Qdrant Vector Database (Port 8007)

### Direct Qdrant API
Access vector database directly:

```bash
# Get collection info
curl http://localhost:8007/collections/memories

# Search vectors
curl -X POST http://localhost:8007/collections/memories/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, 0.3, ...],
    "limit": 10
  }'
```

---

## 🔗 Service Health Endpoints

### Zen Coordinator Health
```bash
curl http://localhost:8020/health
```

### Individual Service Health
```bash
curl http://localhost:8001/health  # Filesystem
curl http://localhost:8002/health  # Git
curl http://localhost:8003/health  # Terminal
curl http://localhost:8004/health  # Database
curl http://localhost:8005/health  # Memory
```

---

## 📈 Monitoring Endpoints

### Service Status
```bash
curl http://localhost:8020/status
```

### Metrics
```bash
curl http://localhost:8020/metrics
```

---

## Error Responses

```json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "service_name"
}
```

## Rate Limiting
- Default: 100 requests per minute per IP
- Configurable via environment variables
- Returns HTTP 429 when exceeded

## Authentication
Currently supports:
- Environment variable based API keys for external services
- PostgreSQL database authentication
- Future: OAuth2, JWT tokens