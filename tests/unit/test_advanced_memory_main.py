from __future__ import annotations

import importlib.util
import sys
import types
from dataclasses import dataclass
from pathlib import Path

import pytest


PROJECT_ROOT = Path("/home/orchestration")
ADVANCED_MEMORY_DIR = PROJECT_ROOT / "mcp-servers" / "advanced-memory-mcp"


def _import_module(module_name: str, path: Path):
    if str(ADVANCED_MEMORY_DIR) not in sys.path:
        sys.path.insert(0, str(ADVANCED_MEMORY_DIR))
    if "asyncpg" not in sys.modules:
        asyncpg_stub = types.ModuleType("asyncpg")
        asyncpg_stub.Pool = object
        sys.modules["asyncpg"] = asyncpg_stub
    if "sentence_transformers" not in sys.modules:
        sentence_stub = types.ModuleType("sentence_transformers")
        class SentenceTransformer:
            def __init__(self, *args, **kwargs):
                self.args = args
            def encode(self, text, normalize_embeddings=True):
                return [0.1, 0.2, 0.3]
        sentence_stub.SentenceTransformer = SentenceTransformer
        sys.modules["sentence_transformers"] = sentence_stub
    if "qdrant_client" not in sys.modules:
        qdrant_stub = types.ModuleType("qdrant_client")
        class QdrantClient:
            def __init__(self, *args, **kwargs):
                pass
        qdrant_stub.QdrantClient = QdrantClient
        sys.modules["qdrant_client"] = qdrant_stub
    if "qdrant_client.http.models" not in sys.modules:
        models_stub = types.ModuleType("qdrant_client.http.models")
        class Distance:
            COSINE = "cosine"
        class MatchValue:
            def __init__(self, value):
                self.value = value
        class FieldCondition:
            def __init__(self, key, match):
                self.key = key
                self.match = match
        class Filter:
            def __init__(self, must):
                self.must = must
        class PointStruct:
            def __init__(self, id, vector, payload):
                self.id = id
                self.vector = vector
                self.payload = payload
        class VectorParams:
            def __init__(self, size, distance):
                self.size = size
                self.distance = distance
        models_stub.Distance = Distance
        models_stub.MatchValue = MatchValue
        models_stub.FieldCondition = FieldCondition
        models_stub.Filter = Filter
        models_stub.PointStruct = PointStruct
        models_stub.VectorParams = VectorParams
        http_stub = types.ModuleType("qdrant_client.http")
        http_stub.models = models_stub
        sys.modules["qdrant_client.http"] = http_stub
        sys.modules["qdrant_client.http.models"] = models_stub
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


main = _import_module("advanced_memory_main_test", ADVANCED_MEMORY_DIR / "main.py")


class FakeProviderClient:
    def __init__(self) -> None:
        self.embedded_documents: list[str] = []
        self.embedded_queries: list[str] = []
        self.generated_queries: list[tuple[str, list[dict[str, object]]]] = []

    async def embed_document(self, text: str) -> list[float]:
        self.embedded_documents.append(text)
        return [0.1, 0.2, 0.3]

    async def embed_query(self, text: str) -> list[float]:
        self.embedded_queries.append(text)
        return [0.3, 0.2, 0.1]

    async def generate_answer(self, query: str, context_items: list[dict[str, object]]) -> str:
        self.generated_queries.append((query, context_items))
        return "mocked answer"


@dataclass
class FakeCollection:
    name: str


class FakeCollectionsResponse:
    def __init__(self, names: list[str]) -> None:
        self.collections = [FakeCollection(name=name) for name in names]


class FakeHit:
    def __init__(self, content: str, category: str, score: float, embedding_id: str) -> None:
        self.payload = {"content": content, "category": category, "metadata": {"source": "mock"}}
        self.score = score
        self.id = embedding_id


class FakeQdrant:
    def __init__(self) -> None:
        self.collections: list[str] = []
        self.created_sizes: list[int] = []
        self.upserts: list[object] = []
        self.last_search_args: dict[str, object] | None = None

    def get_collections(self) -> FakeCollectionsResponse:
        return FakeCollectionsResponse(self.collections)

    def create_collection(self, collection_name: str, vectors_config) -> None:
        self.collections.append(collection_name)
        self.created_sizes.append(vectors_config.size)

    def upsert(self, collection_name: str, points) -> None:
        self.upserts.append((collection_name, points))

    def search(self, collection_name: str, query_vector, limit: int, score_threshold=None, query_filter=None):
        self.last_search_args = {
            "collection_name": collection_name,
            "query_vector": query_vector,
            "limit": limit,
            "score_threshold": score_threshold,
            "query_filter": query_filter,
        }
        return [
            FakeHit("Vector memory", "research", 0.91, "emb-1"),
            FakeHit("Second memory", "notes", 0.76, "emb-2"),
        ]


