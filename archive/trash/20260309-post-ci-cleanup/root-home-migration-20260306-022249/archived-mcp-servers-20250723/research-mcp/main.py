from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from typing import List, Optional
import os # Added import - forced rebuild 2025-06-29-2015

app = FastAPI(
    title="Research MCP API",
    description="API for research operations (Perplexity AI).",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"

class SearchResult(BaseModel):
    query: str
    response: str
    sources: Optional[List[dict]] = None

@app.post("/research/search", response_model=SearchResult)
async def search_web(query: str, model: str = "llama-3.1-sonar-small-128k-online"):
    """
    Search the web using Perplexity AI.
    """
    if not PERPLEXITY_API_KEY:
        raise HTTPException(status_code=500, detail="PERPLEXITY_API_KEY not set.")

    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are an AI assistant that provides factual information."},
            {"role": "user", "content": query}
        ],
        "return_citations": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            content = data["choices"][0]["message"]["content"]
            sources = data["choices"][0]["message"].get("citations")
            
            return SearchResult(query=query, response=content, sources=sources)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Perplexity API error: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Network error connecting to Perplexity API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))