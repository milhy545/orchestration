#\!/bin/bash
# Memory System CRUD Test Suite
# Target: Memory MCP Server via Zen Coordinator & Direct Access

echo '🧪 MEMORY SYSTEM CRUD TEST SUITE'
echo '================================='
echo "Start time: $(date)"
echo

# Test configuration
ZEN_URL='http://localhost:8020/mcp'
MEMORY_URL='http://localhost:8007'
TEST_ID=$(date +%s)
PASS_COUNT=0
FAIL_COUNT=0

# Helper functions
test_pass() {
    echo "✅ PASS: $1"
    PASS_COUNT=1
}

test_fail() {
    echo "❌ FAIL: $1"
    echo "   Details: $2"
    FAIL_COUNT=1
}

measure_time() {
    local start=$(date +%s%3N)
    "$@"
    local end=$(date +%s%3N)
    echo $((end - start))
}

echo '📝 TEST 1: CREATE (Store Memory via Zen Coordinator)'
echo '------------------------------------------------'

# Test 1a: Store via Zen Coordinator
ZEN_STORE_TIME=$(measure_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "store_memory", "arguments": {"content": "Test memory content ${TEST_ID}", "metadata": {"test_id": "${TEST_ID}", "source": "crud_test", "type": "unit_test"}}}' \
    -o /tmp/zen_store_result.json)

if grep -q '"success": true' /tmp/zen_store_result.json; then
    MEMORY_ID=$(cat /tmp/zen_store_result.json | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*')
    test_pass "Store via Zen Coordinator (${ZEN_STORE_TIME}ms) - ID: $MEMORY_ID"
else
    test_fail "Store via Zen Coordinator" "$(cat /tmp/zen_store_result.json)"
fi

echo
echo '📝 TEST 2: READ (Search Memory via Zen Coordinator)'
echo '------------------------------------------------'

# Test 2a: Search via Zen Coordinator  
ZEN_SEARCH_TIME=$(measure_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Test memory content ${TEST_ID}", "limit": 5}}' \
    -o /tmp/zen_search_result.json)

if grep -q "Test memory content ${TEST_ID}" /tmp/zen_search_result.json; then
    FOUND_COUNT=$(cat /tmp/zen_search_result.json | grep -o '"total_count": [0-9]*' | grep -o '[0-9]*')
    test_pass "Search via Zen Coordinator (${ZEN_SEARCH_TIME}ms) - Found: $FOUND_COUNT"
else
    test_fail "Search via Zen Coordinator" "$(cat /tmp/zen_search_result.json)"
fi

echo
echo '📝 TEST 3: CREATE (Direct Memory MCP)'
echo '-----------------------------------'

# Test 3a: Store directly to Memory MCP
DIRECT_STORE_TIME=$(measure_time curl -s -X POST $MEMORY_URL/memory/store \
    -H 'Content-Type: application/json' \
    -d '{"content": "Direct MCP test ${TEST_ID}", "metadata": {"test_id": "${TEST_ID}", "source": "direct_mcp", "type": "unit_test"}}' \
    -o /tmp/direct_store_result.json)

if grep -q '"success": true' /tmp/direct_store_result.json; then
    DIRECT_MEMORY_ID=$(cat /tmp/direct_store_result.json | grep -o '"memory_id": [0-9]*' | grep -o '[0-9]*')
    test_pass "Store via Direct MCP (${DIRECT_STORE_TIME}ms) - ID: $DIRECT_MEMORY_ID"
else
    test_fail "Store via Direct MCP" "$(cat /tmp/direct_store_result.json)"
fi

echo
echo '📝 TEST 4: READ (Direct Memory MCP)'
echo '--------------------------------'

# Test 4a: Search directly from Memory MCP
DIRECT_SEARCH_TIME=$(measure_time curl -s -X POST $MEMORY_URL/memory/search \
    -H 'Content-Type: application/json' \
    -d '{"query": "Direct MCP test ${TEST_ID}", "limit": 5}' \
    -o /tmp/direct_search_result.json)

if grep -q "Direct MCP test ${TEST_ID}" /tmp/direct_search_result.json; then
    DIRECT_FOUND_COUNT=$(cat /tmp/direct_search_result.json | grep -o '"total_count": [0-9]*' | grep -o '[0-9]*')
    test_pass "Search via Direct MCP (${DIRECT_SEARCH_TIME}ms) - Found: $DIRECT_FOUND_COUNT"
else
    test_fail "Search via Direct MCP" "$(cat /tmp/direct_search_result.json)"
fi

echo
echo '📝 TEST 5: CONSISTENCY CHECK'
echo '---------------------------'

# Test 5a: Cross-platform search consistency
CROSS_SEARCH_TIME=$(measure_time curl -s -X POST $ZEN_URL \
    -H 'Content-Type: application/json' \
    -d '{"tool": "search_memories", "arguments": {"query": "Direct MCP test ${TEST_ID}", "limit": 5}}' \
    -o /tmp/cross_search_result.json)

if grep -q "Direct MCP test ${TEST_ID}" /tmp/cross_search_result.json; then
    test_pass "Cross-platform consistency (${CROSS_SEARCH_TIME}ms)"
else
    test_fail "Cross-platform consistency" "Zen Coordinator cannot find direct MCP stored memory"
fi

echo
echo '📝 TEST 6: PERFORMANCE VALIDATION'
echo '--------------------------------'

# Performance thresholds
MAX_RESPONSE_TIME=100

# Check response times
if [ $ZEN_STORE_TIME -le $MAX_RESPONSE_TIME ]; then
    test_pass "Zen Store Performance (${ZEN_STORE_TIME}ms <= ${MAX_RESPONSE_TIME}ms)"
else
    test_fail "Zen Store Performance" "Response time ${ZEN_STORE_TIME}ms exceeds ${MAX_RESPONSE_TIME}ms threshold"
fi

if [ $DIRECT_STORE_TIME -le $MAX_RESPONSE_TIME ]; then
    test_pass "Direct Store Performance (${DIRECT_STORE_TIME}ms <= ${MAX_RESPONSE_TIME}ms)"
else
    test_fail "Direct Store Performance" "Response time ${DIRECT_STORE_TIME}ms exceeds ${MAX_RESPONSE_TIME}ms threshold"
fi

echo
echo '📊 TEST RESULTS SUMMARY'
echo '======================'
echo "✅ PASSED: $PASS_COUNT tests"
echo "❌ FAILED: $FAIL_COUNT tests"
echo "📈 Performance Metrics:"
echo "   - Zen Store: ${ZEN_STORE_TIME}ms"
echo "   - Zen Search: ${ZEN_SEARCH_TIME}ms"
echo "   - Direct Store: ${DIRECT_STORE_TIME}ms"
echo "   - Direct Search: ${DIRECT_SEARCH_TIME}ms"
echo "   - Cross Search: ${CROSS_SEARCH_TIME}ms"
echo "⏰ Test Duration: $(date) - $(($(date +%s) - $(date -d "$(date)" +%s)))s"

# Overall result
if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 ALL TESTS PASSED - Memory System CRUD is FUNCTIONAL"
    exit 0
else
    echo "⚠️  SOME TESTS FAILED - Memory System needs attention"
    exit 1
fi
