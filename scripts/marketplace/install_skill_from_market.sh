#!/usr/bin/env bash
set -euo pipefail

SKILL=""
VERSION=""
MARKET_URL="${MARKET_BASE_URL:-http://localhost:7034}"
TOKEN="${MARKETPLACE_JWT_TOKEN:-}"
TOKEN_FILE=""
DEST="${HOME}/.codex/skills"
OVERWRITE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill)
      SKILL="$2"
      shift 2
      ;;
    --version)
      VERSION="$2"
      shift 2
      ;;
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
    --dest)
      DEST="$2"
      shift 2
      ;;
    --overwrite)
      OVERWRITE=1
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

if [[ -z "$SKILL" ]]; then
  echo "Missing required --skill <name>" >&2
  exit 1
fi
if [[ -z "$TOKEN" ]]; then
  echo "Missing token. Provide --token or --token-file." >&2
  exit 1
fi

mkdir -p "$DEST"

if [[ -n "$VERSION" ]]; then
  PAYLOAD=$(cat <<JSON
{"client":"codex-cli","install_root":"$DEST","skills":[{"name":"$SKILL","version":"$VERSION"}]}
JSON
)
else
  PAYLOAD=$(cat <<JSON
{"client":"codex-cli","install_root":"$DEST","skills":[{"name":"$SKILL"}]}
JSON
)
fi

PLAN=$(curl -fsS \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "$PAYLOAD" \
  "$MARKET_URL/skills/v1/install-plan")

PLAN_LINE=$(python3 - "$PLAN" <<'PY'
import json
import sys
plan = json.loads(sys.argv[1])
resolved = plan.get("resolved_packages", [])
if not resolved:
    raise SystemExit("No resolved packages in install plan")
pkg = resolved[0]
name = pkg["name"]
version = pkg["version"]
sha = pkg.get("sha256", "")
print(f"{name}\t{version}\t{sha}")
PY
)

RESOLVED_NAME=$(echo "$PLAN_LINE" | cut -f1)
RESOLVED_VERSION=$(echo "$PLAN_LINE" | cut -f2)
RESOLVED_SHA=$(echo "$PLAN_LINE" | cut -f3)
DOWNLOAD_URL="$MARKET_URL/skills/v1/packages/$RESOLVED_NAME/$RESOLVED_VERSION/download"

TMP_ARCHIVE=$(mktemp)
TMP_EXTRACT=$(mktemp -d)
trap 'rm -f "$TMP_ARCHIVE"; rm -rf "$TMP_EXTRACT"' EXIT

curl -fLsS \
  -H "Authorization: Bearer $TOKEN" \
  "$DOWNLOAD_URL" \
  -o "$TMP_ARCHIVE"

if [[ -n "$RESOLVED_SHA" ]]; then
  ACTUAL_SHA=$(sha256sum "$TMP_ARCHIVE" | awk '{print $1}')
  if [[ "$ACTUAL_SHA" != "$RESOLVED_SHA" ]]; then
    echo "Checksum mismatch: expected $RESOLVED_SHA got $ACTUAL_SHA" >&2
    exit 1
  fi
fi

tar -xzf "$TMP_ARCHIVE" -C "$TMP_EXTRACT"

TARGET="$DEST/$RESOLVED_NAME"
if [[ -e "$TARGET" && "$OVERWRITE" -ne 1 ]]; then
  echo "Target exists: $TARGET (use --overwrite to replace)" >&2
  exit 1
fi

if [[ -e "$TARGET" && "$OVERWRITE" -eq 1 ]]; then
  rm -rf "$TARGET"
fi

if [[ -d "$TMP_EXTRACT/$RESOLVED_NAME" ]]; then
  mkdir -p "$TARGET"
  cp -a "$TMP_EXTRACT/$RESOLVED_NAME"/. "$TARGET"/
else
  mkdir -p "$TARGET"
  cp -a "$TMP_EXTRACT"/. "$TARGET"/
fi

echo "Installed skill: $RESOLVED_NAME@$RESOLVED_VERSION -> $TARGET"
