#!/usr/bin/env python3
"""
Qdrant MCP Service - Vector database operations, embeddings, similarity search
Port: 8023
"""
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
import os
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Qdrant client
qdrant_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Application lifespan manager\"\"\"
    global qdrant_client
    
    # Startup
    try:
        qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
        qdrant_client = AsyncQdrantClient(url=qdrant_url, timeout=60)
        
        # Test connection
        collections = await qdrant_client.get_collections()
        logger.info(f\"Qdrant connection successful. Found {len(collections.collections)} collections\")
    except Exception as e:
        logger.error(f\"Failed to connect to Qdrant: {e}\")
        qdrant_client = None
    
    yield
    
    # Shutdown
    if qdrant_client:
        await qdrant_client.close()
        logger.info(\"Qdrant client closed\")

app = FastAPI(
    title=\"Qdrant MCP Service\",
    description=\"Vector database operations, embeddings, and similarity search\",
    version=\"1.0.0\",
    lifespan=lifespan
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Request/Response Models
class CollectionRequest(BaseModel):
    \"\"\"Collection management request\"\"\"
    operation: str = Field(..., description=\"create, delete, list, info\")
    collection_name: Optional[str] = None
    vector_size: Optional[int] = None
    distance: Optional[str] = \"Cosine\"  # Cosine, Euclid, Dot

class VectorRequest(BaseModel):
    \"\"\"Vector operations request\"\"\"
    operation: str = Field(..., description=\"insert, update, delete, get\")
    collection_name: str
    points: Optional[List[Dict[str, Any]]] = None
    point_id: Optional[Union[int, str]] = None
    vector: Optional[List[float]] = None
    payload: Optional[Dict[str, Any]] = None

class SearchRequest(BaseModel):
    \"\"\"Vector search request\"\"\"
    collection_name: str
    query_vector: List[float]
    limit: int = 10
    score_threshold: Optional[float] = None
    filter: Optional[Dict[str, Any]] = None
    with_payload: bool = True
    with_vectors: bool = False

class SimilarityRequest(BaseModel):
    \"\"\"Similarity search request\"\"\"
    collection_name: str
    text_query: Optional[str] = None  # For text-based search
    vector_query: Optional[List[float]] = None  # Direct vector search
    limit: int = 10
    threshold: float = 0.7

@app.get(\"/health\")
async def health_check():
    \"\"\"Health check endpoint\"\"\"
    qdrant_status = \"healthy\" if qdrant_client else \"disconnected\"
    
    info = {}
    if qdrant_client:
        try:
            collections = await qdrant_client.get_collections()
            info = {
                \"collections_count\": len(collections.collections),
                \"collections\": [col.name for col in collections.collections]
            }
        except Exception as e:
            qdrant_status = f\"error: {str(e)}\"
    
    return {
        \"status\": \"healthy\",
        \"service\": \"Qdrant MCP\",
        \"port\": 8023,
        \"timestamp\": datetime.now().isoformat(),
        \"features\": [\"collections\", \"vectors\", \"search\", \"similarity\"],
        \"qdrant\": {
            \"status\": qdrant_status,
            \"info\": info
        }
    }

@app.post(\"/tools/collection\")
async def collection_tool(request: CollectionRequest) -> Dict[str, Any]:
    \"\"\"
    Collection management
    
    Tool: collection
    Description: Create, delete, list, get info about vector collections
    \"\"\"
    if not qdrant_client:
        raise HTTPException(status_code=503, detail=\"Qdrant connection not available\")
    
    try:
        if request.operation == \"create\":
            if not request.collection_name or not request.vector_size:
                raise HTTPException(status_code=400, detail=\"Collection name and vector size required\")
            
            distance_map = {
                \"Cosine\": Distance.COSINE,
                \"Euclid\": Distance.EUCLID,
                \"Dot\": Distance.DOT
            }
            
            distance_func = distance_map.get(request.distance, Distance.COSINE)
            
            await qdrant_client.create_collection(
                collection_name=request.collection_name,
                vectors_config=VectorParams(size=request.vector_size, distance=distance_func)
            )
            
            return {
                \"operation\": \"create\",
                \"collection_name\": request.collection_name,
                \"vector_size\": request.vector_size,
                \"distance\": request.distance,
                \"success\": True,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"delete\":
            if not request.collection_name:
                raise HTTPException(status_code=400, detail=\"Collection name required\")
            
            await qdrant_client.delete_collection(request.collection_name)
            
            return {
                \"operation\": \"delete\",
                \"collection_name\": request.collection_name,
                \"success\": True,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"list\":
            collections = await qdrant_client.get_collections()
            
            collection_list = []
            for col in collections.collections:
                info = await qdrant_client.get_collection(col.name)
                collection_list.append({
                    \"name\": col.name,
                    \"vectors_count\": info.vectors_count,
                    \"points_count\": info.points_count,
                    \"status\": info.status.value
                })
            
            return {
                \"operation\": \"list\",
                \"collections\": collection_list,
                \"collection_count\": len(collection_list),
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"info\":
            if not request.collection_name:
                raise HTTPException(status_code=400, detail=\"Collection name required\")
            
            info = await qdrant_client.get_collection(request.collection_name)
            
            return {
                \"operation\": \"info\",
                \"collection_name\": request.collection_name,
                \"info\": {
                    \"status\": info.status.value,
                    \"vectors_count\": info.vectors_count,
                    \"points_count\": info.points_count,
                    \"segments_count\": info.segments_count,
                    \"config\": {
                        \"vector_size\": info.config.params.vectors.size,
                        \"distance\": info.config.params.vectors.distance.value
                    }
                },
                \"timestamp\": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f\"Unknown operation: {request.operation}\")
        
    except Exception as e:
        logger.error(f\"Collection operation failed: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"Collection operation failed: {str(e)}\")

@app.post(\"/tools/vector\")
async def vector_tool(request: VectorRequest) -> Dict[str, Any]:
    \"\"\"
    Vector operations
    
    Tool: vector
    Description: Insert, update, delete, get vectors and their payloads
    \"\"\"
    if not qdrant_client:
        raise HTTPException(status_code=503, detail=\"Qdrant connection not available\")
    
    try:
        if request.operation == \"insert\":
            if not request.points:
                raise HTTPException(status_code=400, detail=\"Points required for insert\")
            
            points = []
            for point_data in request.points:
                point = PointStruct(
                    id=point_data.get(\"id\"),
                    vector=point_data.get(\"vector\"),
                    payload=point_data.get(\"payload\", {})
                )
                points.append(point)
            
            result = await qdrant_client.upsert(
                collection_name=request.collection_name,
                points=points
            )
            
            return {
                \"operation\": \"insert\",
                \"collection_name\": request.collection_name,
                \"points_inserted\": len(points),
                \"operation_id\": result.operation_id,
                \"status\": result.status.value,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"update\":
            if not request.point_id or not request.vector:
                raise HTTPException(status_code=400, detail=\"Point ID and vector required for update\")
            
            point = PointStruct(
                id=request.point_id,
                vector=request.vector,
                payload=request.payload or {}
            )
            
            result = await qdrant_client.upsert(
                collection_name=request.collection_name,
                points=[point]
            )
            
            return {
                \"operation\": \"update\",
                \"collection_name\": request.collection_name,
                \"point_id\": request.point_id,
                \"operation_id\": result.operation_id,
                \"status\": result.status.value,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"delete\":
            if not request.point_id:
                raise HTTPException(status_code=400, detail=\"Point ID required for delete\")
            
            result = await qdrant_client.delete(
                collection_name=request.collection_name,
                points_selector=[request.point_id]
            )
            
            return {
                \"operation\": \"delete\",
                \"collection_name\": request.collection_name,
                \"point_id\": request.point_id,
                \"operation_id\": result.operation_id,
                \"status\": result.status.value,
                \"timestamp\": datetime.now().isoformat()
            }
            
        elif request.operation == \"get\":
            if not request.point_id:
                raise HTTPException(status_code=400, detail=\"Point ID required for get\")
            
            points = await qdrant_client.retrieve(
                collection_name=request.collection_name,
                ids=[request.point_id],
                with_vectors=True,
                with_payload=True
            )
            
            if not points:
                return {
                    \"operation\": \"get\",
                    \"collection_name\": request.collection_name,
                    \"point_id\": request.point_id,
                    \"found\": False,
                    \"timestamp\": datetime.now().isoformat()
                }
            
            point = points[0]
            return {
                \"operation\": \"get\",
                \"collection_name\": request.collection_name,
                \"point_id\": request.point_id,
                \"point\": {
                    \"id\": point.id,
                    \"vector\": point.vector,
                    \"payload\": point.payload
                },
                \"found\": True,
                \"timestamp\": datetime.now().isoformat()
            }
        
        else:
            raise HTTPException(status_code=400, detail=f\"Unknown operation: {request.operation}\")
        
    except Exception as e:
        logger.error(f\"Vector operation failed: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"Vector operation failed: {str(e)}\")

@app.post(\"/tools/search\")
async def search_tool(request: SearchRequest) -> Dict[str, Any]:
    \"\"\"
    Vector similarity search
    
    Tool: search
    Description: Find similar vectors with optional filtering and scoring
    \"\"\"
    if not qdrant_client:
        raise HTTPException(status_code=503, detail=\"Qdrant connection not available\")
    
    try:
        # Build filter if provided
        search_filter = None
        if request.filter:
            conditions = []
            for field, value in request.filter.items():
                conditions.append(FieldCondition(key=field, match=MatchValue(value=value)))
            if conditions:
                search_filter = Filter(must=conditions)
        
        results = await qdrant_client.search(
            collection_name=request.collection_name,
            query_vector=request.query_vector,
            limit=request.limit,
            score_threshold=request.score_threshold,
            query_filter=search_filter,
            with_payload=request.with_payload,
            with_vectors=request.with_vectors
        )
        
        search_results = []
        for result in results:
            result_data = {
                \"id\": result.id,
                \"score\": result.score
            }
            
            if request.with_payload:
                result_data[\"payload\"] = result.payload
            
            if request.with_vectors:
                result_data[\"vector\"] = result.vector
            
            search_results.append(result_data)
        
        return {
            \"collection_name\": request.collection_name,
            \"query_vector_size\": len(request.query_vector),
            \"results\": search_results,
            \"result_count\": len(search_results),
            \"limit\": request.limit,
            \"score_threshold\": request.score_threshold,
            \"timestamp\": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f\"Search operation failed: {str(e)}\")
        raise HTTPException(status_code=500, detail=f\"Search operation failed: {str(e)}\")

@app.get(\"/tools/list\")
async def list_tools():
    \"\"\"List all available MCP tools\"\"\"
    return {
        \"tools\": [
            {
                \"name\": \"collection\",
                \"description\": \"Manage vector collections - create, delete, list, get info\",
                \"parameters\": {
                    \"operation\": \"string (required: create|delete|list|info)\",
                    \"collection_name\": \"string (optional, collection name)\",
                    \"vector_size\": \"integer (optional, vector dimension for create)\",
                    \"distance\": \"string (optional: Cosine|Euclid|Dot, default Cosine)\"
                }
            },
            {
                \"name\": \"vector\",
                \"description\": \"Vector operations - insert, update, delete, get points\",
                \"parameters\": {
                    \"operation\": \"string (required: insert|update|delete|get)\",
                    \"collection_name\": \"string (required, collection name)\",
                    \"points\": \"array (optional, list of points for insert)\",
                    \"point_id\": \"string|integer (optional, point ID)\",
                    \"vector\": \"array (optional, vector values)\",
                    \"payload\": \"object (optional, metadata payload)\"
                }
            },
            {
                \"name\": \"search\",
                \"description\": \"Vector similarity search with filtering and scoring\",
                \"parameters\": {
                    \"collection_name\": \"string (required, collection name)\",
                    \"query_vector\": \"array (required, query vector)\",
                    \"limit\": \"integer (optional, max results, default 10)\",
                    \"score_threshold\": \"float (optional, minimum similarity score)\",
                    \"filter\": \"object (optional, payload filter conditions)\",
                    \"with_payload\": \"boolean (optional, include payload, default true)\",
                    \"with_vectors\": \"boolean (optional, include vectors, default false)\"
                }
            }
        ]
    }

if __name__ == \"__main__\":
    import uvicorn
    uvicorn.run(app, host=\"0.0.0.0\", port=8000)