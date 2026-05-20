"""Minimal Vercel preview entrypoint for the orchestration monorepo."""

import json
from typing import Any


async def app(scope: dict[str, Any], receive: Any, send: Any) -> None:
    if scope["type"] != "http":
        return

    body = json.dumps({"status": "ok", "service": "orchestration"}).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"content-length", str(len(body)).encode()),
    ]

    await send({"type": "http.response.start", "status": 200, "headers": headers})
    await send({"type": "http.response.body", "body": body})
