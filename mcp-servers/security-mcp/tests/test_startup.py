#!/usr/bin/env python3
"""
Startup tests for Security MCP Service
Verifies that syntax error fix works and service can start
"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if 'main' in sys.modules:
    del sys.modules['main']

from main import app

client = TestClient(app)


class TestServiceStartup:
    """Test that service starts without syntax errors"""

    def test_service_imports_successfully(self):
        """Test that main.py imports without syntax errors"""
        # If we got here, import succeeded
        assert app is not None

    def test_health_endpoint_works(self):
        """Test that health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Security MCP"

    def test_tools_list_endpoint_works(self):
        """Test that tools list endpoint works"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert isinstance(data["tools"], list)
        # Security MCP should have JWT and encryption tools
        assert len(data["tools"]) >= 2
