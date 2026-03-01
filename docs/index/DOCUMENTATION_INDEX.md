# Documentation Index - Orchestration MCP Platform

## Quick Start

1. **[../README.md](../README.md)** - Documentation front door
2. **[../operations/DEPLOYMENT.md](../operations/DEPLOYMENT.md)** - Deployment and bring-up
3. **[../operations/PORTAINER_DEPLOYMENT.md](../operations/PORTAINER_DEPLOYMENT.md)** - Portainer deployment
4. **[../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)** - MCP/API reference
5. **[../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)** - Operational troubleshooting

---

## Repository Layout Notes

- Operational guides previously in repo root are now under [`docs/manuals/`](../manuals/).
- Generated reports and audit summaries are under [`docs/reports/`](../reports/).
- Historical planning and migration notes are under [`docs/archive/`](../archive/).
- Ad-hoc diagnostic scripts are organized in [`scripts/diagnostics/`](../../scripts/diagnostics/) and legacy one-offs in [`scripts/legacy/`](../../scripts/legacy/).

## Documentation Categories

### Core Entry Points

### Architecture
- [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
- [../architecture/MEGA_MCP_COMPATIBILITY.md](../architecture/MEGA_MCP_COMPATIBILITY.md)
- [../architecture/VAULT_VARIANT_B.md](../architecture/VAULT_VARIANT_B.md)

### Operations
- [../operations/DEPLOYMENT.md](../operations/DEPLOYMENT.md)
- [../operations/MONITORING.md](../operations/MONITORING.md)
- [../operations/PORTAINER_DEPLOYMENT.md](../operations/PORTAINER_DEPLOYMENT.md)
- [../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)

### API
- [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
- [../api/API_REFERENCE.md](../api/API_REFERENCE.md)
- [../api/SERVICES_DOCUMENTATION.md](../api/SERVICES_DOCUMENTATION.md)

### Security
- [../security/SECURITY_SCAN_SUMMARY.md](../security/SECURITY_SCAN_SUMMARY.md)

### Reports
- [../reports/](../reports/)

### Historical Archive
- [../archive/](../archive/)

---

## Documentation Usage Guide

### For New Users
1. Start with [../README.md](../README.md)
2. Continue with [../operations/DEPLOYMENT.md](../operations/DEPLOYMENT.md)
3. Use [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
4. Keep [../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md) handy

### For Developers
1. [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
2. [../api/SERVICES_DOCUMENTATION.md](../api/SERVICES_DOCUMENTATION.md)
3. [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
4. [../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)

### For System Administrators
1. [../operations/PORTAINER_DEPLOYMENT.md](../operations/PORTAINER_DEPLOYMENT.md)
2. [../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)
3. [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
4. [../README.md](../README.md)

### For AI Agents
1. [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
2. [../api/SERVICES_DOCUMENTATION.md](../api/SERVICES_DOCUMENTATION.md)
3. [../architecture/MEGA_MCP_COMPATIBILITY.md](../architecture/MEGA_MCP_COMPATIBILITY.md)

---

## Quick Reference

### Current Entry Points
- **Production Server**: 192.168.0.58 (Home Automation Server)
- **GitHub Repository**: [milhy545/orchestration](https://github.com/milhy545/orchestration)
- **Docs Front Door**: [../README.md](../README.md)

### Critical Ports
- **7000**: ZEN Coordinator (main entry point)
- **7001-7017**: MCP Services (internal only)
- **7021**: PostgreSQL database
- **7022**: Redis cache
- **6333**: Qdrant vector database
- **9001**: Portainer Agent (required for Portainer)

### API Endpoints
- **Health**: `http://192.168.0.58:7000/health`
- **Services**: `http://192.168.0.58:7000/services`
- **Tools**: `http://192.168.0.58:7000/tools/list`
- **Native MCP JSON-RPC**: `http://192.168.0.58:7000/mcp/rpc` (POST, recommended)
- **Legacy MCP Gateway**: `http://192.168.0.58:7000/mcp` (POST, compatibility mode)

### Quick Health Check
```bash
# Overall system health
curl http://192.168.0.58:7000/health

# List all services
curl http://192.168.0.58:7000/services

# Test native MCP JSON-RPC handshake
curl -X POST http://192.168.0.58:7000/mcp/rpc \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# Legacy custom request (compatibility mode)
curl -X POST http://192.168.0.58:7000/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool":"system_info","arguments":{}}'
```

---

## Maintenance Notes

- Prefer adding new documents into the correct category instead of the `docs/` root.
- Treat `docs/archive/` as retained historical documentation, not current operational guidance.
- Treat top-level `archive/` as a retention zone for project artifacts, not documentation.
