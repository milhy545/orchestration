#!/usr/bin/env bash
set -euo pipefail

SECURITY_MCP_URL="${SECURITY_MCP_URL:-http://localhost:7008}"
USERNAME="${1:-market-client}"
EXPIRE_MINUTES="${2:-120}"
EXPORT_FILE=""

if [[ "${3:-}" == "--export-file" && -n "${4:-}" ]]; then
  EXPORT_FILE="$4"
fi

PAYLOAD=$(cat <<JSON
{"username":"${USERNAME}","permissions":["market:read"],"expire_minutes":${EXPIRE_MINUTES}}
JSON
)

RESPONSE=$(curl -fsS \
  -H "Content-Type: application/json" \
  -X POST \
  -d "$PAYLOAD" \
  "${SECURITY_MCP_URL}/tools/jwt_token")

TOKEN=$(python3 - <<'PY' "$RESPONSE"
import json
import sys
obj = json.loads(sys.argv[1])
print(obj.get("access_token", ""))
PY
)

if [[ -z "$TOKEN" ]]; then
  echo "Failed to mint marketplace token" >&2
  exit 1
fi

if [[ -n "$EXPORT_FILE" ]]; then
  mkdir -p "$(dirname "$EXPORT_FILE")"
  {
    echo "export MARKETPLACE_JWT_TOKEN=$TOKEN"
    echo "export MARKET_BASE_URL=${MARKET_BASE_URL:-http://localhost:7034}"
  } > "$EXPORT_FILE"
  chmod 600 "$EXPORT_FILE"
  echo "Token exported to $EXPORT_FILE"
else
  echo "MARKETPLACE_JWT_TOKEN=$TOKEN"
fi
