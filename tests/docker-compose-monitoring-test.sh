#!/bin/bash
#
# Docker Compose Monitoring Stack Test
# Tests monitoring services configuration in docker-compose.yml
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"

echo "=========================================="
echo "  Docker Compose Monitoring Test"
echo "=========================================="
echo ""

FAILURES=0

# Test 1: Validate docker-compose.yml syntax
echo "Test 1: Validating docker-compose.yml syntax..."
if python3 -c "import yaml; yaml.safe_load(open('$COMPOSE_FILE'))" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} docker-compose.yml is valid YAML"
else
    echo -e "${RED}✗${NC} docker-compose.yml has invalid YAML syntax"
    ((FAILURES++))
fi

# Test 2: Check monitoring services are defined
echo ""
echo "Test 2: Checking monitoring services are defined..."

SERVICES=("prometheus" "grafana" "loki" "promtail")
for service in "${SERVICES[@]}"; do
    if grep -q "^  $service:" "$COMPOSE_FILE"; then
        echo -e "${GREEN}✓${NC} Service '$service' is defined"
    else
        echo -e "${RED}✗${NC} Service '$service' is NOT defined"
        ((FAILURES++))
    fi
done

# Test 3: Check volume mounts
echo ""
echo "Test 3: Checking volume mounts..."

# Prometheus volume
if grep -A10 "^  prometheus:" "$COMPOSE_FILE" | grep -q "monitoring/prometheus/prometheus.yml"; then
    echo -e "${GREEN}✓${NC} Prometheus config volume is mounted"
else
    echo -e "${RED}✗${NC} Prometheus config volume is NOT mounted"
    ((FAILURES++))
fi

# Grafana provisioning volume
if grep -A10 "^  grafana:" "$COMPOSE_FILE" | grep -q "monitoring/grafana/provisioning"; then
    echo -e "${GREEN}✓${NC} Grafana provisioning volume is mounted"
else
    echo -e "${RED}✗${NC} Grafana provisioning volume is NOT mounted"
    ((FAILURES++))
fi

# Loki config volume
if grep -A10 "^  loki:" "$COMPOSE_FILE" | grep -q "monitoring/loki/loki-config.yml"; then
    echo -e "${GREEN}✓${NC} Loki config volume is mounted"
else
    echo -e "${RED}✗${NC} Loki config volume is NOT mounted"
    ((FAILURES++))
fi

# Promtail config volume
if grep -A10 "^  promtail:" "$COMPOSE_FILE" | grep -q "monitoring/promtail/promtail-config.yml"; then
    echo -e "${GREEN}✓${NC} Promtail config volume is mounted"
else
    echo -e "${RED}✗${NC} Promtail config volume is NOT mounted"
    ((FAILURES++))
fi

# Test 4: Check persistent volumes
echo ""
echo "Test 4: Checking persistent volumes..."

VOLUMES=("prometheus-data" "grafana-data" "loki-data")
for volume in "${VOLUMES[@]}"; do
    if grep -q "^  $volume:" "$COMPOSE_FILE"; then
        echo -e "${GREEN}✓${NC} Volume '$volume' is defined"
    else
        echo -e "${RED}✗${NC} Volume '$volume' is NOT defined"
        ((FAILURES++))
    fi
done

# Test 5: Check port mappings
echo ""
echo "Test 5: Checking port mappings..."

declare -A PORT_MAP=(
    ["prometheus"]="7028:9090"
    ["grafana"]="7031:3000"
    ["loki"]="7032:3100"
)

for service in "${!PORT_MAP[@]}"; do
    port="${PORT_MAP[$service]}"
    if grep -A10 "^  $service:" "$COMPOSE_FILE" | grep -q "\"$port\""; then
        echo -e "${GREEN}✓${NC} $service port mapping: $port"
    else
        echo -e "${RED}✗${NC} $service port mapping incorrect (expected: $port)"
        ((FAILURES++))
    fi
done

# Test 6: Check dependencies
echo ""
echo "Test 6: Checking service dependencies..."

# Grafana should depend on prometheus and loki
GRAFANA_DEPS=$(grep -A20 "^  grafana:" "$COMPOSE_FILE" | grep -A5 "depends_on:")
if echo "$GRAFANA_DEPS" | grep -q "prometheus" && echo "$GRAFANA_DEPS" | grep -q "loki"; then
    echo -e "${GREEN}✓${NC} Grafana depends on prometheus and loki"
else
    echo -e "${RED}✗${NC} Grafana dependencies are incorrect"
    ((FAILURES++))
fi

# Promtail should depend on loki
if grep -A15 "^  promtail:" "$COMPOSE_FILE" | grep -A5 "depends_on:" | grep -q "loki"; then
    echo -e "${GREEN}✓${NC} Promtail depends on loki"
else
    echo -e "${RED}✗${NC} Promtail dependency on loki is missing"
    ((FAILURES++))
fi

# Test 7: Check environment variables
echo ""
echo "Test 7: Checking environment variables..."

# Grafana admin credentials
if grep -A15 "^  grafana:" "$COMPOSE_FILE" | grep -q "GF_SECURITY_ADMIN_USER"; then
    echo -e "${GREEN}✓${NC} Grafana admin user is configured"
else
    echo -e "${RED}✗${NC} Grafana admin user is NOT configured"
    ((FAILURES++))
fi

if grep -A15 "^  grafana:" "$COMPOSE_FILE" | grep -q "GF_SECURITY_ADMIN_PASSWORD"; then
    echo -e "${GREEN}✓${NC} Grafana admin password is configured"
else
    echo -e "${RED}✗${NC} Grafana admin password is NOT configured"
    ((FAILURES++))
fi

# Test 8: Check network
echo ""
echo "Test 8: Checking network configuration..."

for service in "${SERVICES[@]}"; do
    if grep -A20 "^  $service:" "$COMPOSE_FILE" | grep -A2 "networks:" | grep -q "mcp-network"; then
        echo -e "${GREEN}✓${NC} $service is on mcp-network"
    else
        echo -e "${RED}✗${NC} $service is NOT on mcp-network"
        ((FAILURES++))
    fi
done

# Summary
echo ""
echo "=========================================="
echo "  Test Summary"
echo "=========================================="
echo ""

if [ $FAILURES -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "Docker compose monitoring configuration is valid."
    exit 0
else
    echo -e "${RED}✗ $FAILURES test(s) failed${NC}"
    echo ""
    echo "Please fix the issues above."
    exit 1
fi
