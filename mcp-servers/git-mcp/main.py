import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

app = FastAPI(
    title="Git MCP API",
    description="API for Git operations with security controls.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Security configuration
GIT_TIMEOUT = 30  # seconds
MAX_LOG_ENTRIES = 1000
MAX_DIFF_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_REPOSITORIES = ["/data", "/workspace", "/tmp", "/home"]


def validate_repository_path(path: str) -> str:
    """
    Validate repository path to prevent path traversal and unauthorized access

    Args:
        path: Repository path to validate

    Returns:
        Validated absolute path

    Raises:
        HTTPException: If path is invalid or not allowed
    """
    if not path:
        raise HTTPException(status_code=400, detail="Repository path cannot be empty")

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Resolve to absolute path and normalize
    try:
        resolved_path = Path(path).resolve()  # lgtm[py/path-injection]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")

    # Check if path is within allowed repositories
    allowed = any(
        resolved_path.is_relative_to(Path(allowed_repo).resolve())
        for allowed_repo in ALLOWED_REPOSITORIES
    )
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access to repository {resolved_path} is not allowed. Allowed locations: {ALLOWED_REPOSITORIES}",
        )

    # Verify it's actually a git repository
    # lgtm[py/path-injection] - resolved_path is restricted to allowed repositories
    if not (resolved_path / ".git").exists():
        raise HTTPException(
            status_code=400, detail=f"Path {resolved_path} is not a git repository"
        )

    return str(resolved_path)


class GitStatus(BaseModel):
    status: str
    repository: str


class GitLog(BaseModel):
    log: List[str]
    count: int
    repository: str


class GitDiff(BaseModel):
    diff: str
    truncated: bool = False
    repository: str


@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        # Check git is available
        # lgtm[py/path-injection] - validated_path is restricted to allowed repositories
        result = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, timeout=5
        )
        return {
            "status": "healthy",
            "service": "Git MCP",
            "git_version": result.stdout.strip(),
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Git unavailable: {str(e)}")


@app.get("/git/{path:path}/status", response_model=GitStatus)
async def git_status(path: str):
    """
    Get git repository status with security validation.
    """
    try:
        # Validate repository path
        validated_path = validate_repository_path(path)

        # lgtm[py/path-injection] - validated_path is restricted to allowed repositories
        result = subprocess.run(
            ["git", "-C", validated_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        return GitStatus(status=result.stdout, repository=validated_path)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git command timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get git status: {str(e)}"
        )


@app.get("/git/{path:path}/log", response_model=GitLog)
async def git_log(
    path: str,
    limit: int = Query(
        5, ge=1, le=MAX_LOG_ENTRIES, description="Number of commits to show"
    ),
):
    """
    Get git commit log with limits.
    """
    try:
        # Validate repository path
        validated_path = validate_repository_path(path)

        # lgtm[py/path-injection] - validated_path is restricted to allowed repositories
        result = subprocess.run(
            ["git", "-C", validated_path, "log", f"-n{limit}", "--oneline"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        log_lines = result.stdout.strip().split("\n") if result.stdout.strip() else []

        return GitLog(log=log_lines, count=len(log_lines), repository=validated_path)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git command timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get git log: {str(e)}")


@app.get("/git/{path:path}/diff", response_model=GitDiff)
async def git_diff(path: str):
    """
    Get git diff with size limits.
    """
    try:
        # Validate repository path
        validated_path = validate_repository_path(path)

        result = subprocess.run(
            ["git", "-C", validated_path, "diff"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        diff_output = result.stdout
        truncated = False

        # Truncate if too large
        if len(diff_output) > MAX_DIFF_SIZE:
            diff_output = diff_output[:MAX_DIFF_SIZE] + "\n... (diff truncated)"
            truncated = True

        return GitDiff(diff=diff_output, truncated=truncated, repository=validated_path)

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git command timed out")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Git command failed: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get git diff: {str(e)}")
