# Agent Working Notes

This document summarizes repository expectations for agent-driven maintenance work on Orchestration.

## Ground Rules

- Treat the repository in this workspace as the source of truth.
- Use `docker-compose.yml`, active service code, and the documentation inventory as the primary reference set.
- Prefer the active docs tree over archived write-ups when resolving naming, ports, endpoints, or workflows.

## Repository Map

- `mega_orchestrator/`: Mega-Orchestrator HTTP bridge, provider registry, routing, memory, and stdio tooling.
- `mcp-servers/`: public MCP and HTTP services.
- `services/vault-secrets-ui/`: Vault-backed runtime secrets UI and API.
- `scripts/`: health checks, monitoring, diagnostics, marketplace helpers, and migration utilities.
- `docs/`: current documentation.

## Recommended Checks

- `pytest`
- `./scripts/health-check.sh`
- `./scripts/monitoring-health-check.sh`
- `bash tests/docker-compose-monitoring-test.sh`

## Documentation Rule

When a public endpoint, MCP tool, script entry point, or supported workflow changes, update:

1. the relevant API or service reference
2. any affected operations or manual pages
3. `docs/api/public_surface_inventory.json`
4. `tests/test_docs_coverage.py` if validation rules need to change
