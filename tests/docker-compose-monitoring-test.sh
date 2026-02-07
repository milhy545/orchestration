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

compose_check() {
    local check_type=$1
    shift

    python3 - "$COMPOSE_FILE" "$check_type" "$@" <<'PY'
import sys
import yaml

compose_file = sys.argv[1]
check_type = sys.argv[2]
args = sys.argv[3:]

try:
    with open(compose_file, encoding="utf-8") as f:
        compose = yaml.safe_load(f) or {}
except Exception:
    sys.exit(1)

if not isinstance(compose, dict):
    sys.exit(1)

services = compose.get("services")
volumes = compose.get("volumes")
if not isinstance(services, dict):
    services = {}
if not isinstance(volumes, dict):
    volumes = {}


def normalize_list_or_dict(value):
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.keys())
    return []


def env_has_key(service_env, key):
    if isinstance(service_env, dict):
        return key in service_env
    if isinstance(service_env, list):
        return any(isinstance(item, str) and item.split("=", 1)[0] == key for item in service_env)
    return False


result = False

if check_type == "service_exists":
    service = args[0]
    result = service in services
elif check_type == "service_has_volume_substring":
    service, expected = args
    service_cfg = services.get(service, {})
    mounts = service_cfg.get("volumes") if isinstance(service_cfg, dict) else []
    if isinstance(mounts, list):
        result = any(expected in str(mount) for mount in mounts)
elif check_type == "volume_exists":
    volume = args[0]
    result = volume in volumes
elif check_type == "service_has_port":
    service, expected = args
    service_cfg = services.get(service, {})
    ports = service_cfg.get("ports") if isinstance(service_cfg, dict) else []
    if isinstance(ports, list):
        result = any(str(port) == expected for port in ports)
elif check_type == "service_depends_on":
    service, dependency = args
    service_cfg = services.get(service, {})
    depends_on = service_cfg.get("depends_on") if isinstance(service_cfg, dict) else []
    deps = normalize_list_or_dict(depends_on)
    result = dependency in deps
elif check_type == "service_has_env_key":
    service, env_key = args
    service_cfg = services.get(service, {})
    environment = service_cfg.get("environment") if isinstance(service_cfg, dict) else []
    result = env_has_key(environment, env_key)
elif check_type == "service_on_network":
    service, network = args
    service_cfg = services.get(service, {})
    networks = service_cfg.get("networks") if isinstance(service_cfg, dict) else []
    result = network in normalize_list_or_dict(networks)

sys.exit(0 if result else 1)
PY
}

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
    if compose_check service_exists "$service"; then
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
if compose_check service_has_volume_substring "prometheus" "monitoring/prometheus/prometheus.yml"; then
    echo -e "${GREEN}✓${NC} Prometheus config volume is mounted"
else
    echo -e "${RED}✗${NC} Prometheus config volume is NOT mounted"
    ((FAILURES++))
fi

# Grafana provisioning volume
if compose_check service_has_volume_substring "grafana" "monitoring/grafana/provisioning"; then
    echo -e "${GREEN}✓${NC} Grafana provisioning volume is mounted"
else
    echo -e "${RED}✗${NC} Grafana provisioning volume is NOT mounted"
    ((FAILURES++))
fi

# Loki config volume
if compose_check service_has_volume_substring "loki" "monitoring/loki/loki-config.yml"; then
    echo -e "${GREEN}✓${NC} Loki config volume is mounted"
else
    echo -e "${RED}✗${NC} Loki config volume is NOT mounted"
    ((FAILURES++))
fi

# Promtail config volume
if compose_check service_has_volume_substring "promtail" "monitoring/promtail/promtail-config.yml"; then
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
    if compose_check volume_exists "$volume"; then
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
    if compose_check service_has_port "$service" "$port"; then
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
if compose_check service_depends_on "grafana" "prometheus" && compose_check service_depends_on "grafana" "loki"; then
    echo -e "${GREEN}✓${NC} Grafana depends on prometheus and loki"
else
    echo -e "${RED}✗${NC} Grafana dependencies are incorrect"
    ((FAILURES++))
fi

# Promtail should depend on loki
if compose_check service_depends_on "promtail" "loki"; then
    echo -e "${GREEN}✓${NC} Promtail depends on loki"
else
    echo -e "${RED}✗${NC} Promtail dependency on loki is missing"
    ((FAILURES++))
fi

# Test 7: Check environment variables
echo ""
echo "Test 7: Checking environment variables..."

# Grafana admin credentials
if compose_check service_has_env_key "grafana" "GF_SECURITY_ADMIN_USER"; then
    echo -e "${GREEN}✓${NC} Grafana admin user is configured"
else
    echo -e "${RED}✗${NC} Grafana admin user is NOT configured"
    ((FAILURES++))
fi

if compose_check service_has_env_key "grafana" "GF_SECURITY_ADMIN_PASSWORD"; then
    echo -e "${GREEN}✓${NC} Grafana admin password is configured"
else
    echo -e "${RED}✗${NC} Grafana admin password is NOT configured"
    ((FAILURES++))
fi

# Test 8: Check network
echo ""
echo "Test 8: Checking network configuration..."

for service in "${SERVICES[@]}"; do
    if compose_check service_on_network "$service" "mcp-network"; then
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
