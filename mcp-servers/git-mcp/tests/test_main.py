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
MODULE_NAME = "git_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app

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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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


class TestGitCommit:
    """Test git commit functionality"""

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_commit_success(self, mock_run, mock_validate_repo):
        """Test successful git commit"""
        status_result = MagicMock()
        status_result.stdout = "M file1.txt\n"
        status_result.stderr = ""

        add_result = MagicMock()
        add_result.stdout = ""
        add_result.stderr = ""

        commit_result = MagicMock()
        commit_result.stdout = "[main abc1234] test commit"
        commit_result.stderr = ""

        head_result = MagicMock()
        head_result.stdout = "abc1234def5678\n"
        head_result.stderr = ""

        mock_run.side_effect = [status_result, add_result, commit_result, head_result]

        response = client.post(
            "/git/tmp/repo/commit",
            json={"message": "test commit"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["commit"] == "abc1234def5678"
        assert data["message"] == "test commit"

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_commit_no_changes(self, mock_run, mock_validate_repo):
        """Test commit rejection when repository is clean"""
        status_result = MagicMock()
        status_result.stdout = ""
        status_result.stderr = ""
        mock_run.return_value = status_result

        response = client.post(
            "/git/tmp/repo/commit",
            json={"message": "test commit"},
        )
        assert response.status_code == 400
        assert "no changes to commit" in response.json()["detail"].lower()


class TestGitPush:
    """Test git push functionality"""

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_push_success(self, mock_run, mock_validate_repo):
        """Test successful git push"""
        status_result = MagicMock(stdout="", stderr="")
        branch_result = MagicMock(stdout="main\n", stderr="")
        upstream_result = MagicMock(stdout="origin/main\n", stderr="")
        push_result = MagicMock(stdout="Everything up-to-date\n", stderr="")
        mock_run.side_effect = [status_result, branch_result, upstream_result, push_result]

        response = client.post("/git/tmp/repo/push", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert data["remote"] == "origin"
        assert data["branch"] == "main"

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_push_dirty_tree_rejected(self, mock_run, mock_validate_repo):
        """Test push rejection with dirty tree"""
        status_result = MagicMock(stdout=" M file.txt\n", stderr="")
        mock_run.return_value = status_result

        response = client.post("/git/tmp/repo/push", json={})
        assert response.status_code == 400
        assert "working tree is not clean" in response.json()["detail"].lower()

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_git_push_missing_upstream(self, mock_run, mock_validate_repo):
        """Test push rejection when upstream is missing"""
        status_result = MagicMock(stdout="", stderr="")
        branch_result = MagicMock(stdout="main\n", stderr="")
        mock_run.side_effect = [
            status_result,
            branch_result,
            subprocess.CalledProcessError(128, ["git"], stderr="no upstream"),
        ]

        response = client.post("/git/tmp/repo/push", json={})
        assert response.status_code == 400
        assert "upstream branch is not configured" in response.json()["detail"].lower()

    def test_git_push_force_rejected(self):
        """Test force push rejection"""
        response = client.post("/git/tmp/repo/push", json={"force": True})
        assert response.status_code == 400
        assert "force push" in response.json()["detail"].lower()

    def test_git_push_set_upstream_rejected(self):
        """Test upstream setup rejection"""
        response = client.post("/git/tmp/repo/push", json={"set_upstream": True})
        assert response.status_code == 400
        assert "upstream setup" in response.json()["detail"].lower()


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
            assert response.status_code in [403, 404]

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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
    @patch('subprocess.run')
    def test_command_timeout(self, mock_run, mock_validate_repo):
        """Test that git commands have timeout"""
        # After refactoring, should have timeout
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

        response = client.get("/git/tmp/repo/status")
        assert response.status_code == 408


class TestIntegration:
    """Integration tests"""

    @patch(f"{MODULE_NAME}.validate_repository_path", return_value="/tmp/repo")
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
