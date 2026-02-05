# Security Scan Report - Security MCP Service

**Service:** Security MCP
**Port:** 7008
**Scan Date:** 2025-11-17
**Status:** ⚠️ SYNTAX ERROR + MEDIUM ISSUES

## Executive Summary
Found **1 CRITICAL** syntax error and **2 MEDIUM** severity issues.

## Critical Issues

### 1. ⚠️ CRITICAL - Syntax Error in FastAPI Initialization
- **Location:** `main.py:30-36`
- **Severity:** CRITICAL (Service won't start)
- **Type:** Syntax Error

**Vulnerable Code:**
```python
app = FastAPI(
# Prometheus metrics instrumentation                  # ❌ Comment in wrong place
Instrumentator().instrument(app).expose(app)         # ❌ Code in FastAPI init
    title="Security MCP Service",
    description="Authentication, encryption, and security validation tools",
    version="1.0.0"
)
```

**Risk:** Service will not start - Python syntax error
**Fix Required:**
```python
app = FastAPI(
    title="Security MCP Service",
    description="Authentication, encryption, and security validation tools",
    version="1.0.0"
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)
```

## Medium Severity Issues

### 2. 🟡 MEDIUM - Hardcoded Secret Key
- **Location:** `main.py:41`
- **Severity:** MEDIUM
- **CWE:** CWE-798 (Use of Hard-coded Credentials)

**Issue:**
```python
SECRET_KEY = secrets.token_urlsafe(32)  # ❌ Regenerated on each restart
```

**Risk:**
- JWT tokens become invalid on server restart
- Different keys across multiple instances
- Session invalidation issues

**Fix Required:**
```python
import os

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    logger.warning("JWT_SECRET_KEY not set, generating random key (dev only)")
    SECRET_KEY = secrets.token_urlsafe(32)
```

### 3. 🟡 MEDIUM - Insecure Decryption Logic
- **Location:** `main.py:273-287`
- **Severity:** MEDIUM

**Vulnerable Code:**
```python
if request.key:
    key = request.key.encode()
else:
    password_bytes = request.password.encode()
    salt = base64.urlsafe_b64decode(request.password.encode())  # ❌ Salt from password?
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt[:16],
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
```

**Issue:** Salt derivation is broken - decoding password as salt
**Risk:** Decryption will fail or use incorrect salt
**Fix Required:** Store and transmit salt with encrypted data

## Low Severity Issues

### 4. 🟢 LOW - Password Strength Check Not Enforced
- **Location:** `main.py:152-179`
- **Severity:** LOW

**Issue:** Password strength is checked but weak passwords are still hashed
**Recommendation:** Add option to reject weak passwords

### 5. 🟢 LOW - SSL Certificate Validation Limited
- **Location:** `main.py:304-365`
- **Severity:** LOW

**Issue:** Basic SSL check without extended validation
**Recommendation:** Add checks for:
- Certificate revocation (OCSP/CRL)
- Certificate chain validation
- Hostname mismatch detection

## Security Strengths

✅ **Good Practices:**
1. Uses bcrypt for password hashing with configurable rounds
2. Uses Fernet for symmetric encryption
3. Uses PBKDF2HMAC for key derivation
4. Implements JWT with expiration
5. SSL/TLS certificate checking
6. Password strength analysis

## Recommendations

### Immediate Actions Required:
1. ✅ Fix FastAPI syntax error (CRITICAL)
2. ⚠️ Fix decryption salt handling (MEDIUM)
3. ⚠️ Use environment variable for SECRET_KEY (MEDIUM)

### Security Enhancements:
1. Add rate limiting for password verification (prevent brute force)
2. Add audit logging for all security operations
3. Implement key rotation mechanism
4. Add certificate pinning option for SSL checks
5. Store encrypted data with metadata (algorithm, salt, IV)

### Code Example - Proper Encryption/Decryption:
```python
import json
import base64

class SecureEncryption:
    @staticmethod
    def encrypt_with_password(data: str, password: str) -> dict:
        """Encrypt data and return metadata"""
        password_bytes = password.encode()
        salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())

        return {
            "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
            "salt": base64.urlsafe_b64encode(salt).decode(),
            "algorithm": "Fernet",
            "kdf": "PBKDF2HMAC",
            "iterations": 100000
        }

    @staticmethod
    def decrypt_with_password(encrypted_package: dict, password: str) -> str:
        """Decrypt data using metadata"""
        password_bytes = password.encode()
        salt = base64.urlsafe_b64decode(encrypted_package["salt"].encode())

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=encrypted_package["iterations"],
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

        fernet = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(
            encrypted_package["encrypted_data"].encode()
        )
        decrypted_data = fernet.decrypt(encrypted_bytes)

        return decrypted_data.decode()
```

### Code Example - Rate Limiting:
```python
from fastapi import Request
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/tools/password_verify")
@limiter.limit("5/minute")  # Max 5 attempts per minute
async def password_verify_tool(request: Request, verify_request: PasswordVerifyRequest):
    # ... verification logic
```

## Compliance Notes
- **OWASP Top 10:** A02:2021 – Cryptographic Failures
- **NIST:** Follows NIST password hashing guidelines (bcrypt)
- **PCI DSS:** Encryption implementation needs key management improvements

## Next Steps
1. Fix syntax error immediately
2. Implement proper key management
3. Add rate limiting for password operations
4. Enhance error handling to prevent information leakage
5. Add comprehensive logging

---
**Auditor Notes:**
Generally good security practices, but needs immediate syntax fix and improved key/secret management. The service implements industry-standard cryptographic operations but needs better operational security.
