from __future__ import annotations

import asyncio
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


def load_setting(name: str, default: str | None = None) -> str | None:
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        value = Path(file_path).read_text(encoding="utf-8").strip()
        if value:
            return value
        return default

    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _normalize_base_url(url: str) -> str:
    return url.rstrip("/")


class ProviderError(RuntimeError):
    """Raised when an embedding or generation provider is misconfigured or fails."""


@dataclass(slots=True)
class RuntimeConfig:
    embedding_provider: str
    generation_provider: str
    local_embedding_model: str
    gemini_api_key: str
    gemini_embedding_model: str
    ollama_base_url: str
    ollama_embedding_model: str
    ollama_chat_model: str
    openai_compat_base_url: str
    openai_compat_api_key: str
    openai_compat_embed_model: str
    openai_compat_chat_model: str
    inception_api_key: str
    inception_base_url: str
    inception_model: str
    request_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "RuntimeConfig":
        return cls(
            embedding_provider=(load_setting("EMBEDDING_PROVIDER", "local") or "local").strip().lower(),
            generation_provider=(load_setting("GENERATION_PROVIDER", "none") or "none").strip().lower(),
            local_embedding_model=load_setting("LOCAL_EMBEDDING_MODEL", "all-MiniLM-L6-v2") or "all-MiniLM-L6-v2",
            gemini_api_key=load_setting("GEMINI_API_KEY", "") or "",
            gemini_embedding_model=load_setting("GEMINI_EMBED_MODEL", "gemini-embedding-001") or "gemini-embedding-001",
            ollama_base_url=_normalize_base_url(load_setting("OLLAMA_BASE_URL", "http://127.0.0.1:11434") or "http://127.0.0.1:11434"),
            ollama_embedding_model=load_setting("OLLAMA_EMBED_MODEL", "nomic-embed-text") or "nomic-embed-text",
            ollama_chat_model=load_setting("OLLAMA_CHAT_MODEL", "llama3.2") or "llama3.2",
            openai_compat_base_url=_normalize_base_url(load_setting("OPENAI_COMPAT_BASE_URL", "") or ""),
            openai_compat_api_key=load_setting("OPENAI_COMPAT_API_KEY", "") or "",
            openai_compat_embed_model=load_setting("OPENAI_COMPAT_EMBED_MODEL", "") or "",
            openai_compat_chat_model=load_setting("OPENAI_COMPAT_CHAT_MODEL", "") or "",
            inception_api_key=load_setting("INCEPTION_API_KEY", "") or "",
            inception_base_url=_normalize_base_url(load_setting("INCEPTION_BASE_URL", "https://api.inceptionlabs.ai/v1") or "https://api.inceptionlabs.ai/v1"),
            inception_model=load_setting("INCEPTION_MODEL", "mercury") or "mercury",
            request_timeout_seconds=float(load_setting("ADVANCED_MEMORY_HTTP_TIMEOUT", "60") or "60"),
        )


