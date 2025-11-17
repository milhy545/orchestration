# Security Scan Report - Network MCP Service

**Service:** Network MCP
**Port:** 8006
**Scan Date:** 2025-11-17
**Status:** ⚠️ MEDIUM ISSUES FOUND

## Executive Summary
Found **3 MEDIUM** severity vulnerabilities related to SSRF and resource abuse.

## Medium Severity Issues

### 1. 🟡 MEDIUM - Server-Side Request Forgery (SSRF)
- **Location:** `main.py:88-134` (http_request_tool)
- **Severity:** MEDIUM
- **CWE:** CWE-918 (Server-Side Request Forgery)

**Vulnerable Code:**
```python
@app.post("/tools/http_request")
async def http_request_tool(request: HttpRequest) -> HttpResponse:
    async with httpx.AsyncClient(follow_redirects=request.follow_redirects) as client:
        kwargs = {
            "method": request.method.upper(),
            "url": str(request.url),  # ❌ No URL validation
            "timeout": request.timeout or 30
        }
        response = await client.request(**kwargs)
```

**Risk:**
- Access to internal services (localhost, 127.0.0.1, 169.254.169.254)
- Cloud metadata endpoints (AWS, GCP, Azure)
- Internal network scanning

**Attack Vectors:**
```bash
# Access AWS metadata
curl -X POST http://localhost:8006/tools/http_request \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'

# Access internal Redis
curl -X POST http://localhost:8006/tools/http_request \
  -d '{"url": "http://redis:6379/"}'

# Scan internal network
curl -X POST http://localhost:8006/tools/http_request \
  -d '{"url": "http://10.0.0.1:22/"}'
```

**Fix Required:**
- Implement URL whitelist/blacklist
- Block private IP ranges (RFC 1918)
- Block cloud metadata endpoints
- Add DNS rebinding protection

---

### 2. 🟡 MEDIUM - Webhook URL Validation Missing
- **Location:** `main.py:136-162` (webhook_create_tool)
- **Severity:** MEDIUM
- **CWE:** CWE-918 (SSRF via webhooks)

**Vulnerable Code:**
```python
@app.post("/tools/webhook_create")
async def webhook_create_tool(config: WebhookConfig) -> Dict[str, Any]:
    # Store webhook configuration
    active_webhooks[config.webhook_id] = config  # ❌ No URL validation

    webhook_url = f"http://localhost:8006/webhooks/{config.webhook_id}"
```

**Risk:**
- Webhooks can target internal services
- Potential for SSRF via webhook forwarding
- No rate limiting on webhook creation

**Fix Required:**
- Validate webhook target URLs
- Implement webhook signing/verification
- Add rate limiting

---

### 3. 🟡 MEDIUM - DNS Lookup Information Disclosure
- **Location:** `main.py:210-259` (dns_lookup_tool)
- **Severity:** MEDIUM
- **CWE:** CWE-200 (Information Exposure)

**Vulnerable Code:**
```python
@app.post("/tools/dns_lookup")
async def dns_lookup_tool(lookup: DnsLookup) -> Dict[str, Any]:
    # Perform DNS query
    answers = resolver.resolve(lookup.hostname, lookup.record_type)  # ❌ No restrictions
```

**Risk:**
- Internal network enumeration via DNS
- Information gathering about internal infrastructure
- Potential for DNS tunneling detection

**Fix Required:**
- Limit DNS lookups to public domains
- Add rate limiting
- Log all DNS queries for monitoring

---

### 4. 🟡 MEDIUM - No Rate Limiting
- **Location:** All endpoints
- **Severity:** MEDIUM
- **CWE:** CWE-770 (Allocation of Resources Without Limits)

**Risk:**
- API abuse
- Resource exhaustion
- DDoS amplification (via DNS, HTTP requests)

**Fix Required:** Add rate limiting to all endpoints

---

### 5. 🟡 MEDIUM - Webhook Secret Not Enforced
- **Location:** `main.py:190-208` (forward_webhook)
- **Severity:** MEDIUM

**Vulnerable Code:**
```python
async def forward_webhook(config: WebhookConfig, payload: Dict[str, Any]):
    headers = {"Content-Type": "application/json"}
    if config.secret:
        headers["X-Webhook-Secret"] = config.secret  # ❌ Secret in header, not HMAC
```

**Risk:**
- Weak webhook authentication
- No verification of webhook authenticity
- Plaintext secret transmission

**Fix Required:** Implement HMAC signature verification

