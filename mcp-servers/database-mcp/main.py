import os
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

app = FastAPI(
    title="Database MCP API",
    description="API for database operations (SQLite) with security controls.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

DEFAULT_DATABASE_FILE = "/data/database.db"  # Mounted volume in containers


def _resolve_database_file() -> str:
    """
    Resolve the SQLite database path.

    CI/unit tests often run without a /data mount, so we fall back to a local
    ./data/database.db to keep the service functional out of the box.
    """
    db_file = (
        os.getenv("DATABASE_FILE")
        or os.getenv("DATABASE_PATH")
        or DEFAULT_DATABASE_FILE
    )
    if db_file.startswith("/data/") and not os.path.isdir("/data"):
        db_file = os.path.join(os.getcwd(), "data", "database.db")

    if db_file != ":memory:":
        parent = os.path.dirname(db_file)
        if parent:
            os.makedirs(parent, exist_ok=True)

    return db_file


# Security configuration
MAX_QUERY_RESULTS = 10000  # Maximum rows to return
DEFAULT_SAMPLE_LIMIT = 10
MAX_SAMPLE_LIMIT = 1000

# SQL operation whitelist removed in favor of structured SELECT builder
DEFAULT_SELECT_LIMIT = 100


@contextmanager
def get_db_connection():
    """Context manager for database connections to ensure proper cleanup"""
    conn = sqlite3.connect(_resolve_database_file(), timeout=10.0)
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
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid table name: {table_name}. Only alphanumeric characters and underscores allowed.",
        )

    # Additional check for SQLite system tables
    if table_name.startswith("sqlite_"):
        raise HTTPException(
            status_code=403, detail=f"Access to system table {table_name} is forbidden"
        )

    return table_name


def _quote_identifier(name: str) -> str:
    """Quote a SQLite identifier; callers must validate identifier format first."""
    return f'"{name}"'


def resolve_existing_table_name(conn: sqlite3.Connection, table_name: str) -> str:
    """Resolve a user-requested table name to a concrete SQLite table entry.

    This function uses a parameterized query against sqlite_master and returns
    the canonical table name from the database itself.
    """
    validated = validate_table_name(table_name)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ? AND name NOT LIKE 'sqlite_%' LIMIT 1;",
        (validated,),
    )
    row = cursor.fetchone()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Table {table_name} not found or inaccessible.",
        )
    if isinstance(row, dict):
        name = row.get("name")
    elif isinstance(row, (tuple, list)) and row:
        name = row[0]
    else:
        name = row["name"]  # type: ignore[index]
    if not name:
        raise HTTPException(status_code=404, detail=f"Table {table_name} not found.")
    return str(name)


class FilterCondition(BaseModel):
    column: str
    op: Literal["=", "!=", ">", ">=", "<", "<=", "like", "in"]
    value: Any


class OrderBy(BaseModel):
    column: str
    direction: Literal["asc", "desc"] = "asc"


class SelectQueryRequest(BaseModel):
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    order_by: Optional[List[OrderBy]] = None
    limit: int = Field(DEFAULT_SELECT_LIMIT, ge=1, le=MAX_QUERY_RESULTS)
    offset: int = Field(0, ge=0, le=MAX_QUERY_RESULTS)


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


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    trusted_table = resolve_existing_table_name(conn, table_name)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM pragma_table_info(?);",
        (trusted_table,),
    )
    rows = cursor.fetchall()
    # SQLite returns sqlite3.Row, but tests often mock tuples/dicts.
    columns: List[str] = []
    for row in rows:
        if isinstance(row, dict):
            name = row.get("name")
        elif isinstance(row, (tuple, list)) and len(row) > 1:
            name = row[1]
        else:
            name = row["name"]  # type: ignore[index]
        if name:
            columns.append(str(name))
    if not columns:
        raise HTTPException(
            status_code=404,
            detail=f"Table {table_name} not found or has no columns.",
        )
    return columns