class FakeConn:
    def __init__(self, rows=None) -> None:
        self.rows = rows or []
        self.executed: list[tuple[str, tuple[object, ...]]] = []

    async def execute(self, query: str) -> None:
        self.executed.append((query, ()))

    async def fetchval(self, query: str) -> int:
        self.executed.append((query, ()))
        return 1

    async def fetchrow(self, query: str, *args):
        self.executed.append((query, args))
        return {"id": 7, "created_at": __import__("datetime").datetime(2026, 3, 8, 12, 0, 0)}

    async def fetch(self, query: str, *args):
        self.executed.append((query, args))
        return self.rows


class FakeAcquire:
    def __init__(self, conn: FakeConn) -> None:
        self.conn = conn

    async def __aenter__(self) -> FakeConn:
        return self.conn

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class FakePool:
    def __init__(self, rows=None) -> None:
        self.conn = FakeConn(rows=rows)

    def acquire(self) -> FakeAcquire:
        return FakeAcquire(self.conn)

    async def close(self) -> None:
        return None


def _install_runtime_fakes(rows=None) -> tuple[FakeProviderClient, FakeQdrant, FakePool]:
    provider = FakeProviderClient()
    qdrant = FakeQdrant()
    pool = FakePool(rows=rows)
    main.provider_client = provider
    main.qdrant = qdrant
    main.db_pool = pool
    main.embedding_model = object()
    main.runtime_config = main.RuntimeConfig.from_env()
    main.runtime_config.embedding_provider = "gemini"
    main.runtime_config.generation_provider = "inception"
    return provider, qdrant, pool


@pytest.mark.asyncio
async def test_store_memory_uses_provider_embeddings(monkeypatch) -> None:
    monkeypatch.setattr(main.uuid, "uuid4", lambda: "fixed-uuid")
    provider, qdrant, pool = _install_runtime_fakes()

    result = await main.handle_store_memory(
        {"content": "Stored memory", "category": "research", "metadata": {"topic": "ai"}}
    )

    assert provider.embedded_documents == ["Stored memory"]
    assert result["embedding_id"] == "fixed-uuid"
    assert result["embedding_provider"] == "gemini"
    assert qdrant.created_sizes == [3]
    assert qdrant.upserts
    assert pool.conn.executed


@pytest.mark.asyncio
async def test_answer_with_context_combines_results_and_calls_generation(monkeypatch) -> None:
    rows = [
        {
            "id": 1,
            "content": "Vector memory",
            "category": "research",
            "metadata_json": '{"source": "db"}',
            "embedding_id": "emb-db-1",
            "created_at": __import__("datetime").datetime(2026, 3, 8, 12, 0, 0),
        },
        {
            "id": 2,
            "content": "DB only memory",
            "category": "notes",
            "metadata_json": '{"source": "db"}',
            "embedding_id": "emb-db-2",
            "created_at": __import__("datetime").datetime(2026, 3, 8, 12, 1, 0),
        },
    ]
    provider, qdrant, _pool = _install_runtime_fakes(rows=rows)
    monkeypatch.setattr(main, "COLLECTION_NAME", "advanced_memories")

    result = await main.handle_answer_with_context({"query": "What do we know?", "limit": 3, "threshold": 0.4})

    assert provider.embedded_queries == ["What do we know?"]
    assert result["generation_provider"] == "inception"
    assert result["answer"] == "mocked answer"
    assert result["total_unique"] == 3
    assert provider.generated_queries
    generated_query, context_items = provider.generated_queries[0]
    assert generated_query == "What do we know?"
    assert len(context_items) == 3
    assert qdrant.last_search_args is not None


@pytest.mark.asyncio
async def test_health_reports_provider_configuration() -> None:
    _provider, _qdrant, _pool = _install_runtime_fakes()
    main.runtime_config.embedding_provider = "ollama"
    main.runtime_config.generation_provider = "openai_compatible"
    main.runtime_config.ollama_base_url = "http://192.168.0.55:11434"
    main.runtime_config.inception_api_key = ""
    main.runtime_config.gemini_api_key = "set"
    main.runtime_config.openai_compat_base_url = "http://192.168.0.77:1234/v1"

    result = await main.health_check()

    assert result["status"] == "healthy"
    assert result["service"] == "advanced-memory-mcp"
    assert result["providers"]["embedding"] == "ollama"
    assert result["providers"]["generation"] == "openai_compatible"
    assert result["providers"]["gemini_configured"] is True
    assert result["providers"]["openai_compatible_configured"] is True
    assert result["providers"]["ollama_configured"] is True
    assert "ollama_base_url" not in result["providers"]


@pytest.mark.asyncio
async def test_tools_list_exposes_answer_with_context() -> None:
    result = await main.list_tools()
    names = [tool["name"] for tool in result["tools"]]
    assert "answer_with_context" in names
