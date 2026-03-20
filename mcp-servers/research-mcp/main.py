import json
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

app = FastAPI(
    title="Research MCP API - Enhanced",
    description="Complete Perplexity AI research API with all 4 variants and 3 switchable models.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class SearchResult(BaseModel):
    query: str
    response: str
    sources: Optional[List[str]] = None
    model_used: str
    search_type: str


class StructuredResult(BaseModel):
    query: str
    structured_data: dict
    sources: Optional[List[str]] = None
    model_used: str


@app.get("/health")
async def health() -> Dict[str, Any]:
    """Basic health endpoint for orchestration reachability checks."""
    configured = bool(PERPLEXITY_API_KEY and PERPLEXITY_API_KEY != "your_perplexity_api_key_here")
    return {
        "status": "healthy",
        "service": "research-mcp",
        "perplexity_configured": configured,
    }


# 1. Latest News Search


@app.post("/research/news", response_model=SearchResult)
async def search_news(
    query: str,
    model: str = Query(
        "sonar-pro",
        description="Model: sonar-pro, sonar-reasoning-pro, sonar-deep-research",
    ),
):
    """Latest news search with real-time information."""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant that provides the latest news and current events.",
            },
            {"role": "user", "content": query},
        ],
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            sources = data.get("citations", [])

            return SearchResult(
                query=query,
                response=content,
                sources=sources,
                model_used=model,
                search_type="news",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 2. Domain Search


@app.post("/research/domain", response_model=SearchResult)
async def search_domain(
    query: str,
    domains: List[str] = Query(..., description="Domain filters like ['arxiv.org']"),
    recency: str = Query("month", description="Recency filter: day, week, month, year"),
    model: str = Query(
        "sonar-pro",
        description="Model: sonar-pro, sonar-reasoning-pro, sonar-deep-research",
    ),
):
    """Search specific domains with recency filtering."""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI research assistant focused on domain-specific sources.",
            },
            {"role": "user", "content": query},
        ],
        "search_domain_filter": domains,
        "search_recency_filter": recency,
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            sources = data.get("citations", [])

            return SearchResult(
                query=query,
                response=content,
                sources=sources,
                model_used=model,
                search_type="domain",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 3. Academic Search


@app.post("/research/academic", response_model=SearchResult)
async def search_academic(
    query: str,
    model: str = Query(
        "sonar-pro",
        description="Model: sonar-pro, sonar-reasoning-pro, sonar-deep-research",
    ),
):
    """Academic and peer-reviewed research search."""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant specialized in academic research and peer-reviewed sources.",
            },
            {"role": "user", "content": query},
        ],
        "search_filter": "academic",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            sources = data.get("citations", [])

            return SearchResult(
                query=query,
                response=content,
                sources=sources,
                model_used=model,
                search_type="academic",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 4. Structured Outputs


@app.post("/research/structured", response_model=StructuredResult)
async def search_structured(
    query: str,
    schema: dict,
    model: str = Query(
        "sonar-pro",
        description="Model: sonar-pro, sonar-reasoning-pro, sonar-deep-research",
    ),
):
    """Structured data extraction with JSON schema."""
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are an AI assistant that provides structured data responses.",
            },
            {"role": "user", "content": query},
        ],
        "response_format": {"type": "json_schema", "json_schema": {"schema": schema}},
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                PERPLEXITY_API_URL, headers=headers, json=payload, timeout=90
            )
            response.raise_for_status()
            data = response.json()

            content = data["choices"][0]["message"]["content"]
            sources = data.get("citations", [])

            # Parse JSON response
            try:
                structured_data = json.loads(content)
            except json.JSONDecodeError:
                structured_data = {"raw_response": content}

            return StructuredResult(
                query=query,
                structured_data=structured_data,
                sources=sources,
                model_used=model,
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoint (backward compatibility)


@app.post("/research/search", response_model=SearchResult)
async def search_web(query: str, model: str = "sonar-pro"):
    """Legacy endpoint - redirects to news search."""
    return await search_news(query, model)
