from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from vault_secrets_ui.vault import VaultClient


def test_headers_reads_token(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123\n", encoding="utf-8")
    client = VaultClient("http://vault:8200", token_file)
    assert client.headers() == {"X-Vault-Token": "abc123"}


def test_headers_rejects_empty_token(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("", encoding="utf-8")
    client = VaultClient("http://vault:8200", token_file)
    with pytest.raises(ValueError):
        client.headers()


@pytest.mark.asyncio
async def test_read_secret_handles_404(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=404, json={})

    transport = httpx.MockTransport(handler)
    client = VaultClient("http://vault:8200", token_file)
    original = httpx.AsyncClient

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            super().__init__(transport=transport, *args, **kwargs)

    httpx.AsyncClient = MockAsyncClient
    try:
        assert await client.read_secret("orchestration/demo") == {}
    finally:
        httpx.AsyncClient = original


@pytest.mark.asyncio
async def test_write_secret_and_probe(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123", encoding="utf-8")
    seen = {"post": False, "health": False}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/sys/health"):
            seen["health"] = True
            return httpx.Response(status_code=200, json={})
        seen["post"] = True
        return httpx.Response(status_code=200, json={})

    transport = httpx.MockTransport(handler)
    client = VaultClient("http://vault:8200", token_file)
    original = httpx.AsyncClient

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            super().__init__(transport=transport, *args, **kwargs)

    httpx.AsyncClient = MockAsyncClient
    try:
        await client.write_secret("orchestration/demo", {"API_KEY": "secret"})
        assert await client.probe() is True
    finally:
        httpx.AsyncClient = original

    assert seen == {"post": True, "health": True}


@pytest.mark.asyncio
async def test_read_secret_returns_payload(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123", encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={"data": {"data": {"API_KEY": "secret"}}},
        )

    transport = httpx.MockTransport(handler)
    client = VaultClient("http://vault:8200", token_file)
    original = httpx.AsyncClient

    class MockAsyncClient(httpx.AsyncClient):
        def __init__(self, *args, **kwargs):
            super().__init__(transport=transport, *args, **kwargs)

    httpx.AsyncClient = MockAsyncClient
    try:
        assert await client.read_secret("orchestration/demo") == {"API_KEY": "secret"}
    finally:
        httpx.AsyncClient = original


@pytest.mark.asyncio
async def test_probe_handles_transport_errors(tmp_path: Path) -> None:
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123", encoding="utf-8")
    client = VaultClient("http://vault:8200", token_file)
    original = httpx.AsyncClient

    class BrokenAsyncClient(httpx.AsyncClient):
        async def __aenter__(self):
            raise httpx.ConnectError("boom")

    httpx.AsyncClient = BrokenAsyncClient
    try:
        assert await client.probe() is False
    finally:
        httpx.AsyncClient = original
