#!/bin/sh
set -eu

export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
RUNTIME_DIR="/vault/runtime"
ROOT_TOKEN_FILE="$RUNTIME_DIR/root.token"
UNSEAL_KEY_FILE="$RUNTIME_DIR/unseal.key"
ADMIN_TOKEN_FILE="$RUNTIME_DIR/admin.token"
READ_TOKEN_FILE="$RUNTIME_DIR/read.token"
MIGRATION_SCRIPT="$RUNTIME_DIR/migrate-secrets.sh"

mkdir -p "$RUNTIME_DIR"
chmod 700 "$RUNTIME_DIR"

wait_for_api() {
  i=0
  while true; do
    set +e
    vault status >/dev/null 2>&1
    code=$?
    set -e
    if [ "$code" -eq 0 ] || [ "$code" -eq 2 ]; then
      return 0
    fi
    i=$((i + 1))
    if [ "$i" -ge 60 ]; then
      echo "Vault API did not become ready in time" >&2
      exit 1
    fi
    sleep 2
  done
}

status_json() {
  set +e
  output="$(vault status -format=json 2>/dev/null)"
  code=$?
  set -e
  if [ -n "$output" ]; then
    printf '%s' "$output"
  fi
  return "$code"
}

is_initialized() {
  status_json 2>/dev/null | grep -Eq '"initialized"[[:space:]]*:[[:space:]]*true'
}

is_sealed() {
  status_json 2>/dev/null | grep -Eq '"sealed"[[:space:]]*:[[:space:]]*true'
}

require_file() {
  file="$1"
  if [ ! -s "$file" ]; then
    echo "Required Vault bootstrap file missing or empty: $file" >&2
    exit 1
  fi
}

generate_secret() {
  head -c 48 /dev/urandom | base64 | tr -d '\r\n'
}

init_vault_if_needed() {
  if is_initialized; then
    return 0
  fi

  init_json="$(vault operator init -key-shares=1 -key-threshold=1 -format=json)"
  compact_json="$(printf '%s' "$init_json" | tr -d '\r\n')"
  printf '%s' "$compact_json" | sed -n 's/.*"root_token"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' > "$ROOT_TOKEN_FILE"
  printf '%s' "$compact_json" | sed -n 's/.*"unseal_keys_b64"[[:space:]]*:[[:space:]]*\[[[:space:]]*"\([^"]*\)".*/\1/p' > "$UNSEAL_KEY_FILE"
  require_file "$ROOT_TOKEN_FILE"
  require_file "$UNSEAL_KEY_FILE"
  chmod 600 "$ROOT_TOKEN_FILE" "$UNSEAL_KEY_FILE"
}

unseal_vault_if_needed() {
  if ! is_sealed; then
    return 0
  fi
  require_file "$UNSEAL_KEY_FILE"
  vault operator unseal "$(tr -d '\r\n' < "$UNSEAL_KEY_FILE")" >/dev/null
}

login_root() {
  require_file "$ROOT_TOKEN_FILE"
  export VAULT_TOKEN="$(tr -d '\r\n' < "$ROOT_TOKEN_FILE")"
  if [ -z "$VAULT_TOKEN" ]; then
    echo "Vault root token is empty" >&2
    exit 1
  fi
}

ensure_secret_engine() {
  if ! vault secrets list | grep -q '^secret/'; then
    vault secrets enable -path=secret kv-v2 >/dev/null
  fi
}

write_tokens() {
  ADMIN_TOKEN="$(vault token create -policy=vault-admin -field=token)"
  READ_TOKEN="$(vault token create -policy=vault-read -field=token)"
  printf '%s' "$ADMIN_TOKEN" > "$ADMIN_TOKEN_FILE"
  printf '%s' "$READ_TOKEN" > "$READ_TOKEN_FILE"
  chmod 600 "$ADMIN_TOKEN_FILE" "$READ_TOKEN_FILE"
}

import_migration_snapshot() {
  if [ ! -f "$MIGRATION_SCRIPT" ]; then
    return 0
  fi
  chmod 700 "$MIGRATION_SCRIPT"
  sanitized_script="$RUNTIME_DIR/.migrate-secrets.sanitized.sh"
  grep -v '^export VAULT_TOKEN=' "$MIGRATION_SCRIPT" > "$sanitized_script"
  chmod 700 "$sanitized_script"
  "$sanitized_script"
  rm -f "$sanitized_script"
  rm -f "$MIGRATION_SCRIPT"
}

seed_secret() {
  path="$1"
  shift

  if vault kv get "$path" >/dev/null 2>&1; then
    return 0
  fi

  vault kv put "$path" "$@" >/dev/null
}

wait_for_api
init_vault_if_needed
unseal_vault_if_needed
login_root
ensure_secret_engine

vault policy write vault-admin /vault/config/admin-policy.hcl >/dev/null
vault policy write vault-read /vault/config/read-policy.hcl >/dev/null
write_tokens
import_migration_snapshot

seed_secret "secret/orchestration/mega-orchestrator" \
  OPENAI_API_KEY="" \
  ANTHROPIC_API_KEY="" \
  GEMINI_API_KEY="" \
  GOOGLE_API_KEY="" \
  PERPLEXITY_API_KEY="" \
  MARKETPLACE_JWT_TOKEN=""

seed_secret "secret/orchestration/advanced-memory-mcp" \
  EMBEDDING_PROVIDER="local" \
  GENERATION_PROVIDER="none" \
  LOCAL_EMBEDDING_MODEL="all-MiniLM-L6-v2" \
  GEMINI_API_KEY="" \
  GEMINI_EMBED_MODEL="gemini-embedding-001" \
  OLLAMA_BASE_URL="http://127.0.0.1:11434" \
  OLLAMA_EMBED_MODEL="nomic-embed-text" \
  OLLAMA_CHAT_MODEL="llama3.2" \
  OPENAI_COMPAT_BASE_URL="" \
  OPENAI_COMPAT_API_KEY="" \
  OPENAI_COMPAT_EMBED_MODEL="" \
  OPENAI_COMPAT_CHAT_MODEL="" \
  INCEPTION_API_KEY="" \
  INCEPTION_BASE_URL="https://api.inceptionlabs.ai/v1" \
  INCEPTION_MODEL="mercury"

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
  GEMINI_API_KEY="" \
  NOTION_API_KEY=""

seed_secret "secret/orchestration/gmail-mcp" \
  EMAIL_ADDRESS="" \
  EMAIL_PASSWORD="" \
  IMAP_SERVER="imap.gmail.com" \
  SMTP_SERVER="smtp.gmail.com" \
  SMTP_PORT="587"

seed_secret "secret/orchestration/internal-auth" \
  JWT_SECRET="$(generate_secret)"

seed_secret "secret/orchestration/perplexity-hub" \
  PERPLEXITY_API_KEY="" \
  OPENAI_API_KEY=""

echo "Vault bootstrap completed."
