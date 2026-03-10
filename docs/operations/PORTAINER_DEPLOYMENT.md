# Portainer Deployment Notes

Portainer can manage the compose stack, but the source of truth remains the repository `docker-compose.yml` and the active documentation set.

## Portainer Workflow

1. Import the compose stack from the repository.
2. Provide the same environment variables used by local compose deployments.
3. Validate volumes and daemon-visible paths before the first deploy.
4. After deployment, run the same health-check scripts documented for non-Portainer workflows.

## Ports and Services to Validate

- `7000` Mega-Orchestrator
- `7001-7013`, `7015-7026`, `7034` service APIs
- `7021-7023`, `7027-7032`, `7018-7020`, `7474`, `7687` support services

## Post-Deploy Verification

- `docker compose ps`
- `./scripts/health-check.sh`
- `./scripts/monitoring-health-check.sh`
- `GET /health` on `mega-orchestrator` and `marketplace-mcp`

Do not use historical counts of tools or services as acceptance criteria. Validate against the running compose stack and the current documentation inventory.
