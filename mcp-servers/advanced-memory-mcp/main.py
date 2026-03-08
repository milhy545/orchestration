import json
import os
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from providers import ProviderClient, ProviderError, RuntimeConfig

DATABASE_URL = os.getenv("MCP_DATABASE_URL", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-vector:6333")
COLLECTION_NAME = os.getenv("ADVANCED_MEMORY_COLLECTION", "advanced_memories")

db_pool: Optional[asyncpg.Pool] = None
qdrant: Any | None = None
embedding_model: Any | None = None
runtime_config: RuntimeConfig = RuntimeConfig.from_env()
provider_client: Optional[ProviderClient] = None


@dataclass
class VectorParams:
    size: int
    distance: str


@dataclass
class MatchValue:
    value: str


@dataclass
class FieldCondition:
    key: str
    match: MatchValue


@dataclass
class Filter:
    must: List[FieldCondition]


@dataclass
class PointStruct:
    id: str
    vector: List[float]
    payload: Dict[str, Any]


@dataclass
class CollectionInfo:
    name: str


@dataclass
class CollectionsResponse:
    collections: List[CollectionInfo]


@dataclass
class SearchHit:
    id: str
    score: float
    payload: Dict[str, Any]


class HttpQdrantClient:
    def __init__(self, url: str, timeout: int = 10) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(f"{self.url}{path}", data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Qdrant HTTP {exc.code}: {detail or exc.reason}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Qdrant unreachable: {exc.reason}") from exc

    def get_collections(self) -> CollectionsResponse:
        payload = self._request("GET", "/collections")
        items = payload.get("result", {}).get("collections", [])
        return CollectionsResponse(collections=[CollectionInfo(name=item["name"]) for item in items])

    def create_collection(self, collection_name: str, vectors_config: VectorParams) -> None:
        self._request(
            "PUT",
            f"/collections/{collection_name}",
            {
                "vectors": {
                    "size": vectors_config.size,
                    "distance": str(vectors_config.distance).capitalize(),
                }
            },
        )

    def upsert(self, collection_name: str, points: List[PointStruct]) -> None:
        self._request(
            "PUT",
            f"/collections/{collection_name}/points?wait=true",
            {
                "points": [
                    {"id": point.id, "vector": point.vector, "payload": point.payload}
                    for point in points
                ]
            },
        )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int,
        score_threshold: float | None = None,
        query_filter: Filter | None = None,
    ) -> List[SearchHit]:
        payload: dict[str, Any] = {"vector": query_vector, "limit": limit}
        if score_threshold is not None:
            payload["score_threshold"] = score_threshold
        if query_filter is not None:
            payload["filter"] = {
                "must": [
                    {"key": condition.key, "match": {"value": condition.match.value}}
                    for condition in query_filter.must
                ]
            }
        response = self._request("POST", f"/collections/{collection_name}/points/search", payload)
        hits = response.get("result", [])
        return [
            SearchHit(
                id=str(hit.get("id", "")),
                score=float(hit.get("score", 0.0)),
                payload=hit.get("payload", {}) or {},
            )
            for hit in hits
        ]


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


def encode_local_text(text: str) -> List[float]:
    if embedding_model is None:
        raise ProviderError("Local embedding model not loaded")
    embedding = embedding_model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def get_provider_client() -> ProviderClient:
    if provider_client is None:
        raise HTTPException(status_code=503, detail="Provider client not initialized")
    return provider_client


async def ensure_pg_table() -> None:
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS advanced_memories (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'general',
                metadata_json JSONB DEFAULT '{}',
                embedding_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )


def ensure_qdrant_collection(vector_size: int) -> None:
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=vector_size, distance="cosine"),
        )


