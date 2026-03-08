from __future__ import annotations

from pathlib import Path
from typing import Any

from vault_secrets_ui.models import ServiceDefinition


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def render_runtime_env(service: ServiceDefinition, data: dict[str, Any]) -> str:
    lines = [
        "# Auto-generated from Vault by vault-secrets-ui.",
        "# Do not edit it directly.",
        "",
        f"SERVICE_NAME={shell_quote(service.id)}",
        f"VAULT_SECRET_PATH={shell_quote('secret/data/' + service.vault_path)}",
    ]

    for field in service.fields:
        value = data.get(field.name, field.default)
        if value in ("", None):
            continue
        if service.delivery_mode == "file" and field.secret:
            lines.append(
                f"export {field.target_env}_FILE={shell_quote(str(secret_file_path(service, field.target_env)))}"
            )
            continue
        lines.append(f"export {field.target_env}={shell_quote(str(value))}")

    lines.append("")
    return "\n".join(lines)


def secret_file_path(service: ServiceDefinition, target_env: str) -> Path:
    env_path = Path(service.env_file)
    return env_path.parent / "secrets" / service.id / target_env


def write_secret_file(service: ServiceDefinition, target_env: str, value: str) -> None:
    target_path = secret_file_path(service, target_env)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if value in ("", None):
        target_path.unlink(missing_ok=True)
        return
    temp_path = target_path.with_suffix(".tmp")
    temp_path.write_text(str(value), encoding="utf-8")
    temp_path.chmod(0o600)
    temp_path.replace(target_path)


def write_runtime_env(service: ServiceDefinition, data: dict[str, Any]) -> None:
    target_path = Path(service.env_file)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if service.delivery_mode == "file":
        for field in service.fields:
            if not field.secret:
                continue
            write_secret_file(service, field.target_env, data.get(field.name, field.default))
    temp_path = target_path.with_suffix(f"{target_path.suffix}.tmp")
    temp_path.write_text(render_runtime_env(service, data), encoding="utf-8")
    temp_path.replace(target_path)
