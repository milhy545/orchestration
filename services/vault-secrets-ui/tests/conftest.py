from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vault_secrets_ui.app_factory import create_app


class FakeVaultClient:
    def __init__(self, store: dict[str, dict[str, str]] | None = None, reachable: bool = True) -> None:
        self.store = store or {}
        self.reachable = reachable

    async def read_secret(self, path: str) -> dict[str, str]:
        return dict(self.store.get(path, {}))

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        self.store[path] = dict(data)

    async def probe(self) -> bool:
        return self.reachable


class ValueErrorVaultClient:
    async def read_secret(self, path: str) -> dict[str, str]:
        raise ValueError("Vault token file is empty")

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        raise ValueError("Vault token file is empty")

    async def probe(self) -> bool:
        return False


@pytest.fixture()
def temp_config(tmp_path: Path) -> Path:
    config = {
        "services": [
            {
                "id": "demo",
                "label": "DEMO",
                "vault_path": "orchestration/demo",
                "env_file": str(tmp_path / "runtime" / "demo.env"),
                "restart_target": "demo-service",
                "description": "Demo service for testing.",
                "fields": [
                    {
                        "name": "API_KEY",
                        "label": "API Key",
                        "target_env": "API_KEY",
                        "input_type": "password",
                        "secret": True,
                        "placeholder": "secret-...",
                        "default": "DEFAULT_SECRET",
                    },
                    {
                        "name": "PUBLIC_URL",
                        "label": "Public URL",
                        "target_env": "PUBLIC_URL",
                        "input_type": "text",
                        "secret": False,
                        "placeholder": "https://example.com",
                        "default": "",
                    },
                ],
            }
        ]
    }
    config_path = tmp_path / "services.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return config_path


@pytest.fixture()
def temp_template(tmp_path: Path) -> Path:
    template = tmp_path / "vault_webui.html"
    template.write_text(
        "<html><title>VAULT_OS // KEY CONSOLE</title>{{SERVICE_OPTIONS}}<script>const serviceMetadata = {{SERVICE_METADATA_JSON}};</script></html>",
        encoding="utf-8",
    )
    return template


@pytest.fixture()
def fake_vault() -> FakeVaultClient:
    return FakeVaultClient(
        store={
            "orchestration/demo": {
                "API_KEY": "stored-secret",
                "PUBLIC_URL": "https://demo.example",
            }
        }
    )


@pytest.fixture()
def client(temp_config: Path, temp_template: Path, fake_vault: FakeVaultClient) -> TestClient:
    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: fake_vault,
    )
    return TestClient(app)
