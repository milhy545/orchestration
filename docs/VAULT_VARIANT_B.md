# Vault Variant B

`Vault Variant B` adds a lightweight Vault-backed secrets overlay on top of the main orchestration stack without replacing the base `docker-compose.yml`.

## What It Adds

- `vault` on `${VAULT_PORT:-7070}` backed by the HashiCorp Vault dev server
- `vault-bootstrap` to seed policies, shared runtime tokens, and initial secret paths
- `vault-agent-common` to render env snapshots into `/vault/runtime/*.env`
- `vault-secrets-ui` on `${VAULT_WEBUI_PORT:-10000}` with the restored 3-theme retro Web UI

The overlay is intentionally additive. The base stack remains usable without Vault.

## Files

- `docker-compose.vault.yml`
- `infra/vault/*`
- `services/vault-secrets-ui/*`
- `scripts/vault-variant-b-smoke.sh`

## Start

```bash
docker compose -f docker-compose.yml -f docker-compose.vault.yml up -d --build
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

## Secret Paths

The restored UI and render loop manage these paths:

- `secret/orchestration/mega-orchestrator`
- `secret/orchestration/research-mcp`
- `secret/orchestration/advanced-memory-mcp`
- `secret/orchestration/zen-mcp-server`
- `secret/orchestration/common-mcp`
- `secret/orchestration/perplexity-hub`

The first four map to active services in the current stack. `common-mcp` and `perplexity-hub` are preserved as legacy secret namespaces from the original variant so the recovered UI matches the historical behavior.

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

## Runtime Rendered Files

`vault-agent-common` renders env snapshots into the shared runtime volume:

- `/vault/runtime/mega-orchestrator.env`
- `/vault/runtime/research-mcp.env`
- `/vault/runtime/advanced-memory-mcp.env`
- `/vault/runtime/zen-mcp-server.env`
- `/vault/runtime/common-mcp.env`
- `/vault/runtime/perplexity-hub.env`

These files are mounted read-only into selected containers so the runtime snapshots are visible inside the stack. The current overlay does not force-reexec existing service entrypoints; it restores the original shared secret storage path first and leaves deeper runtime sourcing to a follow-up pass if needed.

## Smoke Test

```bash
./scripts/vault-variant-b-smoke.sh
```

The smoke script validates compose syntax and probes health endpoints if the stack is already running.
