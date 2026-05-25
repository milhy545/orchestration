import sys
import os
from pathlib import Path
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock

# Add claude-agent to path
sys.path.append(str(Path(__file__).parent.parent.parent / 'claude-agent'))

# We need to be careful importing because of the try-except import in the module
from claude_session_bridge import find_claude_credentials

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

    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': mock_keyring}):
        result = find_claude_credentials()
        assert result == {'api_key': 'keyring-key'}

def test_find_claude_credentials_config_file():
    """Test that config files are checked if env var and keyring are missing"""
    config_data = {"api_key": "file-key", "other": "data"}
    config_json = json.dumps(config_data)

    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': None}), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=config_json)):

        result = find_claude_credentials()
        assert result == config_data

def test_find_claude_credentials_no_creds():
    """Test that None is returned if no credentials found anywhere"""
    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': None}), \
         patch('pathlib.Path.exists', return_value=False):

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_invalid_json():
    """Test that invalid JSON in config file is handled gracefully"""
    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': None}), \
         patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data='invalid json')):

        # Mock exists to return True for the first path, then False for others
        mock_exists.side_effect = [True, False, False, False]

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_missing_key():
    """Test that config file without api_key is skipped"""
    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': None}), \
         patch('pathlib.Path.exists') as mock_exists, \
         patch('builtins.open', mock_open(read_data='{"not_api_key": "value"}')):

        mock_exists.side_effect = [True, False, False, False]

        result = find_claude_credentials()
        assert result is None

def test_find_claude_credentials_multiple_paths():
    """Test that it continues to search other paths if one fails"""
    config_data = {"api_key": "second-path-key"}
    config_json = json.dumps(config_data)

    with patch('os.getenv', return_value=None), \
         patch.dict('sys.modules', {'keyring': None}), \
         patch('pathlib.Path.exists') as mock_exists:

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
