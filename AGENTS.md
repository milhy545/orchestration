# Repository Guidelines

## Project Structure
- `mcp-servers/`: individual MCP microservices, each with its own `requirements.txt` and `Dockerfile`
- `mega_orchestrator/`, `claude-agent/`, `claude-agent-env/`: orchestration core and agent runtime components
- `config/`: shared build and dependency configuration
- `monitoring/`: Prometheus, Grafana, Loki, and Promtail configuration
- `docs/`: active documentation, indexed from `docs/README.md`
- `scripts/`: operator, health-check, marketplace, and migration scripts
- `tests/`: repository-level tests and cross-service checks

## Build, Test, and Development Commands
- `docker compose up -d`: start the default stack in the background
- `docker compose down`: stop the stack
- `docker compose logs -f <service>`: follow logs for one service
- `./scripts/monitoring-health-check.sh`: validate the monitoring configuration and wiring
- `bash tests/docker-compose-monitoring-test.sh`: verify the monitoring-related compose sections
- `pytest`: run repository tests and service tests under `tests/` and `mcp-servers/*/tests`

## Coding Style
- Follow the existing conventions inside each service
- Use 4 spaces and PEP 8 for Python
- Keep YAML files, including `docker-compose.yml`, at 2-space indentation
- Keep test naming compatible with `pytest.ini`: `test_*.py`, `Test*`, and `test_*`

## Testing Rules
- Pytest markers: `unit`, `integration`, `security`, `performance`, `slow`
- When `pytest-cov` is used, the minimum coverage target is `fail_under = 70`
- Add or update tests next to the service you change whenever practical

## Commits and Pull Requests
- Prefer short descriptive commits, optionally with a scope prefix such as `docs:`
- Pull requests should explain the reason for the change and list the commands that were run
- Changes that touch Docker or monitoring should mention the affected services and any new environment variables

## Security and Configuration
- Copy `.env.example` to `.env` before starting the stack
- Never commit secrets; use `.env`, Vault, or another secure external store

## 🧠 FORAI Memory Integration & Tagging System

All AI agents operating within this repository MUST use the **FORAI** tagging system when storing or retrieving context in the Memory MCP.

### Usage for Agents:
1. **Storing:** Always inject `"FORAI"` along with contextual keywords into the `metadata.tags` array (e.g., `{"tags": ["FORAI", "architecture", "refactor"]}`).
2. **Retrieving:** Use the `vector_search` tool with the `FORAI` filter or `semantic_search` focusing on FORAI concepts.
3. **Mega-Orchestrator:** Route all memory requests through `mega-orchestrator` on port 7000 using `store_semantic_memory` or `store_memory` tools.
