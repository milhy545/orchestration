# Repository Guidelines for External Agents

## Project Structure

- `mcp-servers/`: individual MCP microservices, each with its own `requirements.txt` and `Dockerfile`.
- `mega_orchestrator/`, `claude-agent/`, `claude-agent-env/`: orchestration core and agent-related components.
- `config/`: shared configuration, including `config/requirements.txt` and `config/Dockerfile`.
- `monitoring/`: Prometheus, Grafana, Loki, and Promtail configuration.
- `docs/`: current documentation. Start with `docs/README.md`.
- `scripts/`: operator scripts for health checks, diagnostics, migrations, marketplace tasks, and backups.
- `tests/`: cross-service tests and helper utilities.

## Core Commands

- `docker-compose up -d`
- `docker-compose down`
- `docker-compose logs -f <service>`
- `./scripts/monitoring-health-check.sh`
- `bash tests/docker-compose-monitoring-test.sh`
- `pytest`

## Coding and Review Rules

- Respect the conventions already used inside each service.
- Use 4-space indentation and PEP 8 for Python.
- Keep YAML indentation at 2 spaces.
- Add tests next to the service being changed.
- Never commit secrets; use `.env` files or an external secrets system.

## Documentation Rule

If a change affects a public endpoint, MCP tool, script, or operator workflow, update the relevant active documentation in the same change set.
