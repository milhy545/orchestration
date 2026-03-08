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
  echo "Vault read token missing or empty: $TOKEN_FILE" >&2
  exit 65
}

shell_quote() {
  printf "%s" "$1" | sed "s/'/'\\\\''/g; 1s/^/'/; \$s/\$/'/"
}

write_assignment() {
  key="$1"
  value="$2"
  printf '%s=' "$key"
  shell_quote "$value"
  printf '\n'
}

write_secret_file() {
  service="$1"
  target_key="$2"
  value="$3"
  secret_dir="$RUNTIME_DIR/secrets/$service"
  target_path="$secret_dir/$target_key"
  tmp_path="$target_path.tmp"

  mkdir -p "$secret_dir"

  if [ -z "$value" ]; then
    rm -f "$target_path" "$tmp_path"
    return 0
  fi

  printf '%s' "$value" > "$tmp_path"
  chmod 600 "$tmp_path"
  mv "$tmp_path" "$target_path"
}

read_first_value() {
  path_spec="$1"
  source_key="$2"
  OLD_IFS="$IFS"
  IFS='|'
  set -- $path_spec
  IFS="$OLD_IFS"

  for path in "$@"; do
    value="$(vault kv get -field="$source_key" "$path" 2>/dev/null || true)"
    if [ -n "$value" ]; then
      printf '%s' "$value"
      return 0
    fi
  done

  return 0
}

write_key() {
  path_spec="$1"
  source_key="$2"
  target_key="$3"
  outfile="$4"
  value="$(read_first_value "$path_spec" "$source_key")"
  write_assignment "$target_key" "$value" >> "$outfile"
}

render_env_file() {
  service="$1"
  path="$2"
  key_specs="$3"
  delivery_mode="${4:-env}"
  tmp_file="$RUNTIME_DIR/$service.env.tmp"
  out_file="$RUNTIME_DIR/$service.env"

  cat "$HEADER_FILE" > "$tmp_file"
  write_assignment "SERVICE_NAME" "$service" >> "$tmp_file"
  write_assignment "VAULT_SECRET_PATH" "$path" >> "$tmp_file"

  for spec in $key_specs; do
    case "$spec" in
      *=*)
        source_key="${spec%%=*}"
        target_key="${spec#*=}"
        ;;
      *)
        source_key="$spec"
        target_key="$spec"
        ;;
    esac
    value="$(read_first_value "$path" "$source_key")"
    if [ "$delivery_mode" = "file" ]; then
      write_secret_file "$service" "$target_key" "$value"
      if [ -n "$value" ]; then
        write_assignment "${target_key}_FILE" "$RUNTIME_DIR/secrets/$service/$target_key" >> "$tmp_file"
      fi
    else
      write_assignment "$target_key" "$value" >> "$tmp_file"
    fi
  done

  mv "$tmp_file" "$out_file"
}

render_all() {
  render_env_file \
    "mega-orchestrator" \
    "secret/orchestration/mega-orchestrator|secret/orchestration/internal-auth" \
    "OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY PERPLEXITY_API_KEY MARKETPLACE_JWT_TOKEN JWT_SECRET" \
    "file"

  render_env_file \
    "perplexity-hub" \
    "secret/orchestration/perplexity-hub" \
    "PERPLEXITY_API_KEY OPENAI_API_KEY" \
    "file"

  render_env_file \
    "advanced-memory-mcp" \
    "secret/orchestration/advanced-memory-mcp" \
    "EMBEDDING_PROVIDER GENERATION_PROVIDER LOCAL_EMBEDDING_MODEL GEMINI_API_KEY GEMINI_EMBED_MODEL OLLAMA_BASE_URL OLLAMA_EMBED_MODEL OLLAMA_CHAT_MODEL OPENAI_COMPAT_BASE_URL OPENAI_COMPAT_API_KEY OPENAI_COMPAT_EMBED_MODEL OPENAI_COMPAT_CHAT_MODEL INCEPTION_API_KEY INCEPTION_BASE_URL INCEPTION_MODEL" \
    "file"

  render_env_file \
    "zen-mcp-server" \
    "secret/orchestration/zen-mcp-server" \
    "DEFAULT_MODEL OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY GOOGLE_API_KEY XAI_API_KEY OPENROUTER_API_KEY DIAL_API_KEY DIAL_API_HOST DIAL_API_VERSION CUSTOM_API_URL CUSTOM_API_KEY CUSTOM_MODEL_NAME DISABLED_TOOLS MAX_MCP_OUTPUT_TOKENS" \
    "file"

  render_env_file \
    "common-mcp" \
    "secret/orchestration/common-mcp" \
    "OPENAI_API_KEY ANTHROPIC_API_KEY GEMINI_API_KEY NOTION_API_KEY" \
    "file"

  render_env_file \
    "gmail-mcp" \
    "secret/orchestration/gmail-mcp" \
    "EMAIL_ADDRESS EMAIL_PASSWORD IMAP_SERVER SMTP_SERVER SMTP_PORT" \
    "file"

  render_env_file \
    "security-mcp" \
    "secret/orchestration/internal-auth" \
    "JWT_SECRET=JWT_SECRET_KEY" \
    "file"

  render_env_file \
    "marketplace-mcp" \
    "secret/orchestration/internal-auth" \
    "JWT_SECRET" \
    "file"

}

load_token
wait_for_vault

while true; do
  render_all
  sleep "$INTERVAL"
done
