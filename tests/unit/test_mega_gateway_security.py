"""Focused authentication and authorisation coverage for Mega gateway."""

from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from mega_gateway.app import GatewayConfig, create_app
from mega_gateway.security import pkce_s256


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
    )
    client = TestClient(TestServer(create_app(config)))
    await client.start_server()
    yield client, config
    await client.close()
    await backend_server.close()


async def _authorise(client: TestClient, config: GatewayConfig) -> str:
    params = {
        "response_type": "code",
        "client_id": "chatgpt",
        "redirect_uri": REDIRECT,
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
    assert (await resource.json())["authorization_servers"] == [str(client.make_url("/")).rstrip("/")]
    server = await client.get("/.well-known/oauth-authorization-server")
    assert (await server.json())["code_challenge_methods_supported"] == ["S256"]
