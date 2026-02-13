#\!/bin/bash
# Orchestration Service Chain Test Suite
# Target: Multi-service workflows via Zen Coordinator

echo '🔗 ORCHESTRATION WORKFLOW CHAIN TEST SUITE'
echo '==========================================='
echo "Start time: $(date)"
echo

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=tests/lib/e2e_preflight.sh
source "$PROJECT_ROOT/tests/lib/e2e_preflight.sh"

ZEN_URL='http://localhost:7000/mcp'
TEST_ID=$(date +%s)
PASS_COUNT=0
FAIL_COUNT=0
TOTAL_START_TIME=$(date +%s%3N)

# Helper functions
test_pass() {
    echo "✅ PASS: $1"
    PASS_COUNT=$((PASS_COUNT+1))
}

test_fail() {
    echo "❌ FAIL: $1"
    echo "   Details: $2"
    FAIL_COUNT=$((FAIL_COUNT+1))
}

measure_workflow_time() {
    local start=$(date +%s%3N)
    "$@"
    local end=$(date +%s%3N)
    echo $((end - start))
}

# Preflight checks

e2e_require_cmd curl
e2e_require_http "ZEN Coordinator health" "http://localhost:7000/health"

echo "✅ Preflight passed: ZEN Coordinator is reachable"
echo
echo '📊 PRE-TEST: Service Discovery'
echo '=============================='

# Check all required services
echo '🔍 Checking Zen Coordinator status...'
ZEN_STATUS=$(curl -s http://localhost:7000/health)
if echo "$ZEN_STATUS" | grep -q '"status": "healthy"'; then
    test_pass "Zen Coordinator is healthy"
    echo "   Services: $(echo "$ZEN_STATUS" | grep -o '"services_running": [0-9]*' | grep -o '[0-9]*') running"
else
    test_fail "Zen Coordinator not responding" "$ZEN_STATUS"
    exit 1
fi

echo
echo '🔗 WORKFLOW 1: System Information Chain'
echo '======================================'
echo 'Chain: Terminal → Memory → Database'

# Step 1: Execute system command via Terminal MCP
echo '1️⃣ Step 1: Terminal MCP - Get system information'
TERMINAL_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "uname -a"}}' \
    -o /tmp/workflow1_terminal.json)

if grep -q '"success": true' /tmp/workflow1_terminal.json; then
    SYSTEM_INFO=$(cat /tmp/workflow1_terminal.json | grep -o '"stdout": "[^"]*"' | cut -d'"' -f4)
    test_pass "Terminal MCP execution (${TERMINAL_TIME}ms)"
    echo "   System: $SYSTEM_INFO"
else
    test_fail "Terminal MCP execution" "$(cat /tmp/workflow1_terminal.json)"
fi

# Step 2: Store system info in Memory MCP
echo '2️⃣ Step 2: Memory MCP - Store system information'
MEMORY_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "store_memory", "arguments": {"content": "System Info Chain ${TEST_ID}: '"$SYSTEM_INFO"'", "metadata": {"workflow": "system_info_chain", "test_id": "${TEST_ID}", "step": "2", "source": "terminal_mcp"}}}' \
    -o /tmp/workflow1_memory.json)

if grep -q '"success": true' /tmp/workflow1_memory.json; then
    MEMORY_ID=$(cat /tmp/workflow1_memory.json | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*')
    test_pass "Memory MCP storage (${MEMORY_TIME}ms) - ID: $MEMORY_ID"
else
    test_fail "Memory MCP storage" "$(cat /tmp/workflow1_memory.json)"
fi

# Step 3: Verify data persistence via search
echo '3️⃣ Step 3: Memory MCP - Verify workflow data'
SEARCH_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "System Info Chain ${TEST_ID}", "limit": 3}}' \
    -o /tmp/workflow1_search.json)

if grep -q "System Info Chain ${TEST_ID}" /tmp/workflow1_search.json; then
    test_pass "Workflow data verification (${SEARCH_TIME}ms)"
