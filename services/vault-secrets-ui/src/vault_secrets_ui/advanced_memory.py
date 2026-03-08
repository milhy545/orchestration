from __future__ import annotations

from typing import Any

import httpx

DISCOVERY_TIMEOUT_SECONDS = 20.0
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
INCEPTION_BASE_URL = "https://api.inceptionlabs.ai/v1"
LOCAL_EMBEDDING_MODELS = [
    "all-MiniLM-L6-v2",
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-mpnet-base-v2",
]


def _normalize_base_url(url: str) -> str:
    return str(url or "").strip().rstrip("/")


def _normalize_openai_compatible_base_url(url: str) -> str:
    normalized = _normalize_base_url(url)
    if normalized.endswith("/v1"):
        return normalized
    return f"{normalized}/v1" if normalized else normalized


def _selected_model(state: dict[str, Any], field_name: str) -> str:
    value = state.get(field_name)
    return str(value or "").strip()


def _pick_model(models: list[str], preferred: str) -> str:
    if preferred and preferred in models:
        return preferred
    if models:
        return models[0]
    return preferred


def _ok_result(
    *,
    provider: str,
    resolved_base_url: str,
    models: list[str],
    selected_model: str,
    model_field: str,
    requires_api_key: bool,
    requires_base_url: bool,
    message: str,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "resolved_base_url": resolved_base_url,
        "models": models,
        "selected_model": selected_model,
        "model_field": model_field,
        "requires_api_key": requires_api_key,
        "requires_base_url": requires_base_url,
        "status": "ok",
        "error": "",
        "message": message,
    }


def _error_result(
    *,
    provider: str,
    resolved_base_url: str,
    model_field: str,
    requires_api_key: bool,
    requires_base_url: bool,
    error: str,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "resolved_base_url": resolved_base_url,
        "models": [],
        "selected_model": "",
        "model_field": model_field,
        "requires_api_key": requires_api_key,
        "requires_base_url": requires_base_url,
        "status": "error",
        "error": error,
        "message": error,
    }


async def _http_get_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=DISCOVERY_TIMEOUT_SECONDS) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict):
        raise ValueError("Provider returned an invalid payload")
    return payload


