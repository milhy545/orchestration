from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastapi.testclient import TestClient

from vault_secrets_ui.app_factory import create_app


class FakeVaultClient:
    def __init__(self) -> None:
        self.store = {
            "orchestration/advanced-memory-mcp": {
                "EMBEDDING_PROVIDER": "gemini",
                "GENERATION_PROVIDER": "inception",
                "GEMINI_API_KEY": "gem-key",
                "INCEPTION_API_KEY": "inc-key",
            }
        }

    async def read_secret(self, path: str) -> dict[str, str]:
        return dict(self.store.get(path, {}))

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        self.store[path] = dict(data)

    async def probe(self) -> bool:
        return True


def build_advanced_memory_config(tmp_path: Path) -> Path:
    payload = {
        "services": [
            {
                "id": "advanced-memory-mcp",
                "label": "ADVANCED MEMORY MCP",
                "vault_path": "orchestration/advanced-memory-mcp",
                "env_file": str(tmp_path / "runtime" / "advanced-memory-mcp.env"),
                "restart_target": "advanced-memory-mcp",
                "delivery_mode": "file",
                "description": "Advanced memory test service.",
                "fields": [
                    {"name": "EMBEDDING_PROVIDER", "label": "Embedding Provider", "target_env": "EMBEDDING_PROVIDER", "input_type": "text", "secret": False, "default": "local"},
                    {"name": "GENERATION_PROVIDER", "label": "Generation Provider", "target_env": "GENERATION_PROVIDER", "input_type": "text", "secret": False, "default": "none"},
                    {"name": "LOCAL_EMBEDDING_MODEL", "label": "Local Embedding Model", "target_env": "LOCAL_EMBEDDING_MODEL", "input_type": "text", "secret": False, "default": "all-MiniLM-L6-v2"},
                    {"name": "GEMINI_API_KEY", "label": "Gemini API Key", "target_env": "GEMINI_API_KEY", "input_type": "password", "secret": True, "default": ""},
                    {"name": "GEMINI_EMBED_MODEL", "label": "Gemini Embed Model", "target_env": "GEMINI_EMBED_MODEL", "input_type": "text", "secret": False, "default": "gemini-embedding-001"},
                    {"name": "OLLAMA_BASE_URL", "label": "Ollama Base URL", "target_env": "OLLAMA_BASE_URL", "input_type": "text", "secret": False, "default": "http://127.0.0.1:11434"},
                    {"name": "OLLAMA_EMBED_MODEL", "label": "Ollama Embed Model", "target_env": "OLLAMA_EMBED_MODEL", "input_type": "text", "secret": False, "default": "nomic-embed-text"},
                    {"name": "OLLAMA_CHAT_MODEL", "label": "Ollama Chat Model", "target_env": "OLLAMA_CHAT_MODEL", "input_type": "text", "secret": False, "default": "llama3.2"},
                    {"name": "OPENAI_COMPAT_BASE_URL", "label": "OpenAI Compat URL", "target_env": "OPENAI_COMPAT_BASE_URL", "input_type": "text", "secret": False, "default": ""},
                    {"name": "OPENAI_COMPAT_API_KEY", "label": "OpenAI Compat Key", "target_env": "OPENAI_COMPAT_API_KEY", "input_type": "password", "secret": True, "default": ""},
                    {"name": "OPENAI_COMPAT_EMBED_MODEL", "label": "Compat Embed Model", "target_env": "OPENAI_COMPAT_EMBED_MODEL", "input_type": "text", "secret": False, "default": ""},
                    {"name": "OPENAI_COMPAT_CHAT_MODEL", "label": "Compat Chat Model", "target_env": "OPENAI_COMPAT_CHAT_MODEL", "input_type": "text", "secret": False, "default": ""},
                    {"name": "INCEPTION_API_KEY", "label": "Inception API Key", "target_env": "INCEPTION_API_KEY", "input_type": "password", "secret": True, "default": ""},
                    {"name": "INCEPTION_MODEL", "label": "Inception Model", "target_env": "INCEPTION_MODEL", "input_type": "text", "secret": False, "default": "mercury"},
                ],
            }
        ]
    }
    config_path = tmp_path / "services.json"
    config_path.write_text(json.dumps(payload), encoding="utf-8")
    return config_path