else
    test_fail "Workflow data verification" "$(cat /tmp/workflow1_search.json)"
fi

WORKFLOW1_TOTAL=$((TERMINAL_TIME + MEMORY_TIME + SEARCH_TIME))
echo "   📊 Workflow 1 Total Time: ${WORKFLOW1_TOTAL}ms"

echo
echo '🔗 WORKFLOW 2: Container Health Chain'
echo '===================================='
echo 'Chain: Terminal → Memory → Search → Report'

# Step 1: Get container status
echo '1️⃣ Step 1: Get Docker container status'
CONTAINER_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "docker ps --format \"{{.Names}},{{.Status}}\" | head -5"}}' \
    -o /tmp/workflow2_containers.json)

if grep -q '"success": true' /tmp/workflow2_containers.json; then
    CONTAINER_STATUS=$(cat /tmp/workflow2_containers.json | grep -o '"stdout": "[^"]*"' | cut -d'"' -f4)
    test_pass "Container status retrieval (${CONTAINER_TIME}ms)"
    echo "   Containers: $(echo "$CONTAINER_STATUS" | wc -l) found"
else
    test_fail "Container status retrieval" "$(cat /tmp/workflow2_containers.json)"
fi

# Step 2: Store health metrics
echo '2️⃣ Step 2: Store health metrics in memory'
HEALTH_MEMORY_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "store_memory", "arguments": {"content": "Health Check ${TEST_ID}: '"$CONTAINER_STATUS"'", "metadata": {"workflow": "health_chain", "test_id": "${TEST_ID}", "type": "health_metrics", "timestamp": "'$(date)'"}}' \
    -o /tmp/workflow2_health_memory.json)

if grep -q '"success": true' /tmp/workflow2_health_memory.json; then
    HEALTH_MEMORY_ID=$(cat /tmp/workflow2_health_memory.json | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*')
    test_pass "Health metrics storage (${HEALTH_MEMORY_TIME}ms) - ID: $HEALTH_MEMORY_ID"
else
    test_fail "Health metrics storage" "$(cat /tmp/workflow2_health_memory.json)"
fi

# Step 3: Generate health report
echo '3️⃣ Step 3: Generate consolidated health report'
REPORT_TIME=$(measure_workflow_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Health Check", "limit": 5}}' \
    -o /tmp/workflow2_report.json)

if grep -q "Health Check" /tmp/workflow2_report.json; then
    HEALTH_RECORDS=$(cat /tmp/workflow2_report.json | grep -o '"total_count": [0-9]*' | grep -o '[0-9]*')
    test_pass "Health report generation (${REPORT_TIME}ms) - $HEALTH_RECORDS records"
else
    test_fail "Health report generation" "$(cat /tmp/workflow2_report.json)"
fi

WORKFLOW2_TOTAL=$((CONTAINER_TIME + HEALTH_MEMORY_TIME + REPORT_TIME))
echo "   📊 Workflow 2 Total Time: ${WORKFLOW2_TOTAL}ms"

echo
echo '🔗 WORKFLOW 3: Concurrent Operations Test'
echo '========================================'
echo 'Test: 3 simultaneous workflows'

# Launch 3 concurrent workflows
echo '⚡ Launching concurrent workflows...'
CONCURRENT_START=$(date +%s%3N)

# Workflow A: File system info
curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "df -h | head -3"}}' \
    -o /tmp/concurrent_a.json &
PID_A=$\!

# Workflow B: Memory usage  
curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "free -m"}}' \
    -o /tmp/concurrent_b.json &
PID_B=$\!

# Workflow C: Process count
curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "ps aux | wc -l"}}' \
    -o /tmp/concurrent_c.json &
PID_C=$\!

# Wait for all to complete
wait $PID_A $PID_B $PID_C
CONCURRENT_END=$(date +%s%3N)
CONCURRENT_TIME=$((CONCURRENT_END - CONCURRENT_START))

