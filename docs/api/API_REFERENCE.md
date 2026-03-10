# API Reference

This file is the exhaustive reference for the platform's public routes, tool catalogs, and operator-visible scripts.

## Mega-Orchestrator (`7000`, `mega-orchestrator`)

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/mcp` | Unified tool dispatch endpoint; also accepts JSON-RPC payloads |
| `POST` | `/mcp/rpc` | JSON-RPC compatible alias for MCP clients |
| `POST` | `/mcp/{service}` | Direct dispatch to one registered downstream service |
| `GET` | `/health` | Gateway health and downstream snapshot |
| `GET` | `/services` | Registered service registry with health and routing metadata |
| `GET` | `/tools/list` | Unified tool catalog built from the currently exposed working subset |
| `GET` | `/mcp/schema` | Canonical MCP schema and resources exposed by the gateway |
| `GET` | `/status` | Human-oriented gateway status summary |
| `GET` | `/stats` | Request and uptime statistics |
| `GET` | `/providers` | Provider registry visibility |
| `GET` | `/modes` | SAGE routing modes |
| `GET` | `/memory/stats` | Gateway memory-system counters |
| `GET` | `/files/stats` | Gateway file-storage counters |
| `GET` | `/debug/cache` | Cache visibility for diagnostics |
| `GET` | `/debug/contexts/{session_id}` | Session-specific debug context inspection |

## Route-Oriented MCP Services

### Filesystem MCP (`7001`, `filesystem-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `GET` | `/files/{path}` | List directory contents |
| `GET` | `/file/{path}` | Read file contents |
| `POST` | `/file/write` | Write or overwrite a file |
| `GET` | `/search/files` | Search files by name or content filters |
| `GET` | `/analyze/{path}` | Return file metadata and analysis |

Public tools: `file_read`, `file_write`, `file_list`, `file_search`, `file_analyze`

### Git MCP (`7002`, `git-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `GET` | `/git/{path}/status` | Repository working tree status |
| `GET` | `/git/{path}/log` | Commit history |
| `GET` | `/git/{path}/diff` | Diff view |
| `POST` | `/git/{path}/commit` | Commit staged or selected changes |
| `POST` | `/git/{path}/push` | Push to remote |

Public tools: `git_status`, `git_log`, `git_diff`, `git_commit`, `git_push`

### Terminal MCP (`7003`, `terminal-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/command` | Execute a shell command |
| `GET` | `/directory` | Inspect a directory |
| `GET` | `/processes` | List processes |

Public tools: `execute_command`, `directory`, `processes`, `system_info`

### Database MCP (`7004`, `database-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/db/execute` | Execute database queries |
| `GET` | `/db/tables` | List tables |
| `GET` | `/db/schema/{table_name}` | Inspect one table schema |
| `GET` | `/db/sample/{table_name}` | Return sample rows |

Public tools: `db_query`, `db_tables`, `db_schema`, `db_sample`

### Memory MCP (`7005`, `memory-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/memory/store` | Store a memory item |
| `GET` | `/memory/list` | List stored memories |
| `GET` | `/memory/search` | Search stored memories |
| `DELETE` | `/memory/{memory_id}` | Delete one memory entry |
| `GET` | `/memory/stats` | Memory statistics |

Public tools: `store_memory`, `list_memories`, `search_memories`, `delete_memory`, `memory_stats`

### Research MCP (`7011`, `research-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/research/news` | News research |
| `POST` | `/research/domain` | Domain research |
| `POST` | `/research/academic` | Academic search |
| `POST` | `/research/structured` | Structured result generation |
| `POST` | `/research/search` | Generic research search |

### Gmail MCP (`7015`, `gmail-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Service health |
| `POST` | `/tool/{tool_name}` | Generic tool dispatch wrapper |
| `POST` | `/gmail/search` | Search mail |
| `POST` | `/gmail/send` | Send mail |
| `POST` | `/gmail/forward` | Forward mail |
| `GET` | `/gmail/email/{email_id}` | Fetch one message |
| `POST` | `/gmail/count` | Count matching mail |
| `GET` | `/gmail/labels` | List labels |
| `POST` | `/gmail/labels` | Create label |
| `POST` | `/gmail/labels/apply` | Apply labels |
| `POST` | `/gmail/move` | Move messages |

