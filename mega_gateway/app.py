"""aiohttp application exposing an OAuth-protected MCP subset."""

from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from aiohttp import ClientSession, ClientTimeout, web

from .security import (
    DCR_RESERVATION_LIMIT,
    PAIRING_RESERVATION_LIMIT,
    DEFAULT_TOOL_NAMES,
    GatewayStore,
    OAuthError,
    ReservationLimiter,
)


ALLOWED_TOOLS = DEFAULT_TOOL_NAMES
ALLOWED_MCP_METHODS = frozenset({"initialize", "notifications/initialized", "ping", "tools/list", "tools/call"})


def _csv(value: str | None) -> frozenset[str]:
    return frozenset(item.strip() for item in (value or "").split(",") if item.strip())


@dataclass(frozen=True)
class GatewayConfig:
    database_path: Path = Path("/data/mega-gateway.sqlite3")
    admin_socket: Path = Path("/run/mega-gateway/admin.sock")
    backend_url: str = "http://mega-orchestrator:7000/mcp"
    chatgpt_client_id: str = "chatgpt"
    gemini_spark_client_id: str = "gemini-spark"
    chatgpt_redirect_uris: frozenset[str] = field(default_factory=frozenset)
    gemini_spark_redirect_uris: frozenset[str] = field(default_factory=frozenset)
    chatgpt_registration_redirect_hosts: frozenset[str] = field(default_factory=frozenset)
    public_base_url: str = ""

    @classmethod
    def from_environment(cls) -> "GatewayConfig":
        public_base_url = os.getenv("MEGA_GATEWAY_PUBLIC_BASE_URL", "")
        if not _valid_public_base_url(public_base_url):
            raise RuntimeError("MEGA_GATEWAY_PUBLIC_BASE_URL must be an absolute HTTPS URL without a path")
        redirect_hosts = _csv(os.getenv("MEGA_GATEWAY_CHATGPT_REGISTRATION_REDIRECT_HOSTS"))
        if not redirect_hosts:
            raise RuntimeError("MEGA_GATEWAY_CHATGPT_REGISTRATION_REDIRECT_HOSTS must list approved HTTPS hosts")
        return cls(
            database_path=Path(os.getenv("MEGA_GATEWAY_DB", "/data/mega-gateway.sqlite3")),
            admin_socket=Path(os.getenv("MEGA_GATEWAY_ADMIN_SOCKET", "/run/mega-gateway/admin.sock")),
            backend_url=os.getenv("MEGA_GATEWAY_BACKEND_URL", "http://mega-orchestrator:7000/mcp"),
            chatgpt_client_id=os.getenv("MEGA_GATEWAY_CHATGPT_CLIENT_ID", "chatgpt"),
            gemini_spark_client_id=os.getenv("MEGA_GATEWAY_GEMINI_SPARK_CLIENT_ID", "gemini-spark"),
            chatgpt_redirect_uris=_csv(os.getenv("MEGA_GATEWAY_CHATGPT_REDIRECT_URIS")),
            gemini_spark_redirect_uris=_csv(os.getenv("MEGA_GATEWAY_GEMINI_SPARK_REDIRECT_URIS")),
            chatgpt_registration_redirect_hosts=frozenset(host.lower() for host in redirect_hosts),
            public_base_url=public_base_url.rstrip("/"),
        )

    def profile_for(self, client_id: str, redirect_uri: str) -> str | None:
        profiles = (
            ("chatgpt", self.chatgpt_client_id, self.chatgpt_redirect_uris),
            ("gemini-spark", self.gemini_spark_client_id, self.gemini_spark_redirect_uris),
        )
        for profile, expected_client, allowed_redirects in profiles:
            if client_id == expected_client and redirect_uri in allowed_redirects:
                return profile
        return None


def _valid_public_base_url(value: str) -> bool:
    parsed = urlparse(value)
    return (
        parsed.scheme == "https"
        and bool(parsed.netloc)
        and parsed.path in ("", "/")
        and not parsed.params
        and not parsed.query
        and not parsed.fragment
        and not parsed.username
        and not parsed.password
    )


def _valid_s256_challenge(value: str | None) -> bool:
    return bool(value) and len(value) == 43 and value.isascii() and all(
        character.isalnum() or character in "-_" for character in value
    )


def _profile_for(app: web.Application, client_id: str, redirect_uri: str) -> str | None:
    return app[CONFIG_KEY].profile_for(client_id, redirect_uri) or app[STORE_KEY].registered_profile_for(
        client_id, redirect_uri
    )


