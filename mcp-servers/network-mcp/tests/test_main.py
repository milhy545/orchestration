#!/usr/bin/env python3
"""
Network MCP Service Tests
"""
import pytest
import asyncio

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import json
import socket

# Import the main app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if 'main' in sys.modules:
    del sys.modules['main']

from main import app

client = TestClient(app)

class TestNetworkMCPHealth:
    """Test health and basic functionality"""
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Network MCP"
        assert data["port"] == 7006
        assert "features" in data
        assert len(data["features"]) == 4

    def test_tools_list_endpoint(self):
        """Test tools listing"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) == 4
        
        tool_names = [tool["name"] for tool in data["tools"]]
        expected_tools = ["http_request", "webhook_create", "dns_lookup", "api_test"]
        
        for tool in expected_tools:
            assert tool in tool_names

class TestHttpRequestTool:
    """Test HTTP request functionality"""
    
    @patch('socket.getaddrinfo')
    @patch('httpx.AsyncClient')
    def test_http_request_get(self, mock_client, mock_getaddrinfo):
        """Test basic GET request"""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, None, None, None, ("93.184.216.34", 0))
        ]
        # Mock httpx response
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"message": "success"}'
        mock_response.url = "https://api.example.com/test"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        # Test request
        request_data = {
            "url": "https://api.example.com/test",
            "method": "GET"
        }
        
        response = client.post("/tools/http_request", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status_code"] == 200
        assert data["body"] == '{"message": "success"}'
        assert "response_time" in data

    @patch('socket.getaddrinfo')
    @patch('httpx.AsyncClient')
    def test_http_request_post_with_json(self, mock_client, mock_getaddrinfo):
        """Test POST request with JSON body"""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, None, None, None, ("93.184.216.34", 0))
        ]
        mock_response = AsyncMock()
        mock_response.status_code = 201
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"id": 123}'
        mock_response.url = "https://api.example.com/create"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        request_data = {
            "url": "https://api.example.com/create",
            "method": "POST",
            "headers": {"Authorization": "Bearer token123"},
            "body": {"name": "test", "value": 42}
        }
        
        response = client.post("/tools/http_request", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status_code"] == 201

class TestWebhookTool:
    """Test webhook functionality"""
    
    def test_webhook_create(self):
        """Test webhook creation"""
        webhook_data = {
            "webhook_id": "test-webhook-123",
            "url": "https://example.com/callback",
            "secret": "secret123",
            "events": ["push", "pull_request"],
            "active": True
        }
        
        response = client.post("/tools/webhook_create", json=webhook_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["webhook_id"] == "test-webhook-123"
        assert "webhook_url" in data
        assert data["target_url"] == "https://example.com/callback"
        assert data["events"] == ["push", "pull_request"]

    def test_webhook_receiver(self):
        """Test webhook payload reception"""
        # First create a webhook
        webhook_data = {
            "webhook_id": "test-receiver",
            "url": "https://example.com/callback",
            "active": True
        }
        
        create_response = client.post("/tools/webhook_create", json=webhook_data)
        assert create_response.status_code == 200
        
        # Send payload to webhook
        payload = {"event": "test", "data": {"key": "value"}}
        
        response = client.post("/webhooks/test-receiver", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "received"
        assert data["webhook_id"] == "test-receiver"

    def test_webhook_not_found(self):
        """Test webhook not found error"""
        payload = {"event": "test"}
        
        response = client.post("/webhooks/nonexistent", json=payload)
        assert response.status_code == 404

class TestDnsLookupTool:
    """Test DNS lookup functionality"""
    
    @patch('socket.gethostbyname')
    def test_dns_lookup_a_record_fallback(self, mock_gethostbyname):
        """Test DNS A record lookup with socket fallback"""
        mock_gethostbyname.return_value = "93.184.216.34"
        
        lookup_data = {
            "hostname": "example.com",
            "record_type": "A"
        }
        
        response = client.post("/tools/dns_lookup", json=lookup_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["hostname"] == "example.com"
        assert data["record_type"] == "A"
        assert "93.184.216.34" in data["results"]

    def test_dns_lookup_invalid_hostname(self):
        """Test DNS lookup with invalid hostname"""
        lookup_data = {
            "hostname": "this-domain-does-not-exist-12345.invalid",
            "record_type": "A"
        }
        
        response = client.post("/tools/dns_lookup", json=lookup_data)
        assert response.status_code == 404

class TestApiTestTool:
    """Test API testing functionality"""
    
    @patch('socket.getaddrinfo')
    @patch('httpx.AsyncClient')
    def test_api_test_success(self, mock_client, mock_getaddrinfo):
        """Test successful API endpoint testing"""
        mock_getaddrinfo.return_value = [
            (socket.AF_INET, None, None, None, ("93.184.216.34", 0))
        ]
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.content = b'{"status": "ok"}'
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        test_data = {
            "base_url": "https://api.example.com",
            "endpoints": ["/health", "/status", "/version"],
            "expected_status": 200
        }
        
        response = client.post("/tools/api_test", json=test_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_endpoints"] == 3
        assert data["successful_endpoints"] >= 0
        assert "results" in data
        assert len(data["results"]) == 3


class TestSSRFProtection:
    """Test SSRF protections"""

    def test_http_request_blocks_localhost(self):
        response = client.post("/tools/http_request", json={
            "url": "http://127.0.0.1",
            "method": "GET"
        })
        assert response.status_code == 403

class TestIntegration:
    """Integration tests"""
    
    def test_webhooks_list_empty(self):
        """Test webhook listing when empty"""
        response = client.get("/webhooks")
        assert response.status_code == 200
        
        data = response.json()
        assert "active_webhooks" in data
        assert "webhooks" in data

    def test_webhook_logs_empty(self):
        """Test webhook logs when empty"""
        response = client.get("/webhook-logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_logs" in data
        assert "logs" in data

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
