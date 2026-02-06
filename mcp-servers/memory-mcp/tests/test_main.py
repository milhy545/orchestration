#!/usr/bin/env python3
"""
Memory MCP Service Tests
Tests for PostgreSQL memory operations, security, and performance
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, Mock
import psycopg2

# Import the main app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app

client = TestClient(app)


class TestMemoryMCPHealth:
    """Test health check functionality"""

    @patch('main.get_memory_connection')
    def test_health_check_success(self, mock_get_conn):
        """Test successful health check"""
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "memory-mcp"

    @patch('main.get_memory_connection')
    def test_health_check_failure(self, mock_get_conn):
        """Test health check with database failure"""
        mock_get_conn.side_effect = Exception("Database connection failed")

        response = client.get("/health")
        assert response.status_code == 500


class TestStoreMemory:
    """Test memory storage functionality"""

    @patch('main.get_memory_connection')
    def test_store_memory_success(self, mock_get_conn):
        """Test successful memory storage"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'timestamp': MagicMock(isoformat=lambda: '2024-01-01T00:00:00')
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        memory_data = {
            "content": "Test memory content",
            "type": "user",
            "importance": 0.8,
            "agent": "test-agent"
        }

        response = client.post("/memory/store", json=memory_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data

    @patch('main.get_memory_connection')
    def test_store_memory_with_metadata(self, mock_get_conn):
        """Test storing memory with metadata"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'timestamp': MagicMock(isoformat=lambda: '2024-01-01T00:00:00')
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        memory_data = {
            "content": "Test memory",
            "metadata": {"key": "value", "tags": ["test", "example"]}
        }

        response = client.post("/memory/store", json=memory_data)
        assert response.status_code == 200

    @patch('main.get_memory_connection')
    def test_store_memory_database_error(self, mock_get_conn):
        """Test memory storage with database error"""
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Database error")

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        memory_data = {"content": "Test memory"}

        response = client.post("/memory/store", json=memory_data)
        assert response.status_code == 500


class TestListMemories:
    """Test memory listing functionality"""

    @patch('main.get_memory_connection')
    def test_list_memories_success(self, mock_get_conn):
        """Test successful memory listing"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'content': 'Memory 1',
                'type': 'user',
                'importance': 0.5,
                'agent': 'claude-code',
                'timestamp': MagicMock(isoformat=lambda: '2024-01-01T00:00:00'),
                'metadata': {}
            },
            {
                'id': 2,
                'content': 'Memory 2',
                'type': 'system',
                'importance': 0.8,
                'agent': 'claude-code',
                'timestamp': MagicMock(isoformat=lambda: '2024-01-01T00:01:00'),
                'metadata': {'tag': 'test'}
            }
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/list")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 2
        assert data[0]["content"] == "Memory 1"

    @patch('main.get_memory_connection')
    def test_list_memories_with_pagination(self, mock_get_conn):
        """Test memory listing with pagination"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/list?limit=10&offset=20")
        assert response.status_code == 200

        # Verify pagination parameters were used
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        assert args[1] == (10, 20)


class TestSearchMemories:
    """Test memory search functionality"""

    @patch('main.get_memory_connection')
    def test_search_memories_success(self, mock_get_conn):
        """Test successful memory search"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {
                'id': 1,
                'content': 'Test memory with search term',
                'type': 'user',
                'importance': 0.9,
                'agent': 'claude-code',
                'timestamp': MagicMock(isoformat=lambda: '2024-01-01T00:00:00'),
                'metadata': {}
            }
        ]

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/search?query=search")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert "search term" in data[0]["content"]

    @patch('main.get_memory_connection')
    def test_search_memories_empty_result(self, mock_get_conn):
        """Test memory search with no results"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/search?query=nonexistent")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 0


class TestDeleteMemory:
    """Test memory deletion functionality"""

    @patch('main.get_memory_connection')
    def test_delete_memory_success(self, mock_get_conn):
        """Test successful memory deletion"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.delete("/memory/1")
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

    @patch('main.get_memory_connection')
    def test_delete_memory_not_found(self, mock_get_conn):
        """Test deleting non-existent memory"""
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 0

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.delete("/memory/999")
        assert response.status_code == 404


class TestMemoryStats:
    """Test memory statistics functionality"""

    @patch('main.get_memory_connection')
    def test_memory_stats_success(self, mock_get_conn):
        """Test getting memory statistics"""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            'total_memories': 100,
            'avg_importance': 0.65,
            'unique_agents': 3,
            'unique_types': 2
        }

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/stats")
        assert response.status_code == 200

        data = response.json()
        assert data["total_memories"] == 100
        assert data["average_importance"] == 0.65
        assert data["unique_agents"] == 3


class TestSecurity:
    """Test security validations"""

    @patch('main.get_memory_connection')
    def test_sql_injection_protection_in_search(self, mock_get_conn):
        """Test that search uses parameterized queries"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Try SQL injection in search query
        response = client.get("/memory/search?query='; DROP TABLE unified_memory; --")
        assert response.status_code == 200

        # Verify parameterized query was used
        mock_cursor.execute.assert_called_once()
        args = mock_cursor.execute.call_args[0]
        # Query string should contain ILIKE %s (parameterized)
        assert "%s" in args[0]


class TestPerformance:
    """Test performance and resource limits"""

    @patch('main.get_memory_connection')
    def test_large_limit_parameter(self, mock_get_conn):
        """Test handling of very large limit parameter"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        # Try very large limit
        response = client.get("/memory/list?limit=1000000")
        # Should handle or limit the parameter


class TestConnectionManagement:
    """Test database connection management"""

    @patch('main.get_memory_connection')
    def test_connection_closed_on_success(self, mock_get_conn):
        """Test that connection is closed after successful operation"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/list")
        assert response.status_code == 200

        # Verify connection was closed
        mock_conn.close.assert_called_once()

    @patch('main.get_memory_connection')
    def test_connection_closed_on_error(self, mock_get_conn):
        """Test that connection is closed even on error"""
        mock_cursor = MagicMock()
        mock_cursor.fetchall.side_effect = Exception("Database error")

        mock_conn = MagicMock()
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_get_conn.return_value = mock_conn

        response = client.get("/memory/list")
        # Should still close connection
        mock_conn.close.assert_called_once()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
