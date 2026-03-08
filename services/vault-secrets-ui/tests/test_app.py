from __future__ import annotations

from pathlib import Path

import httpx
from fastapi.testclient import TestClient

from vault_secrets_ui.app_factory import _default_paths, create_app


class ValueErrorVaultClient:
    async def read_secret(self, path: str) -> dict[str, str]:
        raise ValueError("Vault token file is empty")

    async def write_secret(self, path: str, data: dict[str, str]) -> None:
        raise ValueError("Vault token file is empty")

    async def probe(self) -> bool:
        return False


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "healthy"
    assert payload["vault_reachable"] is True
    assert "vault_addr" not in payload


def test_services_endpoint_exposes_fields(client) -> None:
    response = client.get("/api/services")
    payload = response.json()
    assert response.status_code == 200
    assert payload["services"][0]["fields"][0]["name"] == "API_KEY"


def test_get_secrets_merges_defaults(client) -> None:
    response = client.get("/api/secrets/demo")
    payload = response.json()
    assert response.status_code == 200
    assert payload["data"]["API_KEY"] == "stored-secret"
    assert payload["data"]["PUBLIC_URL"] == "https://demo.example"


def test_get_secrets_adds_missing_field_defaults(temp_config, temp_template) -> None:
    class SparseVaultClient:
        async def read_secret(self, path: str) -> dict[str, str]:
            return {}

        async def write_secret(self, path: str, data: dict[str, str]) -> None:
            return None

        async def probe(self) -> bool:
            return True

    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: SparseVaultClient(),
    )
    response = TestClient(app).get("/api/secrets/demo")
    payload = response.json()
    assert payload["data"]["API_KEY"] == "DEFAULT_SECRET"


def test_put_secrets_writes_runtime_env(client, temp_config) -> None:
    response = client.put(
        "/api/secrets/demo",
        json={"data": {"API_KEY": "rotated", "PUBLIC_URL": "https://new.example"}},
    )
    assert response.status_code == 200
    env_file = temp_config.parent / "runtime" / "demo.env"
    assert env_file.exists()
    assert "export API_KEY='rotated'" in env_file.read_text(encoding="utf-8")


def test_unknown_service_returns_404(client) -> None:
    response = client.get("/api/secrets/missing")
    assert response.status_code == 404


def test_index_renders_html(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "VAULT_OS // KEY CONSOLE" in response.text


def test_default_paths() -> None:
    config_path, template_path = _default_paths(Path("/tmp/demo"))
    assert config_path == Path("/tmp/demo/services.json")
    assert template_path == Path("/tmp/demo/src/vault_secrets_ui/templates/vault_webui.html")


def test_default_vault_client_factory_path(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "services.json"
    config_path.write_text(
        '{"services":[{"id":"demo","label":"DEMO","vault_path":"orchestration/demo","env_file":"/tmp/demo.env","restart_target":"demo","description":"demo","fields":[{"name":"API_KEY","label":"API Key","target_env":"API_KEY"}]}]}',
        encoding="utf-8",
    )
    template_path = tmp_path / "vault_webui.html"
    template_path.write_text(
        "<html><title>VAULT_OS // KEY CONSOLE</title>{{SERVICE_OPTIONS}}<script>const serviceMetadata = {{SERVICE_METADATA_JSON}};</script></html>",
        encoding="utf-8",
    )
    token_file = tmp_path / "admin.token"
    token_file.write_text("abc123", encoding="utf-8")

    monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
    monkeypatch.setenv("VAULT_TOKEN_FILE", str(token_file))

    original_probe = httpx.AsyncClient

    class MockAsyncClient(httpx.AsyncClient):
        async def __aenter__(self):
            return self

        async def get(self, *args, **kwargs):
            return httpx.Response(status_code=200, json={})

    httpx.AsyncClient = MockAsyncClient
    try:
        app = create_app(config_path=config_path, template_path=template_path)
        response = TestClient(app).get("/health")
    finally:
        httpx.AsyncClient = original_probe

    assert response.status_code == 200
    assert response.json()["vault_reachable"] is True
    assert "vault_addr" not in response.json()


def test_get_secrets_handles_value_error(temp_config, temp_template) -> None:
    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: ValueErrorVaultClient(),
    )
    response = TestClient(app).get("/api/secrets/demo")
    assert response.status_code == 500


def test_get_secrets_handles_http_status_error(temp_config, temp_template) -> None:
    class FailingVaultClient:
        async def read_secret(self, path: str) -> dict[str, str]:
            request = httpx.Request("GET", "http://vault:8200/v1/secret/data/orchestration/demo")
            response = httpx.Response(status_code=403, request=request, text="denied")
            raise httpx.HTTPStatusError("denied", request=request, response=response)

        async def write_secret(self, path: str, data: dict[str, str]) -> None:
            return None

        async def probe(self) -> bool:
            return False

    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: FailingVaultClient(),
    )
    response = TestClient(app).get("/api/secrets/demo")
    assert response.status_code == 403
    assert response.json()["detail"] == "denied"


