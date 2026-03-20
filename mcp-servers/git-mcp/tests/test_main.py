#!/usr/bin/env python3
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import subprocess
import sys
import importlib.util
from pathlib import Path
import os

# Import the main app
module_path = Path(__file__).resolve().parents[1] / 'main.py'
MODULE_NAME = 'git_mcp_main'
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
spec.loader.exec_module(module)

app = module.app
client = TestClient(app)

class TestGitMCPHealth:
    def test_health_endpoint(self):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

class TestGitStatus:
    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_status_success(self, mock_run, mock_validate_repo):
        mock_result = MagicMock(stdout='M file1.txt\nA file2.txt\n', returncode=0)
        mock_run.return_value = mock_result
        response = client.get('/git/tmp/repo/status')
        assert response.status_code == 200

    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_status_failure(self, mock_run, mock_validate_repo):
        mock_run.side_effect = subprocess.CalledProcessError(1, ['git'], stderr='fatal error')
        response = client.get('/git/tmp/repo/status')
        assert response.status_code == 500

class TestGitLog:
    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_log_success(self, mock_run, mock_validate_repo):
        mock_rev = MagicMock(stdout='2', returncode=0)
        mock_log = MagicMock(stdout='abc commit 1\ndef commit 2\n', returncode=0)
        mock_run.side_effect = [mock_rev, mock_log]
        response = client.get('/git/tmp/repo/log')
        assert response.status_code == 200

    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_log_empty_repository(self, mock_run, mock_validate_repo):
        mock_rev = MagicMock(stdout='0', returncode=0)
        mock_run.return_value = mock_rev
        response = client.get('/git/tmp/repo/log')
        assert response.status_code == 200

class TestGitCommit:
    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_commit_success(self, mock_run, mock_validate_repo):
        m_status = MagicMock(stdout='M file.txt', returncode=0)
        m_ok = MagicMock(returncode=0)
        m_head = MagicMock(stdout='abc123456', returncode=0)
        mock_run.side_effect = [m_status, m_ok, m_ok, m_head]
        response = client.post('/git/tmp/repo/commit', json={'message': 'test commit'})
        assert response.status_code == 200

class TestGitPush:
    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_git_push_success(self, mock_run, mock_validate_repo):
        m = MagicMock(stdout='main', returncode=0)
        mock_run.side_effect = [m, m, m, m, m, m]
        response = client.post('/git/tmp/repo/push', json={})
        assert response.status_code in [200, 400]

class TestSecurityValidation:
    def test_path_validation(self):
        response = client.get('/git/../../../etc/passwd/status')
        assert response.status_code in [403, 404]

class TestPerformance:
    @patch(f'{MODULE_NAME}.validate_repository_path', return_value='/tmp/repo')
    @patch('subprocess.run')
    def test_command_timeout(self, mock_run, mock_validate):
        mock_run.side_effect = subprocess.TimeoutExpired(['git'], 30)
        response = client.get('/git/tmp/repo/status')
        assert response.status_code == 408
