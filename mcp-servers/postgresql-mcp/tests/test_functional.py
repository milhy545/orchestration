#!/usr/bin/env python3
"""
PostgreSQL MCP Functional Tests

These tests use a lightweight fake asyncpg pool/connection to exercise the main
code paths without a real database, primarily to keep CI coverage above the
global threshold.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient


module_path = Path(__file__).resolve().parents[1] / "main.py"
MODULE_NAME = "postgresql_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app
client = TestClient(app)


class _AcquireCtx:
    def __init__(self, connection: "_FakeConnection"):
        self._connection = connection

    async def __aenter__(self) -> "_FakeConnection":
        return self._connection

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakePool:
    def __init__(self, connection: "_FakeConnection"):
        self._connection = connection

    def acquire(self) -> _AcquireCtx:
        return _AcquireCtx(self._connection)

    def get_size(self) -> int:
        return 1

    def get_min_size(self) -> int:
        return 1

    def get_max_size(self) -> int:
        return 1

    def get_idle_size(self) -> int:
        return 1

    async def close(self) -> None:
        return None


class _FakeConnection:
    async def fetch(self, query: str, *args: Any) -> List[Dict[str, Any]]:
        q = " ".join(query.split()).lower()

        if "from information_schema.columns" in q:
            return [{"column_name": "id"}, {"column_name": "name"}]

        if "from information_schema.tables" in q:
            return [{"table_name": "users", "table_type": "BASE TABLE"}]

        if "from pg_indexes" in q:
            return [{"indexname": "users_pkey", "indexdef": "CREATE UNIQUE INDEX ..."}]

        if q.startswith("select") and '"public"."users"' in q:
            return [{"id": 1, "name": "alice"}]

        return []

    async def fetchrow(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        q = " ".join(query.split()).lower()

        if "select version()" in q:
            return {
                "version": "PostgreSQL 16.0",
                "current_database": "mcp_unified",
                "current_user": "mcp_admin",
                "inet_server_addr": "127.0.0.1",
                "inet_server_port": 5432,
            }

        if "from pg_stat_activity" in q:
            return {
                "total_connections": 1,
                "active_connections": 0,
                "idle_connections": 1,
            }

        if "pg_database_size" in q:
            return {"database_size": "1 MB"}

        if q.startswith("select 1 as test"):
            return {"test": 1, "timestamp": "2026-01-01T00:00:00Z"}

        return None


@pytest.fixture()
def fake_db_pool(monkeypatch):
    pool = _FakePool(_FakeConnection())
    monkeypatch.setattr(module, "db_pool", pool)
    return pool


def test_health_with_pool_info(fake_db_pool):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["database"]["status"] == "healthy"
    assert "pool_info" in data["database"]


def test_query_tool_success(fake_db_pool):
    resp = client.post(
        "/tools/query",
        json={
            "schema_name": "public",
            "table": "users",
            "columns": ["id", "name"],
            "filters": [{"column": "id", "op": "=", "value": 1}],
            "order_by": [{"column": "id", "direction": "desc"}],
            "limit": 10,
            "offset": 0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["row_count"] == 1
    assert data["columns"] == ["id", "name"]


def test_schema_tool_describe_table(fake_db_pool):
    resp = client.post(
        "/tools/schema",
        json={
            "operation": "describe",
            "schema_name": "public",
            "table_name": "users",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "describe"
    assert data["table_name"] == "users"
    assert "columns" in data
    assert "indexes" in data


def test_schema_tool_list_tables(fake_db_pool):
    resp = client.post(
        "/tools/schema",
        json={
            "operation": "list",
            "schema_name": "public",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["operation"] == "list"
    assert data["table_count"] == 1


def test_connection_tool_operations(fake_db_pool):
    for op in ["status", "stats", "test"]:
        resp = client.post("/tools/connection", json={"operation": op})
        assert resp.status_code == 200


def test_schema_tool_unknown_operation(fake_db_pool):
    resp = client.post(
        "/tools/schema",
        json={
            "operation": "bogus",
            "schema_name": "public",
        },
    )
    assert resp.status_code == 422


def test_connection_tool_unknown_operation(fake_db_pool):
    resp = client.post("/tools/connection", json={"operation": "kill_connections"})
    assert resp.status_code == 400
