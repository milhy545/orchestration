#!/bin/sh
set -eu

export VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
TOKEN_FILE="/vault/runtime/read.token"
RUNTIME_DIR="/vault/runtime"
HEADER_FILE="/vault/config/common-mcp.env.tpl"
INTERVAL="${RENDER_INTERVAL_SECONDS:-30}"

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

load_token() {
  if [ -f "$TOKEN_FILE" ]; then
    token="$(tr -d '\r\n' < "$TOKEN_FILE")"
    if [ -n "$token" ]; then
      export VAULT_TOKEN="$token"
      return 0
    fi
  fi

  export VAULT_TOKEN="${VAULT_DEV_ROOT_TOKEN:-dev-root-token}"
}

write_key() {
  path="$1"
  key="$2"
  outfile="$3"
  value="$(vault kv get -field="$key" "$path" 2>/dev/null || true)"
  if [ -n "$value" ]; then
    printf '%s=%s\n' "$key" "$value" >> "$outfile"
  fi
}

render_env_file() {
  service="$1"
  path="$2"
  keys="$3"
  tmp_file="$RUNTIME_DIR/$service.env.tmp"
  out_file="$RUNTIME_DIR/$service.env"

  cat "$HEADER_FILE" > "$tmp_file"
  printf 'SERVICE_NAME=%s\n' "$service" >> "$tmp_file"
  printf 'VAULT_SECRET_PATH=%s\n' "$path" >> "$tmp_file"

  for key in $keys; do
    write_key "$path" "$key" "$tmp_file"
  done

  mv "$tmp_file" "$out_file"
}

render_all() {
  render_env_file \
    "mega-orchestrator" \
    "secret/orchestration/mega-orchestrator" \
    "OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY PERPLEXITY_API_KEY"

  render_env_file \
    "research-mcp" \
    "secret/orchestration/research-mcp" \
    "PERPLEXITY_API_KEY OPENAI_API_KEY"

  render_env_file \
    "advanced-memory-mcp" \
    "secret/orchestration/advanced-memory-mcp" \
    "OPENAI_API_KEY"

  render_env_file \
    "zen-mcp-server" \
    "secret/orchestration/zen-mcp-server" \
    "DEFAULT_MODEL OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY XAI_API_KEY OPENROUTER_API_KEY DIAL_API_KEY DIAL_API_HOST DIAL_API_VERSION CUSTOM_API_URL CUSTOM_API_KEY CUSTOM_MODEL_NAME DISABLED_TOOLS MAX_MCP_OUTPUT_TOKENS"

  render_env_file \
    "common-mcp" \
    "secret/orchestration/common-mcp" \
    "OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY"

  render_env_file \
    "perplexity-hub" \
    "secret/orchestration/perplexity-hub" \
    "PERPLEXITY_API_KEY"
}

load_token
wait_for_vault

while true; do
  render_all
  sleep "$INTERVAL"
done
