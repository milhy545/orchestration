# Orchestration Platform

Orchestration is a Docker-based MCP platform for running a mixed fleet of HTTP services, MCP-compatible tool servers, and operational support services behind a single project layout. The stack is centered on the `mega-orchestrator` gateway and ships with file, git, terminal, database, memory, research, messaging, security, marketplace, and secret-management components.

## Runtime Overview

### Control and integration surfaces

| Component | Host port | Role |
| --- | --- | --- |
| `mega-orchestrator` | `7000` | Unified gateway, service registry, MCP JSON-RPC bridge, health and stats endpoints |
| `marketplace-mcp` | `7034` | Private skills catalog and MCP subregistry protected by JWT scopes |
| `vault-secrets-ui` | `10000` with `docker-compose.vault.yml` | Vault-backed secret editor and runtime env exporter |

### Core MCP services

| Service | Host port | Public contract |
| --- | --- | --- |
| `filesystem-mcp` | `7001` | File browsing, read, write, search, analysis |
| `git-mcp` | `7002` | Repository status, log, diff, commit, push |
| `terminal-mcp` | `7003` | Command execution, directory listing, process listing |
| `database-mcp` | `7004` | SQL execution plus table, schema, and sample inspection |
| `memory-mcp` | `7005` | Persistent memory CRUD and statistics |
| `network-mcp` | `7006` | HTTP requests, webhooks, DNS, API testing |
| `system-mcp` | `7007` | Resource monitoring, processes, disks, system facts |
| `security-mcp` | `7008` | JWT minting, password hashing, encryption, SSL checks |
| `config-mcp` | `7009` | Environment inspection, config files, validation, backups |
| `log-mcp` | `7010` | Log analysis and log search |

### Extended services

| Service | Host port | Public contract |
| --- | --- | --- |
| `research-mcp` | `7011` | News, domain, academic, structured, and generic research APIs |
| `advanced-memory-mcp` | `7012` | Vector-backed memory search through `/tools/list` and `/tools/call` |
| `transcriber-mcp` | `7013` | Audio and URL transcription |
| `vision-mcp` | `7014` | reserved scaffold service currently reusing the system image; no distinct public contract |
| `gmail-mcp` | `7015` | Gmail search, send, forward, labels, move, and generic tool dispatch |
| `forai-mcp` | `7016` | Media-oriented tool server with `forai_*` tools |
| `zen-mcp-server` | `7017` | Multi-model MCP stdio server for code and reasoning tools |
| `mqtt-mcp` | `7019` | MQTT JSON-RPC bridge for publish, subscribe, and message inspection |
| `code-graph-mcp` | `7020` | Neo4j-backed code graph indexing and queries |

### Wrapper and infrastructure services

| Service | Host port | Role |
| --- | --- | --- |
| `postgresql-mcp-wrapper` | `7024` | Read-oriented PostgreSQL wrapper tools |
| `redis-mcp-wrapper` | `7025` | Cache and session tools |
| `qdrant-mcp-wrapper` | `7026` | Vector collection, vector, and search tools |
| `postgresql` | `7021` | Primary relational store |
| `redis` | `7022` | Cache, sessions, and queue primitives |
| `qdrant-vector` | `7023`, `7027` | Vector storage |
| `prometheus` | `7028` | Metrics collection |
| `backup-service` | `7029` | Scheduled backup worker |
| `message-queue` | `7030` | Queue-compatible Redis service |
| `grafana` | `7031` | Dashboards |
| `loki` | `7032` | Log aggregation |
| `mqtt-broker` | `7018` | MQTT broker |
| `neo4j` | `7474`, `7687` | Graph database used by `code-graph-mcp` |

## Quick Start

1. Copy `.env.example` to `.env` and fill in provider, mail, and optional marketplace settings.
2. Confirm the path variables used by `docker-compose.yml`: `PROJECT_ROOT`, `DATA_ROOT`, `MONITORING_ROOT`, and `HOST_HOME_PATH`.
3. Start the default stack:

```bash
docker compose up -d
```

4. Verify the main entrypoints:

```bash
curl http://localhost:7000/health
curl http://localhost:7034/health
./scripts/monitoring-health-check.sh
```

5. Start the Vault overlay when needed:

```bash
docker compose -f docker-compose.yml -f docker-compose.vault.yml up -d
./scripts/vault-variant-b-smoke.sh
```

## Common Workflows

- Discover the unified tool catalog through `GET /tools/list` on `mega-orchestrator`.
- Call tools through `POST /mcp` or `POST /mcp/rpc`.
- Install internal skills from the marketplace with:

```bash
scripts/marketplace/get_market_token.sh
scripts/marketplace/install_skill_from_market.sh --skill <name> --token "$MARKETPLACE_JWT_TOKEN"
```

- Edit runtime secrets through Vault UI after the Vault overlay is running:
  `http://localhost:${VAULT_WEBUI_PORT:-10000}/`

Compatibility namespaces still exist in the Vault overlay for legacy secret mapping, including `common-mcp` and `perplexity-hub`. They are compatibility namespaces, not first-class runtime APIs.

## Documentation Map

- [docs/README.md](docs/README.md): main documentation entry point
- [docs/api/API_DOCUMENTATION.md](docs/api/API_DOCUMENTATION.md): how to call the platform
- [docs/api/API_REFERENCE.md](docs/api/API_REFERENCE.md): complete public endpoint and tool reference
- [docs/api/SERVICES_DOCUMENTATION.md](docs/api/SERVICES_DOCUMENTATION.md): service inventory with ports and dependencies
- [docs/operations/DEPLOYMENT.md](docs/operations/DEPLOYMENT.md): deployment and environment guidance
- [docs/operations/MONITORING.md](docs/operations/MONITORING.md): monitoring stack and operator checks
- [docs/manuals/MANUAL.md](docs/manuals/MANUAL.md): operator manual

## Repository Layout

- `mcp-servers/`: MCP and HTTP microservices
- `mega_orchestrator/`: gateway, provider registry, routing, memory, and MCP bridge code
- `services/vault-secrets-ui/`: Vault-backed secret editor UI and API
- `monitoring/`: Prometheus, Grafana, Loki, and Promtail configuration
- `scripts/`: operational and installation scripts
- `tests/`: repository-level tests, including documentation coverage checks
- `docs/`: active product and operator documentation
- `archive/` and `docs/archive/`: retained historical material not guaranteed to match the current runtime
