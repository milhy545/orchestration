import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, validator

app = FastAPI(
    title="Memory MCP API",
    description="API for memory storage and retrieval operations using PostgreSQL with security controls.",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# PostgreSQL configuration
DATABASE_URL = os.getenv(
    "MCP_DATABASE_URL",
    "postgresql://mcp_admin:mcp_secure_2024@postgresql:5432/mcp_unified",
)

# Security configuration
MAX_CONTENT_SIZE = 1 * 1024 * 1024  # 1MB per memory entry
MAX_LIST_LIMIT = 1000
MAX_SEARCH_LIMIT = 500
DEFAULT_LIST_LIMIT = 100
DEFAULT_SEARCH_LIMIT = 50


@contextmanager
def get_memory_connection():
    """Context manager for PostgreSQL database connections to ensure proper cleanup"""
    conn = None
    try:
        conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
        yield conn
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=500, detail=f"Database connection failed: {str(e)}"
        )
    finally:
        if conn:
            conn.close()


def ensure_table_exists():
    """Ensure the memory table exists"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS unified_memory (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        type VARCHAR(50) DEFAULT 'user',
                        importance REAL DEFAULT 0.5,
                        agent VARCHAR(100) DEFAULT 'claude-code',
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        metadata JSONB DEFAULT '{}'
                    )
                """
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500, detail=f"Table creation failed: {str(e)}"
            )


class MemoryEntry(BaseModel):
    content: str = Field(..., max_length=MAX_CONTENT_SIZE, description="Memory content")
    type: Optional[str] = Field("user", max_length=50)
    importance: Optional[float] = Field(0.5, ge=0.0, le=1.0)
    agent: Optional[str] = Field("claude-code", max_length=100)
    metadata: Optional[Dict[str, Any]] = {}

    @validator("content")
    def validate_content_size(cls, v):
        if len(v) > MAX_CONTENT_SIZE:
            raise ValueError(
                f"Content too large. Maximum size: {MAX_CONTENT_SIZE} bytes"
            )
        return v


class MemoryResponse(BaseModel):
    id: int
    content: str
    type: str
    importance: float
    agent: str
    timestamp: str
    metadata: Dict[str, Any]


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    ensure_table_exists()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        with get_memory_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                return {
                    "status": "healthy",
                    "service": "Memory MCP",
                    "database": "PostgreSQL",
                    "version": "2.1.0",
                    "timestamp": datetime.now().isoformat(),
                }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@app.post("/memory/store", response_model=Dict[str, Any])
async def store_memory(entry: MemoryEntry):
    """Store a memory entry with size validation"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    INSERT INTO unified_memory (content, type, importance, agent, metadata)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, content, type, importance, agent, timestamp, metadata
                """,
                    (
                        entry.content,
                        entry.type,
                        entry.importance,
                        entry.agent,
                        entry.metadata,
                    ),
                )
                result = cursor.fetchone()
                conn.commit()
                return {
                    "success": True,
                    "memory_id": result["id"],
                    "stored_at": result["timestamp"].isoformat(),
                }
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to store memory: {str(e)}"
            )


@app.get("/memory/list", response_model=List[MemoryResponse])
async def list_memories(
    limit: int = Query(
        DEFAULT_LIST_LIMIT,
        ge=1,
        le=MAX_LIST_LIMIT,
        description="Number of memories to return",
    ),
    offset: int = Query(0, ge=0, description="Number of memories to skip"),
):
    """List stored memories with pagination limits"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT id, content, type, importance, agent, timestamp, metadata
                    FROM unified_memory
                    ORDER BY timestamp DESC
                    LIMIT %s OFFSET %s
                """,
                    (limit, offset),
                )
                results = cursor.fetchall()

                memories = []
                for row in results:
                    memories.append(
                        MemoryResponse(
                            id=row["id"],
                            content=row["content"],
                            type=row["type"],
                            importance=row["importance"],
                            agent=row["agent"],
                            timestamp=row["timestamp"].isoformat(),
                            metadata=row["metadata"] or {},
                        )
                    )
                return memories
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to list memories: {str(e)}"
            )


@app.get("/memory/search")
async def search_memories(
    query: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(
        DEFAULT_SEARCH_LIMIT,
        ge=1,
        le=MAX_SEARCH_LIMIT,
        description="Maximum results to return",
    ),
):
    """Search memories by content with query validation"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                # Using parameterized query to prevent SQL injection
                cursor.execute(
                    """
                    SELECT id, content, type, importance, agent, timestamp, metadata
                    FROM unified_memory
                    WHERE content ILIKE %s
                    ORDER BY importance DESC, timestamp DESC
                    LIMIT %s
                """,
                    (f"%{query}%", limit),
                )
                results = cursor.fetchall()

                memories = []
                for row in results:
                    memories.append(
                        MemoryResponse(
                            id=row["id"],
                            content=row["content"],
                            type=row["type"],
                            importance=row["importance"],
                            agent=row["agent"],
                            timestamp=row["timestamp"].isoformat(),
                            metadata=row["metadata"] or {},
                        )
                    )
                return memories
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to search memories: {str(e)}"
            )


@app.delete("/memory/{memory_id}")
async def delete_memory(memory_id: int):
    """Delete a memory entry"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM unified_memory WHERE id = %s", (memory_id,))
                if cursor.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Memory not found")
                conn.commit()
                return {"success": True, "message": f"Memory {memory_id} deleted"}
        except HTTPException:
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(
                status_code=500, detail=f"Failed to delete memory: {str(e)}"
            )


@app.get("/memory/stats")
async def memory_stats():
    """Get memory statistics"""
    with get_memory_connection() as conn:
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT
                        COUNT(*) as total_memories,
                        AVG(importance) as avg_importance,
                        COUNT(DISTINCT agent) as unique_agents,
                        COUNT(DISTINCT type) as unique_types
                    FROM unified_memory
                """
                )
                stats = cursor.fetchone()
                return {
                    "total_memories": stats["total_memories"],
                    "average_importance": (
                        float(stats["avg_importance"])
                        if stats["avg_importance"]
                        else 0.0
                    ),
                    "unique_agents": stats["unique_agents"],
                    "unique_types": stats["unique_types"],
                }
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to get stats: {str(e)}"
            )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
