#!/usr/bin/env python3
"""
PostgreSQL MCP Service - Database operations, queries, connections
Port: 8021
"""
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
import asyncpg
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    Execute SQL queries
    
    Tool: query
    Description: Execute SELECT, INSERT, UPDATE, DELETE queries with parameters
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        async with db_pool.acquire() as connection:
            start_time = datetime.now()
            
            # Execute query based on fetch mode
            if request.fetch_mode == "one":
                result = await connection.fetchrow(request.query, *request.parameters)
                rows = [dict(result)] if result else []
            elif request.fetch_mode == "many":
                limit = request.limit or 100
                result = await connection.fetch(request.query, *request.parameters)
                rows = [dict(row) for row in result[:limit]]
            else:  # "all"
                result = await connection.fetch(request.query, *request.parameters)
                if request.limit:
                    result = result[:request.limit]
                rows = [dict(row) for row in result]
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "success": True,
                "rows": rows,
                "row_count": len(rows),
                "execution_time_seconds": execution_time,
                "fetch_mode": request.fetch_mode,
                "query": request.query,
                "timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Query execution failed: {str(e)}")

@app.post("/tools/transaction")
async def transaction_tool(request: TransactionRequest) -> Dict[str, Any]:
    """
    Execute multiple queries in transaction
    
    Tool: transaction
    Description: Execute multiple queries atomically with rollback support
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        async with db_pool.acquire() as connection:
            start_time = datetime.now()
            results = []
            
            async with connection.transaction():
                for i, query_data in enumerate(request.queries):
                    query = query_data.get('query', '')
                    parameters = query_data.get('parameters', [])
                    
                    try:
                        if query.strip().upper().startswith('SELECT'):
                            result = await connection.fetch(query, *parameters)
                            rows = [dict(row) for row in result]
                        else:
                            result = await connection.execute(query, *parameters)
                            rows = result  # Return execute result (like "INSERT 0 1")
                        
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
            
    except Exception as e:
        logger.error(f"Transaction execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transaction execution failed: {str(e)}")

@app.post("/tools/schema")
async def schema_tool(request: SchemaRequest) -> Dict[str, Any]:
    """
    Manage database schema
    
    Tool: schema
    Description: Describe tables, create/drop/alter table structures
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Database connection not available")
    
    try:
        async with db_pool.acquire() as connection:
            
            if request.operation == "describe":
                if request.table_name:
                    # Describe specific table
                    query = """
                    SELECT column_name, data_type, is_nullable, column_default, character_maximum_length
                    FROM information_schema.columns 
                    WHERE table_schema = $1 AND table_name = $2
                    ORDER BY ordinal_position
                    """
                    result = await connection.fetch(query, request.schema_name, request.table_name)
                    columns = [dict(row) for row in result]
                    
                    # Get table indexes
                    index_query = """
                    SELECT indexname, indexdef
                    FROM pg_indexes 
                    WHERE schemaname = $1 AND tablename = $2
                    """
                    index_result = await connection.fetch(index_query, request.schema_name, request.table_name)
                    indexes = [dict(row) for row in index_result]
                    
                    return {
                        "operation": "describe",
                        "table_name": request.table_name,
                        "schema_name": request.schema_name,
                        "columns": columns,
                        "indexes": indexes,
                        "column_count": len(columns)
                    }
                else:
                    # List all tables
                    query = """
                    SELECT table_name, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = $1
                    ORDER BY table_name
                    """
                    result = await connection.fetch(query, request.schema_name)
                    tables = [dict(row) for row in result]
                    
                    return {
                        "operation": "describe",
                        "schema_name": request.schema_name,
                        "tables": tables,
                        "table_count": len(tables)
                    }
                    
            elif request.operation == "create_table":
                if not request.table_name or not request.table_definition:
                    raise HTTPException(status_code=400, detail="Table name and definition required")
                
                # Build CREATE TABLE statement
                columns_sql = []
                for col_name, col_def in request.table_definition.items():
                    columns_sql.append(f"{col_name} {col_def}")
                
                create_sql = f"""CREATE TABLE {request.schema_name}.{request.table_name} ({', '.join(columns_sql)})"""
                
                await connection.execute(create_sql)
                
                return {
                    "operation": "create_table",
                    "table_name": request.table_name,
                    "schema_name": request.schema_name,
                    "success": True,
                    "sql": create_sql
                }
                
            elif request.operation == "drop_table":
                if not request.table_name:
                    raise HTTPException(status_code=400, detail="Table name required")
                
                drop_sql = f"DROP TABLE {request.schema_name}.{request.table_name}"
                await connection.execute(drop_sql)
                
                return {
                    "operation": "drop_table",
                    "table_name": request.table_name,
                    "schema_name": request.schema_name,
                    "success": True,
                    "sql": drop_sql
                }
            
            else:
                raise HTTPException(status_code=400, detail=f"Unknown operation: {request.operation}")
                
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
                "description": "Execute SQL queries with parameters and different fetch modes",
                "parameters": {
                    "query": "string (required, SQL query to execute)",
                    "parameters": "array (optional, query parameters)",
                    "fetch_mode": "string (optional: all|one|many, default all)",
                    "limit": "integer (optional, max rows to return)",
                    "timeout": "integer (optional, query timeout in seconds)"
                }
            },
            {
                "name": "transaction",
                "description": "Execute multiple queries atomically with rollback support",
                "parameters": {
                    "queries": "array (required, list of query objects with query and parameters)",
                    "rollback_on_error": "boolean (optional, default true)",
                    "timeout": "integer (optional, transaction timeout in seconds)"
                }
            },
            {
                "name": "schema",
                "description": "Manage database schema - describe tables, create/drop tables",
                "parameters": {
                    "operation": "string (required: describe|create_table|drop_table|alter_table)",
                    "table_name": "string (optional, table name for operations)",
                    "schema_name": "string (optional, default 'public')",
                    "table_definition": "object (optional, column definitions for create_table)"
                }
            },
            {
                "name": "connection",
                "description": "Manage database connections and get statistics",
                "parameters": {
                    "operation": "string (required: status|test|stats|kill_connections)",
                    "connection_id": "string (optional, connection to manage)",
                    "max_connections": "integer (optional, connection limit)"
                }
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)