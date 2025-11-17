from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
import sqlite3
import re
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime

app = FastAPI(
    title="Database MCP API",
    description="API for database operations (SQLite) with security controls.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

DATABASE_FILE = "/data/database.db"  # Mounted volume

# Security configuration
MAX_QUERY_RESULTS = 10000  # Maximum rows to return
DEFAULT_SAMPLE_LIMIT = 10
MAX_SAMPLE_LIMIT = 1000

# SQL operation whitelist (allowed keywords in queries)
ALLOWED_OPERATIONS = {"SELECT", "PRAGMA"}
DANGEROUS_OPERATIONS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"}


@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper cleanup"""
    conn = sqlite3.connect(DATABASE_FILE, timeout=10.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def validate_table_name(table_name: str) -> str:
    """
    Validate table name to prevent SQL injection

    Args:
        table_name: Table name to validate

    Returns:
        Validated table name

    Raises:
        HTTPException: If table name is invalid
    """
    # Allow only alphanumeric characters and underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name: {table_name}. Only alphanumeric characters and underscores allowed."
        )

    # Additional check for SQLite system tables
    if table_name.startswith('sqlite_'):
        raise HTTPException(
            status_code=403,
            detail=f"Access to system table {table_name} is forbidden"
        )

    return table_name


def validate_query(query: str) -> None:
    """
    Validate SQL query to prevent dangerous operations

    Args:
        query: SQL query to validate

    Raises:
        HTTPException: If query contains dangerous operations
    """
    query_upper = query.upper().strip()

    # Check for dangerous operations
    for dangerous_op in DANGEROUS_OPERATIONS:
        if dangerous_op in query_upper:
            raise HTTPException(
                status_code=403,
                detail=f"Operation {dangerous_op} is not allowed. Only SELECT queries are permitted."
            )

    # Ensure query starts with allowed operation
    starts_with_allowed = any(query_upper.startswith(op) for op in ALLOWED_OPERATIONS)
    if not starts_with_allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Query must start with one of: {', '.join(ALLOWED_OPERATIONS)}"
        )


class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    truncated: bool = False

class TableInfo(BaseModel):
    name: str

class ColumnInfo(BaseModel):
    name: str
    type: str

class TableSchema(BaseModel):
    table_name: str
    columns: List[ColumnInfo]

@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return {
                "status": "healthy",
                "service": "Database MCP",
                "database": "SQLite",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {str(e)}")


@app.post("/db/execute", response_model=QueryResult)
async def execute_query(
    query: str,
    params: Optional[List[Any]] = None,
    max_rows: int = Query(1000, ge=1, le=MAX_QUERY_RESULTS, description="Maximum rows to return")
):
    """
    Execute SQL SELECT query on database with security validation.
    Only SELECT and PRAGMA queries are allowed.
    """
    if params is None:
        params = []

    try:
        # Validate query for dangerous operations
        validate_query(query)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)

            columns = [description[0] for description in cursor.description] if cursor.description else []

            # Fetch with limit to prevent memory issues
            all_rows = cursor.fetchall()
            total_rows = len(all_rows)
            truncated = total_rows > max_rows
            rows = [list(row) for row in all_rows[:max_rows]]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=total_rows,
                truncated=truncated
            )

    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.get("/db/tables", response_model=List[TableInfo])
async def list_tables():
    """
    List all tables in database.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [TableInfo(name=row["name"]) for row in cursor.fetchall()]
            return tables
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tables: {str(e)}")

@app.get("/db/schema/{table_name}", response_model=TableSchema)
async def describe_table(table_name: str):
    """
    Get table schema information with SQL injection protection.
    """
    try:
        # Validate table name to prevent SQL injection
        validated_table = validate_table_name(table_name)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Safely inject validated table name as identifier using SQLite quoting
            # lgtm[py/sql-injection] - False positive: validated_table is sanitized via regex validation
            cursor.execute(f'PRAGMA table_info("{validated_table}");')
            columns = [ColumnInfo(name=row["name"], type=row["type"]) for row in cursor.fetchall()]

            if not columns:
                raise HTTPException(
                    status_code=404,
                    detail=f"Table {table_name} not found or has no columns."
                )

            return TableSchema(table_name=validated_table, columns=columns)

    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get table schema: {str(e)}")

@app.get("/db/sample/{table_name}", response_model=QueryResult)
async def get_sample_data(
    table_name: str,
    limit: int = Query(DEFAULT_SAMPLE_LIMIT, ge=1, le=MAX_SAMPLE_LIMIT, description="Number of rows to return")
):
    """
    Get sample data from table with SQL injection protection.
    """
    try:
        # Validate table name to prevent SQL injection
        validated_table = validate_table_name(table_name)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Use parameterized query for limit
            # lgtm[py/sql-injection] - False positive: validated_table is sanitized via regex validation
            cursor.execute(f"SELECT * FROM {validated_table} LIMIT ?;", (limit,))

            columns = [description[0] for description in cursor.description] if cursor.description else []
            rows = [list(row) for row in cursor.fetchall()]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=False  # We're using LIMIT, so not truncated
            )

    except HTTPException:
        raise
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sample data: {str(e)}")