# Security Scan Report - Redis MCP Service

**Service:** Redis MCP
**Port:** 8022
**Scan Date:** 2025-11-17
**Status:** ⚠️ CRITICAL + MEDIUM ISSUES FOUND

## Executive Summary
Found **1 CRITICAL** and **3 MEDIUM** severity vulnerabilities.

## Critical Vulnerabilities

### 1. ⚠️ CRITICAL - Redis KEYS Command DoS Vulnerability
- **Location:** `main.py:350`
- **Function:** `session_tool()` operation "list"
- **Severity:** CRITICAL
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)

**Vulnerable Code:**
```python
elif request.operation == "list":
    # List all sessions (be careful with large datasets)
    pattern = f"{session_prefix}*"
    keys = await client.keys(pattern)  # ❌ CRITICAL: KEYS blocks Redis!

    sessions = []
    for key in keys[:100]:  # Limit to first 100
        session_data = await client.get(key)
```

**Risk:**
- **BLOCKS entire Redis instance** during KEYS operation
- Production Redis DoS with thousands of keys
- All other services using Redis become unresponsive
- O(N) complexity where N = number of keys in database

**Attack Vector:**
```bash
# Create many sessions to trigger slow KEYS operation
for i in {1..10000}; do
  curl -X POST http://localhost:8022/tools/session \
    -d '{"operation":"create","session_data":{"user":"test"}}'
done

# Trigger DoS
curl -X POST http://localhost:8022/tools/session \
  -d '{"operation":"list"}'
```

**Fix Required:**
Replace KEYS with SCAN for non-blocking iteration:
```python
elif request.operation == "list":
    pattern = f"{session_prefix}*"
    sessions = []
    cursor = 0
    count = 0
    max_sessions = 100

    # Use SCAN instead of KEYS
    while count < max_sessions:
        cursor, keys = await client.scan(
            cursor=cursor,
            match=pattern,
            count=10
        )

        for key in keys:
            if count >= max_sessions:
                break
            session_data = await client.get(key)
            if session_data:
                session_info = json.loads(session_data)
                sessions.append({
                    "session_id": session_info.get("id"),
                    "created_at": session_info.get("created_at"),
                    "last_accessed": session_info.get("last_accessed")
                })
                count += 1

        if cursor == 0:  # Scan complete
            break
```

## Medium Severity Issues

### 2. 🟡 MEDIUM - NoSQL Injection in Key Names
- **Location:** Multiple locations (cache, session operations)
- **Severity:** MEDIUM
- **CWE:** CWE-943 (Improper Neutralization of Special Elements)

**Vulnerable Code:**
```python
# No validation of key names
await client.get(request.key)  # ❌ No sanitization
session_key = f"{session_prefix}{request.session_id}"  # ❌ No validation
```

**Risk:**
- Key name manipulation
- Potential data access to other user sessions
- Key pattern injection

**Attack Vector:**
```bash
# Access other user's session
curl -X POST http://localhost:8022/tools/session \
  -d '{
    "operation":"get",
    "session_id":"../other_user_session"
  }'
```

**Fix Required:**
- Validate key names against allowed character set
- Use UUID for session IDs
- Sanitize all user input used in key construction

---

### 3. 🟡 MEDIUM - Missing Input Validation
- **Location:** Throughout the service
- **Severity:** MEDIUM

**Issues:**
- No validation on session_data content
- No size limits on values
- No TTL validation (can be negative or very large)

**Fix Required:**
```python
from pydantic import validator

class SessionRequest(BaseModel):
    operation: str
    session_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    ttl: Optional[int] = 3600

    @validator('session_id')
    def validate_session_id(cls, v):
        if v and not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid session_id format')
        return v

    @validator('ttl')
    def validate_ttl(cls, v):
        if v < 1 or v > 86400:  # Max 24 hours
            raise ValueError('TTL must be between 1 and 86400 seconds')
        return v

    @validator('session_data')
    def validate_session_data(cls, v):
        if v:
            # Check serialized size
            if len(json.dumps(v)) > 10000:  # 10KB limit
                raise ValueError('Session data too large')
        return v
```

---

### 4. 🟡 MEDIUM - Race Condition in Session Update
- **Location:** `main.py:310-331`
- **Severity:** MEDIUM

