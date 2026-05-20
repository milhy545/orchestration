#!/usr/bin/env python3
"""
Unit tests for MegaOrchestrator initialization.
"""
import time
import sys
from unittest.mock import MagicMock

# Mock dependencies before importing the module under test
mock_aiohttp = MagicMock()
mock_aiohttp.web = MagicMock()
sys.modules["aiohttp"] = mock_aiohttp
sys.modules["aiohttp.web"] = mock_aiohttp.web
sys.modules["asyncpg"] = MagicMock()
sys.modules["redis"] = MagicMock()
sys.modules["redis.asyncio"] = MagicMock()
sys.modules["aiofiles"] = MagicMock()

import pytest
from mega_orchestrator.mega_orchestrator_complete import MegaOrchestrator, VERSION, BUILD_DATE
from mega_orchestrator.utils.conversation_memory import ConversationMemory
from mega_orchestrator.utils.file_storage import FileStorage
from mega_orchestrator.modes.sage_router import SAGEModeRouter

def test_mega_orchestrator_init_defaults():
    """Test MegaOrchestrator initialization with default values."""
    orchestrator = MegaOrchestrator()

    assert orchestrator.port == 7000
    assert orchestrator.backup_mode is False
    assert orchestrator.version == VERSION
    assert orchestrator.build_date == BUILD_DATE

    # Core components
    assert isinstance(orchestrator.services, dict)
    assert "filesystem" in orchestrator.services
    assert orchestrator.provider_registry is None
    assert isinstance(orchestrator.conversation_memory, ConversationMemory)
    assert isinstance(orchestrator.file_storage, FileStorage)
    assert isinstance(orchestrator.sage_router, SAGEModeRouter)

    # Infrastructure
    assert orchestrator.redis is None
    assert orchestrator.db_pool is None
    assert orchestrator.app is None

    # Statistics
    assert isinstance(orchestrator.stats, dict)
    assert "startup_time" in orchestrator.stats
    assert orchestrator.stats["startup_time"] <= time.time()
    assert orchestrator.stats["requests_processed"] == 0
    assert orchestrator.stats["mode_switches"] == 0
    assert orchestrator.stats["provider_fallbacks"] == 0
    assert orchestrator.stats["memory_contexts"] == 0
    assert orchestrator.stats["file_operations"] == 0

def test_mega_orchestrator_init_custom():
    """Test MegaOrchestrator initialization with custom values."""
    custom_port = 8888
    orchestrator = MegaOrchestrator(port=custom_port, backup_mode=True)

    assert orchestrator.port == custom_port
    assert orchestrator.backup_mode is True
    assert orchestrator.version == VERSION
    assert orchestrator.build_date == BUILD_DATE
