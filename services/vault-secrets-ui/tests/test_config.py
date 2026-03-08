from __future__ import annotations

import json
from pathlib import Path

import pytest

from vault_secrets_ui.config import ServiceRegistry, build_service_metadata, load_service_registry
from vault_secrets_ui.models import ServiceDefinition, ServiceField


def test_service_field_rejects_blank_identifiers() -> None:
    with pytest.raises(ValueError):
        ServiceField(name="", label="API Key", target_env="API_KEY")


def test_service_definition_requires_fields() -> None:
    with pytest.raises(ValueError):
        ServiceDefinition(
            id="demo",
            label="DEMO",
            vault_path="orchestration/demo",
            env_file="/tmp/demo.env",
            restart_target="demo",
            fields=[],
        )


def test_service_definition_rejects_blank_id() -> None:
    with pytest.raises(ValueError):
        ServiceDefinition(
            id="",
            label="DEMO",
            vault_path="orchestration/demo",
            env_file="/tmp/demo.env",
            restart_target="demo",
            fields=[ServiceField(name="API_KEY", label="API Key", target_env="API_KEY")],
        )


def test_registry_rejects_duplicate_ids() -> None:
    service = ServiceDefinition(
        id="demo",
        label="DEMO",
        vault_path="orchestration/demo",
        env_file="/tmp/demo.env",
        restart_target="demo",
        fields=[ServiceField(name="API_KEY", label="API Key", target_env="API_KEY")],
    )
    with pytest.raises(ValueError):
        ServiceRegistry([service, service])


def test_load_service_registry_and_metadata(temp_config: Path) -> None:
    registry = load_service_registry(temp_config)
    service = registry.get("demo")
    metadata = build_service_metadata(service)
    assert registry.ids() == ["demo"]
    assert metadata["restart_target"] == "demo-service"
    assert metadata["runtime_keys"] == {"API_KEY": "API_KEY", "PUBLIC_URL": "PUBLIC_URL"}
    assert len(metadata["fields"]) == 2


def test_registry_get_unknown_service(temp_config: Path) -> None:
    registry = load_service_registry(temp_config)
    with pytest.raises(KeyError):
        registry.get("missing")


def test_load_service_registry_accepts_json(temp_config: Path) -> None:
    payload = json.loads(temp_config.read_text(encoding="utf-8"))
    assert payload["services"][0]["id"] == "demo"
