#!/usr/bin/env python3
"""Tests for marketplace-mcp service."""

import importlib.util
import json
import os
import sys
import tarfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client_and_secret(tmp_path, monkeypatch):
    catalog = tmp_path / "catalog"
    artifacts = catalog / "artifacts"
    artifacts.mkdir(parents=True)

    skill_root = tmp_path / "skill-src"
    (skill_root / "pkg").mkdir(parents=True)
    (skill_root / "pkg" / "SKILL.md").write_text(
        "---\nname: pkg\ndescription: test\n---\n", encoding="utf-8"
    )
    artifact = artifacts / "pkg-1.0.0.tar.gz"
    with tarfile.open(artifact, "w:gz") as tar:
        tar.add(skill_root / "pkg", arcname="pkg")

    import hashlib

    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()

    (catalog / "skills-index.json").write_text(
        json.dumps(
            {
                "skills": [
                    {
                        "name": "pkg",
                        "version": "1.0.0",
                        "description": "test",
                        "archive_url": "artifacts/pkg-1.0.0.tar.gz",
                        "sha256": digest,
                        "tags": ["test"],
                        "source": "internal",
                        "compat": {"clients": ["codex-cli"], "min_version": "0.0.0"},
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    (catalog / "servers-index.json").write_text(
        json.dumps(
            {
                "servers": [
                    {
                        "id": "pkg-mcp",
                        "name": "Pkg MCP",
                        "source": "internal",
                        "tags": ["test"],
                        "versions": [
                            {
                                "version": "1.0.0",
                                "transport": "streamable_http",
                                "endpoint": "http://localhost:7999/mcp",
                                "auth": {"type": "bearer", "scopes": ["market:read"]},
                                "tags": ["test"],
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    (catalog / "trust-policy.json").write_text(
        json.dumps({"policy": "hash-integrity", "required": ["sha256"]}),
        encoding="utf-8",
    )

    monkeypatch.setenv("MARKET_CATALOG_PATH", str(catalog))
    monkeypatch.setenv("JWT_SECRET", "unit-test-secret")
    monkeypatch.setenv("MARKET_BASE_URL", "http://localhost:7034")

    module_path = Path(__file__).resolve().parents[1] / "main.py"
    module_name = "marketplace_mcp_main_tested"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    client = TestClient(module.app)
    return client, "unit-test-secret"


def _auth(secret: str, scopes=None):
    payload = {
        "sub": "tester",
        "scope": scopes or ["market:read"],
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"Authorization": f"Bearer {token}"}


def test_health_open(client_and_secret):
    client, _ = client_and_secret
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["service"] == "marketplace-mcp"


def test_auth_required(client_and_secret):
    client, _ = client_and_secret
    response = client.get("/skills/v1/index")
    assert response.status_code == 401


def test_skills_index_and_resolve(client_and_secret):
    client, secret = client_and_secret
    headers = _auth(secret)

    index = client.get("/skills/v1/index", headers=headers)
    assert index.status_code == 200
    assert index.json()["count"] == 1

    resolved = client.post(
        "/tools/skills_resolve",
        headers=headers,
        json={"arguments": {"name": "pkg"}},
    )
    assert resolved.status_code == 200
    assert resolved.json()["name"] == "pkg"


def test_install_plan(client_and_secret):
    client, secret = client_and_secret
    headers = _auth(secret)

    response = client.post(
        "/skills/v1/install-plan",
        headers=headers,
        json={"client": "codex-cli", "skills": [{"name": "pkg"}]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resolved_packages"][0]["name"] == "pkg"
    assert len(body["steps"]) == 4


def test_download_and_registry(client_and_secret):
    client, secret = client_and_secret
    headers = _auth(secret)

    dl = client.get("/skills/v1/packages/pkg/1.0.0/download", headers=headers)
    assert dl.status_code == 200
    assert dl.headers.get("content-type", "").startswith("application/gzip")

    reg = client.get("/registry/v0.1/servers", headers=headers)
    assert reg.status_code == 200
    assert reg.json()["count"] == 1

    latest = client.get("/registry/v0.1/servers/pkg-mcp/latest", headers=headers)
    assert latest.status_code == 200
    assert latest.json()["latest"]["version"] == "1.0.0"


def test_mcp_jsonrpc_and_legacy(client_and_secret):
    client, secret = client_and_secret
    headers = _auth(secret)

    rpc = client.post(
        "/mcp",
        headers=headers,
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "skills_list", "arguments": {}},
        },
    )
    assert rpc.status_code == 200
    assert rpc.json()["result"]["count"] == 1

    legacy = client.post(
        "/mcp",
        headers=headers,
        json={"tool": "registry_search", "arguments": {"source": "internal"}},
    )
    assert legacy.status_code == 200
    assert legacy.json()["count"] == 1
