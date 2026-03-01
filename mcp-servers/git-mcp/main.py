import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

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
    if not (resolved_path / ".git").exists():  # lgtm[py/path-injection]
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


class GitCommitRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=200)
    author_name: Optional[str] = Field("Mega Orchestrator", max_length=100)
    author_email: Optional[str] = Field("mega-orchestrator@localhost", max_length=200)


class GitCommitResponse(BaseModel):
    success: bool
    commit: str
    repository: str
    message: str


class GitPushRequest(BaseModel):
    set_upstream: bool = False
    force: bool = False


class GitPushResponse(BaseModel):
    success: bool
    repository: str
    remote: str
    branch: str
    pushed: bool
    details: str


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


@app.post("/git/{path:path}/commit", response_model=GitCommitResponse)
async def git_commit(path: str, request: GitCommitRequest):
    """
    Create a commit for already staged changes in a validated repository.
    """
    try:
        validated_path = validate_repository_path(path)

        status_result = subprocess.run(
            ["git", "-C", validated_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        if not status_result.stdout.strip():
            raise HTTPException(status_code=400, detail="No changes to commit")

        subprocess.run(
            ["git", "-C", validated_path, "add", "-A"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        commit_result = subprocess.run(
            [
                "git",
                "-c",
                f"user.name={request.author_name}",
                "-c",
                f"user.email={request.author_email}",
                "-C",
                validated_path,
                "commit",
                "-m",
                request.message,
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        head_result = subprocess.run(
            ["git", "-C", validated_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        commit_hash = head_result.stdout.strip()
        if not commit_hash:
            raise HTTPException(status_code=500, detail="Commit succeeded but hash is unavailable")

        return GitCommitResponse(
            success=True,
            commit=commit_hash,
            repository=validated_path,
            message=request.message,
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git command timed out")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create git commit: {str(e)}")


@app.post("/git/{path:path}/push", response_model=GitPushResponse)
async def git_push(path: str, request: GitPushRequest):
    """
    Push the current branch to its configured upstream.
    """
    try:
        if request.force:
            raise HTTPException(status_code=400, detail="Force push is not allowed")
        if request.set_upstream:
            raise HTTPException(
                status_code=400,
                detail="Automatic upstream setup is not supported in this version",
            )

        validated_path = validate_repository_path(path)

        status_result = subprocess.run(
            ["git", "-C", validated_path, "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )
        if status_result.stdout.strip():
            raise HTTPException(
                status_code=400,
                detail="Working tree is not clean; commit or stash before push",
            )

        branch_result = subprocess.run(
            ["git", "-C", validated_path, "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )
        branch = branch_result.stdout.strip()
        if not branch:
            raise HTTPException(status_code=500, detail="Current branch is unavailable")

        try:
            upstream_result = subprocess.run(
                ["git", "-C", validated_path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"],
                capture_output=True,
                text=True,
                check=True,
                timeout=GIT_TIMEOUT,
            )
        except subprocess.CalledProcessError:
            raise HTTPException(status_code=400, detail="Upstream branch is not configured")

        upstream = upstream_result.stdout.strip()
        if not upstream or "/" not in upstream:
            raise HTTPException(status_code=400, detail="Upstream branch is not configured")
        remote, _, upstream_branch = upstream.partition("/")
        if not remote or not upstream_branch:
            raise HTTPException(status_code=400, detail="Upstream branch is not configured")

        push_result = subprocess.run(
            ["git", "-C", validated_path, "push"],
            capture_output=True,
            text=True,
            check=True,
            timeout=GIT_TIMEOUT,
        )

        details = (push_result.stdout or push_result.stderr or "").strip()
        return GitPushResponse(
            success=True,
            repository=validated_path,
            remote=remote,
            branch=branch,
            pushed=True,
            details=details or f"Pushed {branch} to {remote}/{upstream_branch}",
        )

    except HTTPException:
        raise
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Git command timed out")
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").strip()
        raise HTTPException(status_code=500, detail=f"Git command failed: {stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to push git branch: {str(e)}")
