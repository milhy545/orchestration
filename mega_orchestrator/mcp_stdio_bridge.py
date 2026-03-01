#!/usr/bin/env python3
"""Minimal MCP stdio bridge for Mega Orchestrator."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from mega_orchestrator.mcp_tooling import MCP_TOOL_DEFINITIONS, build_mcp_tools


MEGA_BASE_URL = os.getenv("MEGA_ORCHESTRATOR_URL", "http://127.0.0.1:7000").rstrip("/")
RPC_URL = f"{MEGA_BASE_URL}/mcp/rpc"
SCHEMA_URL = f"{MEGA_BASE_URL}/mcp/schema"


def _write_message(payload: Dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def _read_message() -> Optional[Dict[str, Any]]:
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        decoded = line.decode("ascii", errors="ignore").strip()
        if ":" in decoded:
            key, value = decoded.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    content_length = int(headers.get("content-length", "0"))
    if content_length <= 0:
        return None

    body = sys.stdin.buffer.read(content_length)
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=True).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def _get_json(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=10) as response:
        body = response.read().decode("utf-8")
        return json.loads(body) if body else {}


def _fallback_tools() -> Dict[str, Any]:
    return {"tools": build_mcp_tools(MCP_TOOL_DEFINITIONS.keys())}


def _handle_request(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    request_id = message.get("id")

    if message.get("jsonrpc") != "2.0":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32600, "message": "Invalid Request"},
        }

    method = message.get("method")
    params = message.get("params", {}) or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "serverInfo": {"name": "mega-orchestrator-stdio-bridge", "version": "1.0.0"},
                "capabilities": {"tools": {"listChanged": False}},
            },
        }

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"ok": True}}

    if method == "tools/list":
        try:
            schema = _get_json(SCHEMA_URL)
            result = {"tools": schema.get("tools", [])}
        except Exception:
            result = _fallback_tools()
        return {"jsonrpc": "2.0", "id": request_id, "result": result}

    if method == "tools/call":
        try:
            result = _post_json(
                RPC_URL,
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "method": "tools/call",
                    "params": {
                        "name": params.get("name"),
                        "arguments": params.get("arguments", {}) or {},
                        "session_id": params.get("session_id"),
                        "context_id": params.get("context_id"),
                    },
                },
            )
            return result
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Backend HTTP error {exc.code}: {detail}"},
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32603, "message": f"Backend unreachable: {exc}"},
            }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    while True:
        message = _read_message()
        if message is None:
            return 0
        try:
            response = _handle_request(message)
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32603, "message": f"Internal error: {exc}"},
            }
        if response is not None:
            _write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
