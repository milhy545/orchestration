#!/usr/bin/env python3
"""
Security MCP Service Tests
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import jwt
import bcrypt
import json
import base64

# Import the main app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if 'main' in sys.modules:
    del sys.modules['main']

from main import app, SECRET_KEY, ALGORITHM

client = TestClient(app)

class TestSecurityMCPHealth:
    """Test health and basic functionality"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Security MCP"
        assert data["port"] == 7008
        assert "features" in data
        assert len(data["features"]) == 4
        assert "security" in data

    def test_tools_list_endpoint(self):
        """Test tools listing"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 6
        
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = ["jwt_token", "password_hash", "password_verify", "encrypt", "decrypt", "ssl_check"]
        
        for tool in expected_tools:
            assert tool in tool_names

class TestJWTTokenTool:
    """Test JWT token functionality"""
    
    def test_jwt_token_generation(self):
        """Test JWT token generation"""
        token_data = {
            "username": "testuser",
            "permissions": ["read", "write"],
            "expire_minutes": 60
        }
        
        response = client.post("/tools/jwt_token", json=token_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["username"] == "testuser"
        assert data["permissions"] == ["read", "write"]
        assert "expires_at" in data
        assert data["algorithm"] == ALGORITHM
        
        # Verify token can be decoded
        decoded = jwt.decode(data["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
        assert decoded["sub"] == "testuser"
        assert decoded["permissions"] == ["read", "write"]

    def test_jwt_token_default_expiration(self):
        """Test JWT token with default expiration"""
        token_data = {
            "username": "testuser",
            "permissions": []
        }
        
        response = client.post("/tools/jwt_token", json=token_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["expires_in_seconds"] == 30 * 60  # 30 minutes

class TestPasswordHashTool:
    """Test password hashing functionality"""
    
    def test_password_hash_basic(self):
        """Test basic password hashing"""
        hash_data = {
            "password": "SecurePass123!",
            "salt_rounds": 12
        }
        
        response = client.post("/tools/password_hash", json=hash_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "hashed_password" in data
        assert data["salt_rounds"] == 12
        assert "password_strength" in data
        
        # Verify hash can be used with bcrypt
        is_valid = bcrypt.checkpw(
            "SecurePass123!".encode('utf-8'),
            data["hashed_password"].encode('utf-8')
        )
        assert is_valid

    def test_password_strength_analysis(self):
        """Test password strength analysis"""
        # Strong password
        strong_data = {
            "password": "StrongPass123!@#",
            "salt_rounds": 10
        }
        
        response = client.post("/tools/password_hash", json=strong_data)
        assert response.status_code == 200
        
        data = response.json()
        strength = data["password_strength"]
        assert strength["score"] >= 4
        assert strength["level"] in ["Good", "Strong"]
        
        # Weak password
        weak_data = {
            "password": "weak",
            "salt_rounds": 10
        }
        
        response = client.post("/tools/password_hash", json=weak_data)
        assert response.status_code == 200
        
        data = response.json()
        strength = data["password_strength"]
        assert strength["score"] <= 2
        assert len(strength["issues"]) > 0

class TestPasswordVerifyTool:
    """Test password verification functionality"""
    
    def test_password_verify_success(self):
        """Test successful password verification"""
        # First hash a password
        password = "TestPassword123!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        verify_data = {
            "password": password,
            "hashed_password": hashed.decode('utf-8')
        }
        
        response = client.post("/tools/password_verify", json=verify_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_valid"] is True
        assert "verified_at" in data

    def test_password_verify_failure(self):
        """Test failed password verification"""
        # Hash one password but verify different one
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword456!"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        verify_data = {
            "password": wrong_password,
            "hashed_password": hashed.decode('utf-8')
        }
        
        response = client.post("/tools/password_verify", json=verify_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["is_valid"] is False

class TestEncryptionTools:
    """Test encryption and decryption functionality"""
    
    def test_encrypt_with_password(self):
        """Test data encryption with password"""
        encrypt_data = {
            "data": "Secret message to encrypt",
            "password": "mypassword123"
        }
        
        response = client.post("/tools/encrypt", json=encrypt_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "encrypted_data" in data
        assert data["key_derivation"] == "password"
        assert "key_info" in data
        assert data["algorithm"] == "Fernet"

    def test_encrypt_generate_key(self):
        """Test data encryption with generated key"""
        encrypt_data = {
            "data": "Secret message to encrypt"
        }
        
        response = client.post("/tools/encrypt", json=encrypt_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "encrypted_data" in data
        assert data["key_derivation"] == "generated"
        assert "key_info" in data

class TestSSLCheckTool:
    """Test SSL certificate checking functionality"""
    
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    def test_ssl_check_success(self, mock_ssl_context, mock_socket):
        """Test successful SSL certificate check"""
        # Mock SSL context and socket
        mock_context = MagicMock()
        mock_ssl_context.return_value = mock_context
        
        mock_sock = MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_sock
        
        mock_ssl_sock = MagicMock()
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
        
        # Mock certificate
        mock_cert = {
            'subject': [['CN', 'example.com']],
            'issuer': [['CN', 'Test CA']],
            'notBefore': 'Jan  1 00:00:00 2024 GMT',
            'notAfter': 'Dec 31 23:59:59 2024 GMT',
            'serialNumber': '1234567890',
            'version': 3
        }
        mock_ssl_sock.getpeercert.return_value = mock_cert
        mock_ssl_sock.cipher.return_value = ('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
        
        ssl_data = {
            "hostname": "example.com",
            "port": 443
        }
        
        response = client.post("/tools/ssl_check", json=ssl_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["hostname"] == "example.com"
        assert data["port"] == 443
        assert "certificate" in data
        assert "cipher" in data
        assert "validation" in data

class TestIntegration:
    """Integration tests"""
    
    def test_password_hash_and_verify_integration(self):
        """Test complete password hash and verify workflow"""
        # Hash a password
        password = "IntegrationTest123!"
        hash_data = {
            "password": password,
            "salt_rounds": 10
        }
        
        hash_response = client.post("/tools/password_hash", json=hash_data)
        assert hash_response.status_code == 200
        
        hash_result = hash_response.json()
        hashed_password = hash_result["hashed_password"]
        
        # Verify the same password
        verify_data = {
            "password": password,
            "hashed_password": hashed_password
        }
        
        verify_response = client.post("/tools/password_verify", json=verify_data)
        assert verify_response.status_code == 200
        
        verify_result = verify_response.json()
        assert verify_result["is_valid"] is True

    def test_jwt_token_generation_and_validation(self):
        """Test JWT token generation and manual validation"""
        token_data = {
            "username": "integrationuser",
            "permissions": ["admin", "read", "write"]
        }
        
        response = client.post("/tools/jwt_token", json=token_data)
        assert response.status_code == 200
        
        result = response.json()
        token = result["access_token"]
        
        # Manually decode and validate token
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            assert decoded["sub"] == "integrationuser"
            assert "admin" in decoded["permissions"]
        except jwt.InvalidTokenError:
            pytest.fail("Generated token is invalid")

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])