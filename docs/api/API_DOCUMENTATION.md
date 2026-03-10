# API Documentation

This document explains how the Orchestration platform is exposed to clients. The platform has three main access patterns:

1. `mega-orchestrator` as the unified gateway on port `7000`
2. direct HTTP access to individual MCP and wrapper services
3. special-purpose surfaces such as `marketplace-mcp`, `vault-secrets-ui`, `mqtt-mcp`, and the `zen-mcp-server`

## Base Entry Points

| Surface | Default URL | Primary use |
| --- | --- | --- |
| Mega-Orchestrator | `http://localhost:7000` | Unified health, service discovery, MCP tool routing, JSON-RPC compatibility |
| Marketplace MCP | `http://localhost:7034` | Private skill catalog, MCP subregistry, skill installation plans |
| Vault Secrets UI | `http://localhost:${VAULT_WEBUI_PORT:-10000}` | Inspect and update runtime secrets when the Vault overlay is enabled |

## Authentication Model

### Mega-Orchestrator

- The repository ships the gateway without mandatory application-layer authentication in the default compose file.
- Production or internet-facing deployments should front it with authentication, network policy, and secret management.
- The code reads `MARKETPLACE_JWT_TOKEN` for marketplace-aware operations and uses Redis/PostgreSQL internally.

### Marketplace MCP

- Marketplace routes require a bearer token when `JWT_SECRET` is configured.
- The normal scope for read and install flows is `market:read`.
- The helper script `scripts/marketplace/get_market_token.sh` mints a token through `security-mcp`.

### Vault Secrets UI

- Vault UI relies on a mounted Vault token file and network trust.
- Secret reads and writes are delegated to Vault; the UI also regenerates runtime `.env` exports and reports which service restart is required.

## Integration Patterns

### Unified routing through Mega-Orchestrator

Use `mega-orchestrator` when the client wants one catalog and one MCP-compatible entrypoint.

```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "file_read",
    "arguments": {
      "path": "/home/orchestration/README.md"
    }
  }'
```

### Direct service access

Use direct service APIs when an operator or integration needs service-specific routes, status, or debug behavior. Examples:

- `filesystem-mcp`: `GET /file/{path}` and `POST /file/write`
- `git-mcp`: `GET /git/{path}/status` and `POST /git/{path}/commit`
- `security-mcp`: `POST /tools/jwt_token`
- `network-mcp`: `POST /tools/http_request`

### JSON-RPC compatibility

Several services expose MCP-style JSON-RPC interfaces:

- `mega-orchestrator`: `POST /mcp` and `POST /mcp/rpc`
- `marketplace-mcp`: `POST /mcp`
- `mqtt-mcp`: `POST /mcp`
- `zen-mcp-server`: stdio MCP transport inside the container runtime

## Public Surface Summary

### Mega-Orchestrator

- Service discovery: `/health`, `/services`, `/status`, `/stats`
- Tool discovery and schema: `/tools/list`, `/mcp/schema`
- Tool execution: `/mcp`, `/mcp/rpc`, `/mcp/{service}`
- Internal visibility: `/providers`, `/modes`, `/memory/stats`, `/files/stats`, `/debug/cache`, `/debug/contexts/{session_id}`

See [mega_orchestrator.md](mega_orchestrator.md) for the detailed route contract.

### MCP and wrapper services

Direct service APIs fall into two patterns:

- route-oriented services such as `filesystem-mcp`, `git-mcp`, `database-mcp`, `memory-mcp`, `research-mcp`, `gmail-mcp`, and `transcriber-mcp`
- tool-oriented services that publish `GET /tools/list` and execute via service-specific tool routes or `POST /tools/call`

See [API_REFERENCE.md](API_REFERENCE.md) for the complete reference and [SERVICES_DOCUMENTATION.md](SERVICES_DOCUMENTATION.md) for the full service inventory.

### Marketplace MCP

Marketplace exposes both REST and MCP-compatible surfaces:

- catalog browsing: `/skills/v1/index`
- package metadata and downloads: `/skills/v1/packages/...`
- install plan generation: `POST /skills/v1/install-plan`
- server registry: `/registry/v0.1/servers...`
- MCP compatibility: `GET /tools/list`, `POST /tools/{tool_name}`, `POST /mcp`

### Vault UI

Vault overlay adds:

- `GET /health`
- `GET /api/services`
- `GET /api/secrets/{service}`
- `PUT /api/secrets/{service}`
- `GET /` for the HTML UI

## Operator Scripts with Public Behavior

The following scripts are part of the documented operational contract:

- `scripts/health-check.sh`
- `scripts/monitor-services.sh`
- `scripts/monitoring-health-check.sh`
- `scripts/vault-variant-b-smoke.sh`
- `scripts/marketplace/get_market_token.sh`
- `scripts/marketplace/install_skill_from_market.sh`
- `scripts/marketplace/codex_configure_market.sh`
- `scripts/diagnostics/quick_diagnose.sh`
- `scripts/diagnostics/production_monitor.sh`
- `scripts/backup-databases.sh`
- `scripts/install-mcp.sh`

Their purpose and invocation notes are documented in [API_REFERENCE.md](API_REFERENCE.md) and the operations runbooks.
