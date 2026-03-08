from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _import_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


providers = _import_module(
    "advanced_memory_providers_test",
    PROJECT_ROOT / "mcp-servers" / "advanced-memory-mcp" / "providers.py",
)


def test_load_setting_prefers_file(tmp_path, monkeypatch) -> None:
    secret_file = tmp_path / "gemini.key"
    secret_file.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "from-env")
    monkeypatch.setenv("GEMINI_API_KEY_FILE", str(secret_file))

    assert providers.load_setting("GEMINI_API_KEY") == "from-file"


def test_runtime_config_from_env_uses_normalized_urls(monkeypatch) -> None:
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("GENERATION_PROVIDER", "inception")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://192.168.0.55:11434/")
    monkeypatch.setenv("OPENAI_COMPAT_BASE_URL", "http://192.168.0.77:1234/v1/")

    config = providers.RuntimeConfig.from_env()

    assert config.embedding_provider == "ollama"
    assert config.generation_provider == "inception"
    assert config.ollama_base_url == "http://192.168.0.55:11434"
    assert config.openai_compat_base_url == "http://192.168.0.77:1234/v1"


@pytest.mark.asyncio
async def test_ollama_embedding_parses_modern_response(monkeypatch) -> None:
    config = providers.RuntimeConfig.from_env()
    config.embedding_provider = "ollama"
    client = providers.ProviderClient(config)
    client._post_json = lambda url, payload, headers=None: {"embeddings": [[0.1, 0.2, 0.3]]}

    async def immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(providers.asyncio, "to_thread", immediate_to_thread)

    vector = await client.embed_query("hello")

    assert vector == [0.1, 0.2, 0.3]


@pytest.mark.asyncio
async def test_inception_generation_parses_chat_response(monkeypatch) -> None:
    config = providers.RuntimeConfig.from_env()
    config.generation_provider = "inception"
    config.inception_api_key = "secret"
    client = providers.ProviderClient(config)
    client._post_json = lambda url, payload, headers=None: {
        "choices": [{"message": {"content": "answer from mercury"}}]
    }

    async def immediate_to_thread(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(providers.asyncio, "to_thread", immediate_to_thread)

    answer = await client.generate_answer("What happened?", [{"content": "Stored fact"}])

    assert answer == "answer from mercury"


def test_advanced_memory_vault_definition_matches_runtime() -> None:
    payload = json.loads(
        (PROJECT_ROOT / "services" / "vault-secrets-ui" / "services.json").read_text(
            encoding="utf-8"
        )
    )
    services = {service["id"]: service for service in payload["services"]}
    advanced = services["advanced-memory-mcp"]

    assert advanced["delivery_mode"] == "file"
    field_names = {field["name"] for field in advanced["fields"]}
    assert "EMBEDDING_PROVIDER" in field_names
    assert "GENERATION_PROVIDER" in field_names
    assert "GEMINI_API_KEY" in field_names
    assert "INCEPTION_API_KEY" in field_names
    assert "OPENAI_API_KEY" not in field_names
