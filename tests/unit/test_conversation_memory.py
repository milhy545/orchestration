#!/usr/bin/env python3
"""
Unit tests for conversation memory helpers.
"""
import pytest

pytest.importorskip("asyncpg")
pytest.importorskip("aioredis")

from mega_orchestrator.utils.conversation_memory import ConversationMemory


def test_session_id_is_hex():
    memory = ConversationMemory()
    session_id = memory._generate_session_id()
    assert len(session_id) == 16
    int(session_id, 16)


def test_context_id_is_hex():
    memory = ConversationMemory()
    context_id = memory._generate_context_id("tool", {"a": 1}, None)
    assert len(context_id) == 32
    int(context_id, 16)
