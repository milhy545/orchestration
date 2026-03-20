# Services Documentation

This inventory reflects the services declared in `docker-compose.yml`. The table distinguishes external entrypoints from internal support components and highlights which services expose stable public contracts in this repository.

## Public Entry and MCP Services

| Service | Host port(s) | Type | Purpose |
| --- | --- | --- | --- |
| `mega-orchestrator` | `7000` | gateway | Unified MCP and HTTP gateway |
| `filesystem-mcp` | `7001` | MCP HTTP | File operations |
| `git-mcp` | `7002` | MCP HTTP | Repository operations |
| `terminal-mcp` | `7003` | MCP HTTP | Command execution and process visibility |
| `database-mcp` | `7004` | MCP HTTP | Database inspection and queries |
| `memory-mcp` | `7005` | MCP HTTP | Persistent memory store |
| `network-mcp` | `7006` | MCP tool service | HTTP, webhook, DNS, and API checks |
| `system-mcp` | `7007` | MCP tool service | Host metrics and process information |
| `security-mcp` | `7008` | MCP tool service | JWT, password, encryption, and SSL helpers |
| `config-mcp` | `7009` | MCP tool service | Config validation and backups |
| `log-mcp` | `7010` | MCP tool service | Log analysis and log search |
| `research-mcp` | `7011` | MCP HTTP | Research APIs |
| `advanced-memory-mcp` | `7012` | MCP tool service | Vector memory and semantic recall |
| `transcriber-mcp` | `7013` | **DISABLED** | Audio transcription (HW limited) |
| `vision-mcp` | `7014` | **DISABLED** | Scaffold service (HW limited) |
| `gmail-mcp` | `7015` | MCP HTTP | Gmail search and message operations |
| `forai-mcp` | `7016` | MCP tool service | FORAI media tools |
| `zen-mcp-server` | `7017` | MCP stdio | Multi-model reasoning and code tools |
| `mqtt-broker` | `7018` | broker | MQTT broker |
| `mqtt-mcp` | `7019` | MCP JSON-RPC | MQTT tool bridge |
| `code-graph-mcp` | `7020` | MCP tool service | Code graph indexing and query |
| `postgresql-mcp-wrapper` | `7024` | wrapper API | Read-only PostgreSQL tools |
| `redis-mcp-wrapper` | `7025` | wrapper API | Cache and session tools |
| `qdrant-mcp-wrapper` | `7026` | wrapper API | Qdrant collection, vector, and search tools |
| `marketplace-mcp` | `7034` | catalog API | Private skill catalog and MCP subregistry |

## Infrastructure Services

| Service | Host port(s) | Purpose |
| --- | --- | --- |
| `postgresql` | `7021` | Primary relational storage |
| `redis` | `7022` | Cache and shared transient state |
| `qdrant-vector` | `7023`, `7027` | Vector storage |
| `prometheus` | `7028` | Metrics collection |
| `backup-service` | `7029` | Scheduled backup worker |
| `message-queue` | `7030` | Queue-compatible Redis service |
| `grafana` | `7031` | Dashboards |
| `loki` | `7032` | Log aggregation |
| `promtail` | none | Log shipping |
| `neo4j` | `7474`, `7687` | Graph storage for `code-graph-mcp` |

## Dependencies and Notes

- `mega-orchestrator` depends on PostgreSQL and Redis and maintains the primary service registry used by `/services` and `/tools/list`.
- `advanced-memory-mcp` depends on PostgreSQL, Redis, and Qdrant.
- `marketplace-mcp` uses a catalog mounted from `mcp-servers/marketplace-mcp/catalog`.
- `zen-mcp-server` is documented as an MCP stdio service even though the compose file also publishes a container port and healthcheck.
- `vision-mcp` is intentionally documented as a scaffold to avoid pretending it has a unique API contract.
- `vault-secrets-ui` is not part of the base compose file; it is added by `docker-compose.vault.yml` and documented separately because it is an operator-facing API.

## Supported Operator Scripts

- `scripts/health-check.sh`
- `scripts/monitor-services.sh`
- `scripts/monitoring-health-check.sh`
- `scripts/backup-databases.sh`
- `scripts/diagnostics/quick_diagnose.sh`
- `scripts/diagnostics/production_monitor.sh`
- `scripts/marketplace/get_market_token.sh`
- `scripts/marketplace/codex_configure_market.sh`
- `scripts/marketplace/install_skill_from_market.sh`
- `scripts/vault-variant-b-smoke.sh`
- `scripts/install-mcp.sh`

## Operator Scripts

- `scripts/health-check.sh`
- `scripts/monitor-services.sh`
- `scripts/monitoring-health-check.sh`
- `scripts/backup-databases.sh`
- `scripts/diagnostics/quick_diagnose.sh`
- `scripts/diagnostics/production_monitor.sh`
- `scripts/marketplace/get_market_token.sh`
- `scripts/marketplace/codex_configure_market.sh`
- `scripts/marketplace/install_skill_from_market.sh`
- `scripts/vault-variant-b-smoke.sh`
- `scripts/install-mcp.sh`

## Documentation Ownership

- Route contracts live in [API_REFERENCE.md](API_REFERENCE.md) and [mega_orchestrator.md](mega_orchestrator.md).
- Runtime topology and deployment assumptions live in `docs/architecture/` and `docs/operations/`.
- Machine-readable coverage is maintained in `public_surface_inventory.json`.
