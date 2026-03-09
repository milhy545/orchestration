from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
from typing import List, Optional

app = FastAPI(
    title="Git MCP API",
    description="API for Git operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

class GitStatus(BaseModel):
    status: str

class GitLog(BaseModel):
    log: List[str]

class GitDiff(BaseModel):
    diff: str

@app.get("/git/{path:path}/status", response_model=GitStatus)
async def git_status(path: str):
    """
    Get git repository status.
    """
    try:
        # Expect path to be absolute path inside the container
        full_path = path 
        result = subprocess.run(["git", "-C", full_path, "status", "--porcelain"], capture_output=True, text=True, check=True)
        return GitStatus(status=result.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/git/{path:path}/log", response_model=GitLog)
async def git_log(path: str, limit: int = 5):
    """
    Get git commit log.
    """
    try:
        full_path = path
        result = subprocess.run(["git", "-C", full_path, "log", f"-n{limit}", "--oneline"], capture_output=True, text=True, check=True)
        return GitLog(log=result.stdout.strip().split("\n"))
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/git/{path:path}/diff", response_model=GitDiff)
async def git_diff(path: str):
    """
    Get git diff.
    """
    try:
        full_path = path
        result = subprocess.run(["git", "-C", full_path, "diff"], capture_output=True, text=True, check=True)
        return GitDiff(diff=result.stdout)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))