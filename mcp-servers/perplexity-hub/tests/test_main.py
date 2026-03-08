from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

SERVICE_DIR = Path(__file__).resolve().parents[1]
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

import main as hub_main
from providers import (
    OpenAISynthesizer,
    PerplexityRetriever,
    ProviderConfigurationError,
    ProviderResponseError,
    RetrievalResult,
    build_openai_payload,
    build_perplexity_payload,
    extract_openai_content,
    extract_perplexity_content,
)


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in [
        "PERPLEXITY_API_KEY",
        "PERPLEXITY_API_KEY_FILE",
        "OPENAI_API_KEY",
        "OPENAI_API_KEY_FILE",
        "OPENAI_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)


class BrokenAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self) -> "BrokenAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, *args, **kwargs):
        raise httpx.ReadTimeout("timeout")


class DummyResponse:
    def __init__(self, payload=None, raise_error: Exception | None = None) -> None:
        self._payload = payload or {}
        self._raise_error = raise_error

    def raise_for_status(self) -> None:
        if self._raise_error:
            raise self._raise_error

    def json(self):
        return self._payload


class SingleResponseAsyncClient:
    def __init__(self, response: DummyResponse) -> None:
        self._response = response

    async def __aenter__(self) -> "SingleResponseAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, *args, **kwargs):
        return self._response


def test_load_secret_prefers_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    secret_file = tmp_path / "secret.txt"
    secret_file.write_text("from-file\n", encoding="utf-8")
    monkeypatch.setenv("PERPLEXITY_API_KEY_FILE", str(secret_file))
    monkeypatch.setenv("PERPLEXITY_API_KEY", "from-env")

    assert hub_main._load_secret("PERPLEXITY_API_KEY") == "from-file"


def test_load_secret_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PERPLEXITY_API_KEY_FILE", str(tmp_path / "missing.txt"))

    with pytest.raises(hub_main.HTTPException) as excinfo:
        hub_main._load_secret("PERPLEXITY_API_KEY")
    assert excinfo.value.status_code == 500


def test_build_perplexity_payload_modes() -> None:
    domain_payload = build_perplexity_payload(
        {
            "query": "quantum",
            "mode": "domain",
            "model": "sonar-reasoning-pro",
            "domains": ["arxiv.org"],
            "recency": "week",
        }
    )
    assert domain_payload["search_domain_filter"] == ["arxiv.org"]
    assert domain_payload["search_recency_filter"] == "week"

    academic_payload = build_perplexity_payload(
        {"query": "llm evals", "mode": "academic", "model": "sonar-pro"}
    )
    assert academic_payload["search_filter"] == "academic"

    structured_payload = build_perplexity_payload(
        {
            "query": "extract",
            "mode": "structured",
            "model": "sonar-pro",
            "response_schema": {"type": "object"},
        }
    )
    assert structured_payload["response_format"]["json_schema"]["schema"] == {"type": "object"}


def test_extract_perplexity_content_invalid() -> None:
    with pytest.raises(ProviderResponseError):
        extract_perplexity_content({})


def test_extract_perplexity_content_valid() -> None:
    answer, citations = extract_perplexity_content(
        {"choices": [{"message": {"content": "answer"}}], "citations": [1, "two"]}
    )
    assert answer == "answer"
    assert citations == ["1", "two"]


def test_build_openai_payload_and_extract_content() -> None:
    payload = build_openai_payload(
        {
            "query": "summarize",
            "mode": "structured",
            "response_schema": {"type": "object"},
            "synthesis_model": "gpt-custom",
        },
        RetrievalResult(
            query="summarize",
            mode="structured",
            model_used="sonar-pro",
            response="retrieved",
            sources=["https://example.com"],
        ),
    )
    assert payload["model"] == "gpt-custom"
    assert payload["response_format"] == {"type": "json_object"}
    assert "schema" in payload["messages"][1]["content"]

    assert extract_openai_content({"choices": [{"message": {"content": "ok"}}]}) == "ok"
    assert extract_openai_content({"choices": [{"message": {"content": [{"text": "joined"}]}}]}) == "joined"
    with pytest.raises(ProviderResponseError):
        extract_openai_content({})
    with pytest.raises(ProviderResponseError):
        extract_openai_content({"choices": [{"message": {"content": 7}}]})


@pytest.mark.asyncio
async def test_retriever_and_synthesizer_require_keys() -> None:
    with pytest.raises(ProviderConfigurationError):
        await PerplexityRetriever(None).retrieve({"query": "x", "mode": "news", "model": "sonar-pro"})
    with pytest.raises(ProviderConfigurationError):
        await OpenAISynthesizer(None).synthesize(
            {"query": "x", "mode": "news"},
            RetrievalResult(query="x", mode="news", model_used="sonar-pro", response="answer", sources=[]),
        )


