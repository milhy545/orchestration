# Documentation Index

## Recommended Reading Order

### Operators
1. [../README.md](../README.md)
2. [../operations/DEPLOYMENT.md](../operations/DEPLOYMENT.md)
3. [../operations/MONITORING.md](../operations/MONITORING.md)
4. [../operations/TROUBLESHOOTING.md](../operations/TROUBLESHOOTING.md)
5. [../manuals/MANUAL.md](../manuals/MANUAL.md)

### Integrators
1. [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md)
2. [../api/mega_orchestrator.md](../api/mega_orchestrator.md)
3. [../api/API_REFERENCE.md](../api/API_REFERENCE.md)
4. [../architecture/MEGA_MCP_COMPATIBILITY.md](../architecture/MEGA_MCP_COMPATIBILITY.md)

### Maintainers
1. [../architecture/ARCHITECTURE.md](../architecture/ARCHITECTURE.md)
2. [../api/SERVICES_DOCUMENTATION.md](../api/SERVICES_DOCUMENTATION.md)
3. [../security/SECURITY_SCAN_SUMMARY.md](../security/SECURITY_SCAN_SUMMARY.md)
4. [../archive/README.md](../archive/README.md)

## Active Public Surface

- Gateway: `mega-orchestrator` on `7000`
- Private catalog: `marketplace-mcp` on `7034`
- Vault overlay UI: `vault-secrets-ui` on `10000` when the overlay compose file is enabled
- MCP and wrapper services: `7001` through `7026` depending on the service
- Observability stack: Prometheus `7028`, Grafana `7031`, Loki `7032`

## Source-of-Truth Files

- Runtime topology: `docker-compose.yml`
- Gateway routes: `mega_orchestrator/mega_orchestrator_complete.py`
- Service APIs: `mcp-servers/*/main.py`
- Vault UI API: `services/vault-secrets-ui/app.py`
- Docs coverage inventory: `docs/api/public_surface_inventory.json`