## Low Severity Issues

### 6. 🟢 LOW - In-Memory Storage
- **Location:** `main.py:74-75`
- **Severity:** LOW

**Issue:**
```python
active_webhooks: Dict[str, WebhookConfig] = {}
webhook_logs: List[Dict] = []
```

**Risk:** Data loss on restart, not suitable for production
**Recommendation:** Use Redis or database for persistence

### 7. 🟢 LOW - Unlimited Webhook Logs
- **Location:** `main.py:177-183`
- **Severity:** LOW

**Issue:** Webhook logs grow unbounded
**Fix:** Implement log rotation or size limits

## Recommendations

### Immediate Actions Required:
1. ✅ Implement SSRF protection (MEDIUM)
2. ✅ Add URL validation for webhooks (MEDIUM)
3. ✅ Add rate limiting (MEDIUM)

### Security Enhancements:
1. Add authentication for webhook creation
2. Implement HMAC webhook signing
3. Add request/response size limits
4. Add comprehensive logging and monitoring
5. Implement webhook retry logic with exponential backoff

### Code Example - SSRF Protection:
```python
import ipaddress
from urllib.parse import urlparse

# Blocked IP ranges
BLOCKED_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),      # Private
    ipaddress.ip_network('172.16.0.0/12'),   # Private
    ipaddress.ip_network('192.168.0.0/16'),  # Private
    ipaddress.ip_network('127.0.0.0/8'),     # Loopback
    ipaddress.ip_network('169.254.0.0/16'),  # Link-local
    ipaddress.ip_network('::1/128'),         # IPv6 loopback
    ipaddress.ip_network('fc00::/7'),        # IPv6 private
]

BLOCKED_HOSTNAMES = [
    'localhost',
    'metadata.google.internal',
    '169.254.169.254',  # AWS/Azure metadata
]

def validate_url_safe(url: str) -> bool:
    """Validate URL is safe for SSRF"""
    try:
        parsed = urlparse(url)

        # Check hostname blacklist
        if parsed.hostname.lower() in BLOCKED_HOSTNAMES:
            raise HTTPException(
                status_code=403,
                detail="Access to this hostname is blocked"
            )

        # Resolve hostname to IP
        import socket
        ip_str = socket.gethostbyname(parsed.hostname)
        ip_addr = ipaddress.ip_address(ip_str)

        # Check if IP is in blocked ranges
        for blocked_range in BLOCKED_IP_RANGES:
            if ip_addr in blocked_range:
                raise HTTPException(
                    status_code=403,
                    detail="Access to private IP ranges is blocked"
                )

        return True

    except socket.gaierror:
        raise HTTPException(status_code=400, detail="Invalid hostname")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/tools/http_request")
async def http_request_tool(request: HttpRequest) -> HttpResponse:
    # Validate URL before making request
    validate_url_safe(str(request.url))

    # ... rest of implementation
```

### Code Example - Webhook HMAC Signature:
```python
import hmac
import hashlib

def generate_webhook_signature(payload: dict, secret: str) -> str:
    """Generate HMAC signature for webhook payload"""
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = hmac.new(
        secret.encode(),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    return signature

async def forward_webhook(config: WebhookConfig, payload: Dict[str, Any]):
    """Forward webhook payload with HMAC signature"""
    try:
        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}

            if config.secret:
                signature = generate_webhook_signature(payload, config.secret)
                headers["X-Webhook-Signature"] = f"sha256={signature}"
                headers["X-Webhook-Timestamp"] = str(int(time.time()))

            response = await client.post(
                str(config.url),
                json=payload,
                headers=headers,
                timeout=30
            )
```

### Code Example - Rate Limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/tools/http_request")
@limiter.limit("10/minute")
async def http_request_tool(request: Request, http_req: HttpRequest):
    # ... implementation
```

## Compliance Notes
- **OWASP Top 10:** A10:2021 – Server-Side Request Forgery (SSRF)
- **OWASP API Security:** API8:2023 - Security Misconfiguration

## Next Steps
1. Implement SSRF protection for all HTTP requests
2. Add comprehensive rate limiting
3. Implement proper webhook authentication
4. Add monitoring and alerting for suspicious activity
5. Review and restrict allowed protocols (http, https only)

---
**Auditor Notes:**
The service needs SSRF protection before production deployment. The ability to make arbitrary HTTP requests to any URL presents significant security risks, especially in cloud environments where metadata endpoints can be exploited.
