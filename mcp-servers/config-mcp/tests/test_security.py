#!/usr/bin/env python3
"""
Security tests for Config MCP Service
Tests for vulnerabilities found in security audit
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


class TestPathTraversalProtection:
    """Test path traversal vulnerability fix"""

    def test_read_file_inside_allowed_directory(self):
        """Test that reading files inside allowed directory works"""
        # Create a test file first (may already exist from previous tests)
        response = client.post("/tools/config_file", json={
            "operation": "create",
            "file_path": "test_config.json",
            "format": "json"
        })
        assert response.status_code in [200, 409]  # 200=created, 409=already exists

        # Read it back
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "test_config.json",
            "format": "json"
        })
        assert response.status_code == 200

    def test_path_traversal_blocked_parent_directory(self):
        """Test that path traversal with ../ is blocked"""
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "../etc/passwd",
            "format": "env"
        })
        assert response.status_code == 403
        assert "outside allowed directory" in response.json()["detail"].lower()

    def test_path_traversal_blocked_absolute_path(self):
        """Test that absolute paths outside allowed directory are blocked"""
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "/etc/passwd",
            "format": "env"
        })
        assert response.status_code == 403
        assert "outside allowed directory" in response.json()["detail"].lower()

    def test_path_traversal_blocked_multiple_levels(self):
        """Test that multiple levels of path traversal are blocked"""
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "../../../../../../etc/shadow",
            "format": "env"
        })
        assert response.status_code == 403
        assert "outside allowed directory" in response.json()["detail"].lower()

    def test_path_traversal_blocked_encoded(self):
        """Test that URL-encoded path traversal is blocked"""
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "..%2F..%2Fetc%2Fpasswd",
            "format": "env"
        })
        # FastAPI auto-decodes, so path ends up being checked and blocked (403) or not found (404)
        assert response.status_code in [403, 404]  # Both are secure responses

    def test_path_traversal_write_operation(self):
        """Test that write operations also check path traversal"""
        response = client.post("/tools/config_file", json={
            "operation": "write",
            "file_path": "../../../tmp/malicious.conf",
            "format": "json",
            "content": {"malicious": "data"}
        })
        assert response.status_code == 403
        assert "outside allowed directory" in response.json()["detail"].lower()

    def test_path_traversal_delete_operation(self):
        """Test that delete operations also check path traversal"""
        response = client.post("/tools/config_file", json={
            "operation": "delete",
            "file_path": "../../../../etc/important.conf"
        })
        assert response.status_code == 403


class TestEnvironmentVariableSecurity:
    """Test environment variable access controls"""

    def test_env_var_get_operation(self):
        """Test getting environment variables works"""
        # Set a test var first
        response = client.post("/tools/env_vars", json={
            "operation": "set",
            "key": "TEST_VAR",
            "value": "test_value"
        })
        assert response.status_code == 200

        # Get it back
        response = client.post("/tools/env_vars", json={
            "operation": "get",
            "key": "TEST_VAR"
        })
        assert response.status_code == 200
        assert response.json()["value"] == "test_value"

    def test_env_var_list_with_prefix(self):
        """Test listing environment variables with prefix filter"""
        # Set test vars
        client.post("/tools/env_vars", json={
            "operation": "set",
            "key": "TEST_PREFIX_VAR1",
            "value": "value1"
        })
        client.post("/tools/env_vars", json={
            "operation": "set",
            "key": "TEST_PREFIX_VAR2",
            "value": "value2"
        })

        # List with prefix
        response = client.post("/tools/env_vars", json={
            "operation": "list",
            "prefix": "TEST_PREFIX"
        })
        assert response.status_code == 200
        vars_dict = response.json()["variables"]
        assert "TEST_PREFIX_VAR1" in vars_dict
        assert "TEST_PREFIX_VAR2" in vars_dict

    def test_env_var_delete(self):
        """Test deleting environment variables"""
        # Set a var
        client.post("/tools/env_vars", json={
            "operation": "set",
            "key": "DELETE_ME",
            "value": "temporary"
        })

        # Delete it
        response = client.post("/tools/env_vars", json={
            "operation": "delete",
            "key": "DELETE_ME"
        })
        assert response.status_code == 200
        assert response.json()["deleted"] is True

    def test_env_var_missing_key(self):
        """Test that operations requiring key fail without it"""
        response = client.post("/tools/env_vars", json={
            "operation": "get"
        })
        assert response.status_code == 400
        assert "key required" in response.json()["detail"].lower()


class TestConfigFileOperations:
    """Test configuration file operations"""

    def test_create_json_config(self):
        """Test creating JSON config file"""
        response = client.post("/tools/config_file", json={
            "operation": "create",
            "file_path": "app.json",
            "format": "json"
        })
        assert response.status_code in [200, 409]  # 409 if already exists

    def test_write_and_read_json_config(self):
        """Test writing and reading JSON config"""
        test_data = {"key1": "value1", "key2": 123, "key3": True}

        # Write
        response = client.post("/tools/config_file", json={
            "operation": "write",
            "file_path": "test_write.json",
            "format": "json",
            "content": test_data
        })
        assert response.status_code == 200

        # Read back
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "test_write.json",
            "format": "json"
        })
        assert response.status_code == 200
        assert response.json()["parsed_content"] == test_data

    def test_write_yaml_config(self):
        """Test writing YAML config file"""
        test_data = {"database": {"host": "localhost", "port": 5432}}

        response = client.post("/tools/config_file", json={
            "operation": "write",
            "file_path": "config.yaml",
            "format": "yaml",
            "content": test_data
        })
        assert response.status_code == 200

    def test_write_env_file(self):
        """Test writing .env file"""
        test_data = {"API_KEY": "secret123", "DEBUG": "true"}

        response = client.post("/tools/config_file", json={
            "operation": "write",
            "file_path": ".env",
            "format": "env",
            "content": test_data
        })
        assert response.status_code == 200

    def test_list_config_files(self):
        """Test listing all config files"""
        response = client.post("/tools/config_file", json={
            "operation": "list",
            "file_path": ""
        })
        assert response.status_code == 200
        assert "files" in response.json()
        assert "count" in response.json()

    def test_read_nonexistent_file(self):
        """Test reading non-existent file returns 404"""
        response = client.post("/tools/config_file", json={
            "operation": "read",
            "file_path": "nonexistent_file.json",
            "format": "json"
        })
        assert response.status_code == 404


class TestConfigValidation:
    """Test configuration validation"""

    def test_validate_config_all_valid(self):
        """Test validation with all valid data"""
        response = client.post("/tools/validate", json={
            "config_data": {
                "name": "MyApp",
                "port": 8080,
                "debug": True,
                "version": "1.0.0"
            },
            "required_keys": ["name", "port"],
            "value_types": {
                "name": "string",
                "port": "integer",
                "debug": "boolean"
            }
        })
        assert response.status_code == 200
        assert response.json()["is_valid"] is True
        assert len(response.json()["validation_errors"]) == 0

    def test_validate_config_missing_required_key(self):
        """Test validation fails when required key is missing"""
        response = client.post("/tools/validate", json={
            "config_data": {
                "name": "MyApp"
            },
            "required_keys": ["name", "port"],
            "value_types": {}
        })
        assert response.status_code == 200
        assert response.json()["is_valid"] is False
        assert any("port" in err.lower() for err in response.json()["validation_errors"])

    def test_validate_config_wrong_type(self):
        """Test validation fails when value type is wrong"""
        response = client.post("/tools/validate", json={
            "config_data": {
                "name": "MyApp",
                "port": "should_be_int"
            },
            "required_keys": [],
            "value_types": {
                "port": "integer"
            }
        })
        assert response.status_code == 200
        assert response.json()["is_valid"] is False
        assert any("port" in err.lower() for err in response.json()["validation_errors"])

    def test_validate_config_negative_port(self):
        """Test validation catches negative port numbers"""
        response = client.post("/tools/validate", json={
            "config_data": {
                "server_port": -1
            },
            "required_keys": [],
            "value_types": {}
        })
        assert response.status_code == 200
        # Should warn about negative value for _port field
        errors = response.json()["validation_errors"]
        assert len(errors) > 0


class TestBackupOperations:
    """Test backup and restore functionality"""

    def test_create_backup(self):
        """Test creating a configuration backup"""
        response = client.post("/tools/backup", json={
            "operation": "create",
            "backup_name": "test_backup_001"
        })
        assert response.status_code in [200, 409]  # 409 if already exists

    def test_list_backups(self):
        """Test listing backups"""
        response = client.post("/tools/backup", json={
            "operation": "list"
        })
        assert response.status_code == 200
        assert "backups" in response.json()
        assert "backup_count" in response.json()

    def test_delete_backup(self):
        """Test deleting a backup"""
        # Create backup first
        create_response = client.post("/tools/backup", json={
            "operation": "create",
            "backup_name": "test_delete_backup"
        })

        if create_response.status_code == 200:
            # Delete it
            response = client.post("/tools/backup", json={
                "operation": "delete",
                "backup_name": "test_delete_backup"
            })
            assert response.status_code == 200
            assert response.json()["deleted"] is True


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self):
        """Test that health endpoint works"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "Config MCP"
        assert "features" in data


class TestToolsList:
    """Test tools list endpoint"""

    def test_tools_list(self):
        """Test that tools list endpoint works"""
        response = client.get("/tools/list")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert len(data["tools"]) >= 4  # env_vars, config_file, validate, backup
