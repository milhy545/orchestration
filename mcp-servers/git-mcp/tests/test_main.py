#!/usr/bin/env python3
"""
Git MCP Service Tests
Tests for security, performance, and functionality
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


class TestGitMCPHealth:
    """Test health endpoint"""

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"


class TestGitStatus:
    """Test git status functionality"""

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_status_success(self, mock_run, mock_validate_repo):
        """Test successful git status"""
        mock_result = MagicMock()
        mock_result.stdout = "M file1.txt\nA file2.txt\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_status_failure(self, mock_run, mock_validate_repo):
        """Test git status with error"""
        mock_run.side_effect = subprocess.CalledProcessError(
            128, ["git"], stderr="Not a git repository"
        )

        response = client.get("/git/invalid/path/status")
        assert response.status_code == 500
        assert "git command failed" in response.json()["detail"].lower()


class TestGitLog:
    """Test git log functionality"""

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_log_success(self, mock_run, mock_validate_repo):
        """Test successful git log"""
        mock_result = MagicMock()
        mock_result.stdout = "abc123 commit 1\ndef456 commit 2\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/log")
        assert response.status_code == 200

        data = response.json()
        assert "log" in data
        assert isinstance(data["log"], list)

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_log_with_limit(self, mock_run, mock_validate_repo):
        """Test git log with custom limit"""
        mock_result = MagicMock()
        mock_result.stdout = "abc123 commit 1\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/log?limit=10")
        assert response.status_code == 200

        # Verify limit was passed to git command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "-n10" in args


class TestGitDiff:
    """Test git diff functionality"""

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_diff_success(self, mock_run, mock_validate_repo):
        """Test successful git diff"""
        mock_result = MagicMock()
        mock_result.stdout = "diff --git a/file.txt b/file.txt\n+added line\n"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/diff")
        assert response.status_code == 200

        data = response.json()
        assert "diff" in data

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_diff_empty(self, mock_run, mock_validate_repo):
        """Test git diff with no changes"""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/diff")
        assert response.status_code == 200

        data = response.json()
        assert data["diff"] == ""


class TestSecurityValidation:
    """Test security validations"""

    @patch('subprocess.run')
    def test_path_validation(self, mock_run):
        """Test that dangerous paths are rejected"""
        # After refactoring, these should be blocked
        dangerous_paths = [
            "../../../../etc",
            "/etc/passwd",
            "../../../root"
        ]

        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        for dangerous_path in dangerous_paths:
            response = client.get(f"/git/{dangerous_path}/status")
            assert response.status_code == 403

    @patch('subprocess.run')
    def test_repository_sandbox(self, mock_run):
        """Test that access is restricted to allowed repositories"""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # After refactoring, should validate against allowed repositories


class TestPerformance:
    """Test performance and resource limits"""

    @patch('subprocess.run')
    def test_git_log_excessive_limit(self, mock_run):
        """Test git log with very large limit"""
        mock_result = MagicMock()
        mock_result.stdout = "\n".join([f"commit {i}" for i in range(10000)])
        mock_run.return_value = mock_result

        # Should limit the maximum number of commits
        response = client.get("/git/tmp/repo/log?limit=100000")
        assert response.status_code == 422

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_large_diff_output(self, mock_run, mock_validate_repo):
        """Test handling of large diff output"""
        # Simulate large diff (10MB)
        large_diff = "+" + ("x" * 10 * 1024 * 1024)

        mock_result = MagicMock()
        mock_result.stdout = large_diff
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/diff")
        assert response.status_code == 200
        data = response.json()
        assert data["truncated"] is True

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_command_timeout(self, mock_run, mock_validate_repo):
        """Test that git commands have timeout"""
        # After refactoring, should have timeout
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

        response = client.get("/git/tmp/repo/status")
        assert response.status_code == 408


class TestIntegration:
    """Integration tests"""

    @patch('main.validate_repository_path', return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_complete_workflow(self, mock_run, mock_validate_repo):
        """Test complete git workflow"""
        # Status
        mock_result = MagicMock()
        mock_result.stdout = "M file.txt\n"
        mock_run.return_value = mock_result

        response = client.get("/git/tmp/repo/status")
        assert response.status_code == 200

        # Log
        mock_result.stdout = "abc123 commit 1\n"
        response = client.get("/git/tmp/repo/log")
        assert response.status_code == 200

        # Diff
        mock_result.stdout = "+added line\n"
        response = client.get("/git/tmp/repo/diff")
        assert response.status_code == 200


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
