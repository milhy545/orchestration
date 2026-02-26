#!/usr/bin/env python3
"""
Security MCP Service - Authentication, encryption, security validation
Port: 7008
"""

import base64
import hashlib
import logging
import os
import re
import secrets
import socket
import ssl
import subprocess
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Security MCP Service",
    description="Authentication, encryption, and security validation tools",
    version="1.0.0",
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

security = HTTPBearer(auto_error=False)

# Security configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY") or secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Request/Response Models


class TokenRequest(BaseModel):
    """JWT token generation request"""

    username: str
    permissions: Optional[List[str]] = []
    expire_minutes: Optional[int] = ACCESS_TOKEN_EXPIRE_MINUTES


class PasswordHashRequest(BaseModel):
    """Password hashing request"""

    password: str
    salt_rounds: Optional[int] = 12


class PasswordVerifyRequest(BaseModel):
    """Password verification request"""

    password: str
    hashed_password: str


class EncryptionRequest(BaseModel):
    """Data encryption request"""

    data: str
    password: Optional[str] = None  # If not provided, generates key


class DecryptionRequest(BaseModel):
    """Data decryption request"""

    encrypted_data: str
    password: str
    key: Optional[str] = None


class SSLCheckRequest(BaseModel):
    """SSL certificate check request"""

    hostname: str
    port: Optional[int] = 443
    timeout: Optional[int] = 10


class SecurityAuditRequest(BaseModel):
    """Security audit request"""

    target_type: str = Field(..., description="Type: password, url, email, code")
    target_value: str
    rules: Optional[List[str]] = []


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Security MCP",
        "port": 7008,
        "timestamp": datetime.now().isoformat(),
        "features": ["jwt_token", "password_hash", "encryption", "ssl_check"],
        "security": {
            "algorithm": ALGORITHM,
            "token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
        },
    }


@app.post("/tools/jwt_token")
async def jwt_token_tool(request: TokenRequest) -> Dict[str, Any]:
    """
    Generate JWT authentication token

    Tool: jwt_token
    Description: Generate JWT tokens with custom permissions and expiration
    """
    try:
        # Create token data
        expire = datetime.utcnow() + timedelta(minutes=request.expire_minutes)

        token_data = {
            "sub": request.username,
            "permissions": request.permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
        }

        # Generate token
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_at": expire.isoformat(),
            "expires_in_seconds": request.expire_minutes * 60,
            "username": request.username,
            "permissions": request.permissions,
            "algorithm": ALGORITHM,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"JWT token generation failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Token generation failed: {str(e)}"
        )


@app.post("/tools/password_hash")
async def password_hash_tool(request: PasswordHashRequest) -> Dict[str, Any]:
    """
    Hash password using bcrypt

    Tool: password_hash
    Description: Securely hash passwords using bcrypt with configurable salt rounds
    """
    try:
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=request.salt_rounds)
        hashed_password = bcrypt.hashpw(request.password.encode("utf-8"), salt)

        # Password strength check
        strength_score = 0
        strength_issues = []

        if len(request.password) >= 8:
            strength_score += 1
        else:
            strength_issues.append("Password should be at least 8 characters")

        if re.search(r"[A-Z]", request.password):
            strength_score += 1
        else:
            strength_issues.append("Password should contain uppercase letters")

        if re.search(r"[a-z]", request.password):
            strength_score += 1
        else:
            strength_issues.append("Password should contain lowercase letters")

        if re.search(r"\d", request.password):
            strength_score += 1
        else:
            strength_issues.append("Password should contain numbers")

        if re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'"\\|,.<>\?]', request.password):
            strength_score += 1
        else:
            strength_issues.append("Password should contain special characters")

        strength_levels = ["Very Weak", "Weak", "Fair", "Good", "Strong"]
        strength = strength_levels[min(strength_score, 4)]

        return {
            "hashed_password": hashed_password.decode("utf-8"),
            "salt_rounds": request.salt_rounds,
            "password_strength": {
                "score": strength_score,
                "level": strength,
                "issues": strength_issues,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Password hashing failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Password hashing failed: {str(e)}"
        )


@app.post("/tools/password_verify")
async def password_verify_tool(request: PasswordVerifyRequest) -> Dict[str, Any]:
    """
    Verify password against hash

    Tool: password_verify
    Description: Verify plaintext password against bcrypt hash
    """
    try:
        # Verify password
        is_valid = bcrypt.checkpw(
            request.password.encode("utf-8"), request.hashed_password.encode("utf-8")
        )

        return {"is_valid": is_valid, "verified_at": datetime.now().isoformat()}

    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Password verification failed: {str(e)}"
        )