async def _startup() -> None:
    global db_pool, qdrant, embedding_model, runtime_config, provider_client

    runtime_config = RuntimeConfig.from_env()
    provider_client = ProviderClient(runtime_config, local_embedder=encode_local_text)

    if runtime_config.embedding_provider == "local":
        try:
            from sentence_transformers import SentenceTransformer

            embedding_model = SentenceTransformer(runtime_config.local_embedding_model)
        except ImportError:
            print(
                "Warning: local embedding provider selected but sentence-transformers is not installed"
            )
        except Exception as exc:
            print(f"Warning: failed to load local embedding model: {exc}")

    try:
        qdrant = HttpQdrantClient(url=QDRANT_URL, timeout=10)
    except Exception as exc:
        print(f"Warning: Qdrant connection failed: {exc}")

    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        await ensure_pg_table()
    except Exception as exc:
        print(f"Warning: PostgreSQL connection failed: {exc}")


async def _shutdown() -> None:
    if db_pool:
        await db_pool.close()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await _startup()
    try:
        yield
    finally:
        await _shutdown()


app = FastAPI(
    title="Advanced Memory MCP API",
    description="Advanced memory storage with vector search and configurable embedding/generation providers.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    status = {"status": "healthy", "service": "advanced-memory-mcp", "version": "2.0.0"}
    try:
        if db_pool:
            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            status["database"] = "connected"
        else:
            status["database"] = "disconnected"
    except Exception:
        status["database"] = "error"

    try:
        if qdrant:
            qdrant.get_collections()
            status["qdrant"] = "connected"
        else:
            status["qdrant"] = "disconnected"
    except Exception:
        status["qdrant"] = "error"

    status["providers"] = {
        "embedding": runtime_config.embedding_provider,
        "generation": runtime_config.generation_provider,
        "local_model_loaded": embedding_model is not None,
        "gemini_configured": bool(runtime_config.gemini_api_key),
        "inception_configured": bool(runtime_config.inception_api_key),
        "openai_compatible_configured": bool(runtime_config.openai_compat_base_url),
        "ollama_configured": bool(runtime_config.ollama_base_url),
    }
    status["timestamp"] = datetime.now().isoformat()
    return status


@app.get("/tools/list")
async def list_tools() -> Dict[str, Any]:
    return {
        "tools": [
            {
                "name": "store_memory",
                "description": "Store a memory with provider-backed embedding in Qdrant and metadata in PostgreSQL",
                "parameters": {
                    "content": "string (required, the memory text)",
                    "category": "string (optional, default 'general')",
                    "metadata": "object (optional, additional metadata)",
                },
            },
            {
                "name": "search_memories",
                "description": "Search memories by text content using PostgreSQL ILIKE (backward compatible)",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 5, max results)",
                },
            },
            {
                "name": "semantic_similarity",
                "description": "Find semantically similar memories using configured embedding provider and Qdrant",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 5)",
                    "threshold": "float (optional, default 0.7, minimum similarity score)",
                },
            },
            {
                "name": "vector_search",
                "description": "Full vector search with optional category filter via Qdrant",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 10)",
                    "category": "string (optional, filter by category)",
                },
            },
            {
                "name": "get_context",
                "description": "Retrieve related memories combining text and vector search",
                "parameters": {
                    "topic": "string (required, the topic to get context for)",
                    "depth": "integer (optional, default 3, number of results per method)",
                },
            },
            {
                "name": "answer_with_context",
                "description": "Answer a query from stored memories using the configured generation provider",
                "parameters": {
                    "query": "string (required, question to answer)",
                    "limit": "integer (optional, default 5)",
                    "threshold": "float (optional, default 0.5)",
                },
            },
        ]
    }


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest) -> Dict[str, Any]:
    handlers = {
        "store_memory": handle_store_memory,
        "search_memories": handle_search_memories,
        "semantic_similarity": handle_semantic_similarity,
        "vector_search": handle_vector_search,
        "get_context": handle_get_context,
        "answer_with_context": handle_answer_with_context,
    }
    handler = handlers.get(request.name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.name}")
    try:
        result = await handler(request.arguments)
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except ProviderError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(exc)}") from exc


