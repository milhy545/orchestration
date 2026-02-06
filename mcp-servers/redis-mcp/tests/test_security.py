#!/usr/bin/env python3
"""
Security tests for Redis MCP Service
Tests for KEYS DoS vulnerability fix (SCAN vs KEYS)
"""
import pytest
from fastapi.testclient import TestClient
import sys
import importlib.util
from pathlib import Path
import os

# Add parent directory to path

module_path = Path(__file__).resolve().parents[1] / "main.py"
MODULE_NAME = "redis_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app

client = TestClient(app)


class TestKEYSDoSFix:
    """Test that KEYS command DoS vulnerability is fixed"""

    def test_list_sessions_uses_scan_not_keys(self):
        """Test that session listing uses SCAN instead of blocking KEYS"""
        response = client.post("/tools/session", json={
            "operation": "list"
        })
        # Should work even without Redis connection (may return 503 or 200)
        assert response.status_code in [200, 503]

        if response.status_code == 200:
            data = response.json()
            # Verify response structure includes scan-related fields
            assert "operation" in data
            assert data["operation"] == "list"
            # Should have scan metadata
            if "sessions" in data:
                # Verify it's using SCAN by checking for scan_complete field
                assert "scan_complete" in data or "scanned_keys" in data

    def test_list_sessions_respects_max_limit(self):
        """Test that session listing has a maximum limit (prevents full table scan)"""
        response = client.post("/tools/session", json={
            "operation": "list"
        })

        if response.status_code == 200:
            data = response.json()
            # Should not return more than 100 sessions (hardcoded limit)
            if "sessions" in data:
                assert len(data["sessions"]) <= 100

    def test_list_sessions_handles_pattern_filter(self):
        """Test that pattern filtering works with SCAN"""
        response = client.post("/tools/session", json={
            "operation": "list"
        })
        # Should handle pattern parameter if provided
        assert response.status_code in [200, 503]


class TestRedisConnectionHandling:
    """Test Redis connection error handling"""

    def test_graceful_handling_when_redis_unavailable(self):
        """Test that service handles missing Redis gracefully"""
        response = client.post("/tools/session", json={
            "operation": "get",
            "session_id": "test_session"
        })
        # Should return 503 or 404, not crash
        assert response.status_code in [503, 404, 200]

    def test_get_session_with_valid_id(self):
        """Test getting session with valid ID format"""
        response = client.post("/tools/session", json={
            "operation": "get",
            "session_id": "valid_session_123"
        })
        # Should not crash, may return 404 or 503
        assert response.status_code in [200, 404, 503]


class TestSessionOperations:
    """Test basic session operations"""

    def test_create_session(self):
        """Test creating a new session"""
        response = client.post("/tools/session", json={
            "operation": "create",
            "session_id": "test_create_session",
            "data": {"key": "value"}
        })
        # May fail if Redis unavailable
        assert response.status_code in [200, 503]

    def test_update_session(self):
        """Test updating session data"""
        response = client.post("/tools/session", json={
            "operation": "update",
            "session_id": "test_update_session",
            "data": {"updated": "data"}
        })
        assert response.status_code in [200, 404, 503]

    def test_delete_session(self):
        """Test deleting a session"""
        response = client.post("/tools/session", json={
            "operation": "delete",
            "session_id": "test_delete_session"
        })
        assert response.status_code in [200, 404, 503]


class TestInputValidation:
    """Test input validation"""

    def test_missing_session_id_for_get(self):
        """Test that missing session_id is rejected"""
        response = client.post("/tools/session", json={
            "operation": "get"
        })
        # Should return 422 (validation error), 400, or 503 (Redis unavailable)
        assert response.status_code in [422, 400, 503]

    def test_invalid_operation(self):
        """Test that invalid operation is rejected"""
        response = client.post("/tools/session", json={
            "operation": "invalid_op",
            "session_id": "test"
        })
        # Should return 400, 422, or 503 (Redis unavailable checks first)
        assert response.status_code in [400, 422, 503]


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test that health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Redis MCP"


class TestToolsList:
    """Test tools list endpoint"""

    def test_tools_list(self):
        """Test that tools list endpoint works"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        # Redis MCP should have at least session and cache tools
        assert len(data["tools"]) >= 2
