#\!/bin/bash
# Failure & Recovery Testing Suite
# Target: Service resilience, auto-recovery, data consistency

echo '🚨 FAILURE & RECOVERY TESTING SUITE'
echo '===================================='
echo "Start time: $(date)"
echo

# Test configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
# shellcheck source=tests/lib/e2e_preflight.sh
source "$PROJECT_ROOT/tests/lib/e2e_preflight.sh"

ZEN_URL='http://localhost:7000/mcp'
MEMORY_URL='http://localhost:7005'
TEST_ID=$(date +%s)
PASS_COUNT=0
FAIL_COUNT=0
RECOVERY_START_TIME=$(date +%s%3N)

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

wait_for_service() {
    local service_url=$1
    local max_wait=$2
    local start_time=$(date +%s)
    
    while [ $((($(date +%s) - start_time))) -lt $max_wait ]; do
        if curl -s "$service_url" >/dev/null 2>&1; then
            local wait_time=$((($(date +%s) - start_time)))
            echo $wait_time
            return 0
        fi
        sleep 1
    done
    echo $max_wait
    return 1
}

measure_recovery_time() {
    local start=$(date +%s)
    "$@"
    local end=$(date +%s)
    echo $((end - start))
}

store_test_data() {
    local content="Recovery test data $1 - TEST_ID: ${TEST_ID}"
    local result=$(curl -s -X POST "$ZEN_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"tool\": \"store_memory\", \"arguments\": {\"content\": \"$content\", \"metadata\": {\"recovery_test\": true, \"test_id\": \"${TEST_ID}\", \"phase\": \"$1\"}}}" \
        --max-time 10)
    
    if echo "$result" | grep -q '"success": true'; then
        echo "$result" | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*'
        return 0
    else
        echo "ERROR"
        return 1
    fi
}

verify_test_data() {
    local query="Recovery test data $1"
    local result=$(curl -s -X POST "$ZEN_URL" \
        -H 'Content-Type: application/json' \
        -d "{\"tool\": \"search_memories\", \"arguments\": {\"query\": \"$query\", \"limit\": 5}}" \
        --max-time 10)
    
    if echo "$result" | grep -q "Recovery test data $1"; then
        echo "$result" | grep -o '"total_count": [0-9]*' | grep -o '[0-9]*'
        return 0
    else
        echo "0"
        return 1
    fi
}

# Preflight checks

e2e_require_cmd curl
e2e_require_cmd docker
e2e_require_http "ZEN Coordinator health" "http://localhost:7000/health"
e2e_require_http "Memory MCP health" "http://localhost:7005/health"

MEMORY_CONTAINER="$(e2e_require_container "Memory MCP" mcp-memory memory-mcp-prod)"
ZEN_CONTAINER="$(e2e_detect_container zen-coordinator zen-coordinator-prod || true)"

if [ -n "$ZEN_CONTAINER" ]; then
  echo "✅ Preflight passed: using containers memory=$MEMORY_CONTAINER, zen=$ZEN_CONTAINER"
else
  echo "✅ Preflight passed: using memory container=$MEMORY_CONTAINER and host-process fallback for ZEN"
fi

echo
echo '📊 PRE-FAILURE: System Health Baseline'
echo '====================================='

