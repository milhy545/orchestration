#!/bin/bash
#
# Monitoring Stack Health Check
# Validates Prometheus, Grafana, Loki configuration and connectivity
#

set -e -o pipefail
# Allow arithmetic expressions to return 0 without exiting
set +e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

if ! python3 - <<'PY' >/dev/null 2>&1
import yaml
PY
then
    echo -e "${RED}⛔ BLOCKED${NC} PyYAML is required (install with: pip install pyyaml)"
    exit 2
fi

echo "=========================================="
echo "  MCP Monitoring Stack Health Check"
echo "=========================================="
echo ""

ERRORS=0
WARNINGS=0
DOCKER_COMPOSE="$PROJECT_ROOT/docker-compose.yml"

compose_check() {
    local check_type=$1
    shift

    python3 - "$DOCKER_COMPOSE" "$check_type" "$@" <<'PY'
import sys
import yaml

compose_file = sys.argv[1]
check_type = sys.argv[2]
args = sys.argv[3:]

try:
    with open(compose_file, encoding="utf-8") as f:
        compose = yaml.safe_load(f) or {}
except (yaml.YAMLError, FileNotFoundError):
    sys.exit(1)

if not isinstance(compose, dict):
    sys.exit(1)

services = compose.get("services")
volumes = compose.get("volumes")
if not isinstance(services, dict):
    services = {}
if not isinstance(volumes, dict):
    volumes = {}

result = False

if check_type == "service_exists":
    result = args[0] in services
elif check_type == "volume_exists":
    result = args[0] in volumes
elif check_type == "service_has_port":
    service, expected = args
    service_cfg = services.get(service, {})
    ports = service_cfg.get("ports") if isinstance(service_cfg, dict) else []
    if isinstance(ports, list):
        result = any(str(port) == expected for port in ports)

sys.exit(0 if result else 1)
PY
}

# Function to check file exists
check_file() {
    local file=$1
    local description=$2

    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $description exists: $file"
        return 0
    else
        echo -e "${RED}✗${NC} $description missing: $file"
        ((ERRORS++))
        return 1
    fi
}

# Function to validate YAML
validate_yaml() {
    local file=$1
    local description=$2

    if python3 -c "import yaml; yaml.safe_load(open('$file'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description YAML is valid"
        return 0
    else
        echo -e "${RED}✗${NC} $description YAML is invalid"
        ((ERRORS++))
        return 1
    fi
}

# Function to validate JSON
validate_json() {
    local file=$1
    local description=$2

    if python3 -c "import json; json.load(open('$file'))" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $description JSON is valid"
        return 0
    else
        echo -e "${RED}✗${NC} $description JSON is invalid"
        ((ERRORS++))
        return 1
    fi
}

echo "1. Checking Configuration Files"
echo "-----------------------------------"

# Prometheus
check_file "$MONITORING_DIR/prometheus/prometheus.yml" "Prometheus config"
validate_yaml "$MONITORING_DIR/prometheus/prometheus.yml" "Prometheus config"

# Loki
check_file "$MONITORING_DIR/loki/loki-config.yml" "Loki config"
validate_yaml "$MONITORING_DIR/loki/loki-config.yml" "Loki config"

# Promtail
check_file "$MONITORING_DIR/promtail/promtail-config.yml" "Promtail config"
validate_yaml "$MONITORING_DIR/promtail/promtail-config.yml" "Promtail config"

# Grafana datasources
check_file "$MONITORING_DIR/grafana/provisioning/datasources/datasources.yml" "Grafana datasources"
validate_yaml "$MONITORING_DIR/grafana/provisioning/datasources/datasources.yml" "Grafana datasources"

# Grafana dashboards provisioning
check_file "$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml" "Grafana dashboard provisioning"
validate_yaml "$MONITORING_DIR/grafana/provisioning/dashboards/dashboards.yml" "Grafana dashboard provisioning"

# Grafana dashboard
check_file "$MONITORING_DIR/grafana/provisioning/dashboards/mcp-overview.json" "Grafana MCP dashboard"
validate_json "$MONITORING_DIR/grafana/provisioning/dashboards/mcp-overview.json" "Grafana MCP dashboard"

echo ""
echo "2. Checking Prometheus Configuration"
echo "-----------------------------------"

# Check for required scrape jobs
REQUIRED_JOBS=("prometheus" "zen-coordinator" "mcp-core-services" "mcp-ai-services" "mcp-db-wrappers" "mcp-mqtt")

