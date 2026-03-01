# Mega Orchestrator MCP Compatibility

`mega-orchestrator` now exposes three compatibility layers:

- Legacy custom bridge: `POST /mcp` with `{"tool":"...","arguments":{...}}`
- Native MCP over HTTP JSON-RPC: `POST /mcp` or `POST /mcp/rpc`
- MCP stdio bridge: `python -m mega_orchestrator.mcp_stdio_bridge`

## Network MCP

Use the LAN URL:

```bash
http://192.168.0.58:7000/mcp
```

or the explicit alias:

```bash
http://192.168.0.58:7000/mcp/rpc
```

Supported JSON-RPC methods:

- `initialize`
- `notifications/initialized`
- `tools/list`
- `tools/call`
- `ping`

## Stdio MCP

For clients that prefer command-based MCP:

```bash
MEGA_ORCHESTRATOR_URL=http://192.168.0.58:7000 python -m mega_orchestrator.mcp_stdio_bridge
```

This is the recommended path for:

- Codex CLI (when command-based MCP is easier than network MCP)
- Claude-style stdio MCP clients
- Cursor / Kilo Code style command-based MCP setups

## Notes

- The MCP-exposed tool set is the currently supported working subset.
- Legacy `/tools/list` remains available for custom clients and diagnostics.
- `advanced-memory-mcp` remains outside the MCP-compatible working subset on this hardware.
