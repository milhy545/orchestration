#!/usr/bin/env python3
"""
Database MCP Service Tests
Tests for SQL injection, security vulnerabilities, performance, and functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import sqlite3

# Import the main app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


class TestDatabaseMCPHealth:
    """Test basic functionality"""

    def test_health_check(self):
        """Test if service has health endpoint (should add one)"""
        # This service doesn't have health endpoint yet
        # After refactoring, this should pass
        pass


class TestQueryExecution:
    """Test query execution functionality"""

    @patch('main.get_db_connection')
    def test_execute_select_query(self, mock_get_conn):
        """Test successful SELECT query"""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.post("/db/execute", params={"query": "SELECT * FROM users"})
        assert response.status_code == 200

        data = response.json()
        assert data["columns"] == ["id", "name"]
        assert len(data["rows"]) == 2

    @patch('main.get_db_connection')
    def test_execute_query_with_params(self, mock_get_conn):
        """Test parameterized query"""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.post(
            "/db/execute",
            params={"query": "SELECT * FROM users WHERE id = ?", "params": [1]}
        )
        assert response.status_code == 200

    @patch('main.get_db_connection')
    def test_execute_query_database_error(self, mock_get_conn):
        """Test database error handling"""
        mock_conn = MagicMock()
        mock_conn.cursor.side_effect = sqlite3.Error("Database error")
        mock_get_conn.return_value = mock_conn

        response = client.post("/db/execute", params={"query": "INVALID SQL"})
        assert response.status_code == 500
        assert "database error" in response.json()["detail"].lower()


class TestListTables:
    """Test table listing functionality"""

    @patch('main.get_db_connection')
    def test_list_tables_success(self, mock_get_conn):
        """Test successful table listing"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{"name": "users"}, {"name": "products"}]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/tables")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "users"

    @patch('main.get_db_connection')
    def test_list_tables_empty(self, mock_get_conn):
        """Test listing when no tables exist"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/tables")
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestTableSchema:
    """Test table schema functionality"""

    @patch('main.get_db_connection')
    def test_describe_table_success(self, mock_get_conn):
        """Test successful table description"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {"name": "id", "type": "INTEGER"},
            {"name": "name", "type": "TEXT"}
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/schema/users")
        assert response.status_code == 200

        data = response.json()
        assert data["table_name"] == "users"
        assert len(data["columns"]) == 2

    @patch('main.get_db_connection')
    def test_describe_nonexistent_table(self, mock_get_conn):
        """Test describing non-existent table"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/schema/nonexistent")
        assert response.status_code == 404


class TestSampleData:
    """Test sample data functionality"""

    @patch('main.get_db_connection')
    def test_get_sample_data_success(self, mock_get_conn):
        """Test getting sample data"""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test"), (2, "test2")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/sample/users")
        assert response.status_code == 200

        data = response.json()
        assert len(data["rows"]) == 2

    @patch('main.get_db_connection')
    def test_get_sample_data_with_limit(self, mock_get_conn):
        """Test getting sample data with custom limit"""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = [(1, "test")]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/sample/users?limit=5")
        assert response.status_code == 200


class TestSecurityVulnerabilities:
    """Test SQL injection and other security vulnerabilities"""

    @patch('main.get_db_connection')
    def test_sql_injection_in_table_name(self, mock_get_conn):
        """Test SQL injection attempt in table name"""
        # This test documents the CURRENT vulnerability
        # After refactoring, this should be blocked

        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # SQL injection attempts
        injection_attempts = [
            "users); DROP TABLE users; --",
            "users UNION SELECT * FROM sqlite_master",
            "users; DELETE FROM users; --",
            "'; DROP TABLE users; --"
        ]

        for injection in injection_attempts:
            response = client.get(f"/db/schema/{injection}")
            # Currently this might execute malicious SQL (vulnerability)
            # After fix, should return 400 or 403

    @patch('main.get_db_connection')
    def test_sql_injection_in_sample_limit(self, mock_get_conn):
        """Test SQL injection in limit parameter"""
        mock_cursor = MagicMock()
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # SQL injection through limit
        response = client.get("/db/sample/users?limit=10; DROP TABLE users")
        # Should handle or reject malicious input

    @patch('main.get_db_connection')
    def test_dangerous_query_execution(self, mock_get_conn):
        """Test execution of dangerous queries"""
        mock_cursor = MagicMock()
        mock_cursor.description = None
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        dangerous_queries = [
            "DROP TABLE users",
            "DELETE FROM users",
            "UPDATE users SET password = 'hacked'",
            "INSERT INTO users VALUES ('hacker', 'password')"
        ]

        for dangerous_query in dangerous_queries:
            response = client.post("/db/execute", params={"query": dangerous_query})
            # Currently these will execute (CRITICAL vulnerability)
            # After fix, should be blocked or require authentication


class TestPerformance:
    """Test performance and resource limits"""

    @patch('main.get_db_connection')
    def test_large_result_set_handling(self, mock_get_conn):
        """Test handling of large result sets"""
        # Simulate large result set (10000 rows)
        large_result = [(i, f"name{i}") for i in range(10000)]

        mock_cursor = MagicMock()
        mock_cursor.description = [("id",), ("name",)]
        mock_cursor.fetchall.return_value = large_result

        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.post("/db/execute", params={"query": "SELECT * FROM users"})
        assert response.status_code == 200

        # Should handle large result set
        # But ideally should have pagination or limit

    @patch('main.get_db_connection')
    def test_connection_cleanup(self, mock_get_conn):
        """Test that connections are properly closed"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/db/tables")
        assert response.status_code == 200

        # Verify connection was closed
        mock_conn.close.assert_called_once()


class TestIntegration:
    """Integration tests"""

    @patch('main.get_db_connection')
    def test_complete_workflow(self, mock_get_conn):
        """Test complete database workflow"""
        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # List tables
        mock_cursor.fetchall.return_value = [{"name": "users"}]
        response = client.get("/db/tables")
        assert response.status_code == 200

        # Get schema
        mock_cursor.fetchall.return_value = [{"name": "id", "type": "INTEGER"}]
        response = client.get("/db/schema/users")
        assert response.status_code == 200

        # Get sample data
        mock_cursor.description = [("id",)]
        mock_cursor.fetchall.return_value = [(1,), (2,)]
        response = client.get("/db/sample/users")
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
