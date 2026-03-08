from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path("/home/orchestration")


def _import_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_load_secret_prefers_file(tmp_path, monkeypatch) -> None:
    module = _import_module(
        "mega_orchestrator_utils_secrets_test",
        PROJECT_ROOT / "mega_orchestrator" / "utils" / "secrets.py",
    )
    secret_file = tmp_path / "openai.key"
    secret_file.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "from-env")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(secret_file))

    assert module.load_secret("OPENAI_API_KEY") == "from-file"


def test_provider_registry_uses_file_aware_loader() -> None:
    source = (PROJECT_ROOT / "mega_orchestrator" / "providers" / "registry.py").read_text(
        encoding="utf-8"
    )
    assert 'from mega_orchestrator.utils.secrets import load_secret' in source
    assert 'load_secret("OPENAI_API_KEY")' in source
    assert 'load_secret("ANTHROPIC_API_KEY")' in source
    assert 'load_secret("GEMINI_API_KEY")' in source
    assert 'load_secret("GOOGLE_API_KEY")' in source
    assert 'load_secret("OPENROUTER_API_KEY")' in source
    assert "_read_key_from_file" not in source
    assert "_read_key_from_config" not in source
    assert "/tmp/has_env_backup" not in source


def test_mega_orchestrator_uses_file_aware_marketplace_token() -> None:
    source = (
        PROJECT_ROOT / "mega_orchestrator" / "mega_orchestrator_complete.py"
    ).read_text(encoding="utf-8")
    assert 'from mega_orchestrator.utils.secrets import load_secret' in source
    assert 'load_secret("MARKETPLACE_JWT_TOKEN")' in source


def test_service_modules_read_secret_files() -> None:
    security_source = (
        PROJECT_ROOT / "mcp-servers" / "security-mcp" / "main.py"
    ).read_text(encoding="utf-8")
    marketplace_source = (
        PROJECT_ROOT / "mcp-servers" / "marketplace-mcp" / "main.py"
    ).read_text(encoding="utf-8")
    gmail_source = (
        PROJECT_ROOT / "mcp-servers" / "gmail-mcp" / "src" / "email_client" / "config.py"
    ).read_text(encoding="utf-8")

    assert 'os.getenv(f"{name}_FILE", "").strip()' in security_source
    assert '_load_secret("JWT_SECRET_KEY")' in security_source
    assert 'os.environ.get(f"{name}_FILE", "").strip()' in marketplace_source
    assert 'JWT_SECRET = _load_secret("JWT_SECRET")' in marketplace_source
    assert 'os.getenv(f"{name}_FILE", "").strip()' in gmail_source
    assert '_load_setting("EMAIL_PASSWORD", "your-app-specific-password")' in gmail_source


def test_vault_delivery_modes_are_file_based_for_active_secret_consumers() -> None:
    payload = json.loads(
        (PROJECT_ROOT / "services" / "vault-secrets-ui" / "services.json").read_text(
            encoding="utf-8"
        )
    )
    services = {service["id"]: service for service in payload["services"]}

    assert services["mega-orchestrator"]["delivery_mode"] == "file"
    assert services["gmail-mcp"]["delivery_mode"] == "file"
    assert services["security-mcp"]["delivery_mode"] == "file"
    assert services["marketplace-mcp"]["delivery_mode"] == "file"
    assert services["common-mcp"]["delivery_mode"] == "file"


def test_vault_renderer_uses_file_delivery_for_secret_consumers() -> None:
    source = (PROJECT_ROOT / "infra" / "vault" / "render-envs.sh").read_text(encoding="utf-8")
    assert '"mega-orchestrator"' in source and '"file"' in source
    assert '"gmail-mcp"' in source and '"file"' in source
    assert '"security-mcp"' in source and '"file"' in source
    assert '"marketplace-mcp"' in source and '"file"' in source
    assert '"common-mcp"' in source and '"file"' in source


def test_vault_renderer_requires_read_token_file() -> None:
    source = (PROJECT_ROOT / "infra" / "vault" / "render-envs.sh").read_text(encoding="utf-8")
    assert 'Vault read token missing or empty' in source
    assert 'VAULT_DEV_ROOT_TOKEN' not in source.split('load_token() {', 1)[1].split('}', 1)[0]
