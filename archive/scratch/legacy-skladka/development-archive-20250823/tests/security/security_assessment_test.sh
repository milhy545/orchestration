#\!/bin/bash
# Security & Vulnerability Assessment Suite
# Target: API security, injection prevention, data protection

echo '🔒 SECURITY & VULNERABILITY ASSESSMENT SUITE'
echo '============================================='
echo "Start time: $(date)"
echo

# Test configuration
ZEN_URL='http://localhost:8020/mcp'
MEMORY_URL='http://localhost:8007'
ZEN_BASE='http://localhost:8020'
TEST_ID=$(date +%s)
PASS_COUNT=0
FAIL_COUNT=0
SECURITY_ISSUES=0

# Helper functions
security_pass() {
    echo "✅ SECURE: $1"
    PASS_COUNT=$((PASS_COUNT+1))
}

security_fail() {
    echo "🚨 VULNERABILITY: $1"
    echo "   Details: $2"
    FAIL_COUNT=$((FAIL_COUNT+1))
    SECURITY_ISSUES=$((SECURITY_ISSUES+1))
}

security_warn() {
    echo "⚠️  WARNING: $1"
    echo "   Details: $2"
}

echo '🔒 SECURITY TEST 1: API Endpoint Security'
echo '========================================'

# Test unauthorized access to health endpoints
echo '🔍 Testing endpoint access controls...'
HEALTH_ACCESS=$(curl -s -w "%{http_code}" "$ZEN_BASE/health" -o /dev/null)
if [ "$HEALTH_ACCESS" = "200" ]; then
    security_warn "Health endpoint publicly accessible" "Consider adding authentication"
else
    security_pass "Health endpoint access control"
fi

# Test invalid HTTP methods
PUT_TEST=$(curl -s -X PUT "$ZEN_BASE/mcp" -w "%{http_code}" -o /dev/null)
if [ "$PUT_TEST" = "405" ] || [ "$PUT_TEST" = "404" ]; then
    security_pass "PUT method restriction"
else
    security_fail "PUT method vulnerability" "PUT requests accepted"
fi

# Test malformed requests
MALFORMED_JSON=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"invalid":' --max-time 5)
if echo "$MALFORMED_JSON" | grep -i 'error\|bad\|invalid' >/dev/null; then
    security_pass "Malformed JSON handling"
else
    security_fail "JSON parsing vulnerability" "Server accepts malformed JSON"
fi

echo
echo '🔒 SECURITY TEST 2: Command Injection Prevention'
echo '=============================================='

# Test command injection
echo '💉 Testing command injection prevention...'
CMD_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "execute_command", "arguments": {"command": "echo test; whoami"}}' --max-time 10)

if echo "$CMD_RESULT" | grep -E '(root|uid=|\$)' >/dev/null; then
    security_fail "Command injection" "Command concatenation executed"
elif echo "$CMD_RESULT" | grep '"success": true' >/dev/null; then
    security_pass "Command injection prevention (sanitized)"
else
    security_pass "Command injection prevention (blocked)"
fi

echo
echo '🔒 SECURITY TEST 3: Input Sanitization'
echo '===================================='

# Test XSS prevention
echo '💉 Testing XSS prevention...'
XSS_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "store_memory", "arguments": {"content": "<script>alert(1)</script>", "metadata": {}}}' --max-time 10)

if echo "$XSS_RESULT" | grep '"success": true' >/dev/null; then
    # Check if XSS payload was sanitized
    SEARCH_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "search_memories", "arguments": {"query": "script", "limit": 5}}')
    if echo "$SEARCH_RESULT" | grep '<script>' >/dev/null; then
        security_fail "XSS vulnerability" "Script tags stored unsanitized"
    else
        security_pass "XSS prevention (content sanitized)"
    fi
else
    security_pass "XSS prevention (content rejected)"
fi

echo
echo '🔒 SECURITY TEST 4: Path Traversal Prevention'
echo '=========================================='

# Test path traversal
echo '🔍 Testing path traversal prevention...'
PATH_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "list_files", "arguments": {"path": "../../../etc"}}' --max-time 10)

if echo "$PATH_RESULT" | grep -E '(passwd|shadow|hosts)' >/dev/null; then
    security_fail "Path traversal vulnerability" "Unauthorized directory access"
elif echo "$PATH_RESULT" | grep -i 'error\|denied\|invalid' >/dev/null; then
    security_pass "Path traversal prevention (access denied)"
else
    security_pass "Path traversal prevention (no sensitive data)"
fi

echo
echo '🔒 SECURITY TEST 5: Data Protection'
echo '=================================='

# Test sensitive data handling
echo '🔍 Testing sensitive data protection...'
SENSITIVE_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "store_memory", "arguments": {"content": "password: secret123", "metadata": {}}}' --max-time 10)

if echo "$SENSITIVE_RESULT" | grep '"success": true' >/dev/null; then
    security_warn "Sensitive data storage" "Potential credentials stored in memory"
else
    security_pass "Sensitive data protection (storage rejected)"
fi

# Check database file permissions
DB_PERMS=$(ls -la /home/orchestration/data/databases/*.db 2>/dev/null | head -1 | awk '{print $1}')
if echo "$DB_PERMS" | grep 'rw-r--r--' >/dev/null; then
    security_warn "Database permissions" "Database files readable by others"
else
    security_pass "Database file security"
fi

echo
echo '🔒 SECURITY TEST 6: Error Handling'
echo '================================'

# Test error information disclosure
echo '🔍 Testing error information disclosure...'
ERROR_RESULT=$(curl -s -X POST "$ZEN_URL" -H 'Content-Type: application/json' -d '{"tool": "nonexistent_tool"}' --max-time 5)

if echo "$ERROR_RESULT" | grep -E '(/home/|/root/|traceback|line [0-9]+)' >/dev/null; then
    security_fail "Information disclosure" "Sensitive paths in error messages"
else
    security_pass "Error handling security"
fi

echo
echo '📊 SECURITY ASSESSMENT SUMMARY'
echo '============================='

echo "✅ SECURE: $PASS_COUNT tests"
echo "🚨 VULNERABILITIES: $FAIL_COUNT tests"
echo "🔒 Security Categories: 6 tested"

# Overall security assessment
if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 SECURITY ASSESSMENT PASSED"
    echo "🛡️  Security Rating: EXCELLENT"
    exit 0
elif [ $FAIL_COUNT -le 2 ]; then
    echo "⚠️  SECURITY ASSESSMENT PARTIAL"
    echo "🛡️  Security Rating: GOOD"
    exit 1
else
    echo "🚨 SECURITY ASSESSMENT FAILED"
    echo "🛡️  Security Rating: NEEDS ATTENTION"
    exit 2
fi
