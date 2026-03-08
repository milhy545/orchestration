from __future__ import annotations

from pathlib import Path

from vault_secrets_ui.models import ServiceDefinition, ServiceField
from vault_secrets_ui.runtime import (
    render_runtime_env,
    secret_file_path,
    shell_quote,
    write_runtime_env,
)


def build_service(env_file: str, delivery_mode: str = "env") -> ServiceDefinition:
    return ServiceDefinition(
        id="demo",
        label="DEMO",
        vault_path="orchestration/demo",
        env_file=env_file,
        restart_target="demo-service",
        delivery_mode=delivery_mode,
        fields=[
            ServiceField(name="API_KEY", label="API Key", target_env="API_KEY"),
            ServiceField(
                name="PUBLIC_URL",
                label="Public URL",
                target_env="PUBLIC_URL",
                input_type="text",
                secret=False,
                default="https://default.example",
            ),
        ],
    )


def test_shell_quote_escapes_single_quotes() -> None:
    assert shell_quote("o'hai") == "'o'\"'\"'hai'"


def test_render_runtime_env_uses_defaults(tmp_path: Path) -> None:
    service = build_service(str(tmp_path / "demo.env"))
    rendered = render_runtime_env(service, {"API_KEY": "secret"})
    assert "SERVICE_NAME='demo'" in rendered
    assert "export API_KEY='secret'" in rendered
    assert "export PUBLIC_URL='https://default.example'" in rendered


def test_write_runtime_env_writes_atomically(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "demo.env"
    service = build_service(str(target))
    write_runtime_env(service, {"API_KEY": "secret", "PUBLIC_URL": "https://demo.example"})
    assert target.exists()
    output = target.read_text(encoding="utf-8")
    assert "export PUBLIC_URL='https://demo.example'" in output


def test_render_runtime_env_skips_empty_values(tmp_path: Path) -> None:
    service = build_service(str(tmp_path / "demo.env"))
    rendered = render_runtime_env(service, {"API_KEY": "", "PUBLIC_URL": None})
    assert "export API_KEY" not in rendered
    assert "export PUBLIC_URL" not in rendered


def test_render_runtime_env_uses_file_delivery_for_secrets(tmp_path: Path) -> None:
    service = build_service(str(tmp_path / "demo.env"), delivery_mode="file")
    rendered = render_runtime_env(service, {"API_KEY": "secret", "PUBLIC_URL": "https://demo.example"})
    assert "export API_KEY='secret'" not in rendered
    assert f"export API_KEY_FILE='{secret_file_path(service, 'API_KEY')}'" in rendered
    assert "export PUBLIC_URL='https://demo.example'" in rendered


def test_write_runtime_env_writes_secret_files_for_file_delivery(tmp_path: Path) -> None:
    target = tmp_path / "runtime" / "demo.env"
    service = build_service(str(target), delivery_mode="file")
    write_runtime_env(service, {"API_KEY": "secret", "PUBLIC_URL": "https://demo.example"})
    secret_path = secret_file_path(service, "API_KEY")
    assert secret_path.exists()
    assert secret_path.read_text(encoding="utf-8") == "secret"
    assert oct(secret_path.stat().st_mode & 0o777) == "0o600"
    output = target.read_text(encoding="utf-8")
    assert "API_KEY_FILE" in output
