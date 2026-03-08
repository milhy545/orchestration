from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from vault_secrets_ui.advanced_memory import (
    discover_advanced_memory,
    run_console_command,
)
from vault_secrets_ui.config import ServiceRegistry, build_service_metadata, load_service_registry
from vault_secrets_ui.field_validation import validate_api_key
from vault_secrets_ui.models import ServiceDefinition
from vault_secrets_ui.runtime import write_runtime_env
from vault_secrets_ui.ui import render_ui_html
from vault_secrets_ui.vault import VaultClient


class SecretUpdate(BaseModel):
    data: dict[str, Any]


class AdvancedMemoryDiscoveryRequest(BaseModel):
    state: dict[str, Any]
    target: str = "all"


class AdvancedMemoryConsoleRequest(BaseModel):
    command: str
    state: dict[str, Any] | None = None


class FieldValidationRequest(BaseModel):
    service_id: str
    field_name: str
    state: dict[str, Any]


def _default_paths(base_dir: Path) -> tuple[Path, Path]:
    return (
        base_dir / "services.json",
        base_dir / "src" / "vault_secrets_ui" / "templates" / "vault_webui.html",
    )


def create_app(
    config_path: Path | None = None,
    template_path: Path | None = None,
    vault_client_factory: Callable[[], VaultClient] | None = None,
) -> FastAPI:
    base_dir = Path(__file__).resolve().parents[2]
    default_config_path, default_template_path = _default_paths(base_dir)
    resolved_config_path = config_path or default_config_path
    resolved_template_path = template_path or default_template_path
    registry = load_service_registry(Path(resolved_config_path))

    vault_addr = os.getenv("VAULT_ADDR", "http://vault:8200")
    token_file = Path(os.getenv("VAULT_TOKEN_FILE", "/vault/runtime/admin.token"))

    def default_vault_client() -> VaultClient:
        return VaultClient(base_url=vault_addr, token_file=token_file)

    client_factory = vault_client_factory or default_vault_client

    app = FastAPI(title="Vault Secrets UI", version="2.0.0")
    html_payload = render_ui_html(Path(resolved_template_path), registry)

    def get_service(service_id: str) -> ServiceDefinition:
        try:
            return registry.get(service_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Unknown service") from exc

    def merge_defaults(service: ServiceDefinition, data: dict[str, Any]) -> dict[str, Any]:
        merged = dict(data)
        for field in service.fields:
            if field.name not in merged and field.default not in ("", None):
                merged[field.name] = field.default
        return merged

    @app.get("/health")
    async def health() -> dict[str, Any]:
        vault_reachable = await client_factory().probe()
        return {
            "status": "healthy",
            "service": "vault-secrets-ui",
            "services": registry.ids(),
            "token_file_present": token_file.exists(),
            "vault_reachable": vault_reachable,
        }

    @app.get("/api/services")
    async def api_services() -> dict[str, Any]:
        return {"services": [build_service_metadata(service) for service in registry.all()]}

    @app.get("/api/secrets/{service_id}")
    async def api_get_secrets(service_id: str) -> dict[str, Any]:
        service = get_service(service_id)
        try:
            data = await client_factory().read_secret(service.vault_path)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or "Vault read failed"
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Vault is unreachable") from exc

        data = merge_defaults(service, data)

        return {
            "service": service.id,
            "metadata": build_service_metadata(service),
            "data": data,
        }

    @app.put("/api/secrets/{service_id}")
    async def api_put_secrets(service_id: str, update: SecretUpdate) -> dict[str, Any]:
        service = get_service(service_id)
        try:
            await client_factory().write_secret(service.vault_path, update.data)
            write_runtime_env(service, update.data)
        except ValueError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or "Vault write failed"
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail="Vault is unreachable") from exc

        metadata = build_service_metadata(service)
        return {
            "status": "ok",
            "service": service.id,
            "metadata": metadata,
            "restart_required": metadata["restart_required"],
            "restart_target": metadata["restart_target"],
            "restart_command": metadata["restart_command"],
        }

    @app.post("/api/provider-discovery/advanced-memory")
    async def api_advanced_memory_discovery(request: AdvancedMemoryDiscoveryRequest) -> dict[str, Any]:
        try:
            discovery = await discover_advanced_memory(request.state, target=request.target)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or "Provider discovery failed"
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Provider discovery failed: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return {"status": "ok", "discovery": discovery}

    @app.post("/api/field-validation")
    async def api_field_validation(request: FieldValidationRequest) -> dict[str, Any]:
        service = get_service(request.service_id)
        field = next((item for item in service.fields if item.name == request.field_name), None)
        if field is None:
            raise HTTPException(status_code=404, detail="Unknown field")
        if field.validation is None:
            raise HTTPException(status_code=400, detail="Field does not support API validation")

        result = await validate_api_key(field, request.state)
        return {
            "status": "ok",
            "service": service.id,
            "field_name": field.name,
            **result,
        }

    @app.post("/api/console/advanced-memory")
    async def api_advanced_memory_console(request: AdvancedMemoryConsoleRequest) -> dict[str, Any]:
        command = request.command.strip()
        state = dict(request.state or {})

        if command.lower() == "load":
            service = get_service("advanced-memory-mcp")
            try:
                data = await client_factory().read_secret(service.vault_path)
            except ValueError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text or "Vault read failed"
                raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail="Vault is unreachable") from exc

            merged = merge_defaults(service, data)
            return {
                "status": "ok",
                "output": ["Loaded advanced-memory-mcp secrets from Vault."],
                "state": merged,
            }

        if command.lower() == "save":
            service = get_service("advanced-memory-mcp")
            try:
                await client_factory().write_secret(service.vault_path, state)
                write_runtime_env(service, state)
            except ValueError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            except httpx.HTTPStatusError as exc:
                detail = exc.response.text or "Vault write failed"
                raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
            except httpx.HTTPError as exc:
                raise HTTPException(status_code=502, detail="Vault is unreachable") from exc

            metadata = build_service_metadata(service)
            return {
                "status": "ok",
                "output": [
                    f"Saved advanced-memory-mcp secrets. Restart target: {metadata['restart_target']}",
                    metadata["restart_command"],
                ],
                "restart_target": metadata["restart_target"],
                "restart_command": metadata["restart_command"],
            }

        try:
            result = await run_console_command(command, state)
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text or "Console command failed"
            raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"Console command failed: {exc}") from exc
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        return result

    @app.get("/", response_class=HTMLResponse)
    async def index() -> HTMLResponse:
        return HTMLResponse(html_payload)

    app.state.registry = registry
    app.state.template_path = resolved_template_path
    app.state.config_path = resolved_config_path
    return app