### Transcriber MCP (`7013`, `transcriber-mcp`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/` | Lightweight service status |
| `GET` | `/health` | Health endpoint |
| `POST` | `/transcribe/audio` | Transcribe uploaded audio |
| `POST` | `/transcribe/url` | Transcribe media from a URL |

## Tool-Oriented MCP Services

### Network MCP (`7006`, `network-mcp`)

| Tool or route | Description |
| --- | --- |
| `POST /tools/http_request` | Send an HTTP request with headers, body, timeout, and redirect controls |
| `POST /tools/webhook_create` | Register a webhook definition |
| `POST /webhooks/{webhook_id}` | Receive an inbound webhook event |
| `POST /tools/dns_lookup` | Resolve DNS records |
| `POST /tools/api_test` | Probe a remote API and summarize latency and status |
| `GET /tools/list` | List tool metadata |
| `GET /webhooks` | List active webhook definitions |
| `GET /webhook-logs` | Inspect recent webhook delivery logs |

### System MCP (`7007`, `system-mcp`)

| Tool | Description |
| --- | --- |
| `resource_monitor` | CPU, memory, and host resource inspection |
| `process_list` | Process listing |
| `disk_usage` | Disk space inspection |
| `system_info` | OS and host information |

Routes: `POST /tools/resource_monitor`, `POST /tools/process_list`, `POST /tools/disk_usage`, `POST /tools/system_info`, `GET /tools/list`

### Security MCP (`7008`, `security-mcp`)

| Tool | Description |
| --- | --- |
| `jwt_token` | Mint JWT bearer tokens |
| `password_hash` | Hash passwords with bcrypt |
| `password_verify` | Verify a password against a stored hash |
| `encrypt` | Encrypt application data |
| `decrypt` | Decrypt application data |
| `ssl_check` | Validate certificates and expiry details |

Routes: `POST /tools/jwt_token`, `POST /tools/password_hash`, `POST /tools/password_verify`, `POST /tools/encrypt`, `POST /tools/decrypt`, `POST /tools/ssl_check`, `GET /tools/list`

### Config MCP (`7009`, `config-mcp`)

| Tool | Description |
| --- | --- |
| `env_vars` | Inspect or validate environment variables |
| `config_file` | Inspect or transform config files |
| `validate` | Run configuration validation |
| `backup` | Generate config backups |

Routes: `POST /tools/env_vars`, `POST /tools/config_file`, `POST /tools/validate`, `POST /tools/backup`, `GET /tools/list`

### Log MCP (`7010`, `log-mcp`)

| Tool | Description |
| --- | --- |
| `log_analysis` | Summarize logs and anomalies |
| `log_search` | Search logs with filters |

Routes: `POST /tools/log_analysis`, `POST /tools/log_search`, `GET /tools/list`

### Advanced Memory MCP (`7012`, `advanced-memory-mcp`)

| Tool | Description |
| --- | --- |
| `store_memory` | Store vectorized memory entries |
| `search_memories` | Search memories by text |
| `semantic_similarity` | Semantic similarity search |
| `vector_search` | Vector search with optional filters |
| `get_context` | Return related context bundles |

Routes: `GET /tools/list`, `POST /tools/call`

### Marketplace MCP (`7034`, `marketplace-mcp`)

| Tool or route | Description |
| --- | --- |
| `skills_list` | List skills in the private catalog |
| `skills_resolve` | Resolve one skill and version |
| `registry_search` | Search MCP subregistry servers |
| `registry_get_server` | Return metadata for one server |
| `catalog_validate` | Validate catalog metadata and checksums |
| `POST /tools/{tool_name}` | Call one marketplace-exposed tool route |
| `GET /skills/v1/index` | REST view of the skill catalog |
| `GET /skills/v1/packages/{name}/{version}` | Package metadata |
| `GET /skills/v1/packages/{name}/{version}/download` | Download the skill archive |
| `POST /skills/v1/install-plan` | Generate an installation plan |
| `GET /registry/v0.1/servers` | List registered servers |
| `GET /registry/v0.1/servers/{server_id}` | Inspect one server |
| `GET /registry/v0.1/servers/{server_id}/versions` | List all known versions |
| `GET /registry/v0.1/servers/{server_id}/latest` | Get the latest version |
| `POST /mcp` | MCP JSON-RPC compatibility entrypoint |

### PostgreSQL Wrapper (`7024`, `postgresql-mcp-wrapper`)

