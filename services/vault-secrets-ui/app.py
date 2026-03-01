import json
import os
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://vault:8200").rstrip("/")
VAULT_TOKEN_FILE = os.getenv("VAULT_TOKEN_FILE", "/vault/runtime/admin.token")
RUNTIME_DIR = Path(os.getenv("VAULT_RUNTIME_DIR", "/vault/runtime"))

BASE_DIR = Path(__file__).resolve().parent
UI_TEMPLATE_PATH = BASE_DIR / "vault_webui.html"

SERVICE_CONFIGS = {
    "mega-orchestrator": {
        "label": "MEGA ORCHESTRATOR",
        "vault_path": "orchestration/mega-orchestrator",
        "env_file": "/vault/runtime/mega-orchestrator.env",
        "restart_target": "mega-orchestrator",
        "description": "Primary orchestrator provider keys and marketplace token.",
        "runtime_keys": {
            "OPENAI_API_KEY": "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "GOOGLE_API_KEY": "GOOGLE_API_KEY",
            "PERPLEXITY_API_KEY": "PERPLEXITY_API_KEY",
            "MARKETPLACE_JWT_TOKEN": "MARKETPLACE_JWT_TOKEN",
        },
    },
    "research-mcp": {
        "label": "RESEARCH MCP",
        "vault_path": "orchestration/research-mcp",
        "env_file": "/vault/runtime/research-mcp.env",
        "restart_target": "research-mcp",
        "description": "Perplexity and OpenAI research keys.",
        "runtime_keys": {
            "PERPLEXITY_API_KEY": "PERPLEXITY_API_KEY",
            "OPENAI_API_KEY": "OPENAI_API_KEY",
        },
    },
    "advanced-memory-mcp": {
        "label": "ADVANCED MEMORY MCP",
        "vault_path": "orchestration/advanced-memory-mcp",
        "env_file": "/vault/runtime/advanced-memory-mcp.env",
        "restart_target": "advanced-memory-mcp",
        "description": "Prepared for runtime injection; local runtime validation may be deferred.",
        "runtime_keys": {
            "OPENAI_API_KEY": "OPENAI_API_KEY",
        },
    },
    "zen-mcp-server": {
        "label": "ZEN MCP SERVER",
        "vault_path": "orchestration/zen-mcp-server",
        "env_file": "/vault/runtime/zen-mcp-server.env",
        "restart_target": "zen-mcp-server",
        "description": "Provider keys and model defaults for ZEN MCP.",
        "runtime_keys": {
            "DEFAULT_MODEL": "DEFAULT_MODEL",
            "OPENAI_API_KEY": "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "GOOGLE_API_KEY": "GOOGLE_API_KEY",
            "XAI_API_KEY": "XAI_API_KEY",
            "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
            "DIAL_API_KEY": "DIAL_API_KEY",
            "DIAL_API_HOST": "DIAL_API_HOST",
            "DIAL_API_VERSION": "DIAL_API_VERSION",
            "CUSTOM_API_URL": "CUSTOM_API_URL",
            "CUSTOM_API_KEY": "CUSTOM_API_KEY",
            "CUSTOM_MODEL_NAME": "CUSTOM_MODEL_NAME",
            "DISABLED_TOOLS": "DISABLED_TOOLS",
            "MAX_MCP_OUTPUT_TOKENS": "MAX_MCP_OUTPUT_TOKENS",
        },
    },
    "gmail-mcp": {
        "label": "GMAIL MCP",
        "vault_path": "orchestration/gmail-mcp",
        "env_file": "/vault/runtime/gmail-mcp.env",
        "restart_target": "gmail-mcp",
        "description": "Email credentials and mail transport settings.",
        "runtime_keys": {
            "EMAIL_ADDRESS": "EMAIL_ADDRESS",
            "EMAIL_PASSWORD": "EMAIL_PASSWORD",
            "IMAP_SERVER": "IMAP_SERVER",
            "SMTP_SERVER": "SMTP_SERVER",
            "SMTP_PORT": "SMTP_PORT",
        },
    },
    "security-mcp": {
        "label": "SECURITY MCP",
        "vault_path": "orchestration/internal-auth",
        "env_file": "/vault/runtime/security-mcp.env",
        "restart_target": "security-mcp",
        "description": "Shared internal JWT secret mapped as JWT_SECRET_KEY.",
        "runtime_keys": {
            "JWT_SECRET": "JWT_SECRET_KEY",
        },
    },
    "marketplace-mcp": {
        "label": "MARKETPLACE MCP",
        "vault_path": "orchestration/internal-auth",
        "env_file": "/vault/runtime/marketplace-mcp.env",
        "restart_target": "marketplace-mcp",
        "description": "Shared internal JWT secret mapped as JWT_SECRET.",
        "runtime_keys": {
            "JWT_SECRET": "JWT_SECRET",
        },
    },
    "common-mcp": {
        "label": "COMMON MCP",
        "vault_path": "orchestration/common-mcp",
        "env_file": "/vault/runtime/common-mcp.env",
        "restart_target": "vault-agent-common",
        "description": "Legacy shared namespace preserved for compatibility.",
        "runtime_keys": {
            "OPENAI_API_KEY": "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY": "ANTHROPIC_API_KEY",
            "GEMINI_API_KEY": "GEMINI_API_KEY",
        },
    },
    "perplexity-hub": {
        "label": "PERPLEXITY HUB",
        "vault_path": "orchestration/perplexity-hub",
        "env_file": "/vault/runtime/perplexity-hub.env",
        "restart_target": "research-mcp",
        "description": "Legacy Perplexity namespace preserved for compatibility.",
        "runtime_keys": {
            "PERPLEXITY_API_KEY": "PERPLEXITY_API_KEY",
        },
    },
}

