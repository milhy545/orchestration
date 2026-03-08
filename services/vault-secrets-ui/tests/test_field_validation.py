from __future__ import annotations

import httpx
from fastapi.testclient import TestClient

from vault_secrets_ui.app_factory import create_app
from vault_secrets_ui.field_validation import validate_api_key
from vault_secrets_ui.models import FieldValidationConfig, ServiceField


class FakeVaultClient:
    async def read_secret(self, path: str) -> dict[str, str]:
        return {}

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        return None

    async def probe(self) -> bool:
        return True


def test_validate_api_key_openai_success(monkeypatch) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, method, url, headers=None, json=None):
            return httpx.Response(status_code=200, request=httpx.Request(method, url), json={"data": [{"id": "gpt-4o-mini"}]})

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    field = ServiceField(
        name="OPENAI_API_KEY",
        label="OpenAI API Key",
        target_env="OPENAI_API_KEY",
        validation=FieldValidationConfig(validator="openai", base_url="https://api.openai.com/v1"),
    )
    result = __import__("asyncio").run(validate_api_key(field, {"OPENAI_API_KEY": "sk-test-123456"}))
    assert result["ok"] is True
    assert result["code"] == "ok"


def test_validate_api_key_openai_failure(monkeypatch) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, method, url, headers=None, json=None):
            return httpx.Response(status_code=401, request=httpx.Request(method, url), text="bad key")

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    field = ServiceField(
        name="OPENAI_API_KEY",
        label="OpenAI API Key",
        target_env="OPENAI_API_KEY",
        validation=FieldValidationConfig(validator="openai", base_url="https://api.openai.com/v1"),
    )
    result = __import__("asyncio").run(validate_api_key(field, {"OPENAI_API_KEY": "sk-test-123456"}))
    assert result["ok"] is False
    assert result["code"] == "http_401"


def test_field_validation_endpoint_supports_base_url_context(monkeypatch, tmp_path) -> None:
    class MockAsyncClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def request(self, method, url, headers=None, json=None):
            assert url == "http://127.0.0.1:1234/v1/models"
            return httpx.Response(status_code=200, request=httpx.Request(method, url), json={"data": [{"id": "local-model"}]})

    monkeypatch.setattr(httpx, "AsyncClient", MockAsyncClient)
    config_path = tmp_path / "services.json"
    config_path.write_text(
        """
        {"services":[{"id":"demo","label":"DEMO","vault_path":"orchestration/demo","env_file":"/tmp/demo.env","restart_target":"demo","description":"demo","fields":[{"name":"OPENAI_COMPAT_BASE_URL","label":"Compat URL","target_env":"OPENAI_COMPAT_BASE_URL","input_type":"text","secret":false,"default":"http://127.0.0.1:1234"},{"name":"OPENAI_COMPAT_API_KEY","label":"Compat Key","target_env":"OPENAI_COMPAT_API_KEY","input_type":"password","secret":true,"validation":{"validator":"openai_compatible","base_url_field":"OPENAI_COMPAT_BASE_URL"}}]}]}
        """.strip(),
        encoding="utf-8",
    )
    template_path = tmp_path / "vault_webui.html"
    template_path.write_text(
        "<html><title>VAULT_OS // KEY CONSOLE</title>{{SERVICE_OPTIONS}}<script>const serviceMetadata = {{SERVICE_METADATA_JSON}};</script></html>",
        encoding="utf-8",
    )
    client = TestClient(create_app(config_path=config_path, template_path=template_path, vault_client_factory=lambda: FakeVaultClient()))
    response = client.post(
        "/api/field-validation",
        json={
            "service_id": "demo",
            "field_name": "OPENAI_COMPAT_API_KEY",
            "state": {
                "OPENAI_COMPAT_API_KEY": "sk-local-123456",
                "OPENAI_COMPAT_BASE_URL": "http://127.0.0.1:1234",
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