@pytest.mark.asyncio
async def test_retriever_and_synthesizer_http_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("providers.httpx.AsyncClient", BrokenAsyncClient)

    with pytest.raises(ProviderResponseError):
        await PerplexityRetriever("pplx-test").retrieve(
            {"query": "x", "mode": "news", "model": "sonar-pro"}
        )

    with pytest.raises(ProviderResponseError):
        await OpenAISynthesizer("sk-test").synthesize(
            {"query": "x", "mode": "news"},
            RetrievalResult(query="x", mode="news", model_used="sonar-pro", response="answer", sources=[]),
        )


@pytest.mark.asyncio
async def test_retriever_and_synthesizer_status_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    request = httpx.Request("POST", "https://example.com")
    pplx_error = httpx.HTTPStatusError("bad", request=request, response=httpx.Response(429, request=request))
    openai_error = httpx.HTTPStatusError("bad", request=request, response=httpx.Response(503, request=request))

    monkeypatch.setattr(
        "providers.httpx.AsyncClient",
        lambda **_: SingleResponseAsyncClient(DummyResponse(raise_error=pplx_error)),
    )
    with pytest.raises(ProviderResponseError) as pplx_exc:
        await PerplexityRetriever("pplx-test").retrieve(
            {"query": "x", "mode": "news", "model": "sonar-pro"}
        )
    assert "429" in str(pplx_exc.value)

    monkeypatch.setattr(
        "providers.httpx.AsyncClient",
        lambda **_: SingleResponseAsyncClient(DummyResponse(raise_error=openai_error)),
    )
    with pytest.raises(ProviderResponseError) as openai_exc:
        await OpenAISynthesizer("sk-test").synthesize(
            {"query": "x", "mode": "news"},
            RetrievalResult(query="x", mode="news", model_used="sonar-pro", response="answer", sources=[]),
        )
    assert "503" in str(openai_exc.value)


@pytest.mark.asyncio
async def test_retriever_and_synthesizer_success_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "providers.httpx.AsyncClient",
        lambda **_: SingleResponseAsyncClient(
            DummyResponse(payload={"choices": [{"message": {"content": "retrieved"}}], "citations": ["a"]})
        ),
    )
    retrieval = await PerplexityRetriever("pplx-test").retrieve(
        {"query": "x", "mode": "news", "model": "sonar-pro"}
    )
    assert retrieval.response == "retrieved"
    assert retrieval.sources == ["a"]

    monkeypatch.setattr(
        "providers.httpx.AsyncClient",
        lambda **_: SingleResponseAsyncClient(
            DummyResponse(payload={"choices": [{"message": {"content": "synthesized"}}]})
        ),
    )
    answer, model = await OpenAISynthesizer("sk-test").synthesize(
        {"query": "x", "mode": "news"},
        retrieval,
    )
    assert answer == "synthesized"
    assert model


