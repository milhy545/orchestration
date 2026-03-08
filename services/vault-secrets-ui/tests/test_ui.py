from __future__ import annotations

from pathlib import Path

from vault_secrets_ui.config import load_service_registry
from vault_secrets_ui.ui import render_ui_html


def test_render_ui_html_injects_options_and_metadata(temp_config: Path, temp_template: Path) -> None:
    registry = load_service_registry(temp_config)
    output = render_ui_html(temp_template, registry)
    assert "value=\"demo\"" in output
    assert "restart_command" in output
    assert "VAULT_OS // KEY CONSOLE" in output


def test_render_ui_html_contains_advanced_memory_provider_controls() -> None:
    repo_root = Path("/home/orchestration")
    config_path = repo_root / "services" / "vault-secrets-ui" / "services.json"
    template_path = repo_root / "services" / "vault-secrets-ui" / "src" / "vault_secrets_ui" / "templates" / "vault_webui.html"
    registry = load_service_registry(config_path)
    output = render_ui_html(template_path, registry)

    assert "advanced-memory-mcp" in output
    assert "advancedMemoryConfig" in output
    assert "Embedding Provider" in output
    assert "Generation Provider" in output
    assert "LM Studio / llama.cpp / OpenAI-compatible" in output
    assert "mercury-thinking" in output
    assert "gemini-embedding-001" in output
    assert "/api/field-validation" in output
    assert "validation-modal" in output
