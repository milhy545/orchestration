# Security Scan Report - Research MCP Service

**Service:** Research MCP (Perplexity AI Integration)
**Port:** 8000 (default)
**Scan Date:** 2025-11-17
**Status:** ⚠️ MEDIUM ISSUES FOUND

## Executive Summary
Found **3 MEDIUM** severity vulnerabilities related to API key management and input validation.

## Medium Severity Issues

### 1. 🟡 MEDIUM - API Key Exposure Risk
- **Location:** `main.py:20, 44, 86, 129, 172`
- **Severity:** MEDIUM
- **CWE:** CWE-209 (Information Exposure Through Error Message)

**Vulnerable Code:**
```python
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")  # ❌ No validation

@app.post("/research/news", response_model=SearchResult)
async def search_news(...):
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")  # ❌ Reveals config
```

**Risk:**
- Error messages reveal API key configuration
- API key could leak in error logs
- No validation that API key is valid format

**Fix Required:**
```python
import re

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Validate API key format on startup
if PERPLEXITY_API_KEY:
    if not re.match(r'^pplx-[a-zA-Z0-9]{32,}$', PERPLEXITY_API_KEY):
        logger.error("Invalid PERPLEXITY_API_KEY format")
        PERPLEXITY_API_KEY = None
else:
    logger.error("PERPLEXITY_API_KEY not configured")

def check_api_key_configured():
    """Check API key without revealing configuration"""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Research service not configured"  # ❌ Don't reveal what's missing
        )

@app.post("/research/news")
async def search_news(...):
    check_api_key_configured()
    # ... rest
```

---

### 2. 🟡 MEDIUM - Unvalidated Schema Input
- **Location:** `main.py:165-215` (structured search)
- **Severity:** MEDIUM
- **CWE:** CWE-20 (Improper Input Validation)

**Vulnerable Code:**
```python
@app.post("/research/structured", response_model=StructuredResult)
async def search_structured(
    query: str,
    schema: dict,  # ❌ No validation on schema structure
    model: str = Query(...)
):
    payload = {
        # ...
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "schema": schema  # ❌ Directly passes user schema
            }
        }
    }
```

**Risk:**
- Malformed schema could cause API errors
- Excessive schema complexity could cause timeouts
- No size limits on schema

**Fix Required:**
```python
from pydantic import BaseModel, validator

MAX_SCHEMA_SIZE = 10000  # 10KB

class StructuredSearchRequest(BaseModel):
    query: str
    schema: dict
    model: str = "sonar-pro"

    @validator('query')
    def validate_query(cls, v):
        if len(v) > 5000:
            raise ValueError('Query too long (max 5000 chars)')
        if len(v.strip()) == 0:
            raise ValueError('Query cannot be empty')
        return v

    @validator('schema')
    def validate_schema(cls, v):
        # Check size
        schema_str = json.dumps(v)
        if len(schema_str) > MAX_SCHEMA_SIZE:
            raise ValueError(f'Schema too large (max {MAX_SCHEMA_SIZE} bytes)')

        # Validate it's a valid JSON schema structure
        required_keys = ['type', 'properties']
        if not all(k in v for k in required_keys):
            raise ValueError('Invalid JSON schema structure')

        return v

@app.post("/research/structured")
async def search_structured(request: StructuredSearchRequest):
    # ... implementation
```

---

### 3. 🟡 MEDIUM - No Rate Limiting
- **Location:** All endpoints
- **Severity:** MEDIUM
- **CWE:** CWE-770 (Allocation of Resources Without Limits)

**Risk:**
- API abuse leading to high Perplexity API costs
- Potential account suspension due to rate limit violations
- No protection against automated scraping

**Fix Required:**
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/research/news")
@limiter.limit("10/minute")
async def search_news(request: Request, query: str, model: str = "sonar-pro"):
    # ... implementation

@app.post("/research/structured")
@limiter.limit("5/minute")  # More expensive operation
async def search_structured(request: Request, search_req: StructuredSearchRequest):
    # ... implementation
```

---

### 4. 🟡 MEDIUM - Insufficient Error Handling
- **Location:** All endpoints (lines 74-75, 119-120, etc.)
- **Severity:** MEDIUM

**Vulnerable Code:**
```python
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))  # ❌ Exposes full error
```

**Risk:**
- Perplexity API errors might expose sensitive info
- Stack traces could reveal implementation details
- API key might be in error messages

**Fix Required:**
```python
import traceback

class PerplexityAPIError(Exception):
    """Custom exception for Perplexity API errors"""
    pass

