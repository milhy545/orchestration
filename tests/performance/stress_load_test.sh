#\!/bin/bash
# Stress Testing & Load Performance Suite
# Target: System limits, concurrent operations, graceful degradation

echo '🔥 STRESS TESTING & LOAD PERFORMANCE SUITE'
echo '==========================================='
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
STRESS_START_TIME=$(date +%s%3N)

# Performance tracking arrays
declare -a RESPONSE_TIMES
declare -a CONCURRENT_TIMES
declare -a ERROR_COUNTS

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

stress_operation() {
    local operation=$1
    local data=$2
    local start=$(date +%s%3N)
    local result=$(curl -s -X POST "$ZEN_URL" \
        -H 'Content-Type: application/json' \
        -d "$data" \
        --max-time 10)
    local end=$(date +%s%3N)
    local duration=$((end - start))
    echo "$duration|$result"
}

calculate_stats() {
    local times=("$@")
    local sum=0
    local count=${#times[@]}
    
    for time in "${times[@]}"; do
        sum=$((sum + time))
    done
    
    local avg=$((sum / count))
    echo $avg
}

# Preflight checks

e2e_require_cmd curl
e2e_require_http "ZEN Coordinator health" "http://localhost:7000/health"

echo "✅ Preflight passed: ZEN Coordinator is reachable"
echo
echo '📊 BASELINE: Single Operation Performance'
echo '========================================'

# Baseline measurements for comparison
echo '🔍 Measuring baseline performance...'
BASELINE_STORE=$(stress_operation "store" '{"tool": "store_memory", "arguments": {"content": "Baseline test", "metadata": {"test": "baseline"}}}' | cut -d'|' -f1)
BASELINE_SEARCH=$(stress_operation "search" '{"tool": "search_memories", "arguments": {"query": "Baseline", "limit": 5}}' | cut -d'|' -f1)
BASELINE_TERMINAL=$(stress_operation "terminal" '{"tool": "execute_command", "arguments": {"command": "echo baseline"}}' | cut -d'|' -f1)

echo "📈 Baseline Performance:"
echo "   - Memory Store: ${BASELINE_STORE}ms"
echo "   - Memory Search: ${BASELINE_SEARCH}ms"
echo "   - Terminal Exec: ${BASELINE_TERMINAL}ms"

echo
echo '🔥 STRESS TEST 1: Concurrent Memory Operations'
echo '============================================='
echo 'Target: 25 simultaneous memory store operations'

# Create temporary directory for concurrent results
mkdir -p /tmp/stress_results

# Launch 25 concurrent memory store operations
CONCURRENT_START=$(date +%s%3N)
echo '⚡ Launching 25 concurrent memory store operations...'

for i in $(seq 1 25); do
    {
        result=$(stress_operation "concurrent_store_$i" "{\"tool\": \"store_memory\", \"arguments\": {\"content\": \"Stress test data batch $i - TEST_ID: ${TEST_ID}\", \"metadata\": {\"stress_test\": true, \"batch\": $i, \"test_id\": \"${TEST_ID}\"}}}")
        echo "$result" > /tmp/stress_results/store_$i.result
    } &
done

# Wait for all concurrent operations to complete
wait
CONCURRENT_END=$(date +%s%3N)
CONCURRENT_DURATION=$((CONCURRENT_END - CONCURRENT_START))

echo "⏱️  All operations completed in ${CONCURRENT_DURATION}ms"

# Analyze results
SUCCESS_COUNT=0
TOTAL_RESPONSE_TIME=0
MAX_RESPONSE_TIME=0
MIN_RESPONSE_TIME=999999

for i in $(seq 1 25); do
    if [ -f "/tmp/stress_results/store_$i.result" ]; then
        result_line=$(cat /tmp/stress_results/store_$i.result)
        response_time=$(echo "$result_line" | cut -d'|' -f1)
        result_json=$(echo "$result_line" | cut -d'|' -f2-)
        
        if echo "$result_json" | grep -q '"success": true'; then
            SUCCESS_COUNT=$((SUCCESS_COUNT+1))
            TOTAL_RESPONSE_TIME=$((TOTAL_RESPONSE_TIME + response_time))
            
            if [ $response_time -gt $MAX_RESPONSE_TIME ]; then
                MAX_RESPONSE_TIME=$response_time
            fi
            
            if [ $response_time -lt $MIN_RESPONSE_TIME ]; then
                MIN_RESPONSE_TIME=$response_time
            fi
        fi
    fi
done

if [ $SUCCESS_COUNT -gt 0 ]; then
    AVG_RESPONSE_TIME=$((TOTAL_RESPONSE_TIME / SUCCESS_COUNT))
else
    AVG_RESPONSE_TIME=0
fi

echo "📊 Concurrent Operations Results:"
echo "   - Success Rate: $SUCCESS_COUNT/25 ($(((SUCCESS_COUNT * 100) / 25))%)"
echo "   - Average Response Time: ${AVG_RESPONSE_TIME}ms"
echo "   - Min Response Time: ${MIN_RESPONSE_TIME}ms"
echo "   - Max Response Time: ${MAX_RESPONSE_TIME}ms"
echo "   - Total Duration: ${CONCURRENT_DURATION}ms"

# Performance assessment
DEGRADATION_FACTOR=$(((AVG_RESPONSE_TIME * 100) / BASELINE_STORE))
echo "   - Performance Degradation: ${DEGRADATION_FACTOR}% of baseline"

if [ $SUCCESS_COUNT -ge 23 ]; then
    test_pass "Concurrent operations success rate ($SUCCESS_COUNT/25)"
else
    test_fail "Concurrent operations success rate" "Only $SUCCESS_COUNT/25 operations succeeded"
fi

if [ $AVG_RESPONSE_TIME -le 300 ]; then
    test_pass "Concurrent response time (${AVG_RESPONSE_TIME}ms <= 300ms)"
else
    test_fail "Concurrent response time" "Average ${AVG_RESPONSE_TIME}ms exceeds 300ms threshold"
fi

echo
echo '🔥 STRESS TEST 2: Memory Search Under Load'
echo '========================================'
echo 'Target: 20 simultaneous search operations'

# Search stress test
SEARCH_START=$(date +%s%3N)
echo '🔍 Launching 20 concurrent memory search operations...'

for i in $(seq 1 20); do
    {
        search_result=$(stress_operation "concurrent_search_$i" "{\"tool\": \"search_memories\", \"arguments\": {\"query\": \"Stress test\", \"limit\": 10}}")
        echo "$search_result" > /tmp/stress_results/search_$i.result
    } &
done

wait
SEARCH_END=$(date +%s%3N)
SEARCH_DURATION=$((SEARCH_END - SEARCH_START))

# Analyze search results
SEARCH_SUCCESS=0
SEARCH_TOTAL_TIME=0

for i in $(seq 1 20); do
    if [ -f "/tmp/stress_results/search_$i.result" ]; then
        search_line=$(cat /tmp/stress_results/search_$i.result)
        search_time=$(echo "$search_line" | cut -d'|' -f1)
        search_json=$(echo "$search_line" | cut -d'|' -f2-)
        
        if echo "$search_json" | grep -q '"memories"'; then
            SEARCH_SUCCESS=$((SEARCH_SUCCESS+1))
            SEARCH_TOTAL_TIME=$((SEARCH_TOTAL_TIME + search_time))
        fi
    fi
done

SEARCH_AVG=$(if [ $SEARCH_SUCCESS -gt 0 ]; then echo $((SEARCH_TOTAL_TIME / SEARCH_SUCCESS)); else echo 0; fi)

echo "📊 Search Stress Results:"
echo "   - Success Rate: $SEARCH_SUCCESS/20 ($(((SEARCH_SUCCESS * 100) / 20))%)"
echo "   - Average Response Time: ${SEARCH_AVG}ms"
echo "   - Total Duration: ${SEARCH_DURATION}ms"

if [ $SEARCH_SUCCESS -ge 18 ]; then
    test_pass "Search stress success rate ($SEARCH_SUCCESS/20)"
else
    test_fail "Search stress success rate" "Only $SEARCH_SUCCESS/20 searches succeeded"
fi

echo
echo '🔥 STRESS TEST 3: Large Content Operations'  
echo '========================================='
echo 'Target: Store and retrieve large content blocks'

# Generate large content (approximately 10KB)
LARGE_CONTENT="Large content stress test ${TEST_ID}: "
for i in $(seq 1 100); do
    LARGE_CONTENT="${LARGE_CONTENT}This is a large content block designed to test memory system performance with substantial data volumes. "
done

echo '📦 Testing large content storage...'
LARGE_STORE_TIME=$(stress_operation "large_content" "{\"tool\": \"store_memory\", \"arguments\": {\"content\": \"$LARGE_CONTENT\", \"metadata\": {\"test\": \"large_content\", \"size\": \"large\"}}}" | cut -d'|' -f1)

echo "📊 Large Content Results:"
echo "   - Content Size: ~$(echo "$LARGE_CONTENT" | wc -c) characters"
echo "   - Store Time: ${LARGE_STORE_TIME}ms"

LARGE_DEGRADATION=$(((LARGE_STORE_TIME * 100) / BASELINE_STORE))
echo "   - Size Degradation: ${LARGE_DEGRADATION}% of baseline"

if [ $LARGE_STORE_TIME -le 1000 ]; then
    test_pass "Large content storage (${LARGE_STORE_TIME}ms <= 1000ms)"
else
    test_fail "Large content storage" "Time ${LARGE_STORE_TIME}ms exceeds 1000ms threshold"
fi

echo
echo '🔥 STRESS TEST 4: Workflow Chain Overload'
echo '========================================'
echo 'Target: 10 simultaneous Terminal→Memory workflows'

WORKFLOW_START=$(date +%s%3N)
echo '🔄 Launching 10 concurrent workflows...'

for i in $(seq 1 10); do
    {
        # Terminal → Memory workflow
        terminal_result=$(stress_operation "workflow_terminal_$i" "{\"tool\": \"execute_command\", \"arguments\": {\"command\": \"echo Workflow $i test\"}}")
        if echo "$terminal_result" | cut -d'|' -f2- | grep -q '"success": true'; then
            memory_result=$(stress_operation "workflow_memory_$i" "{\"tool\": \"store_memory\", \"arguments\": {\"content\": \"Workflow $i completed\", \"metadata\": {\"workflow\": $i}}}")
            echo "SUCCESS|$i" > /tmp/stress_results/workflow_$i.result
        else
            echo "FAIL|$i" > /tmp/stress_results/workflow_$i.result
        fi
    } &
done

wait
WORKFLOW_END=$(date +%s%3N)
WORKFLOW_DURATION=$((WORKFLOW_END - WORKFLOW_START))

# Count successful workflows
WORKFLOW_SUCCESS=0
for i in $(seq 1 10); do
    if [ -f "/tmp/stress_results/workflow_$i.result" ] && grep -q "SUCCESS" /tmp/stress_results/workflow_$i.result; then
        WORKFLOW_SUCCESS=$((WORKFLOW_SUCCESS+1))
    fi
done

echo "📊 Workflow Overload Results:"
echo "   - Success Rate: $WORKFLOW_SUCCESS/10 ($(((WORKFLOW_SUCCESS * 100) / 10))%)"
echo "   - Total Duration: ${WORKFLOW_DURATION}ms"
echo "   - Average per Workflow: $(((WORKFLOW_DURATION) / 10))ms"

if [ $WORKFLOW_SUCCESS -ge 8 ]; then
    test_pass "Workflow overload success rate ($WORKFLOW_SUCCESS/10)"
else
    test_fail "Workflow overload success rate" "Only $WORKFLOW_SUCCESS/10 workflows succeeded"
fi

echo
echo '📊 SYSTEM RESOURCE ANALYSIS'
echo '=========================='

# Check system resources during stress test
echo '💾 Checking system resources...'
MEMORY_USAGE=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "execute_command", "arguments": {"command": "free -m | grep Mem"}}' | grep -o '"stdout": "[^"]*"' | cut -d'"' -f4 || echo "N/A")
CONTAINER_STATUS=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "execute_command", "arguments": {"command": "docker stats --no-stream --format \"{{.Container}}: {{.CPUPerc}} {{.MemUsage}}\" | head -3"}}' | grep -o '"stdout": "[^"]*"' | cut -d'"' -f4 || echo "N/A")