| Tool | Description |
| --- | --- |
| `query` | Structured read-only query execution |
| `schema` | Table and schema inspection |
| `connection` | Connection status, statistics, and test operations |

Routes: `POST /tools/query`, `POST /tools/schema`, `POST /tools/connection`, `GET /tools/list`

### Redis Wrapper (`7025`, `redis-mcp-wrapper`)

| Tool | Description |
| --- | --- |
| `cache` | Key-value cache operations |
| `session` | Session create, read, update, delete, and list |

Routes: `POST /tools/cache`, `POST /tools/session`, `GET /tools/list`

### Qdrant Wrapper (`7026`, `qdrant-mcp-wrapper`)

| Tool | Description |
| --- | --- |
| `collection` | Collection create, delete, list, and info |
| `vector` | Vector insert, update, delete, and fetch |
| `search` | Similarity search with payload support |

Routes: `POST /tools/collection`, `POST /tools/vector`, `POST /tools/search`, `GET /tools/list`

### MQTT MCP (`7019`, `mqtt-mcp`)

| Tool or route | Description |
| --- | --- |
| `POST /mcp` | JSON-RPC handler for all MQTT tools |
| `publish_message` | Publish to a topic |
| `subscribe_topic` | Subscribe to a topic |
| `get_mqtt_status` | Inspect broker connection state |
| `list_messages` | Return buffered received messages |

### Code Graph MCP (`7020`, `code-graph-mcp`)

| Tool | Description |
| --- | --- |
| `index_python_project` | Build graph data from a Python codebase |
| `query_code_graph` | Run graph queries |
| `find_dependencies` | Inspect module dependencies |
| `find_callers` | Find callers of a function |
| `detect_circular_imports` | Detect import cycles |

Routes: `GET /tools/list`, `POST /tools/call`

### FORAI MCP (`7016`, `forai-mcp`)

| Tool | Description |
| --- | --- |
| `forai_analyze` | Analyze media input |
| `forai_process` | Process media content |
| `forai_query` | Query FORAI state or outputs |

Routes: `GET /tools/list`, `POST /tools/call`

### ZEN MCP Server (`7017`, `zen-mcp-server`)

`zen-mcp-server` is documented as a stdio MCP server. Its public contract is to list tools and call tools over MCP, and the currently exposed tool set consists of:

- `thinkdeep`
- `codereview`
- `debug`
- `analyze`
- `chat`
- `precommit`
- `testgen`
- `refactor`
- `tracer`
- `fileretrieve`

### Vision MCP (`7014`)

`vision-mcp` is present in `docker-compose.yml` as a scaffold service reusing the `system-mcp` image. It does not define a distinct public contract in this repository and should be treated as a reserved placeholder port rather than a separately documented API.

## Vault Secrets UI (`vault-secrets-ui`)

| Method | Route | Description |
| --- | --- | --- |
| `GET` | `/health` | Vault reachability and token readiness |
| `GET` | `/api/services` | Service metadata, Vault paths, and restart instructions |
| `GET` | `/api/secrets/{service}` | Read current secrets for one service |
| `PUT` | `/api/secrets/{service}` | Write secrets, regenerate runtime env files, and return restart instructions |
| `GET` | `/` | HTML secret-management UI |

Key routes: `GET /api/services`, `GET /api/secrets/{service}`, `PUT /api/secrets/{service}`, `GET /`

## Operator Scripts

| Script | Description |
| --- | --- |
| `scripts/health-check.sh` | Local stack health snapshot |
| `scripts/monitor-services.sh` | Write health and container snapshots for monitoring status files |
| `scripts/monitoring-health-check.sh` | Validate monitoring stack configuration |
| `scripts/vault-variant-b-smoke.sh` | Smoke test the Vault overlay and core entrypoints |
| `scripts/backup-databases.sh` | SQLite database backup helper |
| `scripts/install-mcp.sh` | Bootstrap a new MCP service directory and compose fragment |
| `scripts/diagnostics/quick_diagnose.sh` | Quick shell and Gemini CLI diagnostics |
| `scripts/diagnostics/production_monitor.sh` | Lightweight production health monitor |
| `scripts/marketplace/get_market_token.sh` | Mint a marketplace bearer token via `security-mcp` |
| `scripts/marketplace/install_skill_from_market.sh` | Resolve and install one skill locally |
| `scripts/marketplace/codex_configure_market.sh` | Persist marketplace environment variables for Codex |
