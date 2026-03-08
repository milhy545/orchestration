from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

app = FastAPI(
    title="Memory MCP API",
    description="API for memory storage and retrieval operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Use the existing memory database
MEMORY_DATABASE = "/home/orchestration/data/databases/unified_memory_forai.db"

def get_memory_connection():
    """Get connection to the existing memory database"""
    if not os.path.exists(MEMORY_DATABASE):
        raise HTTPException(status_code=500, detail="Memory database not found")
    
    conn = sqlite3.connect(MEMORY_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class MemoryEntry(BaseModel):
    content: str
    type: Optional[str] = "user"
    importance: Optional[float] = 0.5
    agent: Optional[str] = "claude-code"

class MemorySearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 10
    agent: Optional[str] = None
    type_filter: Optional[str] = None

class MemoryResponse(BaseModel):
    id: int
    content: str
    type: str
    importance: float
    created_at: str
    agent: str
    session_id: Optional[str] = None

class SearchResponse(BaseModel):
    memories: List[MemoryResponse]
    total_count: int

@app.post("/memory/store", response_model=Dict[str, Any])
async def store_memory(memory: MemoryEntry):
    """
    Store a memory entry in the database.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        
        # Generate session ID
        session_id = f"mcp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid()}"
        
        cursor.execute('''
            INSERT INTO memories (content, type, importance, session_id, agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (memory.content, memory.type, memory.importance, session_id, memory.agent))
        
        memory_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "memory_id": memory_id,
            "message": "Memory stored successfully"
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search", response_model=SearchResponse)
async def search_memories(search_query: MemorySearchQuery):
    """
    Search memories based on content.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        
        # Build query with filters
        base_query = "SELECT * FROM memories WHERE content LIKE ?"
        params = [f"%{search_query.query}%"]
        
        if search_query.agent:
            base_query += " AND agent = ?"
            params.append(search_query.agent)
            
        if search_query.type_filter:
            base_query += " AND type = ?"
            params.append(search_query.type_filter)
        
        base_query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(search_query.limit)
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM memories WHERE content LIKE ?"
        count_params = [f"%{search_query.query}%"]
        
        if search_query.agent:
            count_query += " AND agent = ?"
            count_params.append(search_query.agent)
            
        if search_query.type_filter:
            count_query += " AND type = ?"
            count_params.append(search_query.type_filter)
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        memories = [
            MemoryResponse(
                id=row["id"],
                content=row["content"],
                type=row["type"],
                importance=row["importance"],
                created_at=row["created_at"],
                agent=row["agent"],
                session_id=row["session_id"]
            )
            for row in rows
        ]
        
        return SearchResponse(memories=memories, total_count=total_count)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/list", response_model=SearchResponse)
async def list_memories(limit: int = 20, agent: Optional[str] = None):
    """
    List recent memories.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        
        base_query = "SELECT * FROM memories"
        params = []
        
        if agent:
            base_query += " WHERE agent = ?"
            params.append(agent)
        
        base_query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(base_query, params)
        rows = cursor.fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) FROM memories"
        count_params = []
        
        if agent:
            count_query += " WHERE agent = ?"
            count_params.append(agent)
            
        cursor.execute(count_query, count_params)
        total_count = cursor.fetchone()[0]
        
        conn.close()
        
        memories = [
            MemoryResponse(
                id=row["id"],
                content=row["content"],
                type=row["type"],
                importance=row["importance"],
                created_at=row["created_at"],
                agent=row["agent"],
                session_id=row["session_id"]
            )
            for row in rows
        ]
        
        return SearchResponse(memories=memories, total_count=total_count)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/stats", response_model=Dict[str, Any])
async def get_memory_stats():
    """
    Get memory database statistics.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        
        # Total memories
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        # Memories by agent
        cursor.execute("SELECT agent, COUNT(*) FROM memories GROUP BY agent")
        agent_counts = dict(cursor.fetchall())
        
        # Memories by type
        cursor.execute("SELECT type, COUNT(*) FROM memories GROUP BY type")
        type_counts = dict(cursor.fetchall())
        
        # Recent activity (last 24 hours)
        cursor.execute("SELECT COUNT(*) FROM memories WHERE created_at > datetime('now', '-1 day')")
        recent_activity = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_memories": total_memories,
            "agent_counts": agent_counts,
            "type_counts": type_counts,
            "recent_activity_24h": recent_activity,
            "database_path": MEMORY_DATABASE
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/memory/{memory_id}", response_model=Dict[str, Any])
async def delete_memory(memory_id: int):
    """
    Delete a specific memory entry.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Memory not found")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Memory {memory_id} deleted successfully"
        }
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    try:
        conn = get_memory_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
