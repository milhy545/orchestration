import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)
from sentence_transformers import SentenceTransformer

app = FastAPI(
    title="Advanced Memory MCP API",
    description="Advanced memory storage with vector search via Qdrant and sentence-transformers.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration
DATABASE_URL = os.getenv(
    "MCP_DATABASE_URL",
    "postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified",
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-vector:6333")
MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384
COLLECTION_NAME = "advanced_memories"

# Globals initialized at startup
db_pool: Optional[asyncpg.Pool] = None
qdrant: Optional[QdrantClient] = None
model: Optional[SentenceTransformer] = None


def encode_text(text: str) -> List[float]:
    """Encode text into a vector using sentence-transformers."""
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


async def ensure_pg_table():
    """Create the advanced_memories table if it doesn't exist."""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS advanced_memories (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                category VARCHAR(100) DEFAULT 'general',
                metadata_json JSONB DEFAULT '{}',
                embedding_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)


def ensure_qdrant_collection():
    """Create the Qdrant collection if it doesn't exist."""
    collections = [c.name for c in qdrant.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


@app.on_event("startup")
async def startup_event():
    """Initialize connections and model on startup."""
    global db_pool, qdrant, model

    # Load embedding model
    try:
        model = SentenceTransformer(MODEL_NAME)
    except Exception as e:
        print(f"Warning: failed to load model: {e}")

    # Connect to Qdrant
    try:
        qdrant = QdrantClient(url=QDRANT_URL, timeout=10)
        ensure_qdrant_collection()
    except Exception as e:
        print(f"Warning: Qdrant connection failed: {e}")

    # Connect to PostgreSQL
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        await ensure_pg_table()
    except Exception as e:
        print(f"Warning: PostgreSQL connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()


# --- Health ---

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {"status": "healthy", "service": "advanced-memory-mcp", "version": "1.0.0"}
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

    status["model_loaded"] = model is not None
    status["timestamp"] = datetime.now().isoformat()
    return status


# --- MCP Tools API ---

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools."""
    return {
        "tools": [
            {
                "name": "store_memory",
                "description": "Store a memory with vector embedding in Qdrant and metadata in PostgreSQL",
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
                "description": "Find semantically similar memories using vector cosine similarity in Qdrant",
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
        ]
    }


@app.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    """Execute an MCP tool by name."""
    handlers = {
        "store_memory": handle_store_memory,
        "search_memories": handle_search_memories,
        "semantic_similarity": handle_semantic_similarity,
        "vector_search": handle_vector_search,
        "get_context": handle_get_context,
    }
    handler = handlers.get(request.name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.name}")
    try:
        result = await handler(request.arguments)
        return {"success": True, "result": result}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


# --- Tool Handlers ---

async def handle_store_memory(args: Dict[str, Any]) -> Dict[str, Any]:
    content = args.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    category = args.get("category", "general")
    metadata = args.get("metadata") or {}

    # Generate embedding
    if not model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded")
    vector = encode_text(content)

    # Generate unique ID for the Qdrant point
    embedding_id = str(uuid.uuid4())

    # Store vector in Qdrant
    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")
    qdrant.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            PointStruct(
                id=embedding_id,
                vector=vector,
                payload={"content": content, "category": category, "metadata": metadata},
            )
        ],
    )

    # Store metadata in PostgreSQL
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

    if not model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded")
    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")

    query_vector = encode_text(query)
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

    if not model:
        raise HTTPException(status_code=503, detail="Embedding model not loaded")
    if not qdrant:
        raise HTTPException(status_code=503, detail="Qdrant not available")

    query_vector = encode_text(query)

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


async def handle_get_context(args: Dict[str, Any]) -> Dict[str, Any]:
    topic = args.get("topic")
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")
    depth = min(args.get("depth", 3), 20)

    # Text search via PostgreSQL
    text_results = await handle_search_memories({"query": topic, "limit": depth})

    # Vector search via Qdrant
    vector_results = []
    if model and qdrant:
        vector_results = await handle_semantic_similarity(
            {"query": topic, "limit": depth, "threshold": 0.5}
        )

    # Deduplicate by content
    seen_contents = set()
    combined = []
    for item in vector_results + text_results:
        content = item.get("content", "")
        if content not in seen_contents:
            seen_contents.add(content)
            combined.append(item)

    return {
        "topic": topic,
        "text_matches": len(text_results),
        "vector_matches": len(vector_results),
        "combined_results": combined,
        "total_unique": len(combined),
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
