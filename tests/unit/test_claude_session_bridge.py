import sys
import os
from pathlib import Path
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock, AsyncMock
import asyncio

# Add claude-agent to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'claude-agent'))

# Mock dependencies that are missing in the test environment
sys.modules['yaml'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['psutil'] = MagicMock()
sys.modules['aiohttp'] = MagicMock()
sys.modules['requests'] = MagicMock()

# We need to be careful importing because of the try-except import in the module
from claude_session_bridge import find_claude_credentials, run_has_agent_with_auth

def test_find_claude_credentials_env_var():
    """Test that ANTHROPIC_API_KEY environment variable is preferred"""
    with patch('os.getenv') as mock_getenv:
        mock_getenv.side_effect = lambda k, default=None: 'test-api-key' if k == 'ANTHROPIC_API_KEY' else default
        result = find_claude_credentials()
        assert result == {'api_key': 'test-api-key'}

def test_find_claude_credentials_keyring():
    """Test that keyring is checked if env var is missing"""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = 'keyring-key'

    with (
        patch('os.getenv', return_value=None),
        patch.dict('sys.modules', {'keyring': mock_keyring}),
    ):
        result = find_claude_credentials()
        assert result == {'api_key': 'keyring-key'}

def test_find_claude_credentials_config_file():
    """Test that config files are checked if env var and keyring are missing"""
    config_data = {"api_key": "file-key", "other": "data"}
    config_json = json.dumps(config_data)

    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists', return_value=True),          patch('builtins.open', mock_open(read_data=config_json)):

        result = find_claude_credentials()
        assert result == config_data

def test_find_claude_credentials_no_creds():
    """Test that None is returned if no credentials found anywhere"""
    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists', return_value=False):

        result = find_claude_credentials()
        assert result is None

def test_run_has_agent_with_auth_success():
    """Test that run_has_agent_with_auth correctly sets API key and initializes agent"""
    mock_creds = {'api_key': 'test-key'}
    # Use a real dict for environ to test assignment
    mock_env = {}

    with patch('claude_session_bridge.find_claude_credentials', return_value=mock_creds),          patch('os.environ', mock_env),          patch('haiku_agent.HASClaudeAgent') as mock_agent_class:

        mock_agent = mock_agent_class.return_value
        mock_agent.check_resource_usage.return_value = {
            'ram_used_mb': 100, 'ram_percent': 10, 'cpu_percent': 5
        }
        mock_agent.call_mcp_tool = AsyncMock(return_value={'success': True})
        mock_agent.claude_request = AsyncMock(return_value={'success': True, 'content': 'mock response', 'model': 'haiku'})
        mock_agent.health_check = AsyncMock(return_value={
            'agent_status': 'running',
            'resources': {'status': 'ok'},
            'mcp_connectivity': 'ok',
            'claude_api': 'ok'
        })

        asyncio.run(run_has_agent_with_auth())

        assert mock_env['ANTHROPIC_API_KEY'] == 'test-key'
        mock_agent_class.assert_called_once()
        mock_agent.check_resource_usage.assert_called_once()
        mock_agent.call_mcp_tool.assert_called_once()
        mock_agent.claude_request.assert_called_once()
        mock_agent.health_check.assert_called_once()

def test_run_has_agent_with_auth_no_creds():
    """Test run_has_agent_with_auth when no credentials are found"""
    mock_env = {}

    with patch('claude_session_bridge.find_claude_credentials', return_value=None),          patch('os.environ', mock_env),          patch('haiku_agent.HASClaudeAgent') as mock_agent_class:

        mock_agent = mock_agent_class.return_value
        mock_agent.check_resource_usage.return_value = {
            'ram_used_mb': 100, 'ram_percent': 10, 'cpu_percent': 5
        }
        mock_agent.call_mcp_tool = AsyncMock(return_value={'success': True})
        mock_agent.claude_request = AsyncMock(return_value={'success': True, 'content': 'mock response', 'model': 'haiku'})
        mock_agent.health_check = AsyncMock(return_value={
            'agent_status': 'running',
            'resources': {'status': 'ok'}
        })

        asyncio.run(run_has_agent_with_auth())

        assert 'ANTHROPIC_API_KEY' not in mock_env
        mock_agent_class.assert_called_once()

def test_find_claude_credentials_invalid_json():
    """Test that invalid JSON in config file is handled gracefully"""
    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists') as mock_exists,          patch('builtins.open', mock_open(read_data='invalid json')):

        # Mock exists to return True for the first path, then False for others
        mock_exists.side_effect = [True, False, False, False]

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_missing_key():
    """Test that config file without api_key is skipped"""
    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists') as mock_exists,          patch('builtins.open', mock_open(read_data='{"not_api_key": "value"}')):

        mock_exists.side_effect = [True, False, False, False]

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_multiple_paths():
    """Test that it continues to search other paths if one fails"""
    config_data = {"api_key": "second-path-key"}
    config_json = json.dumps(config_data)

    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists') as mock_exists:

        # First path exists but has invalid JSON, second path has valid config
        mock_exists.side_effect = [True, True, False, False]

        # We need a more complex mock for open to return different data
        m = mock_open()
        m.side_effect = [
            mock_open(read_data='invalid').return_value,
            mock_open(read_data=config_json).return_value
        ]

        with patch('builtins.open', m):
            result = find_claude_credentials()
            assert result == config_data

def test_find_claude_credentials_keyring_none():
    """Test that it continues if keyring returns None"""
    mock_keyring = MagicMock()
    mock_keyring.get_password.return_value = None

    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': mock_keyring}),          patch('pathlib.Path.exists', return_value=False):
        result = find_claude_credentials()
        assert result is None
        mock_keyring.get_password.assert_called_with("anthropic", "api_key")

def test_find_claude_credentials_keyring_exception():
    """Test that it continues if keyring raises an exception"""
    mock_keyring = MagicMock()
    mock_keyring.get_password.side_effect = Exception("Keyring error")

    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': mock_keyring}),          patch('pathlib.Path.exists', return_value=False):
        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_permission_error():
    """Test that it continues if a config file has permission error"""
    with patch('os.getenv', return_value=None),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists', return_value=True),          patch('builtins.open', side_effect=PermissionError("Permission denied")):

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_env_empty():
    """Test that it continues if environment variable is an empty string"""
    with patch('os.getenv', return_value=""),          patch.dict('sys.modules', {'keyring': None}),          patch('pathlib.Path.exists', return_value=False):

        result = find_claude_credentials()
        assert result is None
