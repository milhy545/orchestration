from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict, Field

from providers import OpenAISynthesizer, PerplexityRetriever, ProviderConfigurationError, ProviderResponseError


DEFAULT_PERPLEXITY_MODEL = "sonar-pro"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"


def _load_secret(name: str) -> str | None:
    file_path = os.getenv(f"{name}_FILE", "").strip()
    if file_path:
        try:
            value = Path(file_path).read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise HTTPException(status_code=500, detail=f"{name}_FILE could not be read") from exc
        return value or None

    value = os.getenv(name, "").strip()
    return value or None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class HubQueryRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    query: str = Field(..., min_length=1)
    mode: Literal["news", "domain", "academic", "structured"] = "news"
    model: str = DEFAULT_PERPLEXITY_MODEL
    domains: list[str] = Field(default_factory=list)
    recency: Literal["day", "week", "month", "year"] | None = None
    response_schema: dict[str, Any] | None = None
    synthesis_provider: Literal["none", "openai"] = "none"
    synthesis_model: str | None = None


class HubQueryResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    query: str
    mode: str
    retrieval_provider: Literal["perplexity"]
    synthesis_provider: Literal["none", "openai"]
    model_used: str
    sources: list[str]
    answer: str | None = None
    structured_data: dict[str, Any] | None = None
    warnings: list[str] = Field(default_factory=list)
    timestamp: str


class LegacySearchResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    query: str
    response: str
    sources: list[str]
    model_used: str
    search_type: str


class LegacyStructuredResult(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    query: str
    structured_data: dict[str, Any]
    sources: list[str]
    model_used: str


app = FastAPI(
    title="Perplexity HUB",
    description="Canonical research runtime for cited retrieval via Perplexity with optional OpenAI synthesis.",
    version="1.0.0",
)
Instrumentator().instrument(app).expose(app)


def _provider_state() -> dict[str, Any]:
    return {
        "perplexity": {
            "configured": bool(_load_secret("PERPLEXITY_API_KEY")),
            "capabilities": ["retrieval", "citations", "domain-filtering", "academic-search"],
            "default_model": DEFAULT_PERPLEXITY_MODEL,
        },
        "openai": {
            "configured": bool(_load_secret("OPENAI_API_KEY")),
            "capabilities": ["synthesis", "normalization", "structured-postprocessing"],
            "default_model": os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL),
        },
    }


def _validate_request(request: HubQueryRequest) -> None:
    if request.mode == "domain" and not request.domains:
        raise HTTPException(status_code=422, detail="domains are required for domain mode")
    if request.mode != "domain" and request.recency is not None:
        raise HTTPException(status_code=422, detail="recency is only supported for domain mode")
    if request.mode == "structured" and not request.response_schema:
        raise HTTPException(status_code=422, detail="response_schema is required for structured mode")


def _parse_structured(answer: str) -> dict[str, Any]:
    try:
        return json.loads(answer)
    except json.JSONDecodeError:
        return {"raw_response": answer}


async def _execute_query(request: HubQueryRequest) -> HubQueryResponse:
    _validate_request(request)

    retriever = PerplexityRetriever(_load_secret("PERPLEXITY_API_KEY"))
    try:
        retrieval = await retriever.retrieve(request.model_dump())
    except ProviderConfigurationError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except ProviderResponseError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    warnings: list[str] = []
    answer = retrieval.response
    model_used = retrieval.model_used
    synthesis_provider: Literal["none", "openai"] = "none"

    if request.synthesis_provider == "openai":
        openai_key = _load_secret("OPENAI_API_KEY")
        if openai_key:
            synthesizer = OpenAISynthesizer(openai_key)
            try:
                answer, model_used = await synthesizer.synthesize(request.model_dump(), retrieval)
            except ProviderConfigurationError as exc:
                raise HTTPException(status_code=500, detail=str(exc)) from exc
            except ProviderResponseError as exc:
                raise HTTPException(status_code=502, detail=str(exc)) from exc
            synthesis_provider = "openai"
        else:
            warnings.append("OpenAI synthesis requested but OPENAI_API_KEY is not configured.")

    return HubQueryResponse(
        query=request.query,
        mode=request.mode,
        retrieval_provider="perplexity",
        synthesis_provider=synthesis_provider,
        model_used=model_used,
        sources=retrieval.sources,
        answer=None if request.mode == "structured" else answer,
        structured_data=_parse_structured(answer) if request.mode == "structured" else None,
        warnings=warnings,
        timestamp=_utc_now(),
    )


def _legacy_search_response(response: HubQueryResponse) -> LegacySearchResult:
    return LegacySearchResult(
        query=response.query,
        response=response.answer or "",
        sources=response.sources,
        model_used=response.model_used,
        search_type=response.mode,
    )


def _legacy_structured_response(response: HubQueryResponse) -> LegacyStructuredResult:
    return LegacyStructuredResult(
        query=response.query,
        structured_data=response.structured_data or {},
        sources=response.sources,
        model_used=response.model_used,
    )


@app.get("/health")
async def health() -> dict[str, Any]:
    state = _provider_state()
    return {
        "status": "healthy",
        "service": "perplexity-hub",
        "version": "1.0.0",
        "timestamp": _utc_now(),
        "providers": {
            "perplexity": state["perplexity"]["configured"],
            "openai": state["openai"]["configured"],
        },
    }


@app.get("/hub/providers")
async def providers() -> dict[str, Any]:
    return {"providers": _provider_state()}


@app.post("/hub/query", response_model=HubQueryResponse)
async def hub_query(request: HubQueryRequest) -> HubQueryResponse:
    return await _execute_query(request)


@app.post("/research/news", response_model=LegacySearchResult)
async def research_news(query: str, model: str = DEFAULT_PERPLEXITY_MODEL) -> LegacySearchResult:
    return _legacy_search_response(
        await _execute_query(HubQueryRequest(query=query, mode="news", model=model))
    )


@app.post("/research/domain", response_model=LegacySearchResult)
async def research_domain(
    query: str,
    domains: list[str],
    recency: Literal["day", "week", "month", "year"] = "month",
    model: str = DEFAULT_PERPLEXITY_MODEL,
) -> LegacySearchResult:
    return _legacy_search_response(
        await _execute_query(
            HubQueryRequest(
                query=query,
                mode="domain",
                model=model,
                domains=domains,
                recency=recency,
            )
        )
    )


@app.post("/research/academic", response_model=LegacySearchResult)
async def research_academic(query: str, model: str = DEFAULT_PERPLEXITY_MODEL) -> LegacySearchResult:
    return _legacy_search_response(
        await _execute_query(HubQueryRequest(query=query, mode="academic", model=model))
    )


@app.post("/research/structured", response_model=LegacyStructuredResult)
async def research_structured(
    query: str,
    schema: dict[str, Any],
    model: str = DEFAULT_PERPLEXITY_MODEL,
) -> LegacyStructuredResult:
    return _legacy_structured_response(
        await _execute_query(
            HubQueryRequest(
                query=query,
                mode="structured",
                model=model,
                response_schema=schema,
            )
        )
    )


@app.post("/research/search", response_model=LegacySearchResult)
async def research_search(query: str, model: str = DEFAULT_PERPLEXITY_MODEL) -> LegacySearchResult:
    return _legacy_search_response(
        await _execute_query(HubQueryRequest(query=query, mode="news", model=model))
    )
