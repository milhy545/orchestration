# Vault Variant B

`Vault Variant B` adds a lightweight Vault-backed secrets overlay on top of the main orchestration stack without replacing the base `docker-compose.yml`.

## What It Adds

- `vault` on `${VAULT_PORT:-7070}` backed by the HashiCorp Vault dev server
- `vault-bootstrap` to seed policies, shared runtime tokens, and initial secret paths
- `vault-agent-common` to render shell-safe env snapshots into `/vault/runtime/*.env`
- `vault-secrets-ui` on `${VAULT_WEBUI_PORT:-10000}` with the restored 3-theme retro Web UI

The overlay is intentionally additive. The base stack remains usable without Vault, but when the overlay is enabled the selected services start through a Vault runtime wrapper and load secrets from `/vault/runtime/*.env`.

## Files

- `docker-compose.vault.yml`
- `infra/vault/*`
- `services/vault-secrets-ui/*`
- `scripts/vault-variant-b-smoke.sh`

## Start

```bash
docker compose -f docker-compose.yml -f docker-compose.vault.yml up -d --build
```

For a faster first bring-up on this machine, you can target only the Vault-enabled services:

```bash
docker compose -f docker-compose.yml -f docker-compose.vault.yml up -d --build \
  vault vault-bootstrap vault-agent-common vault-secrets-ui \
  postgresql redis mega-orchestrator research-mcp zen-mcp-server \
  gmail-mcp security-mcp marketplace-mcp
```

## Health Checks

```bash
curl -s http://localhost:${VAULT_WEBUI_PORT:-10000}/health
curl -s http://localhost:${VAULT_PORT:-7070}/v1/sys/health
curl -s http://localhost:7000/health
```

Expected:

- `vault-secrets-ui` reports `status: healthy`
- Vault responds on `/v1/sys/health`
- `mega-orchestrator` remains reachable on `7000`
- `vault-secrets-ui` health also reports token-file and Vault connectivity state

## Secret Paths

The restored UI and render loop manage these paths:

- `secret/orchestration/mega-orchestrator`
- `secret/orchestration/research-mcp`
- `secret/orchestration/advanced-memory-mcp`
- `secret/orchestration/zen-mcp-server`
- `secret/orchestration/gmail-mcp`
- `secret/orchestration/internal-auth`
- `secret/orchestration/common-mcp`
- `secret/orchestration/perplexity-hub`

The first six map to active runtime consumers in the current stack. `common-mcp` and `perplexity-hub` are preserved as legacy secret namespaces from the original variant so the recovered UI matches the historical behavior.

## Web UI

Open:

```text
http://localhost:${VAULT_WEBUI_PORT:-10000}
```

The restored UI keeps the original 3-theme variant:

- `PIP-BOY`
- `CYBERPUNK`
- `VIBE AGENT`

It also keeps the EN/CS toggle and JSON editor workflow.

The UI now also shows:

- the target runtime env file
- which service must be restarted
- the exact `docker compose ... restart <service>` command

The first functional version is intentionally **restart-based**: save the secret, then restart the affected service. The Web UI immediately refreshes the relevant `/vault/runtime/*.env` file after each save so you do not need to wait for the periodic render loop before restarting.

## Runtime Rendered Files

`vault-agent-common` renders env snapshots into the shared runtime volume:

- `/vault/runtime/mega-orchestrator.env`
- `/vault/runtime/research-mcp.env`
- `/vault/runtime/advanced-memory-mcp.env`
- `/vault/runtime/zen-mcp-server.env`
- `/vault/runtime/gmail-mcp.env`
- `/vault/runtime/security-mcp.env`
- `/vault/runtime/marketplace-mcp.env`
- `/vault/runtime/common-mcp.env`
- `/vault/runtime/perplexity-hub.env`

These files are mounted read-only into selected containers and sourced at process startup through `infra/vault/run-with-env.sh`. This means updated secrets take effect after the target container is restarted.

## First-Wave Runtime Consumers

The overlay actively injects Vault-backed secrets into these services:

- `mega-orchestrator`
- `research-mcp`
- `zen-mcp-server`
- `gmail-mcp`
- `security-mcp`
- `marketplace-mcp`

`advanced-memory-mcp` is wired for the same pattern, but local runtime validation may be deferred on low-resource hosts.

## Operator Workflow

1. Start the stack with `docker-compose.vault.yml`.
2. Open `http://localhost:${VAULT_WEBUI_PORT:-10000}`.
3. Select a service and upload the JSON payload with the needed secrets.
4. Restart the affected service using the command shown in the UI.
5. Re-check the service health endpoint or behavior through `mega-orchestrator`.

## Smoke Test

```bash
./scripts/vault-variant-b-smoke.sh
```

The smoke script validates compose syntax and probes health endpoints if the stack is already running.
