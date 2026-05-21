#!/usr/bin/env python3
"""
Unit tests for FileStorage utility.
"""
import sys
import asyncio
from unittest.mock import MagicMock, patch

# Mock aiofiles before importing FileStorage because it's a top-level import
# and might not be available in all test environments.
sys.modules["aiofiles"] = MagicMock()

import pytest
from pathlib import Path
from mega_orchestrator.utils.file_storage import FileStorage

# Define the target for patching Path to avoid global side effects
PATH_TARGET = "mega_orchestrator.utils.file_storage.Path"

def test_validate_path_non_existent():
    """Test _validate_path with a non-existent path."""
    storage = FileStorage()
    with patch(PATH_TARGET) as mock_path:
        mock_path.return_value.resolve.return_value.exists.return_value = False
        result = asyncio.run(storage._validate_path("/tmp/non_existent_file.txt"))
        assert result is None

def test_validate_path_not_a_file():
    """Test _validate_path with a directory path."""
    storage = FileStorage()
    with patch(PATH_TARGET) as mock_path:
        mock_instance = mock_path.return_value.resolve.return_value
        mock_instance.exists.return_value = True
        mock_instance.is_file.return_value = False
        result = asyncio.run(storage._validate_path("/tmp"))
        assert result is None

def test_validate_path_outside_allowed():
    """Test _validate_path with a path outside allowed directories."""
    storage = FileStorage()
    with patch(PATH_TARGET) as mock_path:
        mock_instance = mock_path.return_value.resolve.return_value
        mock_instance.exists.return_value = True
        mock_instance.is_file.return_value = True
        mock_instance.__str__.return_value = "/etc/passwd"

        result = asyncio.run(storage._validate_path("/etc/passwd"))
        assert result is None

def test_validate_path_exception():
    """Test _validate_path when an exception occurs during resolution."""
    storage = FileStorage()
    with patch(PATH_TARGET) as mock_path:
        mock_path.return_value.resolve.side_effect = Exception("Resolution failed")
        result = asyncio.run(storage._validate_path("/tmp/some_file.txt"))
        assert result is None

def test_validate_path_valid():
    """Test _validate_path with a valid path in allowed directories."""
    storage = FileStorage()
    valid_path = "/tmp/test_file.txt"

    # We use side_effect to distinguish between calls to Path()
    # Path(file_path) -> returns mock_p
    # Path("/home/milhy777") -> returns mock_allowed_1
    # Path("/tmp") -> returns mock_allowed_2
    # etc.

    mock_p = MagicMock(spec=Path)
    mock_resolved = MagicMock(spec=Path)
    mock_p.resolve.return_value = mock_resolved
    mock_resolved.exists.return_value = True
    mock_resolved.is_file.return_value = True
    mock_resolved.__str__.return_value = valid_path

    mock_allowed_1 = MagicMock(spec=Path)
    mock_allowed_1.__str__.return_value = "/home/milhy777"

    mock_allowed_2 = MagicMock(spec=Path)
    mock_allowed_2.__str__.return_value = "/tmp"

    mock_allowed_3 = MagicMock(spec=Path)
    mock_allowed_3.__str__.return_value = "/home/orchestration/data"

    def path_side_effect(arg):
        if arg == "/tmp/test_file.txt":
            return mock_p
        if arg == "/home/milhy777":
            return mock_allowed_1
        if arg == "/tmp":
            return mock_allowed_2
        if arg == "/home/orchestration/data":
            return mock_allowed_3
        return MagicMock(spec=Path)

    with patch(PATH_TARGET, side_effect=path_side_effect):
        result = asyncio.run(storage._validate_path(valid_path))
        assert result == valid_path