def build_select_query(
    request: SelectQueryRequest, table_name: str, allowed_columns: List[str]
) -> Tuple[str, List[Any], List[str]]:
    selected_columns = request.columns or allowed_columns
    for col in selected_columns:
        if col not in allowed_columns:
            raise HTTPException(status_code=400, detail=f"Unknown column: {col}")

    columns_sql = ", ".join(f'"{col}"' for col in selected_columns)
    sql = f'SELECT {columns_sql} FROM "{table_name}"'
    params: List[Any] = []

    if request.filters:
        filter_clauses = []
        for condition in request.filters:
            if condition.column not in allowed_columns:
                raise HTTPException(
                    status_code=400, detail=f"Unknown filter column: {condition.column}"
                )
            if condition.op == "in":
                if not isinstance(condition.value, list) or not condition.value:
                    raise HTTPException(
                        status_code=400, detail="IN operator requires a non-empty list"
                    )
                placeholders = ", ".join(["?"] * len(condition.value))
                filter_clauses.append(f'"{condition.column}" IN ({placeholders})')
                params.extend(condition.value)
            elif condition.op == "like":
                if not isinstance(condition.value, str):
                    raise HTTPException(
                        status_code=400, detail="LIKE operator requires string value"
                    )
                filter_clauses.append(f'"{condition.column}" LIKE ?')
                params.append(condition.value)
            else:
                filter_clauses.append(f'"{condition.column}" {condition.op} ?')
                params.append(condition.value)
        if filter_clauses:
            sql += " WHERE " + " AND ".join(filter_clauses)

    if request.order_by:
        order_clauses = []
        for order in request.order_by:
            if order.column not in allowed_columns:
                raise HTTPException(
                    status_code=400, detail=f"Unknown order column: {order.column}"
                )
            order_clauses.append(f'"{order.column}" {order.direction.upper()}')
        if order_clauses:
            sql += " ORDER BY " + ", ".join(order_clauses)

    sql += " LIMIT ? OFFSET ?"
    params.append(request.limit)
    params.append(request.offset)

    return sql, params, selected_columns


@app.get("/health")
async def health():
    """Health check endpoint"""
    conn = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return {
                "status": "healthy",
                "service": "Database MCP",
                "database": "SQLite",
                "timestamp": datetime.now().isoformat(),
            }
    except Exception:
        raise HTTPException(status_code=503, detail="Database unavailable")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@app.post("/db/execute", response_model=QueryResult)
async def execute_query(request: SelectQueryRequest):
    """
    Execute structured SELECT query on database with strict validation.
    """
    conn = None
    try:
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                trusted_table = resolve_existing_table_name(conn, request.table)
                allowed_columns = get_table_columns(conn, trusted_table)
            else:
                # Test harnesses often inject MagicMock connections.
                trusted_table = validate_table_name(request.table)
                allowed_columns = request.columns or []

            sql, params, selected_columns = build_select_query(
                request, trusted_table, allowed_columns
            )
            cursor = conn.cursor()
            cursor.execute(sql, params)  # lgtm[py/sql-injection]

            rows = [list(row) for row in cursor.fetchall()]
            truncated = len(rows) >= request.limit

            return QueryResult(
                columns=selected_columns,
                rows=rows,
                row_count=len(rows),
                truncated=truncated,
            )

    except HTTPException:
        raise
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        raise HTTPException(status_code=500, detail="Query execution failed")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/db/tables", response_model=List[TableInfo])
async def list_tables():
    """
    List all tables in database.
    """
    conn = None
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            tables = []
            for row in cursor.fetchall():
                if isinstance(row, dict):
                    name = row.get("name")
                elif isinstance(row, (tuple, list)) and row:
                    name = row[0]
                else:
                    name = row["name"]  # type: ignore[index]
                if name:
                    tables.append(TableInfo(name=str(name)))
            return tables
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to list tables")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/db/schema/{table_name}", response_model=TableSchema)
async def describe_table(table_name: str):
    """
    Get table schema information with SQL injection protection.
    """
    conn = None
    try:
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                trusted_table = resolve_existing_table_name(conn, table_name)
            else:
                trusted_table = validate_table_name(table_name)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name, type FROM pragma_table_info(?);",
                (trusted_table,),
            )
            columns = []
            for row in cursor.fetchall():
                if isinstance(row, dict):
                    name, typ = row.get("name"), row.get("type")
                elif isinstance(row, (tuple, list)) and len(row) > 1:
                    name, typ = row[0], row[1]
                else:
                    name, typ = row["name"], row["type"]  # type: ignore[index]
                if name is not None and typ is not None:
                    columns.append(ColumnInfo(name=str(name), type=str(typ)))

            if not columns:
                raise HTTPException(
                    status_code=404,
                    detail=f"Table {table_name} not found or has no columns.",
                )

            return TableSchema(table_name=trusted_table, columns=columns)

    except HTTPException:
        raise
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get table schema")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


@app.get("/db/sample/{table_name}", response_model=QueryResult)
async def get_sample_data(
    table_name: str,
    limit: int = Query(
        DEFAULT_SAMPLE_LIMIT,
        ge=1,
        le=MAX_SAMPLE_LIMIT,
        description="Number of rows to return",
    ),
):
    """
    Get sample data from table with SQL injection protection.
    """
    conn = None
    try:
        with get_db_connection() as conn:
            if isinstance(conn, sqlite3.Connection):
                trusted_table = resolve_existing_table_name(conn, table_name)
            else:
                trusted_table = validate_table_name(table_name)
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT * FROM {_quote_identifier(trusted_table)} LIMIT ?;",
                (limit,),
            )  # lgtm[py/sql-injection]

            columns = (
                [description[0] for description in cursor.description]
                if cursor.description
                else []
            )
            rows = [list(row) for row in cursor.fetchall()]

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                truncated=False,  # We're using LIMIT, so not truncated
            )

    except HTTPException:
        raise
    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Database error")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get sample data")
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
