"""Focused authentication and authorisation coverage for Mega gateway."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from mega_gateway.app import (
    GatewayConfig,
    STORE_KEY,
    create_app,
)
from mega_gateway.security import ReservationLimiter, pkce_s256


VERIFIER = "A" * 43
REDIRECT = "https://client.example.test/oauth/callback"


async def _admin(socket_path: Path, action: str, **payload: str) -> dict:
    reader, writer = await asyncio.open_unix_connection(str(socket_path))
    writer.write((f'{{"action":"{action}","payload":' + json.dumps(payload) + "}\n").encode())
    await writer.drain()
    response = json.loads((await reader.readline()).decode())
    writer.close()
    await writer.wait_closed()
    return response


@pytest_asyncio.fixture
async def gateway(tmp_path: Path):
    async def backend(request: web.Request) -> web.Response:
        body = await request.json()
        if body["method"] == "tools/list":
            tools = [{"name": "get_context"}, {"name": "terminal_exec"}]
            return web.json_response({"jsonrpc": "2.0", "id": body["id"], "result": {"tools": tools}})
        return web.json_response({"jsonrpc": "2.0", "id": body["id"], "result": {"content": []}})

    backend_app = web.Application()
    backend_app.router.add_post("/mcp", backend)
    backend_server = TestServer(backend_app)
    await backend_server.start_server()
    config = GatewayConfig(
        database_path=tmp_path / "state.sqlite3",
        admin_socket=tmp_path / "admin.sock",
        backend_url=str(backend_server.make_url("/mcp")),
        chatgpt_redirect_uris=frozenset({REDIRECT}),
        chatgpt_registration_redirect_hosts=frozenset({"chatgpt.example.test"}),
        public_base_url="https://gateway.example.test",
    )
    client = TestClient(TestServer(create_app(config)))
    await client.start_server()
    yield client, config
    await client.close()
    await backend_server.close()


async def _authorise(
    client: TestClient, config: GatewayConfig, client_id: str = "chatgpt", redirect_uri: str = REDIRECT
) -> str:
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge_method": "S256",
        "code_challenge": pkce_s256(VERIFIER),
        "state": "opaque-state",
    }
    pending = await client.get("/oauth/authorize", params=params)
    assert pending.status == 200
    pairing_id = re.search(r"pair_[A-Za-z0-9_-]+", await pending.text()).group(0)
    approved = await _admin(config.admin_socket, "pairing.approve", pairing_id=pairing_id)
    assert approved["ok"] is True
    params["pairing_id"] = pairing_id
    callback = await client.get("/oauth/authorize", params=params, allow_redirects=False)
    assert callback.status == 302
    redirect_params = parse_qs(urlparse(callback.headers["Location"]).query)
    assert redirect_params["state"] == ["opaque-state"]
    return redirect_params["code"][0]


@pytest.mark.asyncio
async def test_pkce_authorisation_code_is_bound_and_one_use(gateway) -> None:
    client, config = gateway
    code = await _authorise(client, config)

    wrong = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": "B" * 43,
    })
    assert wrong.status == 400
    assert (await wrong.json())["error"] == "invalid_grant"

    token = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    issued = await token.json()
    assert token.status == 200
    assert issued["expires_in"] == 15 * 60
    assert issued["access_token"].startswith("mg_at_")
    assert issued["refresh_token"].startswith("mg_rt_")
    persisted = config.database_path.read_bytes()
    assert issued["access_token"].encode() not in persisted
    assert issued["refresh_token"].encode() not in persisted
    assert code.encode() not in persisted

    replay = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    assert replay.status == 400


@pytest.mark.asyncio
async def test_revoked_access_token_cannot_call_mcp_and_tool_list_is_filtered(gateway) -> None:
    client, config = gateway
    code = await _authorise(client, config)
    token = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    access = (await token.json())["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    listed = await client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert [tool["name"] for tool in (await listed.json())["result"]["tools"]] == ["get_context"]
    denied = await client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "terminal_exec"},
    })
    assert (await denied.json())["error"]["code"] == -32601

    revoked = await client.post("/oauth/revoke", data={"token": access})
    assert revoked.status == 200
    blocked = await client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": 3, "method": "ping"})
    assert blocked.status == 401
    assert "resource_metadata=" in blocked.headers["WWW-Authenticate"]


@pytest.mark.asyncio
async def test_profile_permissions_and_oauth_discovery_are_enforced(gateway) -> None:
    client, config = gateway
    code = await _authorise(client, config)
    token = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    access_token = (await token.json())["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    changed = await _admin(config.admin_socket, "profile.tool.revoke", profile_id="chatgpt", tool="get_context")
    assert changed["ok"] is True
    denied = await client.post("/mcp", headers=headers, json={
        "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_context"},
    })
    assert (await denied.json())["error"]["code"] == -32601
    restored = await _admin(config.admin_socket, "profile.tool.grant", profile_id="chatgpt", tool="get_context")
    assert "get_context" in restored["data"]["tools"]

    resource = await client.get("/.well-known/oauth-protected-resource")
    assert (await resource.json())["authorization_servers"] == ["https://gateway.example.test"]
    server = await client.get("/.well-known/oauth-authorization-server")
    assert (await server.json())["code_challenge_methods_supported"] == ["S256"]


@pytest.mark.asyncio
async def test_refresh_replay_and_connection_revoke_revoke_the_entire_grant(gateway) -> None:
    client, config = gateway
    code = await _authorise(client, config)
    initial_response = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    initial = await initial_response.json()
    refreshed_response = await client.post("/oauth/token", data={
        "grant_type": "refresh_token", "refresh_token": initial["refresh_token"], "client_id": "chatgpt",
    })
    refreshed = await refreshed_response.json()
    assert refreshed_response.status == 200
    replay = await client.post("/oauth/token", data={
        "grant_type": "refresh_token", "refresh_token": initial["refresh_token"], "client_id": "chatgpt",
    })
    assert replay.status == 400
    blocked = await client.post("/mcp", headers={"Authorization": f"Bearer {refreshed['access_token']}"}, json={
        "jsonrpc": "2.0", "id": 1, "method": "ping",
    })
    assert blocked.status == 401

    code = await _authorise(client, config)
    issued_response = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": "chatgpt",
        "redirect_uri": REDIRECT, "code_verifier": VERIFIER,
    })
    issued = await issued_response.json()
    connections = await _admin(config.admin_socket, "connections.list")
    assert len(connections["data"]) == 1
    revoked = await _admin(
        config.admin_socket, "connections.revoke", connection_id=connections["data"][0]["connection_id"]
    )
    assert revoked["ok"] is True
    blocked = await client.post("/mcp", headers={"Authorization": f"Bearer {issued['access_token']}"}, json={
        "jsonrpc": "2.0", "id": 2, "method": "ping",
    })
    assert blocked.status == 401


@pytest.mark.asyncio
async def test_chatgpt_dynamic_registration_is_host_bound_and_automatic(gateway) -> None:
    client, config = gateway
    redirect_uri = "https://chatgpt.example.test/oauth/callback"
    registration = await client.post("/oauth/register", json={
        "client_name": "ChatGPT connector",
        "redirect_uris": [redirect_uri],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
    })
    metadata = await registration.json()
    assert registration.status == 201
    assert metadata["client_id"].startswith("chatgpt_")
    assert "client_secret" not in metadata
    repeated = await client.post("/oauth/register", json={"redirect_uris": [redirect_uri]})
    assert (await repeated.json())["client_id"] == metadata["client_id"]

    code = await _authorise(client, config, metadata["client_id"], redirect_uri)
    exchange = await client.post("/oauth/token", data={
        "grant_type": "authorization_code", "code": code, "client_id": metadata["client_id"],
        "redirect_uri": redirect_uri, "code_verifier": VERIFIER,
    })
    assert exchange.status == 200
    after_approval = await client.post("/oauth/register", json={"redirect_uris": [redirect_uri]})
    assert (await after_approval.json())["client_id"] == metadata["client_id"]
    rejected = await client.post("/oauth/register", json={"redirect_uris": ["https://other.example.test/callback"]})
    assert rejected.status == 400
    malformed = await client.post("/oauth/register", json={"redirect_uris": [{}]})
    assert malformed.status == 400
    malformed_uri = await client.post("/oauth/register", json={"redirect_uris": ["https://[broken"]})
    assert malformed_uri.status == 400


@pytest.mark.asyncio
async def test_invalid_pkce_challenge_is_rejected_before_persistent_pairing(gateway) -> None:
    client, config = gateway
    response = await client.get("/oauth/authorize", params={
        "response_type": "code", "client_id": "chatgpt", "redirect_uri": REDIRECT,
        "code_challenge_method": "S256", "code_challenge": "A" * 6000,
    })
    assert response.status == 400
    assert config.database_path.read_bytes().count(b"pair_") == 0


@pytest.mark.asyncio
async def test_expired_pairings_and_codes_are_cleaned_before_new_pairing(gateway) -> None:
    client, _ = gateway
    store = client.server.app[STORE_KEY]
    pairing = store.create_pairing(
        client_id="chatgpt", redirect_uri=REDIRECT, profile="chatgpt", code_challenge=pkce_s256(VERIFIER), state=None
    )
    store.connection.execute("UPDATE pairings SET expires_at = 0 WHERE id = ?", (pairing["pairing_id"],))
    store.connection.commit()
    store.create_pairing(
        client_id="chatgpt", redirect_uri=REDIRECT, profile="chatgpt", code_challenge=pkce_s256(VERIFIER), state=None
    )
    assert store.pairing(pairing["pairing_id"]) is None


def test_create_app_does_not_require_a_running_event_loop(tmp_path: Path) -> None:
    environment = {
        **os.environ,
        "PYTHONPATH": str(Path(__file__).parents[2]),
        "MEGA_GATEWAY_DB": str(tmp_path / "state.sqlite3"),
        "MEGA_GATEWAY_ADMIN_SOCKET": str(tmp_path / "admin.sock"),
        "MEGA_GATEWAY_PUBLIC_BASE_URL": "https://gateway.example.test",
        "MEGA_GATEWAY_CHATGPT_REGISTRATION_REDIRECT_HOSTS": "chatgpt.example.test",
    }
    result = subprocess.run(
        [sys.executable, "-c", "from mega_gateway.app import create_app; create_app()"],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_interrupted_family_migration_revokes_nullable_legacy_tokens(tmp_path: Path) -> None:
    database = tmp_path / "legacy.sqlite3"
    connection = sqlite3.connect(database)
    connection.execute(
        "CREATE TABLE tokens (token_hash TEXT PRIMARY KEY, kind TEXT, client_id TEXT, profile TEXT, "
        "expires_at INTEGER, revoked_at INTEGER, replaced_by_hash TEXT, family_id TEXT)"
    )
    connection.execute(
        "INSERT INTO tokens VALUES (?, 'access', 'chatgpt', 'chatgpt', 9999999999, NULL, NULL, NULL)",
        (hashlib.sha256(b'legacy-access').hexdigest(),),
    )
    connection.commit()
    connection.close()

    config = GatewayConfig(
        database_path=database,
        admin_socket=tmp_path / "admin.sock",
        public_base_url="https://gateway.example.test",
    )
    app = create_app(config)
    assert app[STORE_KEY].validate_access("legacy-access") is None
    row = app[STORE_KEY].connection.execute("SELECT family_id, revoked_at FROM tokens").fetchone()
    assert row["family_id"]
    assert row["revoked_at"] is not None
    app[STORE_KEY].close()


def test_reservation_limiter_uses_an_injectable_monotonic_clock() -> None:
    now = [100.0]
    limiter = ReservationLimiter(2, window_seconds=10, clock=lambda: now[0])
    assert limiter.reserve() is True
    assert limiter.reserve() is True
    assert limiter.reserve() is False
    now[0] += 9.999
    assert limiter.reserve() is False
    now[0] += 0.001
    assert limiter.reserve() is True


@pytest.mark.asyncio
async def test_dcr_and_pairing_reservations_are_separate_and_bounded(gateway) -> None:
    client, _ = gateway
    for number in range(16):
        registration = await client.post("/oauth/register", json={
            "redirect_uris": [f"https://chatgpt.example.test/{number}"],
        })
        assert registration.status == 201
    blocked_registration = await client.post("/oauth/register", json={
        "redirect_uris": ["https://chatgpt.example.test/blocked"],
    })
    assert blocked_registration.status == 429

    authorise_params = {
        "response_type": "code", "client_id": "chatgpt", "redirect_uri": REDIRECT,
        "code_challenge_method": "S256", "code_challenge": pkce_s256(VERIFIER),
    }
    for _ in range(32):
        pairing = await client.get("/oauth/authorize", params=authorise_params)
        assert pairing.status == 200
    blocked_pairing = await client.get("/oauth/authorize", params=authorise_params)
    assert blocked_pairing.status == 429
