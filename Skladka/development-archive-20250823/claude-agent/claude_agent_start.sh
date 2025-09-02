#!/bin/bash
# HAS Claude Agent Startup Script
# Optimized for Home Automation Server deployment

AGENT_DIR="/home/orchestration/claude-agent"
VENV_PATH="$AGENT_DIR/venv"
LOG_FILE="$AGENT_DIR/logs/startup.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}🤖 HAS Claude Agent Startup${NC}"
echo "================================="

# Check if we're on HAS
HAS_HOSTNAME=$(hostname)
if [[ "$HAS_HOSTNAME" != *"home-automat"* ]]; then
    echo -e "${RED}❌ This script should run on HAS server only (detected: $HAS_HOSTNAME)${NC}"
    exit 1
fi

# Create logs directory
mkdir -p "$AGENT_DIR/logs"

# Log startup
echo "$(date): Starting HAS Claude Agent" >> "$LOG_FILE"

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}❌ Virtual environment not found at $VENV_PATH${NC}"
    echo -e "${YELLOW}Run setup first: python3 -m venv $VENV_PATH${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${BLUE}🔧 Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"
python -c "import anthropic, aiohttp, psutil, yaml" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Missing dependencies${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install anthropic aiohttp psutil pyyaml
fi

# Check agent files
if [ ! -f "$AGENT_DIR/haiku_agent.py" ]; then
    echo -e "${RED}❌ Agent file not found: $AGENT_DIR/haiku_agent.py${NC}"
    exit 1
fi

# Change to agent directory
cd "$AGENT_DIR"

# Resource check
echo -e "${BLUE}📊 Resource check...${NC}"
python -c "
from haiku_agent import HASClaudeAgent
agent = HASClaudeAgent()
res = agent.check_resource_usage()
print(f'RAM: {res[\"ram_used_mb\"]:.1f}MB ({res[\"ram_percent\"]:.1f}%)')
print(f'CPU: {res[\"cpu_percent\"]:.1f}%')
print(f'Status: {res[\"status\"]}')
"

echo -e "${GREEN}✅ HAS Claude Agent ready!${NC}"
echo ""
echo -e "${YELLOW}Usage options:${NC}"
echo "  python haiku_agent.py              # Interactive mode"
echo "  python haiku_agent.py health       # Health check"
echo "  python haiku_agent.py test         # Test mode"
echo ""
echo -e "${BLUE}Agent directory: $AGENT_DIR${NC}"
echo -e "${BLUE}Log file: $LOG_FILE${NC}"

# Parse command line arguments
case "${1:-interactive}" in
    "health")
        echo -e "${BLUE}🩺 Running health check...${NC}"
        python haiku_agent.py health
        ;;
    "test")
        echo -e "${BLUE}🧪 Running test mode...${NC}"
        python haiku_agent.py test
        ;;
    "interactive"|"")
        echo -e "${BLUE}🎮 Starting interactive mode...${NC}"
        echo -e "${YELLOW}Commands: 'health', 'mcp tool_name', 'quit'${NC}"
        python haiku_agent.py
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Valid options: health, test, interactive"
        exit 1
        ;;
esac