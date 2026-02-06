#!/usr/bin/env python3
"""
PostgreSQL MCP Service - Database operations, queries, connections
Port: 7021

SECURITY: This service implements strict SQL injection prevention:
- Query validation and operation whitelisting
- Parameterized queries for all user inputs
- Identifier validation (table/schema names)
- Query complexity limits
- Comprehensive logging of operations
"""
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Literal

import asyncpg
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
MAX_RESULT_ROWS = 10000  # Maximum rows to return
DEFAULT_SELECT_LIMIT = 100

# Identifier validation (table names, schema names, column names)
IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
SAFE_SCHEMAS = {"public", "information_schema"}  # Allowed schemas


def validate_identifier(identifier: str, identifier_type: str = "identifier") -> str:
    """
    Validate SQL identifiers (table names, schema names, column names)
    to prevent SQL injection via identifier names.

    Args:
        identifier: The identifier to validate
        identifier_type: Type of identifier for error messages

    Returns:
        The validated identifier

    Raises:
        HTTPException: If identifier is invalid
    """
    if not identifier:
        raise HTTPException(
            status_code=400, detail=f"{identifier_type} cannot be empty"
        )

    if len(identifier) > 63:  # PostgreSQL identifier length limit
        raise HTTPException(
            status_code=400, detail=f"{identifier_type} too long (max 63 chars)"
        )

    if not IDENTIFIER_PATTERN.match(identifier):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type}: must start with letter/underscore and contain only alphanumeric/underscore",
        )

    # Block PostgreSQL system prefixes
    if identifier.startswith("pg_"):
        raise HTTPException(
            status_code=403,
            detail=f"{identifier_type} cannot start with 'pg_' (system reserved)",
        )

    return identifier


class FilterCondition(BaseModel):
    column: str
    op: Literal["=", "!=", ">", ">=", "<", "<=", "like", "ilike", "in"]
    value: Any


class OrderBy(BaseModel):
    column: str
    direction: Literal["asc", "desc"] = "asc"


def validate_schema_name(schema_name: str) -> str:
    """Validate and sanitize schema name"""
    validated = validate_identifier(schema_name, "schema_name")

    # Additional check: only allow safe schemas
    if validated not in SAFE_SCHEMAS:
        raise HTTPException(
            status_code=403,
            detail=f"Schema '{validated}' not allowed. Allowed schemas: {', '.join(SAFE_SCHEMAS)}",
        )

    return validated


async def get_table_columns(
    connection: asyncpg.Connection, schema_name: str, table_name: str
) -> List[str]:
    query = """
    SELECT column_name
    FROM information_schema.columns
    WHERE table_schema = $1 AND table_name = $2
    ORDER BY ordinal_position
    """
    rows = await connection.fetch(query, schema_name, table_name)
    columns = [row["column_name"] for row in rows]
    if not columns:
        raise HTTPException(
            status_code=404,
            detail=f"Table {schema_name}.{table_name} not found or has no columns.",
        )
    return columns


def build_select_query(
    request: "SelectQueryRequest",
    schema_name: str,
    table_name: str,
    allowed_columns: List[str],
) -> Tuple[str, List[Any], List[str]]:
    selected_columns = request.columns or allowed_columns
    for col in selected_columns:
        if col not in allowed_columns:
            raise HTTPException(status_code=400, detail=f"Unknown column: {col}")

    columns_sql = ", ".join(f'"{col}"' for col in selected_columns)
    sql = f'SELECT {columns_sql} FROM "{schema_name}"."{table_name}"'
    params: List[Any] = []

    def add_param(value: Any) -> str:
        params.append(value)
        return f"${len(params)}"

    if request.filters:
        filter_clauses = []
        for condition in request.filters:
            if condition.column not in allowed_columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown filter column: {condition.column}",
                )
            if condition.op == "in":
                if not isinstance(condition.value, list) or not condition.value:
                    raise HTTPException(
                        status_code=400,
                        detail="IN operator requires a non-empty list",
                    )
                placeholder = add_param(condition.value)
                filter_clauses.append(f'"{condition.column}" = ANY({placeholder})')
            elif condition.op in {"like", "ilike"}:
                if not isinstance(condition.value, str):
                    raise HTTPException(
                        status_code=400,
                        detail="LIKE/ILIKE operator requires string value",
                    )
                placeholder = add_param(condition.value)
                op = "LIKE" if condition.op == "like" else "ILIKE"
                filter_clauses.append(f'"{condition.column}" {op} {placeholder}')
            else:
                placeholder = add_param(condition.value)
                filter_clauses.append(
                    f'"{condition.column}" {condition.op} {placeholder}'
                )
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

    sql += f" LIMIT {add_param(request.limit)} OFFSET {add_param(request.offset)}"
    return sql, params, selected_columns


# Database connection pool
db_pool = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_pool

    # Startup
    try:
        db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified",
        )
        db_pool = await asyncpg.create_pool(
            db_url, min_size=5, max_size=20, command_timeout=60
        )
        logger.info("Database pool created successfully")
    except Exception as e:
        logger.error(f"Failed to create database pool: {e}")
        db_pool = None

    yield

    # Shutdown
    if db_pool:
        await db_pool.close()
        logger.info("Database pool closed")


