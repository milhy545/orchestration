# Architecture

## System Shape

Orchestration is a compose-managed service mesh centered on a Mega-Orchestrator gateway, a set of direct MCP/HTTP services, a private marketplace, Vault-backed runtime secret management, and observability infrastructure.

## Trust Boundaries

### Public and semi-public entry points

- `mega-orchestrator` on `7000`
- `marketplace-mcp` on `7034`
- `vault-secrets-ui`
- direct service ports used by operators or service-specific clients
- monitoring and support UIs such as Grafana, Prometheus, Loki, PostgreSQL, Redis, Neo4j, and MQTT broker ports

### Internal service network

Most service-to-service traffic stays on the compose bridge network. Persistence and messaging components are consumed by the services rather than acting as the primary user-facing integration layer.

## Main Runtime Components

### Gateway and orchestration

- `mega-orchestrator`: HTTP gateway, service registry, tool routing, stats, and MCP compatibility endpoints.
- `zen-mcp-server`: separate MCP runtime for richer orchestration tool workflows.

### Core services

- Filesystem, git, terminal, database, memory, network, system, security, config, and log services.

### Enhanced services

- Research, advanced memory, transcription, Gmail, marketplace, FORAI, MQTT, code graph, and data-store wrappers.

### Secret management

- `vault-secrets-ui` provides runtime read/write access to the Vault namespaces used by orchestrator and selected services.

### Observability and storage

- PostgreSQL, Redis, Qdrant, Prometheus, Grafana, Loki, Promtail, Neo4j, backup-service, message-queue, and MQTT broker.

## Data and Control Flows

### Tool invocation flow

1. A client discovers tools through `mega-orchestrator` or a direct service.
2. The request is routed either through the orchestrator or directly to a service-specific API.
3. The target service reads backing stores such as PostgreSQL, Redis, Qdrant, or Neo4j when required.
4. Metrics and logs are emitted into the monitoring stack.

### Secret rotation flow

1. An operator reads metadata from `vault-secrets-ui`.
2. The operator updates a secret with `PUT /api/secrets/{service}`.
3. The UI writes the value to Vault and refreshes the generated runtime env files.
4. The response returns the restart target and restart command for the affected service.

## Compatibility Notes

- `vision-mcp` is present in compose as a placeholder and is excluded from stable public-surface guarantees.
- Compatibility Vault namespaces such as `common-mcp` and `perplexity-hub` are maintained for secret mapping, not as first-class runtime APIs.
- Archived documentation remains available for historical traceability but does not define the current architecture.