**Vulnerable Code:**
```python
elif request.operation == "update":
    existing_data = await client.get(session_key)  # ❌ Read
    # ... potential race condition here ...
    session_info = json.loads(existing_data)
    session_info["data"].update(request.session_data)  # ❌ Modify
    await client.setex(session_key, request.ttl, json.dumps(session_info))  # ❌ Write
```

**Risk:**
- Lost updates if multiple requests update same session
- Data corruption in concurrent scenarios

**Fix Required:**
Use Redis transactions or Lua scripts:
```python
# Using Lua script for atomic update
update_script = """
local session_data = redis.call('GET', KEYS[1])
if not session_data then
    return nil
end

local session = cjson.decode(session_data)
local updates = cjson.decode(ARGV[1])

for k, v in pairs(updates) do
    session.data[k] = v
end

session.last_accessed = ARGV[2]
redis.call('SETEX', KEYS[1], ARGV[3], cjson.encode(session))
return session_data
"""

# Register script
update_sha = await client.script_load(update_script)

# Execute atomically
result = await client.evalsha(
    update_sha,
    1,
    session_key,
    json.dumps(request.session_data),
    datetime.now().isoformat(),
    str(request.ttl)
)
```

## Low Severity Issues

### 5. 🟢 LOW - Redis Connection Error Handling
- **Location:** `main.py:156, 250`
- **Severity:** LOW

**Issue:** Generic error handling may mask Redis-specific issues
**Recommendation:** Add specific Redis exception handling

### 6. 🟢 LOW - No Connection Pool Monitoring
- **Location:** Connection pool initialization
- **Severity:** LOW

**Recommendation:** Add connection pool metrics to health check

## Security Strengths

✅ **Good Practices:**
1. Uses connection pooling
2. Implements TTL for cache and sessions
3. JSON serialization for complex data
4. Async/await for non-blocking operations
5. Health check endpoint with Redis status

## Recommendations

### Immediate Actions Required:
1. ✅ Replace KEYS with SCAN (CRITICAL)
2. ⚠️ Add input validation (MEDIUM)
3. ⚠️ Fix race conditions in updates (MEDIUM)

### Security Enhancements:
1. Add authentication for Redis operations
2. Implement key prefix namespacing per user/tenant
3. Add rate limiting
4. Add audit logging for all operations
5. Implement key expiration monitoring
6. Add metrics for cache hit/miss rates

### Code Example - Secure Session ID Generation:
```python
import secrets

def generate_secure_session_id() -> str:
    """Generate cryptographically secure session ID"""
    return secrets.token_urlsafe(32)

@app.post("/tools/session")
async def session_tool(request: SessionRequest) -> Dict[str, Any]:
    if request.operation == "create":
        # Always generate secure session ID
        session_id = generate_secure_session_id()
        # ... rest of logic
```

### Code Example - Input Validation:
```python
import re

def validate_redis_key(key: str) -> str:
    """Validate Redis key format"""
    # Allow only alphanumeric, underscore, hyphen, colon
    if not re.match(r'^[a-zA-Z0-9_:-]+$', key):
        raise HTTPException(
            status_code=400,
            detail="Invalid key format. Allowed: alphanumeric, _, -, :"
        )

    # Limit key length
    if len(key) > 256:
        raise HTTPException(
            status_code=400,
            detail="Key too long (max 256 characters)"
        )

    return key
```

### Code Example - Value Size Limits:
```python
MAX_VALUE_SIZE = 1024 * 1024  # 1MB

def validate_value_size(value: Any) -> None:
    """Validate serialized value size"""
    serialized = json.dumps(value)
    if len(serialized.encode('utf-8')) > MAX_VALUE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Value too large (max {MAX_VALUE_SIZE} bytes)"
        )
```

## Compliance Notes
- **OWASP Top 10:** A04:2021 – Insecure Design (race conditions)
- **Redis Best Practices:** Avoid KEYS in production

## Performance Impact
- KEYS command on large datasets can block Redis for seconds
- SCAN is non-blocking and production-safe
- Consider implementing pagination for list operations

## Next Steps
1. **URGENT:** Replace all KEYS commands with SCAN
2. Add comprehensive input validation
3. Implement atomic operations for updates
4. Add monitoring and alerting
5. Review and implement rate limiting
6. Add session cleanup for expired sessions

---
**Auditor Notes:**
The KEYS command usage is a critical production issue that must be fixed immediately. While Redis is generally well-implemented, the lack of input validation and race conditions in updates present security and reliability risks.