# Verify all succeeded
CONCURRENT_SUCCESS=0
if grep -q '"success": true' /tmp/concurrent_a.json; then CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS+1)); fi
if grep -q '"success": true' /tmp/concurrent_b.json; then CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS+1)); fi  
if grep -q '"success": true' /tmp/concurrent_c.json; then CONCURRENT_SUCCESS=$((CONCURRENT_SUCCESS+1)); fi

if [ $CONCURRENT_SUCCESS -eq 3 ]; then
    test_pass "Concurrent workflows (${CONCURRENT_TIME}ms) - 3/3 succeeded"
else
    test_fail "Concurrent workflows" "Only $CONCURRENT_SUCCESS/3 workflows succeeded"
fi

echo
echo '📊 PERFORMANCE ANALYSIS'
echo '======================'

TOTAL_END_TIME=$(date +%s%3N)
TOTAL_TEST_TIME=$((TOTAL_END_TIME - TOTAL_START_TIME))

echo "🕐 Timing Breakdown:"
echo "   - Workflow 1 (Sequential): ${WORKFLOW1_TOTAL}ms"
echo "   - Workflow 2 (Health): ${WORKFLOW2_TOTAL}ms"  
echo "   - Workflow 3 (Concurrent): ${CONCURRENT_TIME}ms"
echo "   - Total Test Duration: ${TOTAL_TEST_TIME}ms"

# Performance thresholds
MAX_WORKFLOW_TIME=500
MAX_CONCURRENT_TIME=200

if [ $WORKFLOW1_TOTAL -le $MAX_WORKFLOW_TIME ]; then
    test_pass "Sequential workflow performance (${WORKFLOW1_TOTAL}ms <= ${MAX_WORKFLOW_TIME}ms)"
else
    test_fail "Sequential workflow performance" "Time ${WORKFLOW1_TOTAL}ms exceeds ${MAX_WORKFLOW_TIME}ms threshold"
fi

if [ $CONCURRENT_TIME -le $MAX_CONCURRENT_TIME ]; then
    test_pass "Concurrent workflow performance (${CONCURRENT_TIME}ms <= ${MAX_CONCURRENT_TIME}ms)"
else
    test_fail "Concurrent workflow performance" "Time ${CONCURRENT_TIME}ms exceeds ${MAX_CONCURRENT_TIME}ms threshold"
fi

echo
echo '🎯 SERVICE INTEGRATION VALIDATION'
echo '================================='

# Check service mesh connectivity
ZEN_SERVICES=$(echo "$ZEN_STATUS" | grep -o '"[a-z_]*": "http[^"]*"' | wc -l)
if [ $ZEN_SERVICES -ge 6 ]; then
    test_pass "Service mesh integration ($ZEN_SERVICES services connected)"
else
    test_fail "Service mesh integration" "Only $ZEN_SERVICES services available, expected 6+"
fi

echo
echo '📊 FINAL RESULTS SUMMARY'
echo '======================='
echo "✅ PASSED: $PASS_COUNT tests"
echo "❌ FAILED: $FAIL_COUNT tests"
echo "🔗 Workflows Tested: 3 (Sequential, Health, Concurrent)"
echo "⚡ Services Integrated: $ZEN_SERVICES MCP services"
echo "📈 Performance Metrics:"
echo "   - Average workflow: $(((WORKFLOW1_TOTAL + WORKFLOW2_TOTAL) / 2))ms"
echo "   - Concurrent efficiency: ${CONCURRENT_TIME}ms for 3 parallel ops"
echo "   - Total test runtime: ${TOTAL_TEST_TIME}ms"

# Overall assessment
if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL WORKFLOWS PASSED - Orchestration System is FULLY FUNCTIONAL"
    exit 0
else
    echo "⚠️  SOME WORKFLOWS FAILED - Orchestration needs attention"
    exit 1
fi
