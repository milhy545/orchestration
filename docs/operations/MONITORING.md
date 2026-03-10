# Monitoring Guide

## Monitoring Stack

- `prometheus` `7028`: metrics scraping and storage
- `grafana` `7031`: dashboards and alert views
- `loki` `7032`: log aggregation
- `promtail`: log shipping without an external port

## Health Checks

Use these scripts:

- `./scripts/health-check.sh`
- `./scripts/monitor-services.sh`
- `./scripts/monitoring-health-check.sh`
- `./scripts/diagnostics/quick_diagnose.sh`
- `./scripts/diagnostics/production_monitor.sh`

Use these HTTP probes:

- `GET http://localhost:7000/health`
- `GET http://localhost:7034/health`
- `GET http://localhost:7028/-/healthy`
- `GET http://localhost:7032/ready`

## What to Watch

- orchestrator health and service discovery
- database and Redis reachability
- Qdrant and Neo4j availability for memory and code-graph features
- marketplace token configuration
- Vault token readiness and reachability through `vault-secrets-ui`

## Common Monitoring Workflow

1. Run `./scripts/health-check.sh`.
2. Check `docker compose ps`.
3. Open Grafana on `7031`.
4. Query Prometheus or Loki if a service is degraded.
5. Use `quick_diagnose.sh` for a short report before restarting components.
