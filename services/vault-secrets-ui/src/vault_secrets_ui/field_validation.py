from __future__ import annotations

from typing import Any

import httpx

from vault_secrets_ui.models import FieldValidationConfig, ServiceField

VALIDATION_TIMEOUT_SECONDS = 15.0
ANTHROPIC_VERSION = "2023-06-01"
NOTION_VERSION = "2022-06-28"


def _value(state: dict[str, Any], name: str) -> str:
    return str(state.get(name, "") or "").strip()


def _normalize_url(url: str) -> str:
    return str(url or "").strip().rstrip("/")


def _resolve_base_url(config: FieldValidationConfig, state: dict[str, Any]) -> str:
    if config.base_url:
        return _normalize_url(config.base_url)
    if config.base_url_field:
        return _normalize_url(state.get(config.base_url_field, ""))
    return ""


def _ok_result(config: FieldValidationConfig, message: str) -> dict[str, Any]:
    return {
        "ok": True,
        "validator": config.validator,
        "code": "ok",
        "message": message,
        "details": "",
    }


def _error_result(config: FieldValidationConfig, code: str, message: str, details: str = "") -> dict[str, Any]:
    return {
        "ok": False,
        "validator": config.validator,
        "code": code,
        "message": message,
        "details": details,
    }


async def _request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    json_payload: dict[str, Any] | None = None,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=VALIDATION_TIMEOUT_SECONDS) as client:
        response = await client.request(method, url, headers=headers, json=json_payload)
    return response


def _normalize_http_error(config: FieldValidationConfig, response: httpx.Response) -> dict[str, Any]:
    details = response.text.strip()
    status_code = response.status_code
    if status_code in {401, 403}:
        return _error_result(config, f"http_{status_code}", "API key was rejected.", details)
    if status_code == 429:
        return _error_result(config, "http_429", "Provider rate limit hit during validation.", details)
    return _error_result(config, f"http_{status_code}", "Provider validation failed.", details)


async def validate_api_key(field: ServiceField, state: dict[str, Any]) -> dict[str, Any]:
    config = field.validation
    if config is None:
        raise ValueError(f"Field {field.name} does not define validation metadata")

    api_key = _value(state, field.name)
    if not api_key:
        return _error_result(config, "missing_key", f"{field.name} is empty.")

    try:
        if config.validator == "openai":
            return await _validate_openai_compatible(config, api_key, config.base_url or "https://api.openai.com/v1")
        if config.validator == "anthropic":
            return await _validate_anthropic(config, api_key)
        if config.validator in {"gemini", "google_ai_studio"}:
            return await _validate_gemini(config, api_key)
        if config.validator == "perplexity":
            return await _validate_perplexity(config, api_key)
        if config.validator == "xai":
            return await _validate_openai_compatible(config, api_key, config.base_url or "https://api.x.ai/v1")
        if config.validator == "openrouter":
            return await _validate_openrouter(config, api_key)
        if config.validator == "dial":
            return await _validate_dial(config, api_key, state)
        if config.validator == "inception":
            return await _validate_openai_compatible(config, api_key, config.base_url or "https://api.inceptionlabs.ai/v1")
        if config.validator == "openai_compatible":
            return await _validate_openai_compatible(config, api_key, _resolve_base_url(config, state))
        if config.validator == "custom_openai_compatible":
            return await _validate_openai_compatible(config, api_key, _resolve_base_url(config, state))
        if config.validator == "notion":
            return await _validate_notion(config, api_key)
    except httpx.TimeoutException as exc:
        return _error_result(config, "timeout", "Provider validation timed out.", str(exc))
    except httpx.TransportError as exc:
        return _error_result(config, "transport_error", "Provider validation request failed.", str(exc))

    return _error_result(config, "unsupported_validator", f"Unsupported validator: {config.validator}")


async def _validate_openai_compatible(config: FieldValidationConfig, api_key: str, base_url: str) -> dict[str, Any]:
    normalized = _normalize_url(base_url)
    if not normalized:
        return _error_result(config, "missing_base_url", "Validator requires a base URL.")
    if not normalized.endswith("/v1"):
        normalized = f"{normalized}/v1"
    response = await _request("GET", f"{normalized}/models", headers={"Authorization": f"Bearer {api_key}"})
    if response.is_success:
        return _ok_result(config, "API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_anthropic(config: FieldValidationConfig, api_key: str) -> dict[str, Any]:
    response = await _request(
        "GET",
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    if response.is_success:
        return _ok_result(config, "Anthropic API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_gemini(config: FieldValidationConfig, api_key: str) -> dict[str, Any]:
    response = await _request("GET", f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
    if response.is_success:
        return _ok_result(config, "Gemini API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_perplexity(config: FieldValidationConfig, api_key: str) -> dict[str, Any]:
    response = await _request(
        "POST",
        "https://api.perplexity.ai/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json_payload={
            "model": "sonar",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        },
    )
    if response.is_success:
        return _ok_result(config, "Perplexity API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_openrouter(config: FieldValidationConfig, api_key: str) -> dict[str, Any]:
    response = await _request(
        "POST",
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json_payload={
            "model": "openai/gpt-4o-mini",
            "max_tokens": 1,
            "messages": [{"role": "user", "content": "ping"}],
        },
    )
    if response.is_success:
        return _ok_result(config, "OpenRouter API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_dial(config: FieldValidationConfig, api_key: str, state: dict[str, Any]) -> dict[str, Any]:
    base_url = _resolve_base_url(config, state) or "https://core.dialx.ai"
    base_url = _normalize_url(base_url)
    if not base_url.endswith("/openai"):
        base_url = f"{base_url}/openai"
    headers = {"Api-Key": api_key}
    api_version = _value(state, "DIAL_API_VERSION")
    if api_version:
        headers["api-version"] = api_version
    response = await _request("GET", f"{base_url}/models", headers=headers)
    if response.is_success:
        return _ok_result(config, "DIAL API key accepted.")
    return _normalize_http_error(config, response)


async def _validate_notion(config: FieldValidationConfig, api_key: str) -> dict[str, Any]:
    response = await _request(
        "GET",
        "https://api.notion.com/v1/users/me",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_VERSION,
        },
    )
    if response.is_success:
        return _ok_result(config, "Notion API key accepted.")
    return _normalize_http_error(config, response)