@app.post("/tools/encrypt")
async def encrypt_tool(request: EncryptionRequest) -> Dict[str, Any]:
    """
    Encrypt data using Fernet (symmetric encryption)

    Tool: encrypt
    Description: Encrypt data using password-derived key or generate new key
    """
    try:
        if request.password:
            # Derive key from password
            password_bytes = request.password.encode()
            salt = secrets.token_bytes(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
            key_info = base64.urlsafe_b64encode(salt).decode()
        else:
            # Generate random key
            key = Fernet.generate_key()
            key_info = key.decode()

        # Encrypt data
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(request.data.encode())

        return {
            "encrypted_data": base64.urlsafe_b64encode(encrypted_data).decode(),
            "key_derivation": "password" if request.password else "generated",
            "key_info": key_info,
            "algorithm": "Fernet",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Data encryption failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


@app.post("/tools/decrypt")
async def decrypt_tool(request: DecryptionRequest) -> Dict[str, Any]:
    """
    Decrypt data using Fernet

    Tool: decrypt
    Description: Decrypt data using password or provided key
    """
    try:
        if request.key:
            # Use provided key
            key = request.key.encode()
        else:
            # Derive key from password and salt
            password_bytes = request.password.encode()
            # Note: In real implementation, salt would be stored/transmitted with encrypted data
            salt = base64.urlsafe_b64decode(
                request.password.encode()
            )  # Simplified for demo
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt[:16],  # Use first 16 bytes as salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password_bytes))

        # Decrypt data
        fernet = Fernet(key)
        encrypted_bytes = base64.urlsafe_b64decode(request.encrypted_data.encode())
        decrypted_data = fernet.decrypt(encrypted_bytes)

        return {
            "decrypted_data": decrypted_data.decode(),
            "decryption_method": "key" if request.key else "password",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Data decryption failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")


@app.post("/tools/ssl_check")
async def ssl_check_tool(request: SSLCheckRequest) -> Dict[str, Any]:
    """
    Check SSL certificate information

    Tool: ssl_check
    Description: Validate SSL certificates and get certificate details
    """
    try:
        # Create SSL context with modern TLS minimum
        context = ssl.create_default_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2

        # Connect and get certificate
        with socket.create_connection(
            (request.hostname, request.port), timeout=request.timeout
        ) as sock:
            with context.wrap_socket(sock, server_hostname=request.hostname) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()

        # Parse certificate dates
        not_before = datetime.strptime(cert["notBefore"], "%b %d %H:%M:%S %Y %Z")
        not_after = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")

        # Calculate validity
        now = datetime.now()
        is_valid = not_before <= now <= not_after
        expires_in_days = (not_after - now).days

        return {
            "hostname": request.hostname,
            "port": request.port,
            "is_valid": is_valid,
            "certificate": {
                "subject": dict(x[0] for x in cert.get("subject", [])),
                "issuer": dict(x[0] for x in cert.get("issuer", [])),
                "not_before": not_before.isoformat(),
                "not_after": not_after.isoformat(),
                "expires_in_days": expires_in_days,
                "serial_number": cert.get("serialNumber"),
                "version": cert.get("version"),
            },
            "cipher": {
                "name": cipher[0] if cipher else None,
                "protocol": cipher[1] if cipher else None,
                "bits": cipher[2] if cipher else None,
            },
            "validation": {
                "is_expired": now > not_after,
                "expires_soon": expires_in_days <= 30,
                "expires_in_days": expires_in_days,
            },
            "timestamp": datetime.now().isoformat(),
        }

    except socket.timeout:
        raise HTTPException(
            status_code=408,
            detail=f"SSL check timeout for {request.hostname}:{request.port}",
        )
    except socket.gaierror:
        raise HTTPException(
            status_code=404, detail=f"Hostname {request.hostname} not found"
        )
    except ssl.SSLError as e:
        raise HTTPException(status_code=400, detail=f"SSL error: {str(e)}")
    except Exception as e:
        logger.error(f"SSL check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SSL check failed: {str(e)}")


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "jwt_token",
                "description": "Generate JWT tokens with custom permissions and expiration",
                "parameters": {
                    "username": "string (required, username for token)",
                    "permissions": "array (optional, list of permission strings)",
                    "expire_minutes": "integer (optional, default 30 minutes)",
                },
            },
            {
                "name": "password_hash",
                "description": "Securely hash passwords using bcrypt with strength analysis",
                "parameters": {
                    "password": "string (required, password to hash)",
                    "salt_rounds": "integer (optional, default 12 rounds)",
                },
            },
            {
                "name": "password_verify",
                "description": "Verify plaintext password against bcrypt hash",
                "parameters": {
                    "password": "string (required, plaintext password)",
                    "hashed_password": "string (required, bcrypt hash to verify against)",
                },
            },
            {
                "name": "encrypt",
                "description": "Encrypt data using password-derived key or generate new key",
                "parameters": {
                    "data": "string (required, data to encrypt)",
                    "password": "string (optional, password for key derivation)",
                },
            },
            {
                "name": "decrypt",
                "description": "Decrypt data using password or provided key",
                "parameters": {
                    "encrypted_data": "string (required, base64 encrypted data)",
                    "password": "string (required if no key provided)",
                    "key": "string (optional, direct decryption key)",
                },
            },
            {
                "name": "ssl_check",
                "description": "Validate SSL certificates and get certificate details",
                "parameters": {
                    "hostname": "string (required, hostname to check)",
                    "port": "integer (optional, default 443)",
                    "timeout": "integer (optional, default 10 seconds)",
                },
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
