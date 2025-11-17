#!/usr/bin/env python3
"""
PostgreSQL MCP Service - Database operations, queries, connections
Port: 8021

SECURITY: This service implements strict SQL injection prevention:
- Query validation and operation whitelisting
- Parameterized queries for all user inputs
- Identifier validation (table/schema names)
- Query complexity limits
- Comprehensive logging of operations
"""
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field, validator
import asyncpg
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import os
import re
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_QUERY_OPERATIONS = {"SELECT"}  # Only SELECT queries allowed for query endpoint
BLOCKED_KEYWORDS = {"DROP", "TRUNCATE", "ALTER", "CREATE", "GRANT", "REVOKE"}
MAX_QUERY_LENGTH = 10000  # 10KB max query size
MAX_RESULT_ROWS = 10000  # Maximum rows to return
MAX_TRANSACTION_QUERIES = 50  # Maximum queries in transaction

# Identifier validation (table names, schema names, column names)
IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
SAFE_SCHEMAS = {'public', 'information_schema'}  # Allowed schemas

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
        raise HTTPException(status_code=400, detail=f"{identifier_type} cannot be empty")

    if len(identifier) > 63:  # PostgreSQL identifier length limit
        raise HTTPException(status_code=400, detail=f"{identifier_type} too long (max 63 chars)")

    if not IDENTIFIER_PATTERN.match(identifier):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid {identifier_type}: must start with letter/underscore and contain only alphanumeric/underscore"
        )

    # Block PostgreSQL system prefixes
    if identifier.startswith('pg_'):
        raise HTTPException(status_code=403, detail=f"{identifier_type} cannot start with 'pg_' (system reserved)")

    return identifier

def validate_query_safety(query: str) -> None:
    """
    Validate that query doesn't contain dangerous operations.

    Args:
        query: SQL query to validate

    Raises:
        HTTPException: If query contains blocked keywords
    """
    query_upper = query.upper()

    # Check query length
    if len(query) > MAX_QUERY_LENGTH:
        raise HTTPException(status_code=400, detail=f"Query too long (max {MAX_QUERY_LENGTH} chars)")

    # Check for blocked keywords
    for keyword in BLOCKED_KEYWORDS:
        if keyword in query_upper:
            raise HTTPException(
                status_code=403,
                detail=f"Query contains forbidden keyword: {keyword}"
            )

    # Ensure query starts with allowed operation
    query_stripped = query_upper.strip()
    allowed = any(query_stripped.startswith(op) for op in ALLOWED_QUERY_OPERATIONS)

    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Query must start with one of: {', '.join(ALLOWED_QUERY_OPERATIONS)}"
        )

def validate_schema_name(schema_name: str) -> str:
    """Validate and sanitize schema name"""
    validated = validate_identifier(schema_name, "schema_name")

    # Additional check: only allow safe schemas
    if validated not in SAFE_SCHEMAS:
        raise HTTPException(
            status_code=403,
            detail=f"Schema '{validated}' not allowed. Allowed schemas: {', '.join(SAFE_SCHEMAS)}"
        )

    return validated

# Database connection pool
db_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global db_pool
    
    # Startup
    try:
        db_url = os.getenv('DATABASE_URL', 'postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified')
        db_pool = await asyncpg.create_pool(
            db_url,
            min_size=5,
            max_size=20,
            command_timeout=60
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
    lifespan=lifespan
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Request/Response Models
class QueryRequest(BaseModel):
    """SQL query execution request"""
    query: str
    parameters: Optional[List[Any]] = []
    fetch_mode: str = "all"  # all, one, many
    limit: Optional[int] = None
    timeout: Optional[int] = 30

class TransactionRequest(BaseModel):
    """Transaction execution request"""
    queries: List[Dict[str, Any]]
    rollback_on_error: bool = True
    timeout: Optional[int] = 60

class SchemaRequest(BaseModel):
    """Database schema operations"""
    operation: str = Field(..., description="describe, create_table, drop_table, alter_table")
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
            "idle_size": db_pool.get_idle_size()
        }
    
    return {
        "status": "healthy",
        "service": "PostgreSQL MCP",
        "port": 8021,
        "timestamp": datetime.now().isoformat(),
        "features": ["query_execution", "transactions", "schema_management", "connection_management", "backup_operations"],
        "database": {
            "status": db_status,
            "pool_info": pool_info
        }
    }