async def make_perplexity_request(url: str, headers: dict, payload: dict):
    """Centralized API request with proper error handling"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        logger.error(f"Perplexity API HTTP error: {e.response.status_code}")
        if e.response.status_code == 401:
            raise HTTPException(status_code=503, detail="Research service authentication failed")
        elif e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limit exceeded, please try again later")
        else:
            raise HTTPException(status_code=502, detail="Research service unavailable")

    except httpx.TimeoutException:
        logger.error("Perplexity API timeout")
        raise HTTPException(status_code=504, detail="Research request timeout")

    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {str(e)}")
        logger.debug(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal server error")
```

## Low Severity Issues

### 5. 🟢 LOW - No Query Validation
- **Location:** All endpoints
- **Severity:** LOW

**Issue:** No validation on query length or content
**Fix:**
```python
from pydantic import validator

class SearchQuery(BaseModel):
    query: str

    @validator('query')
    def validate_query(cls, v):
        if len(v) > 5000:
            raise ValueError('Query too long (max 5000 characters)')
        if len(v.strip()) < 3:
            raise ValueError('Query too short (min 3 characters)')
        return v.strip()
```

---

### 6. 🟢 LOW - No Request Logging
- **Location:** All endpoints
- **Severity:** LOW

**Issue:** No audit trail of API usage
**Recommendation:**
```python
import logging

audit_logger = logging.getLogger('audit')

@app.post("/research/news")
async def search_news(query: str, model: str = "sonar-pro"):
    audit_logger.info(
        f"research_request type=news model={model} query_length={len(query)}"
    )
    # ... implementation
```

---

### 7. 🟢 LOW - Model Validation Missing
- **Location:** All endpoints
- **Severity:** LOW

**Issue:** Model parameter not validated against allowed values
**Fix:**
```python
from enum import Enum

class PerplexityModel(str, Enum):
    SONAR_PRO = "sonar-pro"
    SONAR_REASONING_PRO = "sonar-reasoning-pro"
    SONAR_DEEP_RESEARCH = "sonar-deep-research"

@app.post("/research/news")
async def search_news(
    query: str,
    model: PerplexityModel = Query(PerplexityModel.SONAR_PRO)
):
    # model is now validated automatically
```

## Security Strengths

✅ **Good Practices:**
1. ✅ Uses environment variables for API key
2. ✅ Uses httpx with timeout
3. ✅ Pydantic response models
4. ✅ Async/await for non-blocking operations
5. ✅ Health check endpoint
6. ✅ Prometheus metrics instrumentation
7. ✅ Proper HTTP status code handling

## Recommendations

### Immediate Actions Required:
1. ⚠️ Improve error handling to avoid API key leakage (MEDIUM)
2. ⚠️ Add rate limiting (MEDIUM)
3. ⚠️ Validate schema input (MEDIUM)

### Security Enhancements:
1. Add authentication for API endpoints
2. Implement request logging and audit trail
3. Add cost tracking for Perplexity API usage
4. Implement caching for repeated queries
5. Add query sanitization
6. Monitor API quota usage

### Code Example - Complete Secure Implementation:
```python
from fastapi import FastAPI, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, validator, Field
from enum import Enum
import httpx
import logging
import os

# Setup
app = FastAPI(title="Research MCP API - Secure")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

audit_logger = logging.getLogger('audit')

# Configuration
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not PERPLEXITY_API_KEY:
    logging.error("PERPLEXITY_API_KEY not configured")

# Enums and Models
class PerplexityModel(str, Enum):
    SONAR_PRO = "sonar-pro"
    SONAR_REASONING_PRO = "sonar-reasoning-pro"
    SONAR_DEEP_RESEARCH = "sonar-deep-research"

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=5000)
    model: PerplexityModel = PerplexityModel.SONAR_PRO

    @validator('query')
    def sanitize_query(cls, v):
        return v.strip()

# Dependencies
async def verify_api_configured():
    """Verify API is configured without revealing details"""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Service temporarily unavailable"
        )

# Secure endpoint
@app.post("/research/news")
@limiter.limit("10/minute")
async def search_news(
    request: Request,
    search_req: SearchRequest,
    _: None = Depends(verify_api_configured)
):
    audit_logger.info(
        f"news_search model={search_req.model.value} "
        f"query_len={len(search_req.query)}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": search_req.model.value,
                    "messages": [
                        {"role": "system", "content": "You are a helpful AI assistant."},
                        {"role": "user", "content": search_req.query}
                    ]
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json()

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        raise HTTPException(status_code=502, detail="External service error")

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request timeout")

    except Exception:
        logging.exception("Unexpected error in news search")
        raise HTTPException(status_code=500, detail="Internal error")
```

## Cost Management

### Recommendations:
1. Track API usage per user/endpoint
2. Set budget alerts for Perplexity API costs
3. Implement response caching for common queries
4. Add cost estimation before expensive operations
5. Monitor and optimize query performance

### Example - Cost Tracking:
```python
import time

class CostTracker:
    MODEL_COSTS = {
        "sonar-pro": 0.001,  # per request (example)
        "sonar-deep-research": 0.005
    }

    @classmethod
    def log_cost(cls, model: str, tokens: int):
        cost = cls.MODEL_COSTS.get(model, 0)
        logger.info(f"api_cost model={model} tokens={tokens} cost=${cost}")
```

## Compliance Notes
- **Data Privacy:** Log queries carefully - may contain PII
- **API ToS:** Ensure compliance with Perplexity AI Terms of Service
- **Rate Limits:** Respect Perplexity API rate limits

## Next Steps
1. Implement rate limiting immediately
2. Improve error handling to prevent information disclosure
3. Add input validation for all endpoints
4. Implement audit logging
5. Add cost tracking and monitoring
6. Consider caching layer for repeated queries

---
**Auditor Notes:**
The service is generally well-structured but needs security hardening around error handling, rate limiting, and input validation before production deployment. The main risk is potential API key exposure and unconstrained API usage leading to high costs.
