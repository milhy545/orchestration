# Mega-Orchestrator API

`mega-orchestrator` is implemented in `mega_orchestrator/mega_orchestrator_complete.py` and exposed on host port `7000`. It is the main catalog and routing surface for clients that want one HTTP entrypoint instead of calling each MCP service directly.

## Route Contract

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/mcp` | Main tool dispatch route; accepts native request bodies and JSON-RPC payloads |
| `POST` | `/mcp/rpc` | JSON-RPC compatible alias |
| `POST` | `/mcp/{service}` | Send a request to one named downstream service |
| `GET` | `/health` | Gateway health plus downstream summary |
| `GET` | `/services` | Registered services with health and routing metadata |
| `GET` | `/tools/list` | Unified tool catalog built from the currently exposed working subset |
| `GET` | `/mcp/schema` | MCP tool and resource schema returned by the gateway |
| `GET` | `/status` | Lightweight status payload |
| `GET` | `/stats` | Requests processed, uptime, mode switches, and related counters |
| `GET` | `/providers` | Provider registry state |
| `GET` | `/modes` | Available SAGE modes and routing data |
| `GET` | `/memory/stats` | Gateway memory metrics |
| `GET` | `/files/stats` | Gateway file-storage metrics |
| `GET` | `/debug/cache` | Cache inspection |
| `GET` | `/debug/contexts/{session_id}` | Debug view into a stored session context |

## Request Shape

### Native tool dispatch

```json
{
  "tool": "file_read",
  "arguments": {
    "path": "/home/orchestration/README.md"
  },
  "mode": "docs",
  "session_id": "optional-session-id",
  "context_id": "optional-context-id"
}
```

### JSON-RPC dispatch

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "file_read",
    "arguments": {
      "path": "/home/orchestration/README.md"
    }
  }
}
```

## Response Notes

- Health and inventory routes return standard JSON objects.
- Tool execution returns the routed service result or an error object.
- The schema route exposes both tool definitions and stable resource URIs such as `mega://health`, `mega://services`, and `mega://schema`.
- Tool availability depends on the gateway's configured service registry and downstream health.

## Example

```bash
curl -X POST http://localhost:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "git_status",
    "arguments": {
      "path": "/workspace/repository"
    }
  }'
```

## Operational Guidance

- Use `GET /tools/list` before building a client-side registry.
- Use `GET /services` to determine which downstream services are currently healthy.
- Do not assume the gateway is an authentication boundary in the default compose deployment.
