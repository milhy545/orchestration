"""FastAPI wrapper for Mega Orchestrator - Vercel-compatible entry point."""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import logging

from mega_orchestrator.mega_orchestrator_complete import MegaOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mega Orchestrator API",
    description="REST API wrapper for Mega Orchestration System",
    version="1.0.0"
)

# Global orchestrator instance
_orchestrator = None

@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator on startup."""
    global _orchestrator
    try:
        _orchestrator = MegaOrchestrator(port=7000, backup_mode=False)
        logger.info("Mega Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Mega Orchestrator: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "mega-orchestrator",
        "version": "1.0.0"
    }

@app.get("/status")
async def status():
    """Get orchestrator status."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        return {
            "status": "running",
            "orchestrator": {
                "port": _orchestrator.port,
                "backup_mode": _orchestrator.backup_mode
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orchestrate")
async def orchestrate(query: str, mode: str = "auto"):
    """Execute orchestration task."""
    if not _orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Execute orchestration
        result = await asyncio.to_thread(
            _orchestrator.process_query,
            query,
            mode
        )
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Orchestration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Mega Orchestrator API",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "orchestrate": "/orchestrate"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
