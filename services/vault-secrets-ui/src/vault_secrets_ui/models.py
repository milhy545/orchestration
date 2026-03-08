from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class FieldValidationConfig(BaseModel):
    validator: str
    base_url_field: str = ""
    base_url: str = ""
    extra_headers: dict[str, str] = Field(default_factory=dict)
    extra_state_fields: list[str] = Field(default_factory=list)


class ServiceField(BaseModel):
    name: str
    label: str
    target_env: str
    input_type: Literal["password", "text", "textarea"] = "password"
    secret: bool = True
    advanced_only: bool = False
    placeholder: str = ""
    default: Any = ""
    help_text: str = ""
    validation: FieldValidationConfig | None = None

    @model_validator(mode="after")
    def validate_name_fields(self) -> "ServiceField":
        for value in (self.name, self.label, self.target_env):
            if not str(value).strip():
                raise ValueError("Service fields require non-empty identifiers")
        if self.validation and not self.secret:
            raise ValueError("Validation is only supported on secret fields")
        return self


class ServiceDefinition(BaseModel):
    id: str
    label: str
    vault_path: str
    env_file: str
    restart_target: str
    delivery_mode: Literal["env", "file"] = "env"
    description: str = ""
    fields: list[ServiceField] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_service(self) -> "ServiceDefinition":
        if not self.id.strip():
            raise ValueError("Service id cannot be empty")
        if not self.fields:
            raise ValueError("Service must define at least one field")
        return self


class ServiceRegistryConfig(BaseModel):
    services: list[ServiceDefinition]