CONFIG_KEY: web.AppKey[GatewayConfig] = web.AppKey("config", GatewayConfig)
STORE_KEY: web.AppKey[GatewayStore] = web.AppKey("store", GatewayStore)
HTTP_KEY: web.AppKey[ClientSession | None] = web.AppKey("http", ClientSession | None)
ADMIN_SERVER_KEY: web.AppKey[asyncio.AbstractServer] = web.AppKey("admin_server", asyncio.AbstractServer)
DCR_RESERVATION_KEY: web.AppKey[ReservationLimiter] = web.AppKey("dcr_reservation", ReservationLimiter)
PAIRING_RESERVATION_KEY: web.AppKey[ReservationLimiter] = web.AppKey("pairing_reservation", ReservationLimiter)


def _json_error(error: str, description: str, status: int = 400) -> web.Response:
    return web.json_response({"error": error, "error_description": description}, status=status)


def _auth_params(request: web.Request) -> dict[str, str]:
    return {key: value for key, value in request.query.items()}


def _redirect(uri: str, params: dict[str, str]) -> web.Response:
    parsed = urlparse(uri)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update(params)
    return web.HTTPFound(urlunparse(parsed._replace(query=urlencode(query))))


def _mcp_error(request_id: Any, code: int, message: str) -> web.Response:
    return web.json_response({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


async def _require_access(request: web.Request) -> dict[str, str] | web.Response:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer ") or not header[7:]:
        response = _json_error("invalid_token", "Bearer access token required", 401)
        response.headers["WWW-Authenticate"] = _bearer_challenge(request, "invalid_token")
        return response
    principal = request.app[STORE_KEY].validate_access(header[7:])
    if not principal:
        response = _json_error("invalid_token", "Access token is invalid, expired, or revoked", 401)
        response.headers["WWW-Authenticate"] = _bearer_challenge(request, "invalid_token")
        return response
    return principal


def _base_url(request: web.Request) -> str:
    """Return the deployment-configured public origin; never trust proxy headers."""
    return request.app[CONFIG_KEY].public_base_url.rstrip("/")


def _bearer_challenge(request: web.Request, error: str) -> str:
    metadata = f'{_base_url(request)}/.well-known/oauth-protected-resource'
    return f'Bearer resource_metadata="{metadata}", error="{error}"'


async def health(_: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "mega-security-gateway"})


async def protected_resource_metadata(request: web.Request) -> web.Response:
    base = _base_url(request)
    return web.json_response(
        {
            "resource": f"{base}/mcp",
            "authorization_servers": [base],
            "bearer_methods_supported": ["header"],
        }
    )


async def authorisation_server_metadata(request: web.Request) -> web.Response:
    base = _base_url(request)
    return web.json_response(
        {
            "issuer": base,
            "authorization_endpoint": f"{base}/oauth/authorize",
            "token_endpoint": f"{base}/oauth/token",
            "revocation_endpoint": f"{base}/oauth/revoke",
            "registration_endpoint": f"{base}/oauth/register",
            "response_types_supported": ["code"],
            "grant_types_supported": ["authorization_code", "refresh_token"],
            "code_challenge_methods_supported": ["S256"],
            "token_endpoint_auth_methods_supported": ["none"],
        }
    )


def _pending_page(pairing_id: str, expires_at: int) -> web.Response:
    # The opaque pairing id is a short-lived browser capability.  The page only
    # polls status and resumes the original authorisation request after approval.
    html = f"""<!doctype html><title>Mega pairing approval</title>
<main><h1>Waiting for local approval</h1><p>Approve pairing <code>{pairing_id}</code> on the local operator socket.</p>
<p id=\"status\">This request expires at {expires_at}.</p></main>
<script>
const id = {json.dumps(pairing_id)};
const original = new URL(window.location.href);
async function poll() {{
  const response = await fetch(`/oauth/pairings/${{encodeURIComponent(id)}}`, {{cache: 'no-store'}});
  const pairing = await response.json();
  document.querySelector('#status').textContent = pairing.status;
  if (pairing.status === 'approved') {{ original.searchParams.set('pairing_id', id); window.location.assign(original); }}
  if (pairing.status === 'pending') setTimeout(poll, 1000);
}}
poll();
</script>"""
    return web.Response(text=html, content_type="text/html", headers={"Cache-Control": "no-store"})


async def pairing_status(request: web.Request) -> web.Response:
    pairing = request.app[STORE_KEY].pairing(request.match_info["pairing_id"])
    if not pairing:
        return _json_error("invalid_request", "Pairing not found", 404)
    return web.json_response({"pairing_id": pairing["id"], "status": pairing["status"], "expires_at": pairing["expires_at"]}, headers={"Cache-Control": "no-store"})


def _valid_registration_redirect_uri(value: Any, allowed_hosts: frozenset[str]) -> bool:
    if not isinstance(value, str) or len(value) > 2048:
        return False
    try:
        parsed = urlparse(value)
        port = parsed.port
    except ValueError:
        return False
    return (
        parsed.scheme == "https"
        and parsed.hostname in allowed_hosts
        and port in (None, 443)
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
    )


async def register_chatgpt_client(request: web.Request) -> web.Response:
    """Register a short-lived public ChatGPT client on a controlled redirect host."""
    try:
        metadata = await request.json()
    except (json.JSONDecodeError, ValueError):
        return _json_error("invalid_client_metadata", "JSON metadata is required")
    if not isinstance(metadata, dict):
        return _json_error("invalid_client_metadata", "Metadata must be an object")
    redirect_uris = metadata.get("redirect_uris")
    if (
        not isinstance(redirect_uris, list)
        or not redirect_uris
        or len(redirect_uris) > 8
        or not all(isinstance(uri, str) for uri in redirect_uris)
        or len(set(redirect_uris)) != len(redirect_uris)
        or not all(_valid_registration_redirect_uri(uri, request.app[CONFIG_KEY].chatgpt_registration_redirect_hosts) for uri in redirect_uris)
    ):
        return _json_error("invalid_redirect_uri", "Use one to eight unique HTTPS redirect URIs")
    if metadata.get("token_endpoint_auth_method", "none") != "none":
        return _json_error("invalid_client_metadata", "Only public PKCE clients are supported")
    grant_types = metadata.get("grant_types")
    if grant_types is not None and (
        not isinstance(grant_types, list)
        or not all(isinstance(grant, str) for grant in grant_types)
        or "authorization_code" not in grant_types
        or not set(grant_types).issubset({"authorization_code", "refresh_token"})
    ):
        return _json_error("invalid_client_metadata", "Only authorization_code and refresh_token grants are supported")
    response_types = metadata.get("response_types")
    if response_types is not None and (
        not isinstance(response_types, list)
        or not all(isinstance(response_type, str) for response_type in response_types)
        or set(response_types) != {"code"}
    ):
        return _json_error("invalid_client_metadata", "Only the code response type is supported")
    client_name = metadata.get("client_name", "ChatGPT")
    if not isinstance(client_name, str) or not client_name.strip() or len(client_name) > 128:
        return _json_error("invalid_client_metadata", "client_name must be a non-empty string up to 128 characters")
    if not request.app[DCR_RESERVATION_KEY].reserve():
        return _json_error("temporarily_unavailable", "Dynamic registration rate limit reached", 429)
    try:
        client_id, issued_at = request.app[STORE_KEY].register_chatgpt_client(redirect_uris)
    except OAuthError as exc:
        return _json_error("invalid_client_metadata", str(exc), 429)
    return web.json_response(
        {
            "client_id": client_id,
            "client_id_issued_at": issued_at,
            "client_name": client_name,
            "redirect_uris": redirect_uris,
            "token_endpoint_auth_method": "none",
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
        },
        status=201,
        headers={"Cache-Control": "no-store"},
    )


async def authorize(request: web.Request) -> web.Response:
    params = _auth_params(request)
    if params.get("response_type") != "code":
        return _json_error("unsupported_response_type", "Only response_type=code is supported")
    client_id, redirect_uri = params.get("client_id", ""), params.get("redirect_uri", "")
    profile = _profile_for(request.app, client_id, redirect_uri)
    if not profile:
        return _json_error("invalid_request", "Unknown client_id or redirect_uri")
    if params.get("code_challenge_method") != "S256" or not _valid_s256_challenge(params.get("code_challenge")):
        return _json_error("invalid_request", "PKCE S256 code_challenge is required")

    pairing_id = params.get("pairing_id")
    if not pairing_id:
        if not request.app[PAIRING_RESERVATION_KEY].reserve():
            return _json_error("temporarily_unavailable", "Pairing creation rate limit reached", 429)
        try:
            pairing = request.app[STORE_KEY].create_pairing(
                client_id=client_id,
                redirect_uri=redirect_uri,
                profile=profile,
                code_challenge=params["code_challenge"],
                state=params.get("state"),
            )
        except OAuthError as exc:
            return _json_error("temporarily_unavailable", str(exc), 429)
        return _pending_page(pairing["pairing_id"], pairing["expires_at"])

    pairing = request.app[STORE_KEY].pairing(pairing_id)
    if not pairing or any(
        pairing[key] != value
        for key, value in (
            ("client_id", client_id),
            ("redirect_uri", redirect_uri),
            ("profile", profile),
            ("code_challenge", params["code_challenge"]),
        )
    ):
        return _json_error("invalid_request", "Pairing does not match this authorisation request")
    if pairing["status"] == "pending":
        return _pending_page(pairing_id, pairing["expires_at"])
    if pairing["status"] != "approved":
        return _json_error("access_denied", "Pairing was denied, expired, or already used", 403)
    try:
        code = request.app[STORE_KEY].issue_code(pairing_id)
    except OAuthError as exc:
        return _json_error("access_denied", str(exc), 403)
    response = {"code": code}
    if pairing["state"] is not None:
        response["state"] = pairing["state"]
    raise _redirect(redirect_uri, response)


async def token(request: web.Request) -> web.Response:
    data = await request.post()
    store = request.app[STORE_KEY]
    try:
        if data.get("grant_type") == "authorization_code":
            tokens = store.redeem_code(
                code=str(data.get("code", "")),
                client_id=str(data.get("client_id", "")),
                redirect_uri=str(data.get("redirect_uri", "")),
                verifier=str(data.get("code_verifier", "")),
            )
        elif data.get("grant_type") == "refresh_token":
            tokens = store.rotate_refresh(str(data.get("refresh_token", "")), str(data.get("client_id", "")))
        else:
            return _json_error("unsupported_grant_type", "Supported grants are authorization_code and refresh_token")
    except OAuthError as exc:
        return _json_error("invalid_grant", str(exc))
    return web.json_response(tokens.response(), headers={"Cache-Control": "no-store", "Pragma": "no-cache"})


async def revoke(request: web.Request) -> web.Response:
    data = await request.post()
    token = str(data.get("token", ""))
    if token:
        request.app[STORE_KEY].revoke(token)
    return web.Response(status=200, headers={"Cache-Control": "no-store"})


def _filtered_tools(payload: dict[str, Any], allowed_tools: frozenset[str]) -> dict[str, Any]:
    try:
        tools = payload["result"]["tools"]
    except (KeyError, TypeError):
        return payload
    payload["result"]["tools"] = [tool for tool in tools if tool.get("name") in allowed_tools]
    return payload


async def mcp(request: web.Request) -> web.Response:
    principal = await _require_access(request)
    if isinstance(principal, web.Response):
        return principal
    try:
        data = await request.json()
    except (json.JSONDecodeError, ValueError):
        return _mcp_error(None, -32700, "Parse error")
    if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
        return _mcp_error(data.get("id") if isinstance(data, dict) else None, -32600, "JSON-RPC 2.0 required")
    method, request_id = data.get("method"), data.get("id")
    if method not in ALLOWED_MCP_METHODS:
        return _mcp_error(request_id, -32601, "Method not exposed by this gateway")
    if method == "tools/call":
        name = (data.get("params") or {}).get("name")
        if name not in request.app[STORE_KEY].tools_for_profile(principal["profile"]):
            return _mcp_error(request_id, -32601, "Tool not exposed by this gateway")
    headers = {"Content-Type": "application/json", "X-Mega-Gateway-Profile": principal["profile"]}
    try:
        session = request.app[HTTP_KEY]
        if session is None:
            return web.Response(status=503, text="MCP gateway is starting")
        async with session.post(request.app[CONFIG_KEY].backend_url, json=data, headers=headers) as upstream:
            body = await upstream.read()
            if upstream.status >= 400:
                return web.Response(status=502, text="MCP backend request failed")
    except asyncio.TimeoutError:
        return web.Response(status=504, text="MCP backend timed out")
    except Exception:
        return web.Response(status=502, text="MCP backend unavailable")
    if method == "tools/list":
        try:
            allowed_tools = request.app[STORE_KEY].tools_for_profile(principal["profile"])
            body = json.dumps(_filtered_tools(json.loads(body), allowed_tools)).encode("utf-8")
        except (json.JSONDecodeError, TypeError):
            return web.Response(status=502, text="MCP backend returned invalid tool list")
    return web.Response(body=body, content_type="application/json")


async def _admin_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter, app: web.Application) -> None:
    """Serve the deliberately tiny JSON-lines operator protocol on a Unix socket."""
    try:
        raw = await asyncio.wait_for(reader.readline(), timeout=5)
        if not raw or len(raw) > 16_384:
            raise ValueError("request must be one JSON line no longer than 16 KiB")
        message = json.loads(raw)
        if not isinstance(message, dict) or not isinstance(message.get("action"), str):
            raise ValueError("action is required")
        payload = message.get("payload", {})
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        store = app[STORE_KEY]
        action = message["action"]
        if action == "status":
            result: Any = {"service": "mega-security-gateway", "profiles": ["chatgpt", "gemini-spark"], "allowed_tools": sorted(ALLOWED_TOOLS)}
        elif action == "pairing.pending":
            result = store.pending_pairings()
        elif action in {"pairing.approve", "pairing.reject"}:
            pairing_id = payload.get("pairing_id")
            if not isinstance(pairing_id, str):
                raise ValueError("pairing_id is required")
            pairing = store.decide_pairing(pairing_id, action == "pairing.approve")
            if pairing is None:
                raise ValueError("pairing not found")
            result = {"pairing_id": pairing["id"], "status": pairing["status"], "expires_at": pairing["expires_at"]}
        elif action == "profile.tools":
            profile = payload.get("profile_id")
            if profile not in (None, "chatgpt", "gemini-spark"):
                raise ValueError("unknown profile")
            result = {"profile": profile or "all", "tools": sorted(ALLOWED_TOOLS) if profile is None else sorted(store.tools_for_profile(profile))}
        elif action in {"profile.tool.grant", "profile.tool.revoke"}:
            profile, tool = payload.get("profile_id"), payload.get("tool")
            if not isinstance(profile, str) or not isinstance(tool, str):
                raise ValueError("profile_id and tool are required")
            store.set_profile_tool(profile, tool, action == "profile.tool.grant")
            result = {"profile": profile, "tools": sorted(store.tools_for_profile(profile))}
        elif action == "connections.list":
            result = store.active_connections()
        elif action in {"audit.recent", "backup.config.check", "funnel.status"}:
            # This gateway never owns Funnel and does not expose backend administration.
            result = [] if action in {"connections.list", "audit.recent"} else {"enabled": False}
        elif action == "connections.revoke":
            token = payload.get("connection_id")
            if not isinstance(token, str):
                raise ValueError("connection_id is required")
            store.revoke_connection(token)
            result = {"revoked": True}
        else:
            raise ValueError("action is not exposed by this gateway")
        response = {"ok": True, "data": result}
    except (ValueError, json.JSONDecodeError, asyncio.TimeoutError) as exc:
        response = {"ok": False, "error": str(exc)}
    writer.write((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
    await writer.drain()
    writer.close()
    await writer.wait_closed()


async def on_startup(app: web.Application) -> None:
    app[HTTP_KEY] = ClientSession(timeout=ClientTimeout(total=10))
    socket_path: Path = app[CONFIG_KEY].admin_socket
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists() or socket_path.is_socket():
        socket_path.unlink()
    app[ADMIN_SERVER_KEY] = await asyncio.start_unix_server(
        lambda reader, writer: _admin_connection(reader, writer, app), path=str(socket_path)
    )
    socket_path.chmod(0o600)


async def on_cleanup(app: web.Application) -> None:
    session = app[HTTP_KEY]
    if session is not None:
        await session.close()
    server = app.get(ADMIN_SERVER_KEY)
    if server:
        server.close()
        await server.wait_closed()
    socket_path: Path = app[CONFIG_KEY].admin_socket
    if socket_path.exists() or socket_path.is_socket():
        socket_path.unlink()
    app[STORE_KEY].close()


def create_app(
    config: GatewayConfig | None = None,
    monotonic_clock: Callable[[], float] = time.monotonic,
) -> web.Application:
    config = config or GatewayConfig.from_environment()
    if not _valid_public_base_url(config.public_base_url):
        raise ValueError("GatewayConfig.public_base_url must be an absolute HTTPS URL without a path")
    app = web.Application(client_max_size=128 * 1024)
    app[CONFIG_KEY] = config
    app[STORE_KEY] = GatewayStore(config.database_path)
    app[HTTP_KEY] = None
    app[DCR_RESERVATION_KEY] = ReservationLimiter(DCR_RESERVATION_LIMIT, clock=monotonic_clock)
    app[PAIRING_RESERVATION_KEY] = ReservationLimiter(PAIRING_RESERVATION_LIMIT, clock=monotonic_clock)
    app.router.add_get("/health", health)
    app.router.add_get("/.well-known/oauth-protected-resource", protected_resource_metadata)
    app.router.add_get("/.well-known/oauth-authorization-server", authorisation_server_metadata)
    app.router.add_get("/oauth/authorize", authorize)
    app.router.add_post("/oauth/register", register_chatgpt_client)
    app.router.add_get("/oauth/pairings/{pairing_id}", pairing_status)
    app.router.add_post("/oauth/token", token)
    app.router.add_post("/oauth/revoke", revoke)
    app.router.add_post("/mcp", mcp)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    return app
