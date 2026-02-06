#!/usr/bin/env python3
"""
PostgreSQL MCP Security Tests

Tests for SQL injection prevention and security controls.
"""
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
import sys
import importlib.util
from pathlib import Path
import os

# Add parent directory to path for imports

module_path = Path(__file__).resolve().parents[1] / "main.py"
spec = importlib.util.spec_from_file_location("main", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["main"] = module
assert spec.loader is not None
spec.loader.exec_module(module)

from main import app, validate_identifier, validate_schema_name

client = TestClient(app)


class TestIdentifierValidation:
    """Test identifier validation (table names, schema names, column names)"""

    def test_valid_identifiers(self):
        """Test that valid identifiers pass validation"""
        assert validate_identifier("users") == "users"
        assert validate_identifier("table_name") == "table_name"
        assert validate_identifier("_private") == "_private"
        assert validate_identifier("Table123") == "Table123"

    def test_invalid_identifier_empty(self):
        """Test that empty identifiers are rejected"""
        with pytest.raises(Exception) as exc_info:
            validate_identifier("")
        assert "cannot be empty" in str(exc_info.value.detail)

    def test_invalid_identifier_too_long(self):
        """Test that identifiers over 63 chars are rejected"""
        long_name = "a" * 64
        with pytest.raises(Exception) as exc_info:
            validate_identifier(long_name)
        assert "too long" in str(exc_info.value.detail)

    def test_invalid_identifier_special_chars(self):
        """Test that identifiers with special characters are rejected"""
        with pytest.raises(Exception):
            validate_identifier("table; DROP TABLE users--")
        with pytest.raises(Exception):
            validate_identifier("table' OR '1'='1")
        with pytest.raises(Exception):
            validate_identifier("table-name")
        with pytest.raises(Exception):
            validate_identifier("table.name")

    def test_invalid_identifier_pg_prefix(self):
        """Test that pg_ prefixed identifiers are rejected (system reserved)"""
        with pytest.raises(Exception) as exc_info:
            validate_identifier("pg_users")
        assert "system reserved" in str(exc_info.value.detail)

    def test_invalid_identifier_starts_with_number(self):
        """Test that identifiers starting with numbers are rejected"""
        with pytest.raises(Exception):
            validate_identifier("123table")


class TestSchemaNameValidation:
    """Test schema name validation"""

    def test_valid_schemas(self):
        """Test that allowed schemas pass validation"""
        assert validate_schema_name("public") == "public"
        assert validate_schema_name("information_schema") == "information_schema"

    def test_invalid_schema(self):
        """Test that non-allowed schemas are rejected"""
        with pytest.raises(Exception) as exc_info:
            validate_schema_name("custom_schema")
        assert "not allowed" in str(exc_info.value.detail)

        with pytest.raises(Exception):
            validate_schema_name("pg_catalog")


class TestQueryEndpointSecurity:
    """Test /tools/query endpoint security"""

    def test_select_query_allowed(self):
        """Test that structured SELECT queries are allowed"""
        response = client.post("/tools/query", json={
            "schema_name": "public",
            "table": "users",
            "columns": ["id"],
            "limit": 1,
            "offset": 0
        })
        # Note: Will fail with 503 if no DB, but should not fail with 403 (forbidden)
        assert response.status_code in [200, 503, 404]

    def test_invalid_table_blocked(self):
        """Test that invalid table names are blocked"""
        response = client.post("/tools/query", json={
            "schema_name": "public",
            "table": "users; DROP TABLE users",
            "columns": ["id"],
            "limit": 1,
            "offset": 0
        })
        assert response.status_code in [400, 403]

    def test_invalid_schema_blocked(self):
        """Test that invalid schema names are blocked"""
        response = client.post("/tools/query", json={
            "schema_name": "pg_catalog",
            "table": "users",
            "columns": ["id"],
            "limit": 1,
            "offset": 0
        })
        assert response.status_code in [403, 422]
        response = client.post("/tools/query", json={
            "query": "SELECT 1",
            "parameters": [],
            "limit": 999999  # Try to request too many rows
        })
        # Should not error, but should cap the limit
        assert response.status_code in [200, 503]


class TestTransactionEndpoint:
    """Test /tools/transaction endpoint (should be disabled)"""

    def test_transaction_disabled(self):
        """Test that transaction endpoint is disabled for security"""
        response = client.post("/tools/transaction", json={
            "queries": [
                {"query": "SELECT 1", "parameters": []}
            ]
        })
        assert response.status_code in [403, 404]
        assert "disabled" in response.json()["detail"].lower()


class TestSchemaEndpointSecurity:
    """Test /tools/schema endpoint security"""

    def test_describe_allowed(self):
        """Test that DESCRIBE operations are allowed"""
        response = client.post("/tools/schema", json={
            "operation": "describe",
            "schema_name": "public"
        })
        # May fail with 503 if no DB, but should not be 403 (forbidden)
        assert response.status_code in [200, 503]

    def test_create_table_blocked(self):
        """Test that CREATE TABLE is blocked"""
        response = client.post("/tools/schema", json={
            "operation": "create_table",
            "table_name": "hack_table",
            "schema_name": "public",
            "table_definition": {"id": "INT"}
        })
        assert response.status_code in [403, 422]

    def test_drop_table_blocked(self):
        """Test that DROP TABLE is blocked"""
        response = client.post("/tools/schema", json={
            "operation": "drop_table",
            "table_name": "users",
            "schema_name": "public"
        })
        assert response.status_code in [403, 422]

    def test_alter_table_blocked(self):
        """Test that ALTER TABLE is blocked"""
        response = client.post("/tools/schema", json={
            "operation": "alter_table",
            "table_name": "users",
            "schema_name": "public"
        })
        assert response.status_code in [403, 422]

    def test_invalid_schema_rejected(self):
        """Test that invalid schema names are rejected"""
        response = client.post("/tools/schema", json={
            "operation": "describe",
            "schema_name": "custom_schema"
        })
        assert response.status_code in [400, 403, 422]

    def test_sql_injection_in_table_name(self):
        """Test that SQL injection in table name is blocked"""
        response = client.post("/tools/schema", json={
            "operation": "describe",
            "table_name": "users; DROP TABLE users--",
            "schema_name": "public"
        })
        assert response.status_code == 400


class TestHealthEndpoint:
    """Test health endpoint"""

    def test_health_check(self):
        """Test that health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
        assert data["service"] == "PostgreSQL MCP"


class TestToolsList:
    """Test tools list endpoint"""

    def test_tools_list(self):
        """Test that tools list reflects security status"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()

        # Check that security information is included
        assert "security_note" in data

        tools = {tool["name"]: tool for tool in data["tools"]}
        assert "transaction" not in tools

        # Check that query tool has security info
        assert "security" in tools["query"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
