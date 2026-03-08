from __future__ import annotations

import json
from pathlib import Path

from vault_secrets_ui.config import ServiceRegistry, build_service_metadata


def render_ui_html(template_path: Path, registry: ServiceRegistry) -> str:
    template = template_path.read_text(encoding="utf-8")
    options = "\n".join(
        f'                        <option value="{service.id}">{service.label}</option>'
        for service in registry.all()
    )
    metadata_json = json.dumps(
        {service.id: build_service_metadata(service) for service in registry.all()},
        indent=2,
    )
    return (
        template.replace("{{SERVICE_OPTIONS}}", options)
        .replace("{{SERVICE_METADATA_JSON}}", metadata_json)
    )
