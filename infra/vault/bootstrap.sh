#!/bin/sh
set -eu

export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
export VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN:-dev-root-token}"
RUNTIME_DIR="/vault/runtime"

mkdir -p "$RUNTIME_DIR"

wait_for_vault() {
  i=0
  while ! vault status >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 60 ]; then
      echo "Vault did not become ready in time" >&2
      exit 1
    fi
    sleep 2
  done
}

seed_secret() {
  path="$1"
  shift

  if vault kv get "$path" >/dev/null 2>&1; then
    return 0
  fi

  vault kv put "$path" "$@" >/dev/null
}

wait_for_vault

if ! vault secrets list | grep -q '^secret/'; then
  vault secrets enable -path=secret kv-v2 >/dev/null
fi

vault policy write vault-admin /vault/config/admin-policy.hcl >/dev/null
vault policy write vault-read /vault/config/read-policy.hcl >/dev/null

ADMIN_TOKEN="$(vault token create -policy=vault-admin -field=token)"
READ_TOKEN="$(vault token create -policy=vault-read -field=token)"

printf '%s' "$ADMIN_TOKEN" > "$RUNTIME_DIR/admin.token"
printf '%s' "$READ_TOKEN" > "$RUNTIME_DIR/read.token"

seed_secret "secret/orchestration/mega-orchestrator" \
  OPENAI_API_KEY="" \
  ANTHROPIC_API_KEY="" \
  GEMINI_API_KEY="" \
  GOOGLE_API_KEY="" \
  PERPLEXITY_API_KEY="" \
  MARKETPLACE_JWT_TOKEN=""

seed_secret "secret/orchestration/research-mcp" \
  PERPLEXITY_API_KEY="" \
  OPENAI_API_KEY=""

seed_secret "secret/orchestration/advanced-memory-mcp" \
  OPENAI_API_KEY=""

seed_secret "secret/orchestration/zen-mcp-server" \
  DEFAULT_MODEL="auto" \
  OPENAI_API_KEY="" \
  ANTHROPIC_API_KEY="" \
  GEMINI_API_KEY="" \
  GOOGLE_API_KEY="" \
  XAI_API_KEY="" \
  OPENROUTER_API_KEY="" \
  DIAL_API_KEY="" \
  DIAL_API_HOST="" \
  DIAL_API_VERSION="" \
  CUSTOM_API_URL="" \
  CUSTOM_API_KEY="" \
  CUSTOM_MODEL_NAME="" \
  DISABLED_TOOLS="" \
  MAX_MCP_OUTPUT_TOKENS="4096"

seed_secret "secret/orchestration/common-mcp" \
  OPENAI_API_KEY="" \
  ANTHROPIC_API_KEY="" \
  GEMINI_API_KEY=""

seed_secret "secret/orchestration/gmail-mcp" \
  EMAIL_ADDRESS="" \
  EMAIL_PASSWORD="" \
  IMAP_SERVER="imap.gmail.com" \
  SMTP_SERVER="smtp.gmail.com" \
  SMTP_PORT="587"

seed_secret "secret/orchestration/internal-auth" \
  JWT_SECRET="change_me_market_jwt"

seed_secret "secret/orchestration/perplexity-hub" \
  PERPLEXITY_API_KEY=""

echo "Vault bootstrap completed."
