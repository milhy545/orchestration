# Documentation Index - Orchestration MCP Platform

## Quick Starters
1. [../README.md](../README.md) — product overview and service map.
2. [../api/API_DOCUMENTATION.md](../api/API_DOCUMENTATION.md) — mega-orchestrator, marketplace, Vault, and MCP bridges.
3. [../api/SERVICES_DOCUMENTATION.md](../api/SERVICES_DOCUMENTATION.md) — active service/tool inventory and links to each tool’s docs.
4. [../operations/DEPLOYMENT.md](../operations/DEPLOYMENT.md) — bring-up, env vars, and cluster wiring.
5. [../operations/MONITORING.md](../operations/MONITORING.md) — observability stack and health checks.

## Documentation Strategy

- **Architecture**: `docs/architecture/` (system design, compatibility, Vault overlay).
- **Operations**: `docs/operations/` (deployment, monitoring, Portainer, troubleshooting).
- **API & Services**: `docs/api/` (mega-orchestrator and MCP tools), new active-service index.
- **Security & Reports**: `docs/security/`, `docs/reports/`.
- **Manuals**: `docs/manuals/` (Gemini, manuals, Vault quick-starts).
- **Archive**: `docs/archive/` (historical plans, migration stories) and top-level `archive/` for retained artifacts.

## Audience Paths

Operators: README → operations docs → monitoring dashboards → reports.  
Integrators: API docs → service inventory → compatibility guide.  
Developers: architecture docs → MCP service descriptions → tooling list.  
Auditors: security summary → reports/audits.  
Researchers: archive/ for past plans plus `docs/README.md` archive guidance.

## Active Public Surface

- `mega-orchestrator` (HTTP 7000): `GET /health`, `/tools/list`, `/services`, `/stats`, `/mcp`, `/mcp/rpc`, `/tools/call`, `/mcp/schema`.
- MCP services (7001-7017): each exposes `/health`, `/tools/list`, MCP tools such as `file_read`, `git_status`, `mcp-transcribe`, `db_query`, etc.
- Enhanced services like `marketplace-mcp`, `gmail-mcp`, and Vault UI (see `services/vault-secrets-ui/app.py`).
- Operational scripts under `scripts/` provide automation entry points (monitoring-health-check, backup, marketplace installs, Vault variant launch).

## Documentation Workflows

When a service/tool changes:
1. Update the relevant `docs/api/*` entry and service/tool table.
2. Reflect new ports/endpoints in `README.md` service map.
3. Refresh `docs/index/DOCUMENTATION_INDEX.md` if the audience path changes.
4. Link new operational scripts from `docs/operations/*` runbooks.

## Maintenance Notes
- Keep new materials in the categorized folder (architecture/api/operations).
- Label historical docs in `docs/archive/` and `archive/` as such.
