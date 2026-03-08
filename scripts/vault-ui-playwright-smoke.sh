#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_URL="${1:-http://127.0.0.1:10000}"

docker run --rm \
  --network host \
  -v "$ROOT_DIR/services/vault-secrets-ui/tests:/tests:ro" \
  mcr.microsoft.com/playwright:v1.52.0-noble \
  bash -lc "mkdir -p /tmp/pw-smoke && cd /tmp/pw-smoke && cp /tests/playwright_smoke.mjs ./playwright_smoke.mjs && npm init -y >/dev/null 2>&1 && npm install playwright@1.52.0 >/dev/null 2>&1 && node ./playwright_smoke.mjs '$TARGET_URL'"
