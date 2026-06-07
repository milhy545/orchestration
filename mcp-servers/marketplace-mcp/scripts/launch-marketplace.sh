#!/usr/bin/env bash
set -euo pipefail

# Marketplace MCP Launcher
# Starts the marketplace service on port 7034 (host) -> 8000 (container)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CATALOG_DIR="$PROJECT_DIR/catalog"
VENV_DIR="$PROJECT_DIR/.venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[marketplace]${NC} $*"; }
warn() { echo -e "${YELLOW}[marketplace]${NC} $*"; }
error() { echo -e "${RED}[marketplace]${NC} $*" >&2; }

# Check if already running
check_running() {
    if curl -s http://localhost:7034/health >/dev/null 2>&1; then
        log "Marketplace is already running on port 7034"
        curl -s http://localhost:7034/health | python3 -m json.tool
        return 0
    fi
    return 1
}

# Setup virtual environment
setup_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    log "Installing dependencies..."
    "$VENV_DIR/bin/pip" install -q -r "$PROJECT_DIR/requirements.txt"
}

# Run skill scanner
run_scanner() {
    log "Running skill scanner..."
    python3 "$SCRIPT_DIR/skill-scanner.py"
}

# Start the server
start_server() {
    log "Starting marketplace-mcp on port 7034..."
    
    # Set environment variables
    export MARKET_CATALOG_PATH="$CATALOG_DIR"
    export MARKET_BASE_URL="http://localhost:7034"
    export JWT_SECRET="${JWT_SECRET:-marketplace-dev-secret}"
    
    # Start with uvicorn
    cd "$PROJECT_DIR"
    "$VENV_DIR/bin/uvicorn" main:app --host 0.0.0.0 --port 7034 --reload &
    
    # Wait for startup
    sleep 2
    
    if curl -s http://localhost:7034/health >/dev/null 2>&1; then
        log "✅ Marketplace started successfully!"
        log "   Health: http://localhost:7034/health"
        log "   Tools: http://localhost:7034/tools/list"
        log "   Skills: http://localhost:7034/skills/v1/index"
        return 0
    else
        error "Failed to start marketplace"
        return 1
    fi
}

# Main
main() {
    log "Marketplace MCP Launcher"
    
    # Check if already running
    if check_running; then
        return 0
    fi
    
    # Setup environment
    setup_venv
    
    # Run scanner to populate catalog
    run_scanner
    
    # Start server
    start_server
}

main "$@"
