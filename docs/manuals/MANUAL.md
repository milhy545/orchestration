# Operator Manual

## Purpose

This manual is the canonical long-form guide for operating the current Orchestration stack.

## What the Stack Provides

- a Mega-Orchestrator gateway on `7000`
- direct MCP and service-specific HTTP APIs on `7001-7026`
- a private skills marketplace on `7034`
- Vault-backed runtime secret management
- PostgreSQL, Redis, Qdrant, Neo4j, MQTT, and observability support services

## Daily Operator Workflow

1. Start or inspect the stack with `docker compose`.
2. Run `./scripts/health-check.sh`.
3. Run `./scripts/monitoring-health-check.sh` when monitoring is relevant.
4. Use `GET /services` and `GET /tools/list` on `7000` to confirm gateway visibility.
5. Use service-specific routes when direct debugging is required.

## Canonical Scripts

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

## Core Public Services

- `mega-orchestrator`: discovery, routing, tool execution, stats
- `filesystem-mcp`, `git-mcp`, `terminal-mcp`, `database-mcp`, `memory-mcp`
- `network-mcp`, `system-mcp`, `security-mcp`, `config-mcp`, `log-mcp`
- `research-mcp`, `advanced-memory-mcp`, `transcriber-mcp`, `gmail-mcp`
- `forai-mcp`, `mqtt-mcp`, `code-graph-mcp`
- `postgresql-mcp-wrapper`, `redis-mcp-wrapper`, `qdrant-mcp-wrapper`
- `marketplace-mcp`
- `vault-secrets-ui`

## Notes on Historical Material

- `docs/archive/` contains superseded plans and migration notes.
- `docs/archive/manuals/` contains old or derived manual formats.
- `vision-mcp` remains a scaffold compose entry and is not a supported production capability.
