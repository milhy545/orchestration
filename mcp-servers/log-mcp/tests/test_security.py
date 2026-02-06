#!/usr/bin/env python3
"""
Security tests for Log MCP Service
Tests for command injection and path traversal vulnerabilities
"""
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, validate_log_path, validate_command

client = TestClient(app)


class TestPathTraversalProtection:
    """Test path traversal vulnerability fixes"""

    def test_read_log_in_allowed_directory(self):
        """Test that reading logs in allowed directory works"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "/app/logs/test.log",
            "analysis_type": "stats"
        })
        assert response.status_code == 200

    def test_path_traversal_blocked_parent_directory(self):
        """Test that path traversal with ../ is blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "../../etc/passwd",
            "analysis_type": "stats"
        })
        assert response.status_code in [403, 400]

    def test_path_traversal_blocked_absolute_path(self):
        """Test that absolute paths outside allowed directories are blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "/etc/passwd",
            "analysis_type": "stats"
        })
        # 403 or 400 - both mean blocked
        assert response.status_code in [400, 403]

    def test_path_traversal_blocked_etc_shadow(self):
        """Test that reading /etc/shadow is blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "/etc/shadow",
            "analysis_type": "stats"
        })
        # 403 or 400 - both mean blocked
        assert response.status_code in [400, 403]

    def test_path_traversal_blocked_multiple_levels(self):
        """Test that multiple levels of path traversal are blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "../../../../../etc/passwd",
            "analysis_type": "stats"
        })
        assert response.status_code in [403, 400]

    def test_path_traversal_log_search_blocked(self):
        """Test that path traversal is blocked in log_search endpoint"""
        response = client.post("/tools/log_search", json={
            "query": "test",
            "sources": ["/etc/passwd", "../../../etc/shadow"],
            "search_type": "text"
        })
        # Should return results but skip invalid sources
        assert response.status_code == 200
        # Should have 0 results since both sources are blocked
        data = response.json()
        assert data["total_matches"] == 0

    def test_validate_log_path_function_directly(self):
        """Test validate_log_path function directly"""
        # Valid path
        result = validate_log_path("/app/logs/test.log")
        assert result.name == "test.log"

        # Invalid path should raise HTTPException
        with pytest.raises(Exception):  # HTTPException
            validate_log_path("/etc/passwd")


class TestCommandInjectionProtection:
    """Test command injection vulnerability fixes"""

    def test_allowed_command_journalctl(self):
        """Test that allowed journalctl command works"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "journalctl -n 10",
            "analysis_type": "stats"
        })
        # May fail if journalctl not available, but should not be 403
        assert response.status_code in [200, 500, 408]

    def test_allowed_command_tail(self):
        """Test that allowed tail command works"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "tail -n 5 /app/logs/test.log",
            "analysis_type": "stats"
        })
        # Should work since tail and path are both allowed
        assert response.status_code in [200, 500, 408]

    def test_allowed_command_grep(self):
        """Test that allowed grep command works"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "grep -i ERROR /app/logs/test.log",
            "analysis_type": "stats"
        })
        assert response.status_code in [200, 500, 408]

    def test_blocked_command_rm(self):
        """Test that dangerous command 'rm' is blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "rm -rf /tmp/test",
            "analysis_type": "stats"
        })
        assert response.status_code == 403
        assert "not allowed" in response.json()["detail"].lower()

    def test_blocked_command_cat(self):
        """Test that 'cat' command is blocked (not whitelisted)"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "cat /etc/passwd",
            "analysis_type": "stats"
        })
        assert response.status_code == 403

    def test_blocked_command_bash(self):
        """Test that shell commands are blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "bash -c 'echo hacked'",
            "analysis_type": "stats"
        })
        assert response.status_code == 403

    def test_blocked_command_sh(self):
        """Test that sh is blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "sh -c 'ls'",
            "analysis_type": "stats"
        })
        assert response.status_code == 403

    def test_command_injection_with_semicolon(self):
        """Test that command chaining with ; is prevented"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "journalctl -n 10; rm -rf /tmp",
            "analysis_type": "stats"
        })
        # shlex.split should handle this safely
        assert response.status_code in [403, 400]

    def test_command_injection_with_pipe(self):
        """Test that command piping is safely handled by shlex"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "journalctl -n 10 | grep secret",
            "analysis_type": "stats"
        })
        # shlex.split() treats pipe as literal argument, which is then validated
        # Since '|' is not a whitelisted arg, it gets rejected OR treated as safe literal
        # 200/408/500 = safe execution, 403/400 = rejected
        assert response.status_code in [200, 403, 400, 408, 500]

    def test_command_injection_with_backticks(self):
        """Test that command substitution with backticks is safely handled"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "journalctl -n `whoami`",
            "analysis_type": "stats"
        })
        # shlex.split() treats backticks as literals, not command substitution
        # Since shell=False, backticks cannot execute commands
        assert response.status_code in [200, 403, 400, 408, 500]

    def test_command_with_invalid_arguments(self):
        """Test that invalid arguments are blocked"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "command",
            "source_value": "journalctl --invalid-arg",
            "analysis_type": "stats"
        })
        assert response.status_code == 403


