#!/usr/bin/env python3
"""
Redis MCP Functional Tests

Use an in-memory fake Redis client to exercise code paths and keep CI coverage
above the global threshold without requiring a real Redis server.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


module_path = Path(__file__).resolve().parents[1] / "main.py"
MODULE_NAME = "redis_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app
client = TestClient(app)


class _FakeRedis:
    def __init__(self, *args: Any, **kwargs: Any):
        self._kv: Dict[str, str] = {}

    async def aclose(self) -> None:
        return None

    async def ping(self) -> bool:
        return True

    async def info(self) -> Dict[str, Any]:
        return {
            "redis_version": "7.2.0",
            "connected_clients": 1,
            "used_memory_human": "1M",
            "uptime_in_seconds": 123,
        }

    async def get(self, key: str) -> Optional[str]:
        return self._kv.get(key)

    async def set(self, key: str, value: str, **kwargs: Any) -> bool:
        # ignore nx/xx semantics for tests
        self._kv[key] = value
        return True

    async def setex(self, key: str, ttl: int, value: str) -> bool:
        self._kv[key] = value
        return True

    async def delete(self, key: str) -> int:
        return 1 if self._kv.pop(key, None) is not None else 0

    async def exists(self, key: str) -> int:
        return 1 if key in self._kv else 0

    async def expire(self, key: str, ttl: int) -> bool:
        return key in self._kv

    async def scan(
        self, *, cursor: int, match: str, count: int
    ) -> Tuple[int, List[str]]:
        # Simple prefix matching for "session:*"
        prefix = match[:-1] if match.endswith("*") else match
        keys = [k for k in sorted(self._kv.keys()) if k.startswith(prefix)]
        return 0, keys[:count]


@pytest.fixture()
def fake_redis(monkeypatch):
    fake = _FakeRedis()

    # Make redis_pool "present"
    monkeypatch.setattr(module, "redis_pool", object())

    # Patch Redis() constructor used by the service to return our singleton fake.
    def _fake_redis_factory(*args: Any, **kwargs: Any) -> _FakeRedis:
        return fake

    monkeypatch.setattr(module.redis, "Redis", _fake_redis_factory)
    return fake


def test_health_check_with_pool(fake_redis):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["redis"]["status"] in {"healthy", "error"}
    assert "info" in data["redis"]


def test_cache_set_get_exists_expire_delete(fake_redis):
    resp = client.post(
        "/tools/cache",
        json={"operation": "set", "key": "k1", "value": {"a": 1}, "ttl": 60},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.post("/tools/cache", json={"operation": "exists", "key": "k1"})
    assert resp.status_code == 200
    assert resp.json()["exists"] is True

    resp = client.post("/tools/cache", json={"operation": "get", "key": "k1"})
    assert resp.status_code == 200
    assert resp.json()["found"] is True
    assert resp.json()["value"] == {"a": 1}

    resp = client.post("/tools/cache", json={"operation": "expire", "key": "k1", "ttl": 5})
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    resp = client.post("/tools/cache", json={"operation": "delete", "key": "k1"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_cache_set_requires_value(fake_redis):
    resp = client.post("/tools/cache", json={"operation": "set", "key": "k2"})
    assert resp.status_code == 400


def test_cache_unknown_operation(fake_redis):
    resp = client.post("/tools/cache", json={"operation": "bogus", "key": "k"})
    assert resp.status_code == 400


def test_session_create_get_update_delete_list(fake_redis):
    # Create
    resp = client.post(
        "/tools/session",
        json={
            "operation": "create",
            "session_id": "s1",
            "session_data": {"x": 1},
            "ttl": 60,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "s1"

    # Get
    resp = client.post(
        "/tools/session",
        json={"operation": "get", "session_id": "s1", "ttl": 60},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["found"] is True
    assert data["session_info"]["data"]["x"] == 1

    # Update
    resp = client.post(
        "/tools/session",
        json={
            "operation": "update",
            "session_id": "s1",
            "session_data": {"y": 2},
            "ttl": 60,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["session_info"]["data"]["y"] == 2

    # List
    resp = client.post("/tools/session", json={"operation": "list"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "list"
    assert data["session_count"] >= 1
    assert any(s["session_id"] == "s1" for s in data["sessions"])

    # Delete
    resp = client.post("/tools/session", json={"operation": "delete", "session_id": "s1"})
    assert resp.status_code == 200
    assert resp.json()["deleted"] is True


def test_session_update_not_found(fake_redis):
    resp = client.post(
        "/tools/session",
        json={
            "operation": "update",
            "session_id": "missing",
            "session_data": {"x": 1},
        },
    )
    assert resp.status_code == 404


def test_session_unknown_operation(fake_redis):
    resp = client.post(
        "/tools/session",
        json={"operation": "bogus", "session_id": "s"},
    )
    assert resp.status_code == 400

