#!/usr/bin/env bash
set -euo pipefail

MARKET_URL="${MARKET_BASE_URL:-http://localhost:7034}"
TOKEN="${MARKETPLACE_JWT_TOKEN:-}"
PERSIST=0
TOKEN_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --market-url)
      MARKET_URL="$2"
      shift 2
      ;;
    --token)
      TOKEN="$2"
      shift 2
      ;;
    --token-file)
      TOKEN_FILE="$2"
      shift 2
      ;;
    --persist)
      PERSIST=1
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

if [[ -n "$TOKEN_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$TOKEN_FILE"
  TOKEN="${MARKETPLACE_JWT_TOKEN:-$TOKEN}"
fi

if [[ -z "$TOKEN" ]]; then
  echo "Missing token. Pass --token or --token-file." >&2
  exit 1
fi

CONFIG_DIR="$HOME/.config/orchestration-market"
mkdir -p "$CONFIG_DIR"
chmod 700 "$CONFIG_DIR"

cat > "$CONFIG_DIR/market.env" <<ENV
export MARKET_BASE_URL=$MARKET_URL
export MARKETPLACE_JWT_TOKEN=$TOKEN
ENV
chmod 600 "$CONFIG_DIR/market.env"

cat > "$CONFIG_DIR/codex-market.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
source "$HOME/.config/orchestration-market/market.env"
echo "Marketplace env loaded: $MARKET_BASE_URL"
SH
chmod 700 "$CONFIG_DIR/codex-market.sh"

if [[ "$PERSIST" -eq 1 ]]; then
  if ! grep -q "orchestration-market/market.env" "$HOME/.bashrc" 2>/dev/null; then
    {
      echo ""
      echo "# Orchestration Marketplace"
      echo "source \"$HOME/.config/orchestration-market/market.env\""
    } >> "$HOME/.bashrc"
    echo "Persisted marketplace env sourcing into ~/.bashrc"
  fi
fi

cat <<MSG
Marketplace configuration written:
  $CONFIG_DIR/market.env

Next steps:
1) source "$CONFIG_DIR/market.env"
2) Install skills via:
   scripts/marketplace/install_skill_from_market.sh --skill my-skills-export
MSG
