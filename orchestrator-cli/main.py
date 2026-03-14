from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Orchestrator CLI", version="1.0.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Orchestrator CLI"}

@app.get("/mcp/services")
async def list_mcp_services():
    return {
        "services": [
            {"name": "git-mcp", "port": 7002, "status": "running"},
            {"name": "terminal-mcp", "port": 7003, "status": "running"},
            {"name": "filesystem-mcp", "port": 7001, "status": "running"}
        ]
    }