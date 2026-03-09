from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
from typing import List, Dict, Any, Optional

app = FastAPI(
    title="Database MCP API",
    description="API for database operations (SQLite).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

DATABASE_FILE = "/data/database.db" # Mounted volume

def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]

class TableInfo(BaseModel):
    name: str

class ColumnInfo(BaseModel):
    name: str
    type: str

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnInfo]

@app.post("/db/execute", response_model=QueryResult)
async def execute_query(query: str, params: Optional[List[Any]] = None):
    """
    Execute SQL query on database.
    """
    if params is None:
        params = []
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        
        conn.close()
        return QueryResult(columns=columns, rows=rows)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/tables", response_model=List[TableInfo])
async def list_tables():
    """
    List all tables in database.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [TableInfo(name=row["name"]) for row in cursor.fetchall()]
        conn.close()
        return tables
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/schema/{table_name}", response_model=TableSchema)
async def describe_table(table_name: str):
    """
    Get table schema information.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = [ColumnInfo(name=row["name"], type=row["type"]) for row in cursor.fetchall()]
        conn.close()
        if not columns:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found or has no columns.")
        return TableSchema(table_name=table_name, columns=columns)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/db/sample/{table_name}", response_model=QueryResult)
async def get_sample_data(table_name: str, limit: int = 10):
    """
    Get sample data from table.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
        
        columns = [description[0] for description in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        
        conn.close()
        return QueryResult(columns=columns, rows=rows)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))