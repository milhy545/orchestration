# Deployment Guide

## Prerequisites

- Docker Engine with compose support
- access to the repository checkout path visible to the Docker daemon
- a populated `.env` file based on `.env.example`
- available storage for PostgreSQL, Redis, Qdrant, Neo4j, and monitoring data

## Required Paths

The compose file uses these path-oriented variables:

- `PROJECT_ROOT`
- `DATA_ROOT`
- `MONITORING_ROOT`
- `HOST_HOME_PATH`
- `ZEN_MCP_SERVER_PATH`

If the Docker daemon runs remotely, set these to daemon-visible absolute paths before starting the stack.

## Important Environment Variables

- `MCP_DATABASE_URL`
- `REDIS_URL`
- `MARKETPLACE_JWT_TOKEN`
- `JWT_SECRET`
- `PERPLEXITY_API_KEY`
- provider keys for orchestrator, research, Gmail, and ZEN services
- `NEO4J_PASSWORD`
- monitoring credentials such as `GRAFANA_ADMIN_USER` and `GRAFANA_ADMIN_PASSWORD`

## Bring-Up Sequence

```bash
cp .env.example .env
docker compose up -d postgresql redis qdrant-vector neo4j
docker compose up -d
./scripts/health-check.sh
./scripts/monitoring-health-check.sh
```

## High-Value Entry Points After Startup

- `http://localhost:7000/health`
- `http://localhost:7000/tools/list`
- `http://localhost:7034/health`
- `http://localhost:7031/`
- `http://localhost:7028/`

## Vault Variant

When runtime secrets are managed through Vault:

- keep the Vault token file available to `vault-secrets-ui`
- use `scripts/vault-variant-b-smoke.sh` after deployment
- restart the target service after secret updates when instructed by the UI response

## Deployment Notes

- `vision-mcp` is a placeholder service and should not be treated as a production capability.
- Wrapper services on `7024-7026` are active APIs and should remain documented.
- `promtail` has no external port and is managed through the compose stack rather than direct user access.
