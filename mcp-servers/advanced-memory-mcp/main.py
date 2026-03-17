import json
import os
import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("advanced-memory-mcp")

app = FastAPI(
    title="Advanced Memory MCP API",
    description="Advanced memory storage with vector search via Qdrant REST and external embeddings.",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuration
DATABASE_URL = os.getenv(
    "MCP_DATABASE_URL",
    "postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified",
)
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant-vector:6333").rstrip('/')
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
EMBEDDING_DIM = 768  # Gemini text-embedding-004 uses 768 dimensions
COLLECTION_NAME = "advanced_memories"

# Globals initialized at startup
db_pool: Optional[asyncpg.Pool] = None
http_client: Optional[httpx.AsyncClient] = None


async def encode_text(text: str) -> List[float]:
    """Encode text into a vector using external Gemini API."""
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set, returning dummy embedding")
        return [0.0] * EMBEDDING_DIM
        
    url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={GEMINI_API_KEY}"
    payload = {
        "model": "models/text-embedding-004",
        "content": {
            "parts": [{"text": text}]
        }
    }
    
    try:
        response = await http_client.post(url, json=payload, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        return data.get("embedding", {}).get("values", [0.0] * EMBEDDING_DIM)
    except Exception as e:
        logger.error(f"Error calling embedding API: {e}")
        return [0.0] * EMBEDDING_DIM


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


async def ensure_qdrant_collection():
    """Create the Qdrant collection via REST if it doesn't exist."""
    try:
        # Check if collection exists
        res = await http_client.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}")
        if res.status_code == 404:
            logger.info(f"Creating Qdrant collection: {COLLECTION_NAME}")
            create_payload = {
                "vectors": {
                    "size": EMBEDDING_DIM,
                    "distance": "Cosine"
                }
            }
            await http_client.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", json=create_payload)
    except Exception as e:
        logger.error(f"Failed to ensure Qdrant collection: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    global db_pool, http_client

    http_client = httpx.AsyncClient()

    # Ensure Qdrant collection
    await ensure_qdrant_collection()

    # Connect to PostgreSQL
    try:
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
        await ensure_pg_table()
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    if db_pool:
        await db_pool.close()
    if http_client:
        await http_client.aclose()


# --- Health ---


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    status = {"status": "healthy", "service": "advanced-memory-mcp", "version": "1.1.0"}
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
        res = await http_client.get(f"{QDRANT_URL}/collections")
        if res.is_success:
            status["qdrant"] = "connected"
        else:
            status["qdrant"] = f"error ({res.status_code})"
    except Exception:
        status["qdrant"] = "disconnected"

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
                "description": "Search memories by text content using PostgreSQL ILIKE",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 5, max results)",
                },
            },
            {
                "name": "semantic_similarity",
                "description": "Find semantically similar memories using vector cosine similarity",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 5)",
                    "threshold": "float (optional, default 0.7, minimum similarity score)",
                },
            },
            {
                "name": "vector_search",
                "description": "Full vector search with optional category filter",
                "parameters": {
                    "query": "string (required, search query)",
                    "limit": "integer (optional, default 10)",
                    "category": "string (optional, filter by category)",
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
    }
    handler = handlers.get(request.name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.name}")
    try:
        result = await handler(request.arguments)
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Tool {request.name} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- Tool Handlers ---


async def handle_store_memory(args: Dict[str, Any]) -> Dict[str, Any]:
    content = args.get("content")
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    category = args.get("category", "general")
    metadata = args.get("metadata") or {}

    # Generate embedding
    vector = await encode_text(content)
    embedding_id = str(uuid.uuid4())

    # Store vector in Qdrant via REST
    point_payload = {
        "points": [
            {
                "id": embedding_id,
                "vector": vector,
                "payload": {
                    "content": content,
                    "category": category,
                    "metadata": metadata,
                }
            }
        ]
    }
    
    res = await http_client.put(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points?wait=true", json=point_payload)
    res.raise_for_status()

    # Store metadata in PostgreSQL
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

    query_vector = await encode_text(query)
    
    search_payload = {
        "vector": query_vector,
        "limit": limit,
        "score_threshold": threshold,
        "with_payload": True
    }
    
    res = await http_client.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json=search_payload)
    res.raise_for_status()
    results = res.json().get("result", [])

    return [
        {
            "content": hit.get("payload", {}).get("content", ""),
            "category": hit.get("payload", {}).get("category", ""),
            "metadata": hit.get("payload", {}).get("metadata", {}),
            "similarity_score": round(hit.get("score", 0.0), 4),
            "embedding_id": hit.get("id"),
        }
        for hit in results
    ]


async def handle_vector_search(args: Dict[str, Any]) -> List[Dict[str, Any]]:
    query = args.get("query")
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    limit = min(args.get("limit", 10), 100)
    category = args.get("category")

    query_vector = await encode_text(query)

    search_payload = {
        "vector": query_vector,
        "limit": limit,
        "with_payload": True
    }
    
    if category:
        search_payload["filter"] = {
            "must": [{"key": "category", "match": {"value": category}}]
        }

    res = await http_client.post(f"{QDRANT_URL}/collections/{COLLECTION_NAME}/points/search", json=search_payload)
    res.raise_for_status()
    results = res.json().get("result", [])

    return [
        {
            "content": hit.get("payload", {}).get("content", ""),
            "category": hit.get("payload", {}).get("category", ""),
            "metadata": hit.get("payload", {}).get("metadata", {}),
            "similarity_score": round(hit.get("score", 0.0), 4),
            "embedding_id": hit.get("id"),
        }
        for hit in results
    ]


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MCP_SERVER_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