for job in "${REQUIRED_JOBS[@]}"; do
    if grep -q "job_name: '$job'" "$MONITORING_DIR/prometheus/prometheus.yml"; then
        echo -e "${GREEN}✓${NC} Job configured: $job"
    else
        echo -e "${YELLOW}⚠${NC} Job missing: $job"
        ((WARNINGS++))
    fi
done

# Count total scrape targets
TARGET_COUNT=$(grep -c "targets:" "$MONITORING_DIR/prometheus/prometheus.yml" || echo "0")
echo -e "${GREEN}✓${NC} Total scrape target groups: $TARGET_COUNT"

echo ""
echo "3. Checking Service Instrumentation"
echo "-----------------------------------"

# Check if services have prometheus-fastapi-instrumentator in requirements
SERVICES=(
    "terminal-mcp" "filesystem-mcp" "database-mcp" "git-mcp" "memory-mcp" "system-mcp"
    "config-mcp" "log-mcp" "network-mcp" "security-mcp"
    "postgresql-mcp" "redis-mcp" "qdrant-mcp" "mqtt-mcp" "research-mcp" "webm-transcriber"
)

INSTRUMENTED=0
NOT_INSTRUMENTED=0

for service in "${SERVICES[@]}"; do
    REQ_FILE="$PROJECT_ROOT/mcp-servers/$service/requirements.txt"
    MAIN_FILE="$PROJECT_ROOT/mcp-servers/$service/main.py"

    if [ -f "$REQ_FILE" ] && grep -q "prometheus-fastapi-instrumentator" "$REQ_FILE"; then
        if [ -f "$MAIN_FILE" ] && grep -q "Instrumentator" "$MAIN_FILE"; then
            echo -e "${GREEN}✓${NC} $service: instrumented"
            ((INSTRUMENTED++))
        else
            echo -e "${YELLOW}⚠${NC} $service: dependency added but not instrumented in code"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}✗${NC} $service: not instrumented"
        ((NOT_INSTRUMENTED++))
        ((ERRORS++))
    fi
done

echo ""
echo "Instrumentation summary: $INSTRUMENTED/${#SERVICES[@]} services instrumented"

echo ""
echo "4. Checking Docker Compose Configuration"
echo "-----------------------------------"

# Check monitoring services defined
MONITORING_SERVICES=("prometheus" "grafana" "loki" "promtail")

for service in "${MONITORING_SERVICES[@]}"; do
    if compose_check service_exists "$service"; then
        echo -e "${GREEN}✓${NC} Service defined: $service"
    else
        echo -e "${RED}✗${NC} Service missing: $service"
        ((ERRORS++))
    fi
done

# Check volumes defined
VOLUMES=("prometheus-data" "grafana-data" "loki-data")

for volume in "${VOLUMES[@]}"; do
    if compose_check volume_exists "$volume"; then
        echo -e "${GREEN}✓${NC} Volume defined: $volume"
    else
        echo -e "${RED}✗${NC} Volume missing: $volume"
        ((ERRORS++))
    fi
done

echo ""
echo "5. Checking Port Mappings"
echo "-----------------------------------"

# Expected ports
declare -A EXPECTED_PORTS=(
    ["prometheus"]="7028:9090"
    ["grafana"]="7031:3000"
    ["loki"]="7032:3100"
)

for service in "${!EXPECTED_PORTS[@]}"; do
    expected="${EXPECTED_PORTS[$service]}"
    if compose_check service_has_port "$service" "$expected"; then
        echo -e "${GREEN}✓${NC} $service port mapping: $expected"
    else
        echo -e "${RED}✗${NC} $service port mapping incorrect (expected: $expected)"
        ((ERRORS++))
    fi
done

echo ""
echo "=========================================="
echo "  Health Check Summary"
echo "=========================================="
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo ""
    echo "Monitoring stack is properly configured."
    echo ""
    echo "To start monitoring:"
    echo "  docker-compose up -d prometheus grafana loki promtail"
    echo ""
    echo "Access points:"
    echo "  - Grafana:    http://localhost:7031 (admin/admin)"
    echo "  - Prometheus: http://localhost:7028"
    echo "  - Loki:       http://localhost:7032"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Checks passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Monitoring stack should work, but review warnings above."
    exit 0
else
    echo -e "${RED}✗ Health check failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors above before deploying monitoring stack."
    exit 1
fi
