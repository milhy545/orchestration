# Orchestration Documentation

This directory contains the active documentation for the current runtime state of the Orchestration platform. Everything under `docs/archive/` is historical material and is excluded from current-state guarantees.

## Start Here

- [index/DOCUMENTATION_INDEX.md](index/DOCUMENTATION_INDEX.md): curated reading order by audience
- [api/API_DOCUMENTATION.md](api/API_DOCUMENTATION.md): entrypoints, authentication, and common integration flows
- [api/API_REFERENCE.md](api/API_REFERENCE.md): complete public endpoint and tool reference
- [api/SERVICES_DOCUMENTATION.md](api/SERVICES_DOCUMENTATION.md): service inventory derived from `docker-compose.yml`

Use the repository root `README.md` on GitHub for the public repo landing page. This `docs/README.md` file is the in-site landing page for the documentation build.

## Documentation Areas

- `architecture/`: system structure, compatibility boundaries, and Vault overlay design
- `operations/`: deployment, monitoring, troubleshooting, and optional Portainer workflow
- `api/`: gateway routes, direct service APIs, wrapper APIs, and tool inventory
- `manuals/`: active operator guides
- `security/`: current security posture and operational security notes
- `archive/`: superseded plans, migrations, and retired manuals

## Maintenance Rules

- Treat `docker-compose.yml`, `mega_orchestrator/`, `mcp-servers/`, and `services/vault-secrets-ui/` as the source of truth.
- When a public route, tool, or service changes, update `docs/api/API_REFERENCE.md` and `docs/api/public_surface_inventory.json` in the same change.
- Keep active documentation in English.
- Use `tests/test_docs_coverage.py` to catch missing coverage, stale terminology, and non-English text in active docs.