def build_template(tmp_path: Path) -> Path:
    template_path = tmp_path / "vault_webui.html"
    template_path.write_text(
        "<html><title>VAULT_OS // KEY CONSOLE</title>{{SERVICE_OPTIONS}}<script>const serviceMetadata = {{SERVICE_METADATA_JSON}};</script></html>",
        encoding="utf-8",
    )
    return template_path


def test_provider_discovery_endpoint(monkeypatch, tmp_path: Path) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, headers=None):
            if urlparse(url).netloc == "generativelanguage.googleapis.com":
                return httpx.Response(
                    status_code=200,
                    request=httpx.Request("GET", url),
                    json={"models": [{"name": "models/gemini-embedding-001", "supportedGenerationMethods": ["embedContent"]}]},
                )
            if urlparse(url).netloc == "api.inceptionlabs.ai":
                return httpx.Response(
                    status_code=200,
                    request=httpx.Request("GET", url),
                    json={"data": [{"id": "mercury"}, {"id": "mercury-coder"}]},
                )
            raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    app = create_app(
        config_path=build_advanced_memory_config(tmp_path),
        template_path=build_template(tmp_path),
        vault_client_factory=lambda: FakeVaultClient(),
    )
    client = TestClient(app)

    response = client.post(
        "/api/provider-discovery/advanced-memory",
        json={
            "state": {
                "EMBEDDING_PROVIDER": "gemini",
                "GENERATION_PROVIDER": "inception",
                "GEMINI_API_KEY": "gem-key",
                "INCEPTION_API_KEY": "inc-key",
                "GEMINI_EMBED_MODEL": "gemini-embedding-001",
                "INCEPTION_MODEL": "mercury",
            },
            "target": "all",
        },
    )

    assert response.status_code == 200
    payload = response.json()["discovery"]
    assert payload["embedding"]["resolved_base_url"] == "https://generativelanguage.googleapis.com/v1beta"
    assert payload["embedding"]["selected_model"] == "gemini-embedding-001"
    assert "mercury" in payload["generation"]["models"]


def test_console_endpoint_supports_discover_and_save(monkeypatch, tmp_path: Path) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def get(self, url: str, headers=None):
            return httpx.Response(
                status_code=200,
                request=httpx.Request("GET", url),
                json={"models": [{"name": "nomic-embed-text"}, {"name": "llama3.2"}]},
            )

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    vault = FakeVaultClient()
    app = create_app(
        config_path=build_advanced_memory_config(tmp_path),
        template_path=build_template(tmp_path),
        vault_client_factory=lambda: vault,
    )
    client = TestClient(app)

    discover = client.post(
        "/api/console/advanced-memory",
        json={
            "command": "discover embedding",
            "state": {
                "EMBEDDING_PROVIDER": "ollama",
                "OLLAMA_BASE_URL": "http://127.0.0.1:11434",
                "OLLAMA_EMBED_MODEL": "nomic-embed-text",
            },
        },
    )
    assert discover.status_code == 200
    assert "discovered" in " ".join(discover.json()["output"]).lower()

    save = client.post(
        "/api/console/advanced-memory",
        json={
            "command": "save",
            "state": {
                "EMBEDDING_PROVIDER": "local",
                "GENERATION_PROVIDER": "none",
                "LOCAL_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
            },
        },
    )
    assert save.status_code == 200
    assert save.json()["restart_target"] == "advanced-memory-mcp"
    assert vault.store["orchestration/advanced-memory-mcp"]["LOCAL_EMBEDDING_MODEL"] == "all-MiniLM-L6-v2"


def test_console_endpoint_loads_saved_state(tmp_path: Path) -> None:
    vault = FakeVaultClient()
    app = create_app(
        config_path=build_advanced_memory_config(tmp_path),
        template_path=build_template(tmp_path),
        vault_client_factory=lambda: vault,
    )
    client = TestClient(app)

    response = client.post("/api/console/advanced-memory", json={"command": "load", "state": {}})
    assert response.status_code == 200
    assert response.json()["state"]["EMBEDDING_PROVIDER"] == "gemini"
