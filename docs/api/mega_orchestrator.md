# Mega Orchestrator API

The orchestrator listens on HTTP `7000` (see `mega_orchestrator/mega_orchestrator_complete.py`). It proxies MCP tools, publishes a unified `/tools/list`, and exposes health/metrics endpoints used by dashboards and automation.

| Endpoint | Method | Description |
| --- | --- | --- |
| `/health` | GET | Health check that validates PostgreSQL + Redis connections plus service registry heartbeat. Returns `{ "status": "ok", "services": {...} }`. |
| `/services` | GET | Lists every MCP service with status, port, and last ping. Useful for dashboards and instrumentation. |
| `/stats` | GET | Aggregated PostgreSQL metrics (requests per tool, error counters, uptime). |
| `/tools/list` | GET | Merged tool catalog with name, description, schema URI, `service`, and `version`. Clients use this to discover MCP tools. |
| `/mcp` | POST | Primary MCP dispatch endpoint. Accepts `{ "tool": "...", "arguments": {...} }` and forwards to the responsible MCP service based on `tools/list`. |
| `/mcp/rpc` | POST | MCP JSON-RPC compatibility mirror (supports `initialize`, `notifications/initialized`, `tools/list`, `tools/call`). |
| `/tools/call` | POST | Alternate entrypoint for calling MCP tools with named parameters (calls forward to `/mcp` internally). |
| `/mcp/schema` | GET | Exposes the canonical tool schema (JSON) used by CLI bridges and external clients (see `mega_orchestrator/mcp_stdio_bridge.py`). |

## Authentication & Headers

- The orchestrator forwards requests without additional auth by default, but production deployments should gate `/mcp`/`/tools/call` behind JWTs (see `.env` for `JWT_SECRET` and `MARKETPLACE_JWT_TOKEN`).
- Use `Content-Type: application/json` for all POST endpoints.

## Example invocation

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

## Tool discovery script

- The orchestrator publishes `GET /tools/list`, which feeds `scripts/marketplace/install_skill_from_market.sh` and CLI helpers (e.g., `mega_orchestrator/mcp_stdio_bridge.py`). Run `scripts/diagnostics/quick_diagnose.sh` after upgrades to regenerate the catalog snapshot.