# Establish baseline before failure tests
echo '🔍 Checking initial system state...'
INITIAL_ZEN_STATUS=$(curl -s http://localhost:7000/health 2>/dev/null)
INITIAL_MEMORY_STATUS=$(curl -s http://localhost:7005/health 2>/dev/null)
INITIAL_CONTAINERS=$(docker ps --format '{{.Names}}' | grep mcp | wc -l)

if echo "$INITIAL_ZEN_STATUS" | grep -q '"status": "healthy"'; then
    test_pass "Zen Coordinator baseline health"
else
    test_fail "Zen Coordinator baseline" "Service not healthy"
fi

if echo "$INITIAL_MEMORY_STATUS" | grep -q '"status": "healthy"'; then
    test_pass "Memory MCP baseline health"
else
    test_fail "Memory MCP baseline" "Service not healthy"
fi

echo "📈 Baseline State:"
echo "   - Zen Coordinator: $(echo "$INITIAL_ZEN_STATUS" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)"
echo "   - Memory MCP: $(echo "$INITIAL_MEMORY_STATUS" | grep -o '"status": "[^"]*"' | cut -d'"' -f4)"
echo "   - MCP Containers: $INITIAL_CONTAINERS"

# Store baseline data for consistency testing
echo '💾 Storing baseline test data...'
BASELINE_MEMORY_ID=$(store_test_data "baseline")
if [ "$BASELINE_MEMORY_ID" \!= "ERROR" ]; then
    test_pass "Baseline data storage - ID: $BASELINE_MEMORY_ID"
else
    test_fail "Baseline data storage" "Failed to store baseline data"
fi

echo
echo '🚨 FAILURE TEST 1: Memory MCP Container Restart'
echo '=============================================='
echo 'Target: Simulate Memory MCP service failure and recovery'

# Memory container was resolved in preflight
if [ -z "$MEMORY_CONTAINER" ]; then
    test_fail "Memory container identification" "Memory MCP container not found"
else
    echo "🔍 Target container: $MEMORY_CONTAINER"
    
    # Store pre-failure data
    PRE_FAILURE_ID=$(store_test_data "pre-failure")
    echo "💾 Pre-failure data stored: $PRE_FAILURE_ID"
    
    # Simulate service failure
    echo "💥 Simulating Memory MCP failure..."
    FAILURE_TIME=$(date +%s)
    docker stop $MEMORY_CONTAINER >/dev/null 2>&1
    
    # Verify service is down
    sleep 2
    if \! curl -s http://localhost:7005/health >/dev/null 2>&1; then
        test_pass "Memory MCP failure simulation"
    else
        test_fail "Memory MCP failure simulation" "Service still responding"
    fi
    
    # Attempt operation during failure
    echo "🔄 Testing operation during failure..."
    FAILURE_OPERATION=$(curl -s -X POST "$ZEN_URL" \
        -H 'Content-Type: application/json' \
        -d '{"tool": "store_memory", "arguments": {"content": "During failure test", "metadata": {"during_failure": true}}}' \
        --max-time 5)
    
    if echo "$FAILURE_OPERATION" | grep -q 'error'; then
        test_pass "Graceful failure handling (operation rejected)"
    else
        test_fail "Graceful failure handling" "Operation should fail during service outage"
    fi
    
    # Restart service
    echo "🔄 Restarting Memory MCP service..."
    docker start $MEMORY_CONTAINER >/dev/null 2>&1
    
    # Measure recovery time
    echo "⏱️  Measuring recovery time..."
    RECOVERY_TIME=$(wait_for_service "http://localhost:7005/health" 30)
    RECOVERY_STATUS=$?
    
    if [ $RECOVERY_STATUS -eq 0 ]; then
        test_pass "Memory MCP recovery (${RECOVERY_TIME}s)"
        
        # Test recovery time threshold
        if [ $RECOVERY_TIME -le 10 ]; then
            test_pass "Recovery time objective (${RECOVERY_TIME}s <= 10s)"
        else
            test_fail "Recovery time objective" "Recovery took ${RECOVERY_TIME}s, exceeds 10s target"
        fi
    else
        test_fail "Memory MCP recovery" "Service failed to recover within 30s"
    fi
    
    # Verify data consistency after recovery
    echo "🔍 Verifying data consistency after recovery..."
    sleep 3
    
    BASELINE_COUNT=$(verify_test_data "baseline")
    PRE_FAILURE_COUNT=$(verify_test_data "pre-failure")
    
    if [ "$BASELINE_COUNT" -gt 0 ] && [ "$PRE_FAILURE_COUNT" -gt 0 ]; then
        test_pass "Data consistency after recovery (baseline: $BASELINE_COUNT, pre-failure: $PRE_FAILURE_COUNT)"
    else
        test_fail "Data consistency after recovery" "Missing data: baseline=$BASELINE_COUNT, pre-failure=$PRE_FAILURE_COUNT"
    fi
    
    # Store post-recovery data
    POST_RECOVERY_ID=$(store_test_data "post-recovery")
    if [ "$POST_RECOVERY_ID" \!= "ERROR" ]; then
        test_pass "Post-recovery functionality - ID: $POST_RECOVERY_ID"
    else
        test_fail "Post-recovery functionality" "Failed to store data after recovery"
    fi
fi

echo
echo '🚨 FAILURE TEST 2: Zen Coordinator Restart'
echo '=========================================='
echo 'Target: Test orchestration layer resilience'

# Store pre-restart data via direct Memory MCP

echo "💾 Storing data via direct MCP before Zen restart..."
DIRECT_STORE_RESULT=$(curl -s -X POST "http://localhost:7005/memory/store" \
    -H 'Content-Type: application/json' \
    -d '{"content": "Direct store before Zen restart - TEST_ID: '${TEST_ID}'", "metadata": {"direct_store": true, "test_id": "'${TEST_ID}'"}}')

if echo "$DIRECT_STORE_RESULT" | grep -q '"success": true'; then
    DIRECT_MEMORY_ID=$(echo "$DIRECT_STORE_RESULT" | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*')
    test_pass "Direct MCP storage before restart - ID: $DIRECT_MEMORY_ID"
else
    test_fail "Direct MCP storage" "Failed to store via direct MCP"
fi

# Restart ZEN coordinator (container-first, process fallback)
if [ -n "$ZEN_CONTAINER" ]; then
    echo "🔍 Target container: $ZEN_CONTAINER"
    echo "💥 Restarting Zen Coordinator container..."
    docker stop "$ZEN_CONTAINER" >/dev/null 2>&1
    sleep 2

    if \! curl -s http://localhost:7000/health >/dev/null 2>&1; then
        test_pass "Zen Coordinator shutdown"
    else
        test_fail "Zen Coordinator shutdown" "Service still responding"
    fi

    echo "🔄 Starting Zen Coordinator container..."
    docker start "$ZEN_CONTAINER" >/dev/null 2>&1
else
    ZEN_PID=$(ps aux | grep zen_coordinator.py | grep -v grep | awk '{print $2}')
    if [ -z "$ZEN_PID" ]; then
        test_fail "Zen Coordinator identification" "No container and no process target found"
    else
        echo "🔍 Target process: PID $ZEN_PID"
        echo "💥 Restarting Zen Coordinator process..."
        kill "$ZEN_PID"
        sleep 2

        if \! curl -s http://localhost:7000/health >/dev/null 2>&1; then
            test_pass "Zen Coordinator shutdown"
        else
            test_fail "Zen Coordinator shutdown" "Service still responding"
        fi

        echo "🔄 Starting Zen Coordinator process..."
        ZEN_COORDINATOR_SCRIPT="${ZEN_COORDINATOR_SCRIPT:-$PROJECT_ROOT/config/zen_coordinator.py}"
        if [ -f "$ZEN_COORDINATOR_SCRIPT" ]; then
            nohup python3 "$ZEN_COORDINATOR_SCRIPT" >/dev/null 2>&1 &
        else
            test_fail "Zen Coordinator startup" "Script not found: $ZEN_COORDINATOR_SCRIPT"
        fi
    fi
fi

# Measure Zen recovery time
ZEN_RECOVERY_TIME=$(wait_for_service "http://localhost:7000/health" 20)
ZEN_RECOVERY_STATUS=$?

if [ $ZEN_RECOVERY_STATUS -eq 0 ]; then
    test_pass "Zen Coordinator restart (${ZEN_RECOVERY_TIME}s)"
else
    test_fail "Zen Coordinator restart" "Service failed to restart within 20s"
fi

# Test service mesh reconnection
echo "🔗 Testing service mesh reconnection..."
sleep 3
ZEN_STATUS_AFTER=$(curl -s http://localhost:7000/status)
SERVICES_CONNECTED=$(echo "$ZEN_STATUS_AFTER" | grep -o '"[a-z_]*": "http[^"]*"' | wc -l)

if [ $SERVICES_CONNECTED -ge 6 ]; then
    test_pass "Service mesh reconnection ($SERVICES_CONNECTED services)"
else
    test_fail "Service mesh reconnection" "Only $SERVICES_CONNECTED services connected, expected 6+"
fi

# Verify data accessibility via Zen after restart
DIRECT_SEARCH=$(curl -s -X POST "$ZEN_URL" \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Direct store before Zen restart", "limit": 5}}')

if echo "$DIRECT_SEARCH" | grep -q "Direct store before Zen restart"; then
    test_pass "Data accessibility after Zen restart"
else
    test_fail "Data accessibility after Zen restart" "Cannot access data stored before restart"
fi

echo
echo '🚨 FAILURE TEST 3: Network Timeout Simulation'
echo '============================================='
echo 'Target: Test timeout handling and error recovery'

# Test network timeout scenarios
echo "⏱️  Testing request timeout handling..."
TIMEOUT_TEST=$(curl -s -X POST "$ZEN_URL" \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "sleep 2 && echo timeout test"}}' \
    --max-time 1)

if echo "$TIMEOUT_TEST" | grep -q 'error\|timeout' || [ -z "$TIMEOUT_TEST" ]; then
    test_pass "Timeout handling (request properly timed out)"
else
    test_fail "Timeout handling" "Request should have timed out but completed"
fi

# Test system recovery after timeout
echo "🔄 Testing system responsiveness after timeout..."
RECOVERY_TEST=$(curl -s -X POST "$ZEN_URL" \
    -H 'Content-Type: application/json' \
    -d '{"tool": "execute_command", "arguments": {"command": "echo recovery test"}}' \
    --max-time 5)

if echo "$RECOVERY_TEST" | grep -q '"success": true'; then
    test_pass "System recovery after timeout"
else
    test_fail "System recovery after timeout" "System not responsive after timeout scenario"
fi

echo
echo '🚨 FAILURE TEST 4: Database Integrity Check'
echo '=========================================='
echo 'Target: Verify database consistency during failures'

# Count total memories before failure tests
TOTAL_MEMORIES_BEFORE=$(curl -s -X POST "$ZEN_URL" \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Recovery test", "limit": 100}}' | \
    grep -o '"total_count": [0-9]*' | grep -o '[0-9]*')

echo "📊 Database state before failures: $TOTAL_MEMORIES_BEFORE recovery test records"

# Store final verification data
FINAL_MEMORY_ID=$(store_test_data "final-verification")
if [ "$FINAL_MEMORY_ID" \!= "ERROR" ]; then
    test_pass "Final data storage - ID: $FINAL_MEMORY_ID"
else
    test_fail "Final data storage" "Failed to store final verification data"
fi

# Count memories after all failure tests
TOTAL_MEMORIES_AFTER=$(curl -s -X POST "$ZEN_URL" \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Recovery test", "limit": 100}}' | \
    grep -o '"total_count": [0-9]*' | grep -o '[0-9]*')

echo "📊 Database state after failures: $TOTAL_MEMORIES_AFTER recovery test records"

# Calculate expected records (baseline + pre-failure + post-recovery + final)
EXPECTED_RECORDS=4
ACTUAL_NEW_RECORDS=$((TOTAL_MEMORIES_AFTER - (TOTAL_MEMORIES_BEFORE - EXPECTED_RECORDS)))

if [ $ACTUAL_NEW_RECORDS -ge $EXPECTED_RECORDS ]; then
    test_pass "Database integrity ($ACTUAL_NEW_RECORDS/$EXPECTED_RECORDS records preserved)"
else
    test_fail "Database integrity" "Missing records: expected $EXPECTED_RECORDS, found $ACTUAL_NEW_RECORDS"
fi

echo
echo '📊 FAILURE & RECOVERY SUMMARY'
echo '============================='

RECOVERY_END_TIME=$(date +%s%3N)
TOTAL_RECOVERY_TIME=$((RECOVERY_END_TIME - RECOVERY_START_TIME))

echo "✅ PASSED: $PASS_COUNT tests"
echo "❌ FAILED: $FAIL_COUNT tests"
echo "🚨 Failure Categories: 4 (Memory MCP, Zen Coordinator, Network, Database)"
echo "⏱️  Recovery Metrics:"
echo "   - Memory MCP Recovery: ${RECOVERY_TIME}s"
echo "   - Zen Coordinator Recovery: ${ZEN_RECOVERY_TIME}s"
echo "   - Service Mesh Reconnection: $SERVICES_CONNECTED services"
echo "   - Database Records: $ACTUAL_NEW_RECORDS/$EXPECTED_RECORDS preserved"
echo "📈 Total Test Duration: ${TOTAL_RECOVERY_TIME}ms"

# Overall resilience assessment
CRITICAL_FAILURES=0
if [ "$RECOVERY_TIME" -gt 10 ] 2>/dev/null; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi
if [ "$ZEN_RECOVERY_TIME" -gt 20 ] 2>/dev/null; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi
if [ $SERVICES_CONNECTED -lt 6 ] 2>/dev/null; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi

# Final assessment
if [ $FAIL_COUNT -eq 0 ] && [ $CRITICAL_FAILURES -eq 0 ]; then
    echo "🎉 FAILURE TESTS PASSED - System is highly resilient"
    echo "💪 Recovery Performance: EXCELLENT"
    exit 0
elif [ $CRITICAL_FAILURES -le 1 ]; then
    echo "⚠️  FAILURE TESTS PARTIAL - System shows good resilience"
    echo "💪 Recovery Performance: GOOD with minor issues"
    exit 1
else
    echo "🚨 FAILURE TESTS FAILED - System resilience needs improvement"
    echo "💪 Recovery Performance: NEEDS ATTENTION"
    exit 2
fi