app = FastAPI(title="Vault Secrets UI", version="1.0.0")


class SecretUpdate(BaseModel):
    data: dict[str, Any]


def _service_metadata(service: str) -> dict[str, Any]:
    try:
        config = SERVICE_CONFIGS[service]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Unknown service") from exc

    restart_target = config["restart_target"]
    return {
        "id": service,
        "label": config["label"],
        "vault_path": config["vault_path"],
        "env_file": config["env_file"],
        "runtime_keys": dict(config["runtime_keys"]),
        "restart_required": True,
        "restart_target": restart_target,
        "restart_command": (
            "docker compose -f docker-compose.yml -f docker-compose.vault.yml "
            f"restart {restart_target}"
        ),
        "description": config["description"],
    }


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
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        resp = await client.get(url, headers=_vault_headers())

    if resp.status_code == 404:
        return {}
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    payload = resp.json()
    return payload.get("data", {}).get("data", {})


async def _vault_put(path: str, data: dict[str, Any]) -> None:
    url = f"{VAULT_ADDR}/v1/secret/data/{path}"
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        resp = await client.post(url, headers=_vault_headers(), json={"data": data})

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _write_runtime_env(metadata: dict[str, Any], data: dict[str, Any]) -> None:
    target_path = Path(metadata["env_file"])
    target_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = target_path.with_suffix(target_path.suffix + ".tmp")

    lines = [
        "# Auto-generated from Vault by vault-secrets-ui.",
        "# This file may also be refreshed by render-envs.sh.",
        "# Do not edit it directly.",
        "",
        f"SERVICE_NAME={_shell_quote(metadata['id'])}",
        f"VAULT_SECRET_PATH={_shell_quote('secret/data/' + metadata['vault_path'])}",
    ]

    for source_key, target_key in metadata["runtime_keys"].items():
        value = data.get(source_key, "")
        if value is None:
            value = ""
        if not isinstance(value, str):
            value = str(value)
        lines.append(f"{target_key}={_shell_quote(value)}")

    tmp_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    tmp_path.replace(target_path)


def _refresh_runtime_exports(vault_path: str, data: dict[str, Any]) -> None:
    for service in SERVICE_CONFIGS:
        metadata = _service_metadata(service)
        if metadata["vault_path"] == vault_path:
            _write_runtime_env(metadata, data)


def _service_secret_path(service: str) -> str:
    return _service_metadata(service)["vault_path"]


async def _probe_vault() -> dict[str, Any]:
    try:
        headers = _vault_headers()
    except HTTPException as exc:
        return {"token_ready": False, "vault_reachable": False, "detail": exc.detail}

    try:
        async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
            resp = await client.get(f"{VAULT_ADDR}/v1/sys/health", headers=headers)
    except httpx.HTTPError as exc:
        return {"token_ready": True, "vault_reachable": False, "detail": str(exc)}

    return {
        "token_ready": True,
        "vault_reachable": resp.status_code < 500,
        "detail": None if resp.status_code < 500 else resp.text,
        "vault_status_code": resp.status_code,
    }


@app.get("/health")
async def health() -> dict[str, Any]:
    probe = await _probe_vault()
    return {
        "status": "healthy" if probe["token_ready"] and probe["vault_reachable"] else "degraded",
        "service": "vault-secrets-ui",
        "vault_addr": VAULT_ADDR,
        "token_file": VAULT_TOKEN_FILE,
        "token_ready": probe["token_ready"],
        "vault_reachable": probe["vault_reachable"],
        "vault_status_code": probe.get("vault_status_code"),
        "detail": probe.get("detail"),
        "services": list(SERVICE_CONFIGS.keys()),
    }


@app.get("/api/services")
async def list_services() -> dict[str, Any]:
    return {"services": [_service_metadata(service) for service in SERVICE_CONFIGS]}


@app.get("/api/secrets/{service}")
async def get_service_secrets(service: str) -> dict[str, Any]:
    metadata = _service_metadata(service)
    path = _service_secret_path(service)
    data = await _vault_get(path)
    return {"service": service, "metadata": metadata, "data": data}


@app.put("/api/secrets/{service}")
async def update_service_secrets(service: str, payload: SecretUpdate) -> dict[str, Any]:
    metadata = _service_metadata(service)
    path = _service_secret_path(service)
    await _vault_put(path, payload.data)
    current_data = await _vault_get(path)
    _refresh_runtime_exports(metadata["vault_path"], current_data)
    return {
        "status": "ok",
        "service": service,
        "restart_required": metadata["restart_required"],
        "restart_target": metadata["restart_target"],
        "restart_command": metadata["restart_command"],
    }


def _render_ui_html() -> str:
    template = UI_TEMPLATE_PATH.read_text(encoding="utf-8")
    options = "\n".join(
        f'                            <option value="{service}">{config["label"]}</option>'
        for service, config in SERVICE_CONFIGS.items()
    )
    metadata_json = json.dumps(
        {service: _service_metadata(service) for service in SERVICE_CONFIGS},
        ensure_ascii=True,
    )
    return (
        template
        .replace("{{SERVICE_OPTIONS}}", options)
        .replace("{{SERVICE_METADATA_JSON}}", metadata_json)
    )


@app.get("/", response_class=HTMLResponse)
async def ui() -> str:
    return _render_ui_html()