app = FastAPI(
    title="PostgreSQL MCP Service",
    description="Database operations, queries, connections, and management",
    version="1.0.0",
    lifespan=lifespan,
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Request/Response Models
class SelectQueryRequest(BaseModel):
    """Structured SELECT query request (safe, read-only)"""

    schema_name: Optional[str] = "public"
    table: str
    columns: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    order_by: Optional[List[OrderBy]] = None
    limit: int = Field(DEFAULT_SELECT_LIMIT, ge=1, le=MAX_RESULT_ROWS)
    offset: int = Field(0, ge=0, le=MAX_RESULT_ROWS)


class SchemaRequest(BaseModel):
    """Database schema operations (read-only)"""

    operation: Literal["describe", "list"] = "describe"
    table_name: Optional[str] = None
    schema_name: Optional[str] = "public"
    table_definition: Optional[Dict[str, Any]] = None


class ConnectionRequest(BaseModel):
    """Database connection management"""

    operation: str = Field(..., description="status, test, stats, kill_connections")
    connection_id: Optional[str] = None
    max_connections: Optional[int] = None


class BackupRequest(BaseModel):
    """Database backup operations"""

    operation: str = Field(..., description="create, restore, list, delete")
    backup_name: Optional[str] = None
    tables: Optional[List[str]] = None
    compress: bool = True


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = "healthy" if db_pool else "disconnected"

    pool_info = {}
    if db_pool:
        pool_info = {
            "size": db_pool.get_size(),
            "min_size": db_pool.get_min_size(),
            "max_size": db_pool.get_max_size(),
            "idle_size": db_pool.get_idle_size(),
        }

    return {
        "status": "healthy",
        "service": "PostgreSQL MCP",
        "port": 7021,
        "timestamp": datetime.now().isoformat(),
        "features": [
            "query_execution",
            "schema_management",
            "connection_management",
        ],
        "database": {"status": db_status, "pool_info": pool_info},
    }


@app.post("/tools/query")
async def query_tool(request: SelectQueryRequest) -> Dict[str, Any]:
    """
    Execute structured SELECT queries (safe, read-only operations)

    Tool: query
    Description: Execute SELECT queries built from validated table/columns/filters
    """
    validated_schema = validate_schema_name(request.schema_name or "public")
    validated_table = validate_identifier(request.table, "table_name")

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    # Enforce result row limits
    request.limit = min(request.limit, MAX_RESULT_ROWS)

    try:
        async with db_pool.acquire() as connection:
            start_time = datetime.now()
            allowed_columns = await get_table_columns(
                connection, validated_schema, validated_table
            )
            sql, params, selected_columns = build_select_query(
                request, validated_schema, validated_table, allowed_columns
            )

            logger.info(
                f"Executing structured query on {validated_schema}.{validated_table}"
            )

            # lgtm[py/sql-injection] - SQL built from validated identifiers and parameterized values
            # lgtm[py/sql-injection] - SQL built from validated identifiers and parameterized values
            result = await connection.fetch(sql, *params)
            rows = [dict(row) for row in result]

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_seconds": execution_time,
                "timestamp": datetime.now().isoformat(),
                "truncated": len(rows) >= request.limit,
                "columns": selected_columns,
                "schema": validated_schema,
                "table": validated_table,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Query execution failed")


@app.post("/tools/schema")
async def schema_tool(request: SchemaRequest) -> Dict[str, Any]:
    """
    Manage database schema (READ-ONLY for security)

    Tool: schema
    Description: Describe tables and view schema information (read-only)

    SECURITY: CREATE/DROP/ALTER operations disabled for security.
    Only DESCRIBE operation is allowed.
    """
    # SECURITY: Validate schema name BEFORE checking db_pool
    validated_schema = validate_schema_name(request.schema_name or "public")

    # SECURITY: Validate table name BEFORE checking db_pool (if provided)
    validated_table = None
    if request.table_name:
        validated_table = validate_identifier(request.table_name, "table_name")

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        async with db_pool.acquire() as connection:

            if request.operation == "describe":
                if validated_table:
                    # Describe specific table (uses parameterized queries - SAFE)
                    # Note: validated_table was already validated before db_pool check
                    query = """
                    SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """
                    result = await connection.fetch(
                        query, validated_schema, validated_table
                    )
                    columns = [dict(row) for row in result]

                    # Get table indexes (parameterized - SAFE)
                    index_query = """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = $1 AND tablename = $2
                    """
                    index_result = await connection.fetch(
                        index_query, validated_schema, validated_table
                    )
                    indexes = [dict(row) for row in index_result]

                    logger.info(
                        f"Described table: {validated_schema}.{validated_table}"
                    )

                    return {
                        "operation": "describe",
                        "table_name": validated_table,
                        "schema_name": validated_schema,
                        "columns": columns,
                        "indexes": indexes,
                        "column_count": len(columns),
                    }
                else:
                    # List all tables (parameterized - SAFE)
                    query = """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = $1
                    ORDER BY table_name
                    """
                    result = await connection.fetch(query, validated_schema)
                    tables = [dict(row) for row in result]

                    logger.info(
                        f"Listed {len(tables)} tables in schema: {validated_schema}"
                    )

                    return {
                        "operation": "describe",
                        "schema_name": validated_schema,
                        "tables": tables,
                        "table_count": len(tables),
                    }

            elif request.operation == "list":
                query = """
                SELECT table_name, table_type
                FROM information_schema.tables
                WHERE table_schema = $1
                ORDER BY table_name
                """
                result = await connection.fetch(query, validated_schema)
                tables = [dict(row) for row in result]

                logger.info(
                    f"Listed {len(tables)} tables in schema: {validated_schema}"
                )

                return {
                    "operation": "list",
                    "schema_name": validated_schema,
                    "tables": tables,
                    "table_count": len(tables),
                }
            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown operation: {request.operation}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Schema operation failed")


@app.post("/tools/connection")
async def connection_tool(request: ConnectionRequest) -> Dict[str, Any]:
    """
    Manage database connections

    Tool: connection
    Description: Check connection status, statistics, and manage connections
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    try:
        async with db_pool.acquire() as connection:

            if request.operation == "status":
                # Get database connection status
                query = "SELECT version(), current_database(), current_user, inet_server_addr(), inet_server_port()"
                result = await connection.fetchrow(query)

                return {
                    "operation": "status",
                    "database_info": dict(result),
                    "pool_status": {
                        "size": db_pool.get_size(),
                        "idle_size": db_pool.get_idle_size(),
                        "min_size": db_pool.get_min_size(),
                        "max_size": db_pool.get_max_size(),
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            elif request.operation == "stats":
                # Get connection statistics
                stats_query = """
                SELECT
                    count(*) as total_connections,
                    count(*) FILTER (WHERE state = 'active') as active_connections,
                    count(*) FILTER (WHERE state = 'idle') as idle_connections
                FROM pg_stat_activity
                WHERE pid != pg_backend_pid()
                """

                result = await connection.fetchrow(stats_query)
                stats = dict(result)

                # Get database size
                size_query = "SELECT pg_size_pretty(pg_database_size(current_database())) as database_size"
                size_result = await connection.fetchrow(size_query)
                stats.update(dict(size_result))

                return {
                    "operation": "stats",
                    "connection_stats": stats,
                    "pool_stats": {
                        "size": db_pool.get_size(),
                        "idle_size": db_pool.get_idle_size(),
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            elif request.operation == "test":
                # Test connection with simple query
                test_query = "SELECT 1 as test, now() as timestamp"
                start_time = datetime.now()
                result = await connection.fetchrow(test_query)
                response_time = (datetime.now() - start_time).total_seconds()

                return {
                    "operation": "test",
                    "success": True,
                    "response_time_seconds": response_time,
                    "test_result": dict(result),
                    "timestamp": datetime.now().isoformat(),
                }

            else:
                raise HTTPException(
                    status_code=400, detail=f"Unknown operation: {request.operation}"
                )

    except Exception as e:
        logger.error(f"Connection operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Connection operation failed")


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "query",
                "description": "Execute structured SELECT queries (read-only, safe operations)",
                "security": "Only SELECT queries via validated table/columns/filters.",
                "parameters": {
                    "schema_name": "string (optional, allowed: public|information_schema, default 'public')",
                    "table": "string (required, table name)",
                    "columns": "array (optional, list of columns to select)",
                    "filters": "array (optional, objects: {column, op, value})",
                    "order_by": "array (optional, objects: {column, direction})",
                    "limit": "integer (optional, max rows to return, capped at 10000)",
                    "offset": "integer (optional, start offset)",
                },
                "example": {
                    "schema_name": "public",
                    "table": "users",
                    "columns": ["id", "email"],
                    "filters": [{"column": "id", "op": "=", "value": 123}],
                    "order_by": [{"column": "id", "direction": "desc"}],
                    "limit": 100,
                },
            },
            {
                "name": "schema",
                "description": "View database schema information (read-only)",
                "security": "Only describe/list operations allowed.",
                "parameters": {
                    "operation": "string (required: describe|list)",
                    "table_name": "string (optional, specific table to describe)",
                    "schema_name": "string (optional, allowed: public|information_schema, default 'public')",
                },
                "example": {
                    "operation": "describe",
                    "table_name": "users",
                    "schema_name": "public",
                },
            },
            {
                "name": "connection",
                "description": "View database connection status and statistics (read-only)",
                "security": "Read-only operations. No connection termination allowed.",
                "parameters": {
                    "operation": "string (required: status|test|stats)",
                    "connection_id": "string (not used, reserved)",
                    "max_connections": "integer (not used, reserved)",
                },
                "example": {"operation": "stats"},
            },
        ],
        "security_note": "This service implements strict security controls to prevent SQL injection and unauthorized database access. All destructive operations are disabled.",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