class ProviderClient:
    def __init__(
        self,
        config: RuntimeConfig,
        local_embedder: Callable[[str], list[float]] | None = None,
    ) -> None:
        self.config = config
        self.local_embedder = local_embedder

    async def embed_document(self, text: str) -> list[float]:
        return await self._embed(text, task_type="RETRIEVAL_DOCUMENT")

    async def embed_query(self, text: str) -> list[float]:
        return await self._embed(text, task_type="RETRIEVAL_QUERY")

    async def generate_answer(self, query: str, context_items: list[dict[str, Any]]) -> str:
        provider = self.config.generation_provider
        if provider == "none":
            raise ProviderError("GENERATION_PROVIDER is not configured")
        if provider == "inception":
            return await asyncio.to_thread(self._generate_inception, query, context_items)
        if provider == "ollama":
            return await asyncio.to_thread(self._generate_ollama, query, context_items)
        if provider == "openai_compatible":
            return await asyncio.to_thread(self._generate_openai_compatible, query, context_items)
        raise ProviderError(f"Unsupported generation provider: {provider}")

    async def _embed(self, text: str, task_type: str) -> list[float]:
        provider = self.config.embedding_provider
        if provider == "local":
            return self._embed_local(text)
        if provider == "gemini":
            return await asyncio.to_thread(self._embed_gemini, text, task_type)
        if provider == "ollama":
            return await asyncio.to_thread(self._embed_ollama, text)
        if provider == "openai_compatible":
            return await asyncio.to_thread(self._embed_openai_compatible, text)
        raise ProviderError(f"Unsupported embedding provider: {provider}")

    def _embed_local(self, text: str) -> list[float]:
        if self.local_embedder is None:
            raise ProviderError("Local embedding model is not loaded")
        return [float(value) for value in self.local_embedder(text)]

    def _embed_gemini(self, text: str, task_type: str) -> list[float]:
        if not self.config.gemini_api_key:
            raise ProviderError("GEMINI_API_KEY is not configured")
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self.config.gemini_embedding_model}:embedContent?key={urllib.parse.quote(self.config.gemini_api_key)}"
        )
        payload = {
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
        }
        response = self._post_json(endpoint, payload)
        values = response.get("embedding", {}).get("values")
        if not isinstance(values, list) or not values:
            raise ProviderError("Gemini embedding response was invalid")
        return [float(value) for value in values]

    def _embed_ollama(self, text: str) -> list[float]:
        if not self.config.ollama_base_url:
            raise ProviderError("OLLAMA_BASE_URL is not configured")
        primary_endpoint = f"{self.config.ollama_base_url}/api/embed"
        fallback_endpoint = f"{self.config.ollama_base_url}/api/embeddings"
        payload = {"model": self.config.ollama_embedding_model, "input": text}

        try:
            response = self._post_json(primary_endpoint, payload)
        except ProviderError:
            response = self._post_json(
                fallback_endpoint,
                {"model": self.config.ollama_embedding_model, "prompt": text},
            )

        if isinstance(response.get("embeddings"), list) and response["embeddings"]:
            first = response["embeddings"][0]
            if isinstance(first, list):
                return [float(value) for value in first]
        if isinstance(response.get("embedding"), list):
            return [float(value) for value in response["embedding"]]
        raise ProviderError("Ollama embedding response was invalid")

    def _embed_openai_compatible(self, text: str) -> list[float]:
        if not self.config.openai_compat_base_url:
            raise ProviderError("OPENAI_COMPAT_BASE_URL is not configured")
        if not self.config.openai_compat_embed_model:
            raise ProviderError("OPENAI_COMPAT_EMBED_MODEL is not configured")
        response = self._post_json(
            f"{self.config.openai_compat_base_url}/embeddings",
            {"model": self.config.openai_compat_embed_model, "input": text},
            headers=self._openai_compatible_headers(),
        )
        data = response.get("data")
        if not isinstance(data, list) or not data:
            raise ProviderError("OpenAI-compatible embedding response was invalid")
        embedding = data[0].get("embedding")
        if not isinstance(embedding, list) or not embedding:
            raise ProviderError("OpenAI-compatible embedding vector was invalid")
        return [float(value) for value in embedding]

    def _generate_inception(self, query: str, context_items: list[dict[str, Any]]) -> str:
        if not self.config.inception_api_key:
            raise ProviderError("INCEPTION_API_KEY is not configured")
        return self._chat_completion(
            f"{self.config.inception_base_url}/chat/completions",
            self.config.inception_model,
            query,
            context_items,
            headers={
                "Authorization": f"Bearer {self.config.inception_api_key}",
                "Content-Type": "application/json",
            },
        )

    def _generate_openai_compatible(self, query: str, context_items: list[dict[str, Any]]) -> str:
        if not self.config.openai_compat_base_url:
            raise ProviderError("OPENAI_COMPAT_BASE_URL is not configured")
        if not self.config.openai_compat_chat_model:
            raise ProviderError("OPENAI_COMPAT_CHAT_MODEL is not configured")
        return self._chat_completion(
            f"{self.config.openai_compat_base_url}/chat/completions",
            self.config.openai_compat_chat_model,
            query,
            context_items,
            headers=self._openai_compatible_headers(),
        )

    def _generate_ollama(self, query: str, context_items: list[dict[str, Any]]) -> str:
        if not self.config.ollama_base_url:
            raise ProviderError("OLLAMA_BASE_URL is not configured")
        response = self._post_json(
            f"{self.config.ollama_base_url}/api/chat",
            {
                "model": self.config.ollama_chat_model,
                "stream": False,
                "messages": self._build_messages(query, context_items),
            },
        )
        content = response.get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Ollama chat response was invalid")
        return content.strip()

    def _chat_completion(
        self,
        endpoint: str,
        model: str,
        query: str,
        context_items: list[dict[str, Any]],
        headers: dict[str, str],
    ) -> str:
        response = self._post_json(
            endpoint,
            {
                "model": model,
                "messages": self._build_messages(query, context_items),
            },
            headers=headers,
        )
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ProviderError("Chat completion response was invalid")
        content = choices[0].get("message", {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("Chat completion content was invalid")
        return content.strip()

    def _build_messages(self, query: str, context_items: list[dict[str, Any]]) -> list[dict[str, str]]:
        context_lines = []
        for index, item in enumerate(context_items, start=1):
            context_lines.append(
                f"[{index}] category={item.get('category', '')} score={item.get('similarity_score', '')}\n"
                f"{item.get('content', '')}"
            )
        context_block = "\n\n".join(context_lines) if context_lines else "No matching memories found."
        return [
            {
                "role": "system",
                "content": (
                    "You answer questions only from provided memory context. "
                    "State uncertainty when the memory context is insufficient."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {query}\n\nMemory context:\n{context_block}",
            },
        ]

    def _openai_compatible_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.openai_compat_api_key:
            headers["Authorization"] = f"Bearer {self.config.openai_compat_api_key}"
        return headers

    def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers or {"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.request_timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"Provider request failed with {exc.code}: {detail}") from exc
        except OSError as exc:
            raise ProviderError(f"Provider request failed: {exc}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ProviderError("Provider returned invalid JSON") from exc
        if not isinstance(parsed, dict):
            raise ProviderError("Provider returned an invalid payload")
        return parsed
