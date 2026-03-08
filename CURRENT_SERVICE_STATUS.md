# Current Service Status

Generated: 2026-03-05 17:47 UTC

## Runtime Summary

- Stack verified from live runtime (`docker ps`, `docker inspect`, HTTP checks).
- `mega-orchestrator` is running and healthy on `:7000`.
- WebUI (Vault) is on `:10000` and healthy.
- `mcp-transcriber` and `mcp-vision` remain intentionally disabled (`restart: no`).

## Running Core Orchestration Services

- `mega-orchestrator` — running (`healthy`) — restart: `unless-stopped`
- `mcp-filesystem` — running — restart: `unless-stopped`
- `mcp-git` — running — restart: `unless-stopped`
- `mcp-terminal` — running — restart: `unless-stopped`
- `mcp-database` — running — restart: `unless-stopped`
- `mcp-memory` — running — restart: `unless-stopped`
- `mcp-security` — running (`healthy`) — restart: `unless-stopped`
- `mcp-config` — running (`healthy`) — restart: `unless-stopped`
- `mcp-log` — running (`healthy`) — restart: `unless-stopped`
- `mcp-perplexity-hub` — running — restart: `unless-stopped`
- `mcp-marketplace` — running (`healthy`) — restart: `unless-stopped`
- `mcp-forai` — running — restart: `unless-stopped`
- `mcp-mqtt` — running (`healthy`) — restart: `unless-stopped`

## Supporting Services

- `mcp-postgresql`, `mcp-redis`, `mcp-qdrant`, `mcp-message-queue`, `mqtt-broker` — running
- `mcp-vault`, `mcp-vault-agent-common`, `mcp-vault-secrets-ui` — running
- `mcp-prometheus`, `mcp-grafana`, `mcp-loki`, `mcp-promtail` — running

## Disabled by Design

- `mcp-transcriber` — exited — restart: `no`
- `mcp-vision` — exited — restart: `no`

## Health Endpoint Verification (latest)

- `http://localhost:7000/health` (`mega-orchestrator`) => `healthy`
- `http://localhost:7001/health` (`mcp-filesystem`) => `healthy`
- `http://localhost:7002/health` (`mcp-git`) => `healthy`
- `http://localhost:7003/health` (`mcp-terminal`) => `healthy`
- `http://localhost:7004/health` (`mcp-database`) => `healthy`
- `http://localhost:7005/health` (`mcp-memory`) => `healthy`
- `http://localhost:7008/health` (`mcp-security`) => `healthy`
- `http://localhost:7009/health` (`mcp-config`) => `healthy`
- `http://localhost:7010/health` (`mcp-log`) => `healthy`
- `http://localhost:7011/health` (`mcp-perplexity-hub`) => `healthy`
- `http://localhost:7016/health` (`mcp-forai`) => `healthy`
- `http://localhost:7019/health` (`mcp-mqtt`) => `healthy`
- `http://localhost:7034/health` (`mcp-marketplace`) => `healthy`
- `http://localhost:10000/health` (`mcp-vault-secrets-ui`) => `healthy`

## Mega-Orchestrator Exposure (optimized)

- `endpoint_profile`: `compact`
- exposed services: `12`
- exposed tools: `13`
- tool list: `db_query`, `execute_command`, `file_list`, `file_read`, `file_write`, `forai_query`, `get_mqtt_status`, `git_log`, `git_status`, `research_query`, `search_memories`, `skills_list`, `store_memory`

## Reboot Behavior

All currently running core orchestration services listed above are configured with `restart: unless-stopped`, so they auto-start after host reboot.
