#!/bin/bash
# MCP Server Installer
# Usage: ./scripts/install-mcp.sh <github_url> <port> [service_name]
#
# Examples:
#   ./scripts/install-mcp.sh https://github.com/user/some-mcp 7033
#   ./scripts/install-mcp.sh https://github.com/user/some-mcp 7033 custom-name

set -euo pipefail

GITHUB_URL="${1:?Usage: $0 <github_url> <port> [service_name]}"
PORT="${2:?Usage: $0 <github_url> <port> [service_name]}"
SERVICE_NAME="${3:-$(basename "$GITHUB_URL" .git)}"
TARGET_DIR="mcp-servers/${SERVICE_NAME}"

echo "📦 Installing MCP server: ${SERVICE_NAME}"
echo "   Source: ${GITHUB_URL}"
echo "   Port: ${PORT}"
echo "   Target: ${TARGET_DIR}"
echo ""

# 1. Clone
if [ -d "$TARGET_DIR" ]; then
    echo "⚠️  Directory ${TARGET_DIR} already exists. Skipping clone."
else
    echo "🔄 Cloning repository..."
    git clone --depth 1 "$GITHUB_URL" "$TARGET_DIR"
    rm -rf "${TARGET_DIR}/.git"
    echo "✅ Cloned successfully"
fi

# 2. Detect project type and create Dockerfile if missing
if [ ! -f "${TARGET_DIR}/Dockerfile" ]; then
    echo "📄 No Dockerfile found. Detecting project type..."

    if [ -f "${TARGET_DIR}/requirements.txt" ] || [ -f "${TARGET_DIR}/pyproject.toml" ] || [ -f "${TARGET_DIR}/setup.py" ]; then
        echo "   Detected: Python project"
        cat > "${TARGET_DIR}/Dockerfile" << 'DOCKERFILE'
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt* pyproject.toml* setup.py* ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null \
    || pip install --no-cache-dir -e . 2>/dev/null \
    || pip install --no-cache-dir .
COPY . .
EXPOSE 8000
CMD ["python", "main.py"]
DOCKERFILE
        echo "✅ Created Python Dockerfile"

    elif [ -f "${TARGET_DIR}/package.json" ]; then
        echo "   Detected: Node.js project"
        cat > "${TARGET_DIR}/Dockerfile" << 'DOCKERFILE'
FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 8000
CMD ["node", "index.js"]
DOCKERFILE
        echo "✅ Created Node.js Dockerfile"

    else
        echo "⚠️  Unknown project type. Creating minimal Python Dockerfile."
        cat > "${TARGET_DIR}/Dockerfile" << 'DOCKERFILE'
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
EXPOSE 8000
CMD ["python", "main.py"]
DOCKERFILE
    fi
else
    echo "✅ Dockerfile already exists"
fi

# 3. Generate docker-compose entry
echo ""
echo "📋 Add this to docker-compose.yml:"
echo ""
echo "  ${SERVICE_NAME}:"
echo "    build:"
echo "      context: ./${TARGET_DIR}"
echo "      dockerfile: Dockerfile"
echo "    container_name: mcp-${SERVICE_NAME}"
echo "    ports:"
echo "      - \"${PORT}:8000\""
echo "    environment:"
echo "      - MCP_SERVER_PORT=8000"
echo "    restart: unless-stopped"
echo "    networks:"
echo "      - mcp-network"
echo ""

# 4. Generate orchestrator registration
echo "📋 Add this to config/zen_coordinator.py MCP_SERVICES dict:"
echo ""
echo "    \"${SERVICE_NAME}\": {"
echo "        \"description\": \"${SERVICE_NAME} MCP Server\","
echo "        \"tools\": [],"
echo "        \"internal_port\": ${PORT},"
echo "        \"status\": \"unknown\","
echo "        \"container\": \"mcp-${SERVICE_NAME}\""
echo "    },"
echo ""

echo "🎉 Done! Review the suggested configurations above and add them manually."
echo "   Then run: docker-compose up -d ${SERVICE_NAME}"