async def handle_store_memory(args: Dict[str, Any]) -> Dict[str, Any]:
    content = args.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    category = args.get("category", "general")
    metadata = args.get("metadata") or {}
    client = get_provider_client()
    vector = await client.embed_document(content)

    embedding_id = str(uuid.uuid4())

    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    ensure_qdrant_collection(len(vector))
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=embedding_id,
                vector=vector,
                payload={
                    "content": content,
                    "category": category,
                    "metadata": metadata,
                    "embedding_provider": runtime_config.embedding_provider,
                },
            )
        ],
    )

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO advanced_memories (content, category, metadata_json, embedding_id)
            VALUES ($1, $2, $3, $4)
            RETURNING id, created_at
            """,
            content,
            category,
            json.dumps(metadata),
            embedding_id,
        )

    return {
        "memory_id": row["id"],
        "embedding_id": embedding_id,
        "category": category,
        "embedding_provider": runtime_config.embedding_provider,
        "stored_at": row["created_at"].isoformat(),
    }


async def handle_search_memories(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = args.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = min(args.get("limit", 5), 100)

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database not available")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id, content, category, metadata_json, embedding_id, created_at
            FROM advanced_memories
            WHERE content ILIKE $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            f"%{query}%",
            limit,
        )

    return [
        {
            "id": row["id"],
            "content": row["content"],
            "category": row["category"],
            "metadata": json.loads(row["metadata_json"]) if row["metadata_json"] else {},
            "created_at": row["created_at"].isoformat(),
        }
        for row in rows
    ]


async def handle_semantic_similarity(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = args.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = min(args.get("limit", 5), 100)
    threshold = args.get("threshold", 0.7)

    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")

    client = get_provider_client()
    query_vector = await client.embed_query(query)
    ensure_qdrant_collection(len(query_vector))
    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        score_threshold=threshold,
    )

    return [
        {
            "content": hit.payload.get("content", ""),
            "category": hit.payload.get("category", ""),
            "metadata": hit.payload.get("metadata", {}),
            "similarity_score": round(hit.score, 4),
            "embedding_id": hit.id,
        }
        for hit in results
    ]


async def handle_vector_search(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = args.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = min(args.get("limit", 10), 100)
    category = args.get("category")

    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")

    client = get_provider_client()
    query_vector = await client.embed_query(query)
    ensure_qdrant_collection(len(query_vector))

    search_filter = None
    if category:
        search_filter = Filter(
            must=[FieldCondition(key="category", match=MatchValue(value=category))]
        )

    results = qdrant.search(
        collection_name=COLLECTION_NAME,
        query_vector=query_vector,
        limit=limit,
        query_filter=search_filter,
    )

    return [
        {
            "content": hit.payload.get("content", ""),
            "category": hit.payload.get("category", ""),
            "metadata": hit.payload.get("metadata", {}),
            "similarity_score": round(hit.score, 4),
            "embedding_id": hit.id,
        }
        for hit in results
    ]


def _deduplicate_results(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen_contents = set()
    combined = []
    for item in items:
        content = item.get("content", "")
        if content and content not in seen_contents:
            seen_contents.add(content)
            combined.append(item)
    return combined


async def handle_get_context(args: Dict[str, Any]) -> Dict[str, Any]:
    topic = args.get("topic")
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    depth = min(args.get("depth", 3), 20)

    text_results = await handle_search_memories({"query": topic, "limit": depth})
    vector_results = []
    if qdrant and provider_client is not None:
        try:
            vector_results = await handle_semantic_similarity(
                {"query": topic, "limit": depth, "threshold": 0.5}
            )
        except HTTPException:
            vector_results = []

    combined = _deduplicate_results(vector_results + text_results)
    return {
        "topic": topic,
        "text_matches": len(text_results),
        "vector_matches": len(vector_results),
        "combined_results": combined,
        "total_unique": len(combined),
    }


async def handle_answer_with_context(args: Dict[str, Any]) -> Dict[str, Any]:
    query = args.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = min(args.get("limit", 5), 20)
    threshold = args.get("threshold", 0.5)

    text_results = await handle_search_memories({"query": query, "limit": limit})
    vector_results = await handle_semantic_similarity(
        {"query": query, "limit": limit, "threshold": threshold}
    )
    combined = _deduplicate_results(vector_results + text_results)
    answer = await get_provider_client().generate_answer(query, combined)
    return {
        "query": query,
        "answer": answer,
        "generation_provider": runtime_config.generation_provider,
        "context_results": combined,
        "total_unique": len(combined),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