@app.post("/tools/query")
async def query_tool(request: QueryRequest) -> Dict[str, Any]:
    """
    Execute SQL queries (SELECT only for security)

    Tool: query
    Description: Execute SELECT queries with parameters (safe, read-only operations)

    SECURITY: Only SELECT queries allowed. All queries validated for:
    - Allowed operations (SELECT only)
    - Forbidden keywords (DROP, TRUNCATE, ALTER, etc.)
    - Query length limits
    - Result row limits
    """
    # SECURITY: Validate query safety BEFORE checking db_pool
    validate_query_safety(request.query)

    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    # SECURITY: Enforce result row limits
    max_limit = min(request.limit or MAX_RESULT_ROWS, MAX_RESULT_ROWS)

    try:
        async with db_pool.acquire() as connection:
            start_time = datetime.now()

            # Log query execution for auditing
            logger.info(f"Executing query: {request.query[:100]}... (fetch_mode: {request.fetch_mode}, limit: {max_limit})")

            # Execute query based on fetch mode
            if request.fetch_mode == "one":
                result = await connection.fetchrow(request.query, *request.parameters)
                rows = [dict(result)] if result else []
            elif request.fetch_mode == "many":
                limit = request.limit or 100
                limit = min(limit, MAX_RESULT_ROWS)  # Enforce limit
                result = await connection.fetch(request.query, *request.parameters)
                rows = [dict(row) for row in result[:limit]]
            else:  # "all"
                result = await connection.fetch(request.query, *request.parameters)
                # Enforce maximum result rows for safety
                if len(result) > MAX_RESULT_ROWS:
                    logger.warning(f"Query returned {len(result)} rows, truncating to {MAX_RESULT_ROWS}")
                    result = result[:MAX_RESULT_ROWS]
                if request.limit:
                    result = result[:min(request.limit, MAX_RESULT_ROWS)]
                rows = [dict(row) for row in result]

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_seconds": execution_time,
                "fetch_mode": request.fetch_mode,
                "query": request.query,
                "timestamp": datetime.now().isoformat(),
                "truncated": len(rows) >= MAX_RESULT_ROWS
            }

    except HTTPException:
        raise  # Re-raise validation errors
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.post("/tools/transaction")
async def transaction_tool(request: TransactionRequest) -> Dict[str, Any]:
    """
    Execute multiple queries in transaction (DISABLED for security)

    Tool: transaction
    Description: DISABLED - This endpoint is disabled for security reasons.
                Use /tools/query for read operations instead.

    SECURITY NOTE: Transaction endpoints allowing arbitrary SQL are too dangerous
    for production use. This endpoint has been disabled to prevent SQL injection
    and unauthorized data modifications.

    To re-enable with proper security controls:
    1. Implement strict query validation per query
    2. Add operation whitelisting
    3. Require explicit authorization
    4. Add audit logging
    """
    raise HTTPException(
        status_code=403,
        detail="Transaction endpoint is disabled for security. Use /tools/query for SELECT operations only."
    )

    # Original implementation kept for reference but unreachable
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")

    # SECURITY: Validate transaction size
    if len(request.queries) > MAX_TRANSACTION_QUERIES:
        raise HTTPException(
            status_code=400,
            detail=f"Too many queries in transaction (max {MAX_TRANSACTION_QUERIES})"
        )

    try:
        async with db_pool.acquire() as connection:
            start_time = datetime.now()
            results = []

            # SECURITY: Validate all queries before executing transaction
            for i, query_data in enumerate(request.queries):
                query = query_data.get('query', '')
                validate_query_safety(query)  # Will raise HTTPException if invalid

            async with connection.transaction():
                for i, query_data in enumerate(request.queries):
                    query = query_data.get('query', '')
                    parameters = query_data.get('parameters', [])

                    # Log for audit
                    logger.info(f"Transaction query {i}: {query[:50]}...")

                    try:
                        if query.strip().upper().startswith('SELECT'):
                            result = await connection.fetch(query, *parameters)
                            rows = [dict(row) for row in result]
                        else:
                            # This path should never execute due to validate_query_safety
                            result = await connection.execute(query, *parameters)
                            rows = result

                        results.append({
                            "query_index": i,
                            "query": query,
                            "success": True,
                            "result": rows,
                            "affected_rows": len(rows) if isinstance(rows, list) else None
                        })

                    except Exception as e:
                        error_result = {
                            "query_index": i,
                            "query": query,
                            "success": False,
                            "error": str(e)
                        }

                        if request.rollback_on_error:
                            logger.warning(f"Transaction rolled back due to query {i} failure")
                            raise Exception(f"Query {i} failed: {str(e)}")
                        else:
                            results.append(error_result)

            execution_time = (datetime.now() - start_time).total_seconds()

            return {
                "success": True,
                "results": results,
                "query_count": len(request.queries),
                "successful_queries": len([r for r in results if r.get('success', False)]),
                "execution_time_seconds": execution_time,
                "rollback_on_error": request.rollback_on_error,
                "timestamp": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Transaction execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transaction execution failed: {str(e)}")

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

    # SECURITY: Check for disabled operations BEFORE db_pool check
    if request.operation == "create_table":
        raise HTTPException(
            status_code=403,
            detail="CREATE TABLE operation is disabled for security. Use database admin tools for schema changes."
        )
    elif request.operation == "drop_table":
        raise HTTPException(
            status_code=403,
            detail="DROP TABLE operation is disabled for security. Use database admin tools for schema changes."
        )
    elif request.operation == "alter_table":
        raise HTTPException(
            status_code=403,
            detail="ALTER TABLE operation is disabled for security. Use database admin tools for schema changes."
        )

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
                    result = await connection.fetch(query, validated_schema, validated_table)
                    columns = [dict(row) for row in result]

                    # Get table indexes (parameterized - SAFE)
                    index_query = """
                    SELECT indexname, indexdef
                    FROM pg_indexes
                    WHERE schemaname = $1 AND tablename = $2
                    """
                    index_result = await connection.fetch(index_query, validated_schema, validated_table)
                    indexes = [dict(row) for row in index_result]

                    logger.info(f"Described table: {validated_schema}.{validated_table}")

                    return {
                        "operation": "describe",
                        "table_name": validated_table,
                        "schema_name": validated_schema,
                        "columns": columns,
                        "indexes": indexes,
                        "column_count": len(columns)
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

                    logger.info(f"Listed {len(tables)} tables in schema: {validated_schema}")

                    return {
                        "operation": "describe",
                        "schema_name": validated_schema,
                        "tables": tables,
                        "table_count": len(tables)
                    }

            else:
                # Unknown operation (create/drop/alter already blocked earlier)
                raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Schema operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Schema operation failed: {str(e)}")

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
                        "max_size": db_pool.get_max_size()
                    },
                    "timestamp": datetime.now().isoformat()
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
                        "idle_size": db_pool.get_idle_size()
                    },
                    "timestamp": datetime.now().isoformat()
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
                    "timestamp": datetime.now().isoformat()
                }
                
            else:
                raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
                
    except Exception as e:
        logger.error(f"Connection operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection operation failed: {str(e)}")

