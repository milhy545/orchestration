#!/usr/bin/env python3
\"\"\"
Redis MCP Service - Cache, session management, pub/sub
Port: 8022
\"\"\"
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
import redis.asyncio as redis
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection pool
redis_pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Application lifespan manager\"\"\"
    global redis_pool
    
    # Startup
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        redis_pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            retry_on_timeout=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        client = redis.Redis(connection_pool=redis_pool)
        await client.ping()
        await client.aclose()
        
        logger.info(\"Redis connection pool created successfully\")
    except Exception as e:
        logger.error(f\"Failed to create Redis connection pool: {e}\")
        redis_pool = None
    
    yield
    
    # Shutdown
    if redis_pool:
        await redis_pool.aclose()
        logger.info(\"Redis connection pool closed\")

app = FastAPI(
    title=\"Redis MCP Service\",
    description=\"Cache, session management, pub/sub, and key-value operations\",
    version=\"1.0.0\",
    lifespan=lifespan
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Request/Response Models
class CacheRequest(BaseModel):
    \"\"\"Cache operations request\"\"\"
    operation: str = Field(..., description=\"get, set, delete, exists, expire\")
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = None  # Time to live in seconds
    nx: Optional[bool] = False  # Only set if key doesn't exist
    ex: Optional[bool] = False  # Only set if key exists

class HashRequest(BaseModel):
    \"\"\"Hash operations request\"\"\"
    operation: str = Field(..., description=\"hget, hset, hgetall, hdel, hexists, hkeys\")
    key: str
    field: Optional[str] = None
    value: Optional[Any] = None
    fields: Optional[Dict[str, Any]] = None

class ListRequest(BaseModel):
    \"\"\"List operations request\"\"\"
    operation: str = Field(..., description=\"lpush, rpush, lpop, rpop, lrange, llen\")
    key: str
    values: Optional[List[Any]] = None
    start: Optional[int] = 0
    end: Optional[int] = -1

class SetRequest(BaseModel):
    \"\"\"Set operations request\"\"\"
    operation: str = Field(..., description=\"sadd, srem, smembers, scard, sismember\")
    key: str
    members: Optional[List[Any]] = None
    member: Optional[Any] = None

class PubSubRequest(BaseModel):
    \"\"\"Pub/Sub operations request\"\"\"
    operation: str = Field(..., description=\"publish, subscribe, unsubscribe\")
    channel: str
    message: Optional[Any] = None
    timeout: Optional[int] = 10

class SessionRequest(BaseModel):
    \"\"\"Session management request\"\"\"
    operation: str = Field(..., description=\"create, get, update, delete, list\")
    session_id: Optional[str] = None
    session_data: Optional[Dict[str, Any]] = None
    ttl: Optional[int] = 3600  # Default 1 hour

@app.get(\"/health\")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    redis_status = \"healthy\" if redis_pool else \"disconnected\"
    
    info = {}
    if redis_pool:
        try:
            client = redis.Redis(connection_pool=redis_pool)
            redis_info = await client.info()
            await client.aclose()
            
            info = {
                \"version\": redis_info.get('redis_version'),
                \"connected_clients\": redis_info.get('connected_clients'),
                \"used_memory_human\": redis_info.get('used_memory_human'),
                \"uptime_in_seconds\": redis_info.get('uptime_in_seconds')
            }
        except Exception as e:
            redis_status = f\"error: {str(e)}\"
    
    return {
        \"status\": \"healthy\",
        \"service\": \"Redis MCP\",
        \"port\": 8022,
        \"timestamp\": datetime.now().isoformat(),
        \"features\": [\"cache\", \"hash\", \"list\", \"set\", \"pubsub\", \"session\"],
        \"redis\": {
            \"status\": redis_status,
            \"info\": info
        }
    }

@app.post(\"/tools/cache\")
async def cache_tool(request: CacheRequest) -> Dict[str, Any]:
    \"\"\"
    Cache operations
    
    Tool: cache
    Description: Get, set, delete, check existence, set expiration for keys
    \"\"\"
    if not redis_pool:
        raise HTTPException(status_code=503, detail=\"Redis connection not available\")
    
    try:
        client = redis.Redis(connection_pool=redis_pool)
        
        if request.operation == \"get\":
            value = await client.get(request.key)
            result = json.loads(value) if value else None
            
            return {
                \"operation\": \"get\",
                \"key\": request.key,
                \"value\": result,
                \"found\": value is not None,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"set\":
            if request.value is None:
                raise HTTPException(status_code=400, detail=\"Value required for set operation\")
            
            value_str = json.dumps(request.value)
            kwargs = {}
            
            if request.ttl:
                kwargs['ex'] = request.ttl
            if request.nx:
                kwargs['nx'] = True
            if request.ex:
                kwargs['xx'] = True
            
            success = await client.set(request.key, value_str, **kwargs)
            
            return {
                \"operation\": \"set\",
                \"key\": request.key,
                \"value\": request.value,
                \"success\": bool(success),
                \"ttl\": request.ttl,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"delete\":
            deleted_count = await client.delete(request.key)
            
            return {
                \"operation\": \"delete\",
                \"key\": request.key,
                \"deleted\": deleted_count > 0,
                \"deleted_count\": deleted_count,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"exists\":
            exists = await client.exists(request.key)
            
            return {
                \"operation\": \"exists\",
                \"key\": request.key,
                \"exists\": bool(exists),
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"expire\":
            if not request.ttl:
                raise HTTPException(status_code=400, detail=\"TTL required for expire operation\")
                
            success = await client.expire(request.key, request.ttl)
            
            return {
                \"operation\": \"expire\",
                \"key\": request.key,
                \"ttl\": request.ttl,
                \"success\": bool(success),
                \"timestamp\": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f\"Unknown operation: {request.operation}\")
        
        await client.aclose()
        
    except Exception as e:
        logger.error(f\"Cache operation failed: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"Cache operation failed: {str(e)}\")

@app.post(\"/tools/session\")
async def session_tool(request: SessionRequest) -> Dict[str, Any]:
    \"\"\"
    Session management
    
    Tool: session
    Description: Create, get, update, delete user sessions with TTL
    \"\"\"
    if not redis_pool:
        raise HTTPException(status_code=503, detail=\"Redis connection not available\")
    
    try:
        client = redis.Redis(connection_pool=redis_pool)
        session_prefix = \"session:\"
        
        if request.operation == \"create\":
            if not request.session_data:
                raise HTTPException(status_code=400, detail=\"Session data required\")
            
            session_id = request.session_id or f\"sess_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}\"
            session_key = f\"{session_prefix}{session_id}\"
            
            session_info = {
                \"id\": session_id,
                \"data\": request.session_data,
                \"created_at\": datetime.now().isoformat(),
                \"last_accessed\": datetime.now().isoformat()
            }
            
            await client.setex(session_key, request.ttl, json.dumps(session_info))
            
            return {
                \"operation\": \"create\",
                \"session_id\": session_id,
                \"session_data\": request.session_data,
                \"ttl\": request.ttl,
                \"expires_at\": (datetime.now() + timedelta(seconds=request.ttl)).isoformat(),
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"get\":
            if not request.session_id:
                raise HTTPException(status_code=400, detail=\"Session ID required\")
            
            session_key = f\"{session_prefix}{request.session_id}\"
            session_data = await client.get(session_key)
            
            if not session_data:
                return {
                    \"operation\": \"get\",
                    \"session_id\": request.session_id,
                    \"found\": False,
                    \"timestamp\": datetime.now().isoformat()
                }
            
            session_info = json.loads(session_data)
            # Update last_accessed
            session_info[\"last_accessed\"] = datetime.now().isoformat()
            await client.setex(session_key, request.ttl, json.dumps(session_info))
            
            return {
                \"operation\": \"get\",
                \"session_id\": request.session_id,
                \"session_info\": session_info,
                \"found\": True,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"update\":
            if not request.session_id or not request.session_data:
                raise HTTPException(status_code=400, detail=\"Session ID and data required\")
            
            session_key = f\"{session_prefix}{request.session_id}\"
            existing_data = await client.get(session_key)
            
            if not existing_data:
                raise HTTPException(status_code=404, detail=\"Session not found\")
            
            session_info = json.loads(existing_data)
            session_info[\"data\"].update(request.session_data)\n            session_info[\"last_accessed\"] = datetime.now().isoformat()
            
            await client.setex(session_key, request.ttl, json.dumps(session_info))
            
            return {
                \"operation\": \"update\",
                \"session_id\": request.session_id,
                \"updated_data\": request.session_data,
                \"session_info\": session_info,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"delete\":
            if not request.session_id:
                raise HTTPException(status_code=400, detail=\"Session ID required\")
            
            session_key = f\"{session_prefix}{request.session_id}\"
            deleted = await client.delete(session_key)
            
            return {
                \"operation\": \"delete\",
                \"session_id\": request.session_id,
                \"deleted\": bool(deleted),
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"list\":
            # List all sessions (be careful with large datasets)
            pattern = f\"{session_prefix}*\"
            keys = await client.keys(pattern)
            
            sessions = []
            for key in keys[:100]:  # Limit to first 100
                session_data = await client.get(key)
                if session_data:
                    session_info = json.loads(session_data)
                    sessions.append({
                        \"session_id\": session_info.get(\"id\"),
                        \"created_at\": session_info.get(\"created_at\"),
                        \"last_accessed\": session_info.get(\"last_accessed\")
                    })
            
            return {
                \"operation\": \"list\",
                \"sessions\": sessions,
                \"session_count\": len(sessions),
                \"total_keys\": len(keys),
                \"timestamp\": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f\"Unknown operation: {request.operation}\")
        
        await client.aclose()
        
    except Exception as e:
        logger.error(f\"Session operation failed: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"Session operation failed: {str(e)}\")

@app.get(\"/tools/list\")
async def list_tools():
    \"\"\"List all available MCP tools\"\"\"
    return {
        \"tools\": [
            {
                \"name\": \"cache\",
                \"description\": \"Key-value cache operations with TTL support\",
                \"parameters\": {
                    \"operation\": \"string (required: get|set|delete|exists|expire)\",
                    \"key\": \"string (required, cache key)\",
                    \"value\": \"any (optional, value to store)\",
                    \"ttl\": \"integer (optional, time to live in seconds)\",
                    \"nx\": \"boolean (optional, only set if key doesn't exist)\",
                    \"ex\": \"boolean (optional, only set if key exists)\"
                }
            },
            {
                \"name\": \"session\",
                \"description\": \"User session management with automatic TTL\",
                \"parameters\": {
                    \"operation\": \"string (required: create|get|update|delete|list)\",
                    \"session_id\": \"string (optional, session identifier)\",
                    \"session_data\": \"object (optional, session data)\",
                    \"ttl\": \"integer (optional, session timeout in seconds, default 3600)\"
                }
            }
        ]
    }

if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8000)