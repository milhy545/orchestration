# Troubleshooting

## First Checks

```bash
docker compose ps
./scripts/health-check.sh
./scripts/monitoring-health-check.sh
./scripts/diagnostics/quick_diagnose.sh
```

## Common Failures

### Orchestrator is degraded

- Check PostgreSQL and Redis first.
- Verify `MCP_DATABASE_URL` and `REDIS_URL`.
- Call `GET /health` and `GET /services` on port `7000`.

### Marketplace calls fail

- Verify `MARKETPLACE_JWT_TOKEN` for orchestrator-side access.
- Verify `JWT_SECRET` on `marketplace-mcp`.
- Call `GET /health` and then a scoped endpoint such as `/skills/v1/index`.

### Vault UI cannot read or write secrets

- Confirm the Vault token file exists and is non-empty.
- Check `VAULT_ADDR`, `VAULT_TOKEN_FILE`, and `VAULT_RUNTIME_DIR`.
- Call `GET /health` on the Vault UI before attempting `PUT /api/secrets/{service}`.

### Memory or vector features fail

- Check `qdrant-vector` availability.
- Confirm `QDRANT_URL` for services that depend on vector search.
- Validate PostgreSQL connectivity for metadata-backed memory flows.

### Code graph or graph-backed features fail

- Confirm Neo4j is up on `7474` and `7687`.
- Verify `NEO4J_URL`, `NEO4J_USER`, and `NEO4J_PASSWORD`.

### Monitoring is incomplete

- Check Prometheus config mounts and Grafana provisioning mounts.
- Confirm Promtail can read Docker container logs.
- Use the monitoring health script before editing dashboards.