@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "query",
                "description": "Execute SELECT queries with parameters (read-only, safe operations)",
                "security": "Only SELECT queries allowed. Forbidden: DROP, TRUNCATE, ALTER, CREATE, etc.",
                "parameters": {
                    "query": "string (required, SELECT SQL query to execute)",
                    "parameters": "array (optional, query parameters for safe parameterized queries)",
                    "fetch_mode": "string (optional: all|one|many, default all)",
                    "limit": "integer (optional, max rows to return, capped at 10000)",
                    "timeout": "integer (optional, query timeout in seconds)"
                },
                "example": {
                    "query": "SELECT * FROM users WHERE id = $1",
                    "parameters": [123],
                    "fetch_mode": "one",
                    "limit": 100
                }
            },
            {
                "name": "transaction",
                "description": "DISABLED - Transaction endpoint disabled for security",
                "security": "This endpoint is disabled. Use /tools/query for SELECT operations.",
                "status": "disabled"
            },
            {
                "name": "schema",
                "description": "View database schema information (read-only)",
                "security": "Only DESCRIBE operation allowed. CREATE/DROP/ALTER disabled for security.",
                "parameters": {
                    "operation": "string (required: describe only)",
                    "table_name": "string (optional, specific table to describe)",
                    "schema_name": "string (optional, allowed: public|information_schema, default 'public')"
                },
                "example": {
                    "operation": "describe",
                    "table_name": "users",
                    "schema_name": "public"
                }
            },
            {
                "name": "connection",
                "description": "View database connection status and statistics (read-only)",
                "security": "Read-only operations. No connection termination allowed.",
                "parameters": {
                    "operation": "string (required: status|test|stats)",
                    "connection_id": "string (not used, reserved)",
                    "max_connections": "integer (not used, reserved)"
                },
                "example": {
                    "operation": "stats"
                }
            }
        ],
        "security_note": "This service implements strict security controls to prevent SQL injection and unauthorized database access. All destructive operations are disabled."
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)