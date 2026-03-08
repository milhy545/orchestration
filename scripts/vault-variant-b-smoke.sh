#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose -f docker-compose.yml -f docker-compose.vault.yml config >/dev/null
echo "compose config: ok"

if curl -fsS "http://127.0.0.1:${VAULT_WEBUI_PORT:-10000}/health" >/tmp/vault_ui_health.json 2>/dev/null; then
  echo "vault-secrets-ui health: ok"
  grep -q '"status":"healthy"' /tmp/vault_ui_health.json && echo "vault-secrets-ui status: healthy"
  grep -q '"vault_reachable":' /tmp/vault_ui_health.json && echo "vault-secrets-ui vault probe: present"
else
  echo "vault-secrets-ui health: skipped (service not running)"
fi

if curl -fsS "http://127.0.0.1:${VAULT_WEBUI_PORT:-10000}/api/services" >/tmp/vault_ui_services.json 2>/dev/null; then
  echo "vault-secrets-ui services: ok"
else
  echo "vault-secrets-ui services: skipped (service not running)"
fi

if curl -fsS "http://127.0.0.1:${VAULT_PORT:-7070}/v1/sys/health" >/dev/null 2>&1; then
  echo "vault health: ok"
else
  echo "vault health: skipped (service not running)"
fi

if curl -fsS "http://127.0.0.1:7000/health" >/dev/null 2>&1; then
  echo "mega-orchestrator health: ok"
else
  echo "mega-orchestrator health: skipped (service not running)"
fi