echo "📈 Resource Utilization:"
echo "   - Memory Status: $MEMORY_USAGE"
echo "   - Container Stats: $CONTAINER_STATUS"

# Cleanup temporary files
rm -rf /tmp/stress_results

echo
echo '📊 STRESS TEST SUMMARY'
echo '====================='

STRESS_END_TIME=$(date +%s%3N)
TOTAL_STRESS_TIME=$((STRESS_END_TIME - STRESS_START_TIME))

echo "✅ PASSED: $PASS_COUNT tests"
echo "❌ FAILED: $FAIL_COUNT tests"
echo "🔥 Stress Test Categories: 4 (Concurrent, Search, Large Content, Workflows)"
echo "⚡ Total Operations: $(((25 + 20 + 1 + 10)))"
echo "📈 Performance Summary:"
echo "   - Baseline Store: ${BASELINE_STORE}ms"
echo "   - Concurrent Avg: ${AVG_RESPONSE_TIME}ms (degradation: ${DEGRADATION_FACTOR}%)"
echo "   - Search Avg: ${SEARCH_AVG}ms"
echo "   - Large Content: ${LARGE_STORE_TIME}ms (degradation: ${LARGE_DEGRADATION}%)"
echo "   - Workflow Success: $WORKFLOW_SUCCESS/10"
echo "⏱️  Total Stress Duration: ${TOTAL_STRESS_TIME}ms"

# Performance thresholds assessment
CRITICAL_FAILURES=0
if [ $AVG_RESPONSE_TIME -gt 500 ]; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi
if [ $LARGE_STORE_TIME -gt 2000 ]; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi
if [ $WORKFLOW_SUCCESS -lt 7 ]; then CRITICAL_FAILURES=$((CRITICAL_FAILURES+1)); fi

# Overall stress test assessment
if [ $FAIL_COUNT -eq 0 ] && [ $CRITICAL_FAILURES -eq 0 ]; then
    echo "🎉 STRESS TESTS PASSED - System handles load gracefully"
    echo "💪 System Performance: EXCELLENT under stress"
    exit 0
elif [ $CRITICAL_FAILURES -le 1 ]; then
    echo "⚠️  STRESS TESTS PARTIAL - System shows some degradation"
    echo "💪 System Performance: GOOD with minor issues"
    exit 1
else
    echo "🚨 STRESS TESTS FAILED - System struggles under load"
    echo "💪 System Performance: NEEDS OPTIMIZATION"
    exit 2
fi