def _extract_model_names(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    names: list[str] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        model_id = item.get("id")
        if isinstance(model_id, str) and model_id.strip():
            names.append(model_id.strip())
    return sorted(set(names))


async def discover_advanced_memory(payload: dict[str, Any], target: str = "all") -> dict[str, Any]:
    state = dict(payload)
    response: dict[str, Any] = {}

    if target in {"embedding", "all"}:
        response["embedding"] = await discover_embedding_provider(state)
    if target in {"generation", "all"}:
        response["generation"] = await discover_generation_provider(state)
    return response


async def discover_embedding_provider(state: dict[str, Any]) -> dict[str, Any]:
    provider = str(state.get("EMBEDDING_PROVIDER", "local") or "local").strip().lower()
    if provider == "local":
        selected = _pick_model(LOCAL_EMBEDDING_MODELS, _selected_model(state, "LOCAL_EMBEDDING_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url="",
            models=LOCAL_EMBEDDING_MODELS,
            selected_model=selected,
            model_field="LOCAL_EMBEDDING_MODEL",
            requires_api_key=False,
            requires_base_url=False,
            message="Local embedding models ready.",
        )

    if provider == "gemini":
        api_key = str(state.get("GEMINI_API_KEY", "") or "").strip()
        if not api_key:
            return _error_result(
                provider=provider,
                resolved_base_url=GEMINI_BASE_URL,
                model_field="GEMINI_EMBED_MODEL",
                requires_api_key=True,
                requires_base_url=False,
                error="GEMINI_API_KEY is required for Gemini model discovery.",
            )
        payload = await _http_get_json(f"{GEMINI_BASE_URL}/models?key={api_key}")
        models: list[str] = []
        for item in payload.get("models", []):
            if not isinstance(item, dict):
                continue
            methods = item.get("supportedGenerationMethods", [])
            if isinstance(methods, list) and "embedContent" in methods:
                name = str(item.get("name", "")).strip()
                if name.startswith("models/"):
                    models.append(name.split("/", 1)[1])
        models = sorted(set(models))
        selected = _pick_model(models, _selected_model(state, "GEMINI_EMBED_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=GEMINI_BASE_URL,
            models=models,
            selected_model=selected,
            model_field="GEMINI_EMBED_MODEL",
            requires_api_key=True,
            requires_base_url=False,
            message="Gemini models discovered.",
        )

    if provider == "ollama":
        base_url = _normalize_base_url(state.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
        if not base_url:
            return _error_result(
                provider=provider,
                resolved_base_url="",
                model_field="OLLAMA_EMBED_MODEL",
                requires_api_key=False,
                requires_base_url=True,
                error="OLLAMA_BASE_URL is required for Ollama model discovery.",
            )
        payload = await _http_get_json(f"{base_url}/api/tags")
        models = sorted(
            {
                str(item.get("name", "")).strip()
                for item in payload.get("models", [])
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            }
        )
        selected = _pick_model(models, _selected_model(state, "OLLAMA_EMBED_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=base_url,
            models=models,
            selected_model=selected,
            model_field="OLLAMA_EMBED_MODEL",
            requires_api_key=False,
            requires_base_url=True,
            message="Ollama models discovered.",
        )

    if provider == "openai_compatible":
        base_url = _normalize_openai_compatible_base_url(state.get("OPENAI_COMPAT_BASE_URL", ""))
        if not base_url:
            return _error_result(
                provider=provider,
                resolved_base_url="",
                model_field="OPENAI_COMPAT_EMBED_MODEL",
                requires_api_key=False,
                requires_base_url=True,
                error="OPENAI_COMPAT_BASE_URL is required for local model discovery.",
            )
        api_key = str(state.get("OPENAI_COMPAT_API_KEY", "") or "").strip()
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
        payload = await _http_get_json(f"{base_url}/models", headers=headers)
        models = _extract_model_names(payload)
        selected = _pick_model(models, _selected_model(state, "OPENAI_COMPAT_EMBED_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=base_url,
            models=models,
            selected_model=selected,
            model_field="OPENAI_COMPAT_EMBED_MODEL",
            requires_api_key=False,
            requires_base_url=True,
            message="OpenAI-compatible models discovered.",
        )

    return _error_result(
        provider=provider,
        resolved_base_url="",
        model_field="",
        requires_api_key=False,
        requires_base_url=False,
        error=f"Unsupported embedding provider: {provider}",
    )


async def discover_generation_provider(state: dict[str, Any]) -> dict[str, Any]:
    provider = str(state.get("GENERATION_PROVIDER", "none") or "none").strip().lower()
    if provider == "none":
        return _ok_result(
            provider=provider,
            resolved_base_url="",
            models=[],
            selected_model="",
            model_field="",
            requires_api_key=False,
            requires_base_url=False,
            message="Generation provider disabled.",
        )

    if provider == "inception":
        api_key = str(state.get("INCEPTION_API_KEY", "") or "").strip()
        if not api_key:
            return _error_result(
                provider=provider,
                resolved_base_url=INCEPTION_BASE_URL,
                model_field="INCEPTION_MODEL",
                requires_api_key=True,
                requires_base_url=False,
                error="INCEPTION_API_KEY is required for Inception model discovery.",
            )
        payload = await _http_get_json(
            f"{INCEPTION_BASE_URL}/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        models = _extract_model_names(payload)
        selected = _pick_model(models, _selected_model(state, "INCEPTION_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=INCEPTION_BASE_URL,
            models=models,
            selected_model=selected,
            model_field="INCEPTION_MODEL",
            requires_api_key=True,
            requires_base_url=False,
            message="Inception models discovered.",
        )

    if provider == "ollama":
        base_url = _normalize_base_url(state.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"))
        if not base_url:
            return _error_result(
                provider=provider,
                resolved_base_url="",
                model_field="OLLAMA_CHAT_MODEL",
                requires_api_key=False,
                requires_base_url=True,
                error="OLLAMA_BASE_URL is required for Ollama model discovery.",
            )
        payload = await _http_get_json(f"{base_url}/api/tags")
        models = sorted(
            {
                str(item.get("name", "")).strip()
                for item in payload.get("models", [])
                if isinstance(item, dict) and str(item.get("name", "")).strip()
            }
        )
        selected = _pick_model(models, _selected_model(state, "OLLAMA_CHAT_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=base_url,
            models=models,
            selected_model=selected,
            model_field="OLLAMA_CHAT_MODEL",
            requires_api_key=False,
            requires_base_url=True,
            message="Ollama models discovered.",
        )

    if provider == "openai_compatible":
        base_url = _normalize_openai_compatible_base_url(state.get("OPENAI_COMPAT_BASE_URL", ""))
        if not base_url:
            return _error_result(
                provider=provider,
                resolved_base_url="",
                model_field="OPENAI_COMPAT_CHAT_MODEL",
                requires_api_key=False,
                requires_base_url=True,
                error="OPENAI_COMPAT_BASE_URL is required for local model discovery.",
            )
        api_key = str(state.get("OPENAI_COMPAT_API_KEY", "") or "").strip()
        headers = {"Authorization": f"Bearer {api_key}"} if api_key else None
        payload = await _http_get_json(f"{base_url}/models", headers=headers)
        models = _extract_model_names(payload)
        selected = _pick_model(models, _selected_model(state, "OPENAI_COMPAT_CHAT_MODEL"))
        return _ok_result(
            provider=provider,
            resolved_base_url=base_url,
            models=models,
            selected_model=selected,
            model_field="OPENAI_COMPAT_CHAT_MODEL",
            requires_api_key=False,
            requires_base_url=True,
            message="OpenAI-compatible models discovered.",
        )

    return _error_result(
        provider=provider,
        resolved_base_url="",
        model_field="",
        requires_api_key=False,
        requires_base_url=False,
        error=f"Unsupported generation provider: {provider}",
    )


def validate_advanced_memory_state(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    embedding_provider = str(payload.get("EMBEDDING_PROVIDER", "local") or "local").strip().lower()
    generation_provider = str(payload.get("GENERATION_PROVIDER", "none") or "none").strip().lower()

    if embedding_provider == "gemini" and not str(payload.get("GEMINI_API_KEY", "") or "").strip():
        errors.append("Embedding provider Gemini requires GEMINI_API_KEY.")
    if embedding_provider == "ollama" and not _normalize_base_url(payload.get("OLLAMA_BASE_URL", "")):
        errors.append("Embedding provider Ollama requires OLLAMA_BASE_URL.")
    if embedding_provider == "openai_compatible" and not _normalize_openai_compatible_base_url(payload.get("OPENAI_COMPAT_BASE_URL", "")):
        errors.append("Embedding provider OpenAI-compatible requires OPENAI_COMPAT_BASE_URL.")

    if generation_provider == "inception" and not str(payload.get("INCEPTION_API_KEY", "") or "").strip():
        errors.append("Generation provider Inception requires INCEPTION_API_KEY.")
    if generation_provider == "ollama" and not _normalize_base_url(payload.get("OLLAMA_BASE_URL", "")):
        errors.append("Generation provider Ollama requires OLLAMA_BASE_URL.")
    if generation_provider == "openai_compatible" and not _normalize_openai_compatible_base_url(payload.get("OPENAI_COMPAT_BASE_URL", "")):
        errors.append("Generation provider OpenAI-compatible requires OPENAI_COMPAT_BASE_URL.")

    return errors


async def run_console_command(command: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = " ".join(str(command or "").strip().lower().split())
    if not normalized:
        return {"status": "error", "output": ["Empty command. Try: help"]}

    if normalized == "help":
        return {
            "status": "ok",
            "output": [
                "Available commands:",
                "help",
                "status",
                "discover embedding",
                "discover generation",
                "discover all",
                "validate",
                "health",
                "clear",
            ],
        }

    if normalized == "status":
        return {
            "status": "ok",
            "output": [
                f"Embedding provider: {payload.get('EMBEDDING_PROVIDER', 'local')}",
                f"Generation provider: {payload.get('GENERATION_PROVIDER', 'none')}",
            ],
        }

    if normalized == "validate":
        errors = validate_advanced_memory_state(payload)
        return {
            "status": "ok" if not errors else "error",
            "output": ["Validation passed."] if not errors else errors,
        }

    if normalized == "health":
        return {"status": "ok", "output": ["Vault UI console online. Provider discovery available."]}

    if normalized == "clear":
        return {"status": "ok", "output": []}

    if normalized in {"discover embedding", "discover generation", "discover all"}:
        target = normalized.split()[-1]
        discovery = await discover_advanced_memory(payload, target=target if target in {"embedding", "generation"} else "all")
        lines: list[str] = []
        for key in ("embedding", "generation"):
            if key not in discovery:
                continue
            item = discovery[key]
            if item["status"] == "ok":
                count = len(item["models"])
                lines.append(f"{key.title()}: discovered {count} model(s) from {item['provider']}.")
            else:
                lines.append(f"{key.title()}: {item['error']}")
        return {"status": "ok", "output": lines, "discovery": discovery}

    return {"status": "error", "output": [f"Unknown command: {command}", "Try: help"]}
