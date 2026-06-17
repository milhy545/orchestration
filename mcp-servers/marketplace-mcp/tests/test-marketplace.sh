#!/usr/bin/env bash
set -uo pipefail

# Marketplace MCP Test Suite

MARKET_URL="${MARKET_URL:-http://192.168.0.58:7034}"
JWT_SECRET="${JWT_SECRET:-change_me_market_jwt}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
SCRIPTS_DIR="$REPO_ROOT/scripts/marketplace"

PASS=0
FAIL=0
TOTAL=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

test_pass() { PASS=$((PASS+1)); TOTAL=$((TOTAL+1)); echo -e "${GREEN}✓${NC} $1"; }
test_fail() { FAIL=$((FAIL+1)); TOTAL=$((TOTAL+1)); echo -e "${RED}✗${NC} $1"; }
test_section() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

generate_token() {
    local scope="${1:-market:read}"
    uv tool run --from PyJWT python3 -c "
import jwt, datetime
JWT_SECRET = '$JWT_SECRET'
payload = {'sub': 'test-agent', 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1), 'scope': '$scope'}
print(jwt.encode(payload, JWT_SECRET, algorithm='HS256'))
" 2>/dev/null
}

test_section "1. Skill Scanner"

if [ -x "$SCRIPTS_DIR/skill-scanner.py" ]; then
    test_pass "Scanner script exists and is executable"
else
    test_fail "Scanner script missing or not executable"
fi

SCANNER_OUTPUT=$(python3 "$SCRIPTS_DIR/skill-scanner.py" 2>&1)
if echo "$SCANNER_OUTPUT" | grep -q "Total unique skills:"; then
    test_pass "Scanner runs and produces output"
else
    test_fail "Scanner failed to run"
fi

if python3 -c "import json; json.load(open('$REPO_ROOT/mcp-servers/marketplace-mcp/catalog/skills-index.json'))" 2>/dev/null; then
    test_pass "Catalog JSON is valid"
else
    test_fail "Catalog JSON is invalid"
fi

test_section "2. Marketplace API"

HEALTH=$(curl -s "$MARKET_URL/health" 2>/dev/null)
if echo "$HEALTH" | grep -q '"status":"healthy"'; then
    test_pass "Health endpoint returns healthy"
else
    test_fail "Health endpoint failed"
fi

STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$MARKET_URL/skills/v1/index" 2>/dev/null)
if [ "$STATUS" = "401" ]; then
    test_pass "API requires authentication (401)"
else
    test_fail "API should return 401, got $STATUS"
fi

TOKEN=$(generate_token)
STATUS=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" "$MARKET_URL/skills/v1/index" 2>/dev/null)
if [ "$STATUS" = "200" ]; then
    test_pass "Token authentication works"
else
    test_fail "Token auth failed, got $STATUS"
fi

COUNT=$(curl -s -H "Authorization: Bearer $TOKEN" "$MARKET_URL/skills/v1/index" 2>/dev/null | python3 -c "import json,sys; print(json.load(sys.stdin).get('count',0))" 2>/dev/null)
if [ "$COUNT" -gt 0 ]; then
    test_pass "Skills list returns $COUNT skills"
else
    test_fail "Skills list returned 0 skills"
fi

test_section "3. Agent Sync"

if [ -x "$SCRIPTS_DIR/agent-sync.py" ]; then
    test_pass "Agent sync script exists"
else
    test_fail "Agent sync script missing"
fi

SYNCED_SKILLS=("update-all-agents" "mega-orchestrator-mcp" "core-rules")
for skill in "${SYNCED_SKILLS[@]}"; do
    if [ -L "$HOME/.pi/agent/skills/$skill" ] || [ -d "$HOME/.pi/agent/skills/$skill" ]; then
        test_pass "Skill synced to Pi: $skill"
    else
        test_fail "Skill not synced to Pi: $skill"
    fi
done

test_section "4. HAS Sync"

if [ -x "$SCRIPTS_DIR/sync-catalog-to-has.sh" ]; then
    test_pass "HAS sync script exists"
else
    test_fail "HAS sync script missing"
fi

if curl -s "$MARKET_URL/health" >/dev/null 2>&1; then
    test_pass "HAS marketplace is reachable"
else
    test_fail "HAS marketplace unreachable"
fi

echo -e "\n${YELLOW}========================================${NC}"
echo -e "${YELLOW}TEST SUMMARY${NC}"
echo -e "${YELLOW}========================================${NC}"
echo -e "Total:  $TOTAL"
echo -e "${GREEN}Passed: $PASS${NC}"
if [ $FAIL -gt 0 ]; then
    echo -e "${RED}Failed: $FAIL${NC}"
else
    echo -e "Failed: 0"
fi
echo -e "${YELLOW}========================================${NC}"

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed.${NC}"
    exit 1
fi
