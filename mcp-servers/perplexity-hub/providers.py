from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import httpx


PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_URL = os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions")
REQUEST_TIMEOUT = float(os.getenv("PERPLEXITY_HUB_TIMEOUT", "60"))
DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

MODE_PROMPTS = {
    "news": "You provide current, cited news and state clearly when details are uncertain.",
    "domain": "You research only within the allowed domains and return cited findings.",
    "academic": "You focus on peer-reviewed, academic, and technical source material.",
    "structured": "You return structured output that follows the provided schema as closely as possible.",
}


class ProviderConfigurationError(RuntimeError):
    """Raised when a required provider secret is not configured."""


class ProviderResponseError(RuntimeError):
    """Raised when an upstream provider returns an invalid response."""


@dataclass(slots=True)
class RetrievalResult:
    query: str
    mode: str
    model_used: str
    response: str
    sources: list[str]


def build_perplexity_payload(request: Mapping[str, Any]) -> dict[str, Any]:
    mode = str(request["mode"])
    payload: dict[str, Any] = {
        "model": request.get("model") or "sonar-pro",
        "messages": [
            {"role": "system", "content": MODE_PROMPTS[mode]},
            {"role": "user", "content": request["query"]},
        ],
    }
    if mode == "domain":
        payload["search_domain_filter"] = request.get("domains") or []
        payload["search_recency_filter"] = request.get("recency") or "month"
    if mode == "academic":
        payload["search_filter"] = "academic"
    if mode == "structured" and request.get("response_schema"):
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"schema": request["response_schema"]},
        }
    return payload


def extract_perplexity_content(payload: Mapping[str, Any]) -> tuple[str, list[str]]:
    try:
        answer = str(payload["choices"][0]["message"]["content"])
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderResponseError("Perplexity response shape was invalid") from exc
    citations = [str(item) for item in payload.get("citations", [])]
    return answer, citations


def build_openai_payload(request: Mapping[str, Any], retrieval: RetrievalResult) -> dict[str, Any]:
    synthesis_model = request.get("synthesis_model") or DEFAULT_OPENAI_MODEL
    source_lines = "\n".join(f"- {source}" for source in retrieval.sources) or "- none"
    instruction = (
        f"Original user query: {request['query']}\n"
        f"Research mode: {request['mode']}\n"
        f"Cited retrieval result:\n{retrieval.response}\n\n"
        f"Sources:\n{source_lines}\n\n"
        "Rewrite the result into a concise, faithful synthesis. Do not invent sources."
    )
    if request.get("mode") == "structured" and request.get("response_schema"):
        instruction += (
            "\nReturn valid JSON that follows this schema as closely as possible:\n"
            f"{json.dumps(request['response_schema'], ensure_ascii=True)}"
        )
    payload = {
        "model": synthesis_model,
        "messages": [
            {
                "role": "system",
                "content": "You are a careful synthesis model. Preserve factual claims and sources.",
            },
            {"role": "user", "content": instruction},
        ],
    }
    if request.get("mode") == "structured":
        payload["response_format"] = {"type": "json_object"}
    return payload


def extract_openai_content(payload: Mapping[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderResponseError("OpenAI response shape was invalid") from exc

    if isinstance(content, str):
        return content
    if isinstance(content, Sequence):
        parts = [item.get("text", "") for item in content if isinstance(item, Mapping)]
        if parts:
            return "".join(parts)
    raise ProviderResponseError("OpenAI response content was invalid")


class PerplexityRetriever:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key or ""

    async def retrieve(self, request: Mapping[str, Any]) -> RetrievalResult:
        if not self.api_key:
            raise ProviderConfigurationError("PERPLEXITY_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
                response = await client.post(
                    PERPLEXITY_API_URL,
                    headers=headers,
                    json=build_perplexity_payload(request),
                )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderResponseError(f"Perplexity request failed with {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError("Perplexity endpoint is unreachable") from exc

        answer, sources = extract_perplexity_content(response.json())
        return RetrievalResult(
            query=str(request["query"]),
            mode=str(request["mode"]),
            model_used=str(request.get("model") or "sonar-pro"),
            response=answer,
            sources=sources,
        )


class OpenAISynthesizer:
    def __init__(self, api_key: str | None) -> None:
        self.api_key = api_key or ""

    async def synthesize(self, request: Mapping[str, Any], retrieval: RetrievalResult) -> tuple[str, str]:
        if not self.api_key:
            raise ProviderConfigurationError("OPENAI_API_KEY not configured")

        payload = build_openai_payload(request, retrieval)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
                response = await client.post(OPENAI_API_URL, headers=headers, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProviderResponseError(f"OpenAI synthesis failed with {exc.response.status_code}") from exc
        except httpx.HTTPError as exc:
            raise ProviderResponseError("OpenAI endpoint is unreachable") from exc

        return extract_openai_content(response.json()), str(payload["model"])
