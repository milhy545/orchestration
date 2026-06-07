#!/usr/bin/env bash
set -euo pipefail

# Sync marketplace catalog from Milhy-PC to HAS
# This script should be run from Milhy-PC

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CATALOG_DIR="$PROJECT_DIR/catalog"

HAS_HOST="HAS"
HAS_PORT="2222"
HAS_SSH_KEY="$HOME/.ssh/unified_ecosystem_key_2026"
HAS_CATALOG_PATH="/home/orchestration/mcp-servers/marketplace-mcp/catalog"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[sync]${NC} $*"; }
warn() { echo -e "${YELLOW}[sync]${NC} $*"; }
error() { echo -e "${RED}[sync]${NC} $*" >&2; }

# Step 1: Run local scanner
log "Step 1: Running skill scanner on Milhy-PC..."
python3 "$SCRIPT_DIR/skill-scanner.py"

# Step 2: Verify catalog exists
if [ ! -f "$CATALOG_DIR/skills-index.json" ]; then
    error "Catalog not found at $CATALOG_DIR/skills-index.json"
    exit 1
fi

# Step 3: Sync catalog to HAS
log "Step 2: Syncing catalog to HAS..."
rsync -avz -e "ssh -i $HAS_SSH_KEY -p $HAS_PORT" \
  "$CATALOG_DIR/" \
  "$HAS_HOST:$HAS_CATALOG_PATH/"

# Step 4: Rebuild marketplace-mcp container on HAS
log "Step 3: Rebuilding marketplace-mcp container on HAS..."
ssh -i "$HAS_SSH_KEY" -p "$HAS_PORT" "$HAS_HOST" << 'EOF'
cd /home/orchestration
docker compose build marketplace-mcp
docker compose up -d marketplace-mcp
sleep 3
docker compose ps marketplace-mcp
EOF

# Step 5: Verify marketplace is running
log "Step 4: Verifying marketplace on HAS..."
sleep 2
if curl -s http://192.168.0.58:7034/health >/dev/null 2>&1; then
    log "✅ Marketplace is running on HAS!"
    curl -s http://192.168.0.58:7034/health | python3 -m json.tool
else
    warn "Marketplace might still be starting. Check: http://192.168.0.58:7034/health"
fi

log "✅ Sync complete!"
