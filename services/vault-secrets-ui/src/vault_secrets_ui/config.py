from __future__ import annotations

import json
from pathlib import Path

from vault_secrets_ui.models import ServiceDefinition, ServiceRegistryConfig


class ServiceRegistry:
    def __init__(self, services: list[ServiceDefinition]) -> None:
        self._services = {service.id: service for service in services}
        if len(self._services) != len(services):
            raise ValueError("Duplicate service ids are not allowed")

    def all(self) -> list[ServiceDefinition]:
        return list(self._services.values())

    def ids(self) -> list[str]:
        return list(self._services.keys())

    def get(self, service_id: str) -> ServiceDefinition:
        try:
            return self._services[service_id]
        except KeyError as exc:
            raise KeyError(f"Unknown service: {service_id}") from exc


def load_service_registry(config_path: Path) -> ServiceRegistry:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    config = ServiceRegistryConfig.model_validate(payload)
    return ServiceRegistry(config.services)


def build_service_metadata(service: ServiceDefinition) -> dict[str, object]:
    return {
        "id": service.id,
        "label": service.label,
        "vault_path": service.vault_path,
        "env_file": service.env_file,
        "runtime_keys": {field.name: field.target_env for field in service.fields},
        "restart_required": True,
        "restart_target": service.restart_target,
        "delivery_mode": service.delivery_mode,
        "restart_command": (
            "docker compose -f docker-compose.yml -f docker-compose.vault.yml "
            f"restart {service.restart_target}"
        ),
        "description": service.description,
        "fields": [field.model_dump() for field in service.fields],
    }