def test_health_and_provider_endpoints(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    secret_file = tmp_path / "openai.txt"
    secret_file.write_text("sk-test", encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY_FILE", str(secret_file))

    health = asyncio.run(hub_main.health())
    assert health["providers"]["openai"] is True

    providers = asyncio.run(hub_main.providers())
    assert providers["providers"]["openai"]["default_model"] == "gpt-4.1-mini"


def test_hub_query_validation_errors() -> None:
    with pytest.raises(hub_main.HTTPException) as domain_exc:
        asyncio.run(hub_main.hub_query(hub_main.HubQueryRequest(query="q", mode="domain", model="sonar-pro")))
    assert domain_exc.value.status_code == 422

    with pytest.raises(hub_main.HTTPException) as structured_exc:
        asyncio.run(
            hub_main.hub_query(hub_main.HubQueryRequest(query="q", mode="structured", model="sonar-pro"))
        )
    assert structured_exc.value.status_code == 422

    with pytest.raises(hub_main.HTTPException) as recency_exc:
        asyncio.run(
            hub_main.hub_query(
                hub_main.HubQueryRequest(query="q", mode="news", model="sonar-pro", recency="week")
            )
        )
    assert recency_exc.value.status_code == 422


def test_hub_query_retrieval_only(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_retrieve(self, request):
        return RetrievalResult(
            query=request["query"],
            mode=request["mode"],
            model_used=request["model"],
            response="retrieved",
            sources=["https://example.com"],
        )

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", fake_retrieve)
    response = asyncio.run(
        hub_main.hub_query(hub_main.HubQueryRequest(query="q", mode="news", model="sonar-pro"))
    )
    assert response.answer == "retrieved"
    assert response.synthesis_provider == "none"
    assert response.warnings == []


def test_hub_query_structured_parse_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_retrieve(self, request):
        return RetrievalResult(
            query=request["query"],
            mode=request["mode"],
            model_used=request["model"],
            response=request["query"],
            sources=["https://example.com"],
        )

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", fake_retrieve)
    good = asyncio.run(
        hub_main.hub_query(
            hub_main.HubQueryRequest(
                query='{"value":"ok"}',
                mode="structured",
                model="sonar-pro",
                response_schema={"type": "object"},
            )
        )
    )
    assert good.structured_data == {"value": "ok"}

    raw = asyncio.run(
        hub_main.hub_query(
            hub_main.HubQueryRequest(
                query="not-json",
                mode="structured",
                model="sonar-pro",
                response_schema={"type": "object"},
            )
        )
    )
    assert raw.structured_data == {"raw_response": "not-json"}


def test_hub_query_openai_skip_and_execute(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_retrieve(self, request):
        return RetrievalResult(
            query=request["query"],
            mode=request["mode"],
            model_used=request["model"],
            response="retrieved",
            sources=["https://example.com"],
        )

    async def fake_synthesize(self, request, retrieval):
        return "synthesized", "gpt-custom"

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", fake_retrieve)
    skipped = asyncio.run(
        hub_main.hub_query(
            hub_main.HubQueryRequest(
                query="q",
                mode="news",
                model="sonar-pro",
                synthesis_provider="openai",
            )
        )
    )
    assert skipped.warnings == ["OpenAI synthesis requested but OPENAI_API_KEY is not configured."]

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(hub_main.OpenAISynthesizer, "synthesize", fake_synthesize)
    synthesized = asyncio.run(
        hub_main.hub_query(
            hub_main.HubQueryRequest(
                query="q",
                mode="news",
                model="sonar-pro",
                synthesis_provider="openai",
            )
        )
    )
    assert synthesized.answer == "synthesized"


def test_hub_query_provider_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    async def config_error(self, request):
        raise ProviderConfigurationError("PERPLEXITY_API_KEY not configured")

    async def response_error(self, request):
        raise ProviderResponseError("Perplexity endpoint is unreachable")

    async def synth_error(self, request, retrieval):
        raise ProviderResponseError("OpenAI endpoint is unreachable")

    async def synth_config_error(self, request, retrieval):
        raise ProviderConfigurationError("OPENAI_API_KEY not configured")

    async def ok_retrieve(self, request):
        return RetrievalResult(
            query=request["query"],
            mode=request["mode"],
            model_used=request["model"],
            response="retrieved",
            sources=[],
        )

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", config_error)
    with pytest.raises(hub_main.HTTPException) as excinfo:
        asyncio.run(hub_main.hub_query(hub_main.HubQueryRequest(query="q", mode="news", model="sonar-pro")))
    assert excinfo.value.status_code == 500

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", response_error)
    with pytest.raises(hub_main.HTTPException) as excinfo:
        asyncio.run(hub_main.hub_query(hub_main.HubQueryRequest(query="q", mode="news", model="sonar-pro")))
    assert excinfo.value.status_code == 502

    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", ok_retrieve)
    monkeypatch.setattr(hub_main.OpenAISynthesizer, "synthesize", synth_error)
    with pytest.raises(hub_main.HTTPException) as excinfo:
        asyncio.run(
            hub_main.hub_query(
                hub_main.HubQueryRequest(
                    query="q",
                    mode="news",
                    model="sonar-pro",
                    synthesis_provider="openai",
                )
            )
        )
    assert excinfo.value.status_code == 502

    monkeypatch.setattr(hub_main.OpenAISynthesizer, "synthesize", synth_config_error)
    with pytest.raises(hub_main.HTTPException) as excinfo:
        asyncio.run(
            hub_main.hub_query(
                hub_main.HubQueryRequest(
                    query="q",
                    mode="news",
                    model="sonar-pro",
                    synthesis_provider="openai",
                )
            )
        )
    assert excinfo.value.status_code == 500


def test_legacy_research_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_retrieve(self, request):
        response = request["query"]
        if request["mode"] == "structured":
            response = '{"value":"ok"}'
        return RetrievalResult(
            query=request["query"],
            mode=request["mode"],
            model_used=request["model"],
            response=response,
            sources=["https://example.com"],
        )

    monkeypatch.setattr(hub_main.PerplexityRetriever, "retrieve", fake_retrieve)
    news = asyncio.run(hub_main.research_news(query="latest", model="sonar-pro"))
    assert news.search_type == "news"

    domain = asyncio.run(
        hub_main.research_domain(
            query="papers",
            domains=["arxiv.org"],
            recency="week",
            model="sonar-pro",
        )
    )
    assert domain.search_type == "domain"

    academic = asyncio.run(hub_main.research_academic(query="evals", model="sonar-pro"))
    assert academic.search_type == "academic"

    legacy = asyncio.run(hub_main.research_search(query="legacy", model="sonar-pro"))
    assert legacy.search_type == "news"

    structured = asyncio.run(
        hub_main.research_structured(
            query="extract",
            schema={"type": "object"},
            model="sonar-pro",
        )
    )
    assert structured.structured_data == {"value": "ok"}
