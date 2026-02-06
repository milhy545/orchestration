#!/usr/bin/env python3
"""
Filesystem MCP Service Tests
Tests for security vulnerabilities, performance, and functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, mock_open
import os

# Import the main app
import sys
import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "main.py"
spec = importlib.util.spec_from_file_location("main", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["main"] = module
assert spec.loader is not None
spec.loader.exec_module(module)

from main import app

client = TestClient(app)


class TestFilesystemMCPHealth:
    """Test health and basic functionality"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestListFiles:
    """Test file listing functionality"""

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.stat')
    @patch('os.path.isfile')
    def test_list_files_success(self, mock_isfile, mock_stat, mock_listdir,
                                mock_isdir, mock_exists):
        """Test successful file listing"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["file1.txt", "dir1", "file2.py"]

        # Mock stat results
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result

        def isfile_side_effect(path):
            return "file" in path

        mock_isfile.side_effect = isfile_side_effect

        response = client.get("/files/tmp")
        assert response.status_code == 200

        data = response.json()
        assert data["path"] == "/tmp"
        assert data["total_count"] == 3
        assert len(data["files"]) == 3

    @patch('os.path.exists')
    def test_list_files_not_found(self, mock_exists):
        """Test listing non-existent directory"""
        mock_exists.return_value = False

        response = client.get("/files/tmp/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_list_files_not_directory(self, mock_isdir, mock_exists):
        """Test listing a file instead of directory"""
        mock_exists.return_value = True
        mock_isdir.return_value = False

        response = client.get("/files/tmp/file.txt")
        assert response.status_code == 400
        assert "not a directory" in response.json()["detail"].lower()

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    def test_list_files_permission_denied(self, mock_listdir, mock_isdir, mock_exists):
        """Test listing directory with permission denied"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.side_effect = PermissionError("Permission denied")

        response = client.get("/files/tmp")
        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()


class TestReadFile:
    """Test file reading functionality"""

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data="Hello, World!")
    def test_read_file_success(self, mock_file, mock_isfile, mock_exists):
        """Test successful file reading"""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        response = client.get("/file/tmp/test.txt")
        assert response.status_code == 200

        data = response.json()
        assert data["path"] == "/tmp/test.txt"
        assert data["content"] == "Hello, World!"
        assert data["size"] == len("Hello, World!")

    @patch('os.path.exists')
    def test_read_file_not_found(self, mock_exists):
        """Test reading non-existent file"""
        mock_exists.return_value = False

        response = client.get("/file/tmp/nonexistent.txt")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_read_file_is_directory(self, mock_isfile, mock_exists):
        """Test reading a directory instead of file"""
        mock_exists.return_value = True
        mock_isfile.return_value = False

        response = client.get("/file/tmp")
        assert response.status_code == 400
        assert "not a file" in response.json()["detail"].lower()

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('builtins.open')
    def test_read_file_permission_denied(self, mock_file, mock_isfile, mock_exists):
        """Test reading file with permission denied"""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        mock_file.side_effect = PermissionError("Permission denied")

        response = client.get("/file/tmp/secret.txt")
        assert response.status_code == 403
        assert "permission denied" in response.json()["detail"].lower()

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data="x" * 20000)
    def test_read_file_size_limit(self, mock_file, mock_isfile, mock_exists):
        """Test file reading size limit (10KB)"""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        response = client.get("/file/tmp/large.txt")
        assert response.status_code == 200

        data = response.json()
        # Should be limited to 10KB (10000 bytes)
        assert data["size"] <= 10000


class TestSecurityVulnerabilities:
    """Test security vulnerabilities and protections"""

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.stat')
    @patch('os.path.isfile')
    def test_path_traversal_directory_listing(self, mock_isfile, mock_stat,
                                              mock_listdir, mock_isdir, mock_exists):
        """Test path traversal attempts in directory listing"""
        # This test documents the CURRENT vulnerability
        # After refactoring, these should be blocked

        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []

        dangerous_paths = [
            "../../../../etc",
            "../../../root",
            "/etc/passwd",
            "/root/.ssh"
        ]

        for dangerous_path in dangerous_paths:
            response = client.get(f"/files/{dangerous_path}")
            # Currently this might work (vulnerability)
            # After fix, should return 403 Forbidden

    @patch('os.path.exists')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data="secret data")
    def test_path_traversal_file_reading(self, mock_file, mock_isfile, mock_exists):
        """Test path traversal attempts in file reading"""
        mock_exists.return_value = True
        mock_isfile.return_value = True

        dangerous_paths = [
            "../../../../etc/passwd",
            "../../../etc/shadow",
            "/root/.ssh/id_rsa"
        ]

        for dangerous_path in dangerous_paths:
            response = client.get(f"/file/{dangerous_path}")
            # Currently this will work (vulnerability)
            # After fix, should return 403 Forbidden

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    def test_sensitive_directory_access(self, mock_listdir, mock_isdir, mock_exists):
        """Test access to sensitive system directories"""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["passwd", "shadow", "hosts"]

        sensitive_dirs = [
            "/etc",
            "/root",
            "/var/log",
            "/proc",
            "/sys"
        ]

        for sensitive_dir in sensitive_dirs:
            response = client.get(f"/files{sensitive_dir}")
            # Should be blocked in secure implementation


class TestPerformance:
    """Test performance and resource limits"""

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.stat')
    @patch('os.path.isfile')
    def test_large_directory_listing(self, mock_isfile, mock_stat,
                                     mock_listdir, mock_isdir, mock_exists):
        """Test listing directory with many files"""
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # Simulate large directory (10000 files)
        mock_listdir.return_value = [f"file{i}.txt" for i in range(10000)]

        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        mock_isfile.return_value = True

        response = client.get("/files/tmp")
        assert response.status_code == 200

        data = response.json()
        # Should handle large directory
        assert data["total_count"] == 10000


class TestIntegration:
    """Integration tests"""

    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('os.listdir')
    @patch('os.stat')
    @patch('os.path.isfile')
    @patch('builtins.open', new_callable=mock_open, read_data="Test content")
    def test_list_and_read_workflow(self, mock_file, mock_isfile, mock_stat,
                                    mock_listdir, mock_isdir, mock_exists):
        """Test complete list directory and read file workflow"""
        # Setup mocks
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = ["file1.txt"]

        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 1024
        mock_stat_result.st_mtime = 1234567890
        mock_stat.return_value = mock_stat_result
        mock_isfile.return_value = True

        # List directory
        list_response = client.get("/files/tmp")
        assert list_response.status_code == 200

        list_data = list_response.json()
        assert len(list_data["files"]) == 1

        # Read file
        read_response = client.get("/file/tmp/file1.txt")
        assert read_response.status_code == 200

        read_data = read_response.json()
        assert read_data["content"] == "Test content"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
