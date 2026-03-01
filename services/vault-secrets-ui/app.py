import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200").rstrip("/")
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "/vault/runtime/admin.token")

BASE_DIR = Path(__file__).resolve().parent
UI_TEMPLATE_PATH = BASE_DIR / "vault_webui.html"

SERVICE_PATHS = {
    "mega-orchestrator": "orchestration/mega-orchestrator",
    "research-mcp": "orchestration/research-mcp",
    "advanced-memory-mcp": "orchestration/advanced-memory-mcp",
    "zen-mcp-server": "orchestration/zen-mcp-server",
    "common-mcp": "orchestration/common-mcp",
    "perplexity-hub": "orchestration/perplexity-hub",
}

app = FastAPI(title="Vault Secrets UI", version="1.0.0")


class SecretUpdate(BaseModel):
    data: dict[str, Any]


def _vault_headers() -> dict[str, str]:
    try:
        token = Path(VAULT_TOKEN_FILE).read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Vault token file missing: {VAULT_TOKEN_FILE}",
        ) from exc

    if not token:
        raise HTTPException(status_code=500, detail="Vault token file is empty")

    return {"X-Vault-Token": token}


async def _vault_get(path: str) -> dict[str, Any]:
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=_vault_headers())

    if resp.status_code == 404:
        return {}
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    payload = resp.json()
    return payload.get("data", {}).get("data", {})


async def _vault_put(path: str, data: dict[str, Any]) -> None:
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=_vault_headers(), json={"data": data})

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)


def _service_secret_path(service: str) -> str:
    try:
        return SERVICE_PATHS[service]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown service") from exc


@app.get("/health")
async def health() -> dict[str, Any]:
    return {
        "status": "healthy",
        "service": "vault-secrets-ui",
        "vault_addr": VAULT_ADDR,
        "services": list(SERVICE_PATHS.keys()),
    }


@app.get("/api/services")
async def list_services() -> dict[str, Any]:
    return {"services": list(SERVICE_PATHS.keys())}


@app.get("/api/secrets/{service}")
async def get_service_secrets(service: str) -> dict[str, Any]:
    path = _service_secret_path(service)
    data = await _vault_get(path)
    return {"service": service, "data": data}


@app.put("/api/secrets/{service}")
async def update_service_secrets(service: str, payload: SecretUpdate) -> dict[str, Any]:
    path = _service_secret_path(service)
    await _vault_put(path, payload.data)
    return {"status": "ok", "service": service}


def _render_ui_html() -> str:
    template = UI_TEMPLATE_PATH.read_text(encoding="utf-8")
    options = "\n".join(
        f'                            <option value="{service}">{service.upper()}</option>'
        for service in SERVICE_PATHS.keys()
    )
    return template.replace("{{SERVICE_OPTIONS}}", options)


@app.get("/", response_class=HTMLResponse)
async def ui() -> str:
    return _render_ui_html()