def test_get_secrets_handles_transport_error(temp_config, temp_template) -> None:
    class FailingVaultClient:
        async def read_secret(self, path: str) -> dict[str, str]:
            raise httpx.ConnectError("boom")

        async def write_secret(self, path: str, data: dict[str, str]) -> None:
            return None

        async def probe(self) -> bool:
            return False

    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: FailingVaultClient(),
    )
    response = TestClient(app).get("/api/secrets/demo")
    assert response.status_code == 502


def test_put_secrets_handles_value_error(temp_config, temp_template) -> None:
    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: ValueErrorVaultClient(),
    )
    response = TestClient(app).put("/api/secrets/demo", json={"data": {"API_KEY": "x"}})
    assert response.status_code == 500


def test_put_secrets_handles_http_status_error(temp_config, temp_template) -> None:
    class FailingVaultClient:
        async def read_secret(self, path: str) -> dict[str, str]:
            return {}

        async def write_secret(self, path: str, data: dict[str, str]) -> None:
            request = httpx.Request("POST", "http://vault:8200/v1/secret/data/orchestration/demo")
            response = httpx.Response(status_code=400, request=request, text="bad payload")
            raise httpx.HTTPStatusError("bad payload", request=request, response=response)

        async def probe(self) -> bool:
            return False

    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: FailingVaultClient(),
    )
    response = TestClient(app).put("/api/secrets/demo", json={"data": {"API_KEY": "x"}})
    assert response.status_code == 400
    assert response.json()["detail"] == "bad payload"


def test_put_secrets_handles_transport_error(temp_config, temp_template) -> None:
    class FailingVaultClient:
        async def read_secret(self, path: str) -> dict[str, str]:
            return {}

        async def write_secret(self, path: str, data: dict[str, str]) -> None:
            raise httpx.ConnectError("boom")

        async def probe(self) -> bool:
            return False

    app = create_app(
        config_path=temp_config,
        template_path=temp_template,
        vault_client_factory=lambda: FailingVaultClient(),
    )
    response = TestClient(app).put("/api/secrets/demo", json={"data": {"API_KEY": "x"}})
    assert response.status_code == 502


def test_e2e_form_workflow(client) -> None:
    index = client.get("/")
    assert "serviceMetadata" in index.text

    initial = client.get("/api/secrets/demo")
    assert initial.status_code == 200

    saved = client.put(
        "/api/secrets/demo",
        json={"data": {"API_KEY": "browser-secret", "PUBLIC_URL": "https://browser.example", "EXTRA_FLAG": "1"}},
    )
    assert saved.status_code == 200
    assert saved.json()["restart_target"] == "demo-service"

    round_trip = client.get("/api/secrets/demo")
    payload = round_trip.json()["data"]
    assert payload["API_KEY"] == "browser-secret"
    assert payload["PUBLIC_URL"] == "https://browser.example"
    assert payload["EXTRA_FLAG"] == "1"
