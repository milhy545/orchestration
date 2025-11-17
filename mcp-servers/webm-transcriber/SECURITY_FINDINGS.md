# Security Scan Report - WebM Transcriber MCP Service

**Service:** WebM Transcriber MCP
**Port:** 8000 (default)
**Scan Date:** 2025-11-17
**Status:** ⚠️ CRITICAL SYNTAX ERROR + MEDIUM ISSUES

## Executive Summary
Found **1 CRITICAL** syntax error, **2 MEDIUM** severity vulnerabilities.

## Critical Issues

### 1. ⚠️ CRITICAL - Syntax Error in FastAPI Initialization
- **Location:** `main.py:13-19`
- **Severity:** CRITICAL (Service won't start)
- **Type:** Syntax Error

**Vulnerable Code:**
```python
app = FastAPI(
# Prometheus metrics instrumentation                  # ❌ Comment in wrong place
Instrumentator().instrument(app).expose(app)         # ❌ Code in FastAPI init
    title="WebM Transcriber MCP Server",
    description="Mock transcription service for WebM files",
    version="1.0.0"
)
```

**Risk:** Service will not start - Python syntax error
**Fix Required:**
```python
app = FastAPI(
    title="WebM Transcriber MCP Server",
    description="Mock transcription service for WebM files",
    version="1.0.0"
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)
```

## Medium Severity Issues

### 2. 🟡 MEDIUM - Unvalidated Base64 Input (DoS Risk)
- **Location:** `main.py:44-69` (transcribe_audio)
- **Severity:** MEDIUM
- **CWE:** CWE-400 (Uncontrolled Resource Consumption)

**Vulnerable Code:**
```python
class AudioTranscribeRequest(BaseModel):
    audio_data: str  # Base64 encoded audio data  # ❌ No size validation
    format: Optional[str] = "webm"
    language: Optional[str] = "auto"

@app.post("/transcribe/audio", response_model=TranscriptionResponse)
async def transcribe_audio(request: AudioTranscribeRequest):
    # ... no validation of audio_data size
```

**Risk:**
- Memory exhaustion from large base64 strings
- CPU exhaustion from base64 decoding
- Potential DoS by sending gigabytes of data

**Attack Vector:**
```python
import base64
import requests

# Generate 100MB of data
large_data = base64.b64encode(b'A' * (100 * 1024 * 1024)).decode()

# Send to service
requests.post(
    'http://localhost:8000/transcribe/audio',
    json={
        'audio_data': large_data,
        'format': 'webm'
    }
)
```

**Fix Required:**
```python
from pydantic import BaseModel, validator
import base64

MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB

class AudioTranscribeRequest(BaseModel):
    audio_data: str
    format: Optional[str] = "webm"
    language: Optional[str] = "auto"

    @validator('audio_data')
    def validate_audio_size(cls, v):
        # Validate it's valid base64
        try:
            decoded = base64.b64decode(v)
        except Exception:
            raise ValueError('Invalid base64 encoding')

        # Check size
        if len(decoded) > MAX_AUDIO_SIZE:
            raise ValueError(f'Audio data too large (max {MAX_AUDIO_SIZE} bytes)')

        return v

    @validator('format')
    def validate_format(cls, v):
        allowed_formats = ['webm', 'mp3', 'wav', 'ogg']
        if v.lower() not in allowed_formats:
            raise ValueError(f'Unsupported format. Allowed: {allowed_formats}')
        return v.lower()

    @validator('language')
    def validate_language(cls, v):
        if v != 'auto':
            # Validate against ISO 639-1 codes
            allowed_languages = ['en', 'es', 'fr', 'de', 'auto']
            if v.lower() not in allowed_languages:
                raise ValueError(f'Unsupported language: {v}')
        return v.lower()
```

---

### 3. 🟡 MEDIUM - SSRF via URL Transcription
- **Location:** `main.py:71-96` (transcribe_url)
- **Severity:** MEDIUM
- **CWE:** CWE-918 (Server-Side Request Forgery)

**Vulnerable Code:**
```python
class URLTranscribeRequest(BaseModel):
    url: str  # ❌ No URL validation
    language: Optional[str] = "auto"

@app.post("/transcribe/url", response_model=TranscriptionResponse)
async def transcribe_url(request: URLTranscribeRequest):
    logger.info(f"Transcribing audio from URL: {request.url}")  # ❌ Logs potentially malicious URL
    # Mock implementation - but real implementation would fetch URL
```

**Risk:**
- Access to internal services
- Cloud metadata endpoint access
- Internal network scanning
- Information disclosure

**Attack Vectors:**
```bash
# Access AWS metadata
curl -X POST http://localhost:8000/transcribe/url \
  -d '{"url": "http://169.254.169.254/latest/meta-data/"}'

# Access internal services
curl -X POST http://localhost:8000/transcribe/url \
  -d '{"url": "http://redis:6379/"}'

# Scan internal network
curl -X POST http://localhost:8000/transcribe/url \
  -d '{"url": "http://10.0.0.1:22/"}'
```

**Fix Required:**
```python
from pydantic import BaseModel, validator, HttpUrl
import ipaddress
from urllib.parse import urlparse

BLOCKED_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('169.254.0.0/16'),  # Cloud metadata
]

BLOCKED_SCHEMES = ['file', 'ftp', 'gopher', 'data']

class URLTranscribeRequest(BaseModel):
    url: HttpUrl  # Pydantic validation
    language: Optional[str] = "auto"

    @validator('url')
    def validate_url_safety(cls, v):
        parsed = urlparse(str(v))

        # Check scheme
        if parsed.scheme in BLOCKED_SCHEMES:
            raise ValueError(f'Scheme {parsed.scheme} not allowed')

        # Only allow http/https
        if parsed.scheme not in ['http', 'https']:
            raise ValueError('Only http and https URLs allowed')

        # Resolve and check IP
        import socket
        try:
            ip_str = socket.gethostbyname(parsed.hostname)
            ip_addr = ipaddress.ip_address(ip_str)

            for blocked_range in BLOCKED_IP_RANGES:
                if ip_addr in blocked_range:
                    raise ValueError('Access to private IP ranges not allowed')

        except socket.gaierror:
            raise ValueError('Invalid hostname')

        return v

@app.post("/transcribe/url")
async def transcribe_url(request: URLTranscribeRequest):
    # URL is now validated
    # ... implementation
```

---

### 4. 🟡 MEDIUM - No Rate Limiting
- **Location:** All endpoints
- **Severity:** MEDIUM
- **CWE:** CWE-770

**Risk:** Service abuse, resource exhaustion
**Fix Required:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/transcribe/audio")
@limiter.limit("10/minute")
async def transcribe_audio(request: Request, transcribe_req: AudioTranscribeRequest):
    # ... implementation

@app.post("/transcribe/url")
@limiter.limit("5/minute")  # More restrictive for URL fetching
async def transcribe_url(request: Request, url_req: URLTranscribeRequest):
    # ... implementation
```

## Low Severity Issues

### 5. 🟢 LOW - Mock Implementation
- **Location:** Both endpoints
- **Severity:** LOW (Information)

**Issue:** Service returns mock transcriptions
**Note:** This is intentional for development, but should be clearly documented

---

### 6. 🟢 LOW - No Authentication
- **Location:** All endpoints
- **Severity:** LOW

**Issue:** No authentication mechanism
**Recommendation:** Add API key or JWT authentication for production

---

### 7. 🟢 LOW - Insufficient Logging
- **Location:** Error handling
- **Severity:** LOW

**Issue:** Limited security event logging
**Recommendation:**
```python
import logging

security_logger = logging.getLogger('security')

@app.post("/transcribe/audio")
async def transcribe_audio(request: Request, transcribe_req: AudioTranscribeRequest):
    client_ip = request.client.host

    # Log security-relevant events
    security_logger.info(
        f"transcribe_request client={client_ip} "
        f"format={transcribe_req.format} "
        f"size={len(transcribe_req.audio_data)}"
    )
```

## Security Strengths

✅ **Good Practices:**
1. ✅ Uses Pydantic models
2. ✅ Async/await implementation
3. ✅ Health check endpoint
4. ✅ Proper logging setup
5. ✅ Mock implementation for testing

## Recommendations

### Immediate Actions Required:
1. ✅ Fix FastAPI syntax error (CRITICAL)
2. ⚠️ Add base64 size validation (MEDIUM)
3. ⚠️ Add URL validation for SSRF protection (MEDIUM)
4. ⚠️ Implement rate limiting (MEDIUM)

### Security Enhancements for Production:
1. Add authentication (API key or JWT)
2. Add file type validation (magic bytes check)
3. Implement virus scanning for uploaded audio
4. Add request/response logging
5. Implement timeout for URL fetching
6. Add metrics and monitoring
7. Implement proper transcription service (replace mock)

### Code Example - Complete Secure Implementation:
```python
from fastapi import FastAPI, HTTPException, Request, Depends
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel, validator, HttpUrl
import base64
import magic  # python-magic for file type detection
import logging

app = FastAPI(
    title="WebM Transcriber MCP Server",
    description="Secure transcription service",
    version="2.0.0"
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

security_logger = logging.getLogger('security')

# Configuration
MAX_AUDIO_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_MIME_TYPES = [
    'audio/webm',
    'audio/mpeg',
    'audio/wav',
    'audio/ogg'
]

# Request Models with Validation
class AudioTranscribeRequest(BaseModel):
    audio_data: str
    format: Optional[str] = "webm"
    language: Optional[str] = "auto"

    @validator('audio_data')
    def validate_audio(cls, v):
        try:
            decoded = base64.b64decode(v)
        except Exception:
            raise ValueError('Invalid base64 encoding')

        if len(decoded) > MAX_AUDIO_SIZE:
            raise ValueError(f'Audio too large (max {MAX_AUDIO_SIZE/1024/1024}MB)')

        # Check file type using magic bytes
        mime = magic.from_buffer(decoded, mime=True)
        if mime not in ALLOWED_MIME_TYPES:
            raise ValueError(f'Invalid file type: {mime}')

        return v

# Secure endpoints
@app.post("/transcribe/audio")
@limiter.limit("10/minute")
async def transcribe_audio(
    request: Request,
    transcribe_req: AudioTranscribeRequest
):
    client_ip = request.client.host

    security_logger.info(
        f"audio_transcribe client={client_ip} "
        f"format={transcribe_req.format} "
        f"size={len(transcribe_req.audio_data)}"
    )

    try:
        # Decode and validate
        audio_bytes = base64.b64decode(transcribe_req.audio_data)

        # TODO: Implement actual transcription
        # result = await transcribe_service.transcribe(audio_bytes)

        return {
            "success": True,
            "transcription": "Mock transcription",
            "execution_time": 0.1
        }

    except Exception as e:
        security_logger.error(f"Transcription error: {type(e).__name__}")
        raise HTTPException(status_code=500, detail="Transcription failed")
```

### Code Example - File Type Validation:
```python
import magic

def validate_audio_file(data: bytes, expected_format: str) -> bool:
    """Validate audio file using magic bytes"""
    mime_type = magic.from_buffer(data, mime=True)

    format_mime_map = {
        'webm': 'audio/webm',
        'mp3': 'audio/mpeg',
        'wav': 'audio/wav',
        'ogg': 'audio/ogg'
    }

    expected_mime = format_mime_map.get(expected_format.lower())

    if mime_type != expected_mime:
        raise ValueError(
            f'File type mismatch. Expected {expected_mime}, got {mime_type}'
        )

    return True
```

## Production Deployment Checklist

- [ ] Fix syntax error in FastAPI initialization
- [ ] Add input size validation (base64 limit)
- [ ] Implement SSRF protection for URL endpoint
- [ ] Add rate limiting to all endpoints
- [ ] Implement authentication (API keys)
- [ ] Add file type validation (magic bytes)
- [ ] Implement virus scanning (ClamAV)
- [ ] Add comprehensive logging
- [ ] Set up monitoring and alerts
- [ ] Implement actual transcription service
- [ ] Add unit and integration tests
- [ ] Security scan with bandit/safety
- [ ] Load testing
- [ ] Documentation update

## Compliance Notes
- **OWASP Top 10:** A10:2021 – SSRF, A04:2021 – Insecure Design
- **Data Privacy:** Audio files may contain sensitive information

## Next Steps
1. **URGENT:** Fix syntax error
2. Implement input validation for audio size
3. Add SSRF protection
4. Implement rate limiting
5. Add authentication layer
6. Replace mock implementation with real transcription service

---
**Auditor Notes:**
Service has critical syntax error preventing startup. Once fixed, needs security hardening around input validation and SSRF protection. Currently mock implementation - needs real transcription service integration before production use.