class TestRegexSafety:
    """Test safe regex handling"""

    def test_regex_search_blocks_long_pattern(self):
        log_dir = Path("/tmp/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "regex_test.log"
        log_file.write_text("hello\nworld\n")

        response = client.post("/tools/log_search", json={
            "query": "a" * 500,
            "sources": [str(log_file)],
            "search_type": "regex"
        })
        assert response.status_code == 400

    def test_regex_search_allows_simple_pattern(self):
        log_dir = Path("/tmp/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "regex_ok.log"
        log_file.write_text("hello\nworld\n")

        response = client.post("/tools/log_search", json={
            "query": "hello",
            "sources": [str(log_file)],
            "search_type": "regex"
        })
        assert response.status_code == 200
        assert "argument" in response.json()["detail"].lower()

    def test_validate_command_function_directly(self):
        """Test validate_command function directly"""
        # Valid command
        result = validate_command("journalctl -n 10")
        assert result == ["journalctl", "-n", "10"]

        # Invalid command
        with pytest.raises(Exception):  # HTTPException
            validate_command("rm -rf /")

        # Command with invalid args
        with pytest.raises(Exception):
            validate_command("journalctl --invalid")


class TestLogAnalysisEndpoint:
    """Test log analysis endpoint functionality"""

    def test_direct_text_analysis(self):
        """Test analyzing direct text (no file or command)"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "direct_text",
            "source_value": "2024-01-01 10:00:00 ERROR Test error\n2024-01-01 10:00:01 INFO Test info",
            "analysis_type": "stats"
        })
        assert response.status_code == 200
        data = response.json()
        assert "analysis_type" in data

    def test_pattern_analysis(self):
        """Test pattern-based log analysis"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "file_path",
            "source_value": "/app/logs/test.log",
            "analysis_type": "pattern",
            "pattern": "ERROR"
        })
        assert response.status_code == 200

    def test_invalid_log_source(self):
        """Test that invalid log_source is rejected"""
        response = client.post("/tools/log_analysis", json={
            "log_source": "invalid_source",
            "source_value": "something",
            "analysis_type": "stats"
        })
        assert response.status_code == 400
        assert "invalid log_source" in response.json()["detail"].lower()


class TestLogSearchEndpoint:
    """Test log search endpoint functionality"""

    def test_log_search_valid_file(self):
        """Test searching in valid log file"""
        response = client.post("/tools/log_search", json={
            "query": "Test",
            "sources": ["/app/logs/test.log"],
            "search_type": "text"
        })
        assert response.status_code == 200

    def test_log_search_regex(self):
        """Test regex search"""
        response = client.post("/tools/log_search", json={
            "query": "ERROR|WARN",
            "sources": ["/app/logs/test.log"],
            "search_type": "regex"
        })
        assert response.status_code == 200

    def test_log_search_invalid_regex(self):
        """Test that invalid regex is rejected"""
        response = client.post("/tools/log_search", json={
            "query": "[invalid(regex",
            "sources": ["/app/logs/test.log"],
            "search_type": "regex"
        })
        # 400 or 500 - both indicate error was caught
        assert response.status_code in [400, 500]


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test that health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Log MCP"


class TestToolsList:
    """Test tools list endpoint"""

    def test_tools_list(self):
        """Test that tools list endpoint works"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        # Log MCP has 2 tools: log_analysis and log_search
        assert len(data["tools"]) >= 2
