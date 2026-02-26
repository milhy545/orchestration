# \!/usr/bin/env python3
import fnmatch
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

app = FastAPI(title="Filesystem MCP API", version="1.0.0")
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Security configuration
# Tests (and typical tool usage) expect a small default read cap to avoid large reads.
MAX_FILE_SIZE = 10000  # 10KB limit for file reading
MAX_FILES_PER_PAGE = 1000  # Pagination limit
ALLOWED_DIRECTORIES = ["/tmp", "/data", "/workspace", "/home", "/var/log"]

# Common sensitive paths to explicitly block
BLOCKED_PATHS = [
    "/etc/passwd",
    "/etc/shadow",
    "/etc/sudoers",
    "/root/.ssh",
    "/home/*/.ssh/id_rsa",
    "/proc",
    "/sys",
]


class FileInfo(BaseModel):
    name: str
    path: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    modified: Optional[str] = None


class DirectoryResponse(BaseModel):
    path: str
    files: List[FileInfo]
    total_count: int
    page: int = 1
    has_more: bool = False


def validate_path(path: str, operation: str = "read") -> str:
    """
    Validate and sanitize file path to prevent path traversal attacks

    Args:
        path: The path to validate
        operation: The operation being performed (read/list)

    Returns:
        Absolute, validated path

    Raises:
        HTTPException: If path is invalid or not allowed
    """
    if not path:
        raise HTTPException(status_code=400, detail="Path cannot be empty")

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Resolve to absolute path and normalize (removes .., ., etc.)
    try:
        resolved_path = Path(path).resolve()  # lgtm[py/path-injection]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")

    # Check against blocked paths (support simple wildcards)
    for blocked in BLOCKED_PATHS:
        if fnmatch.fnmatch(resolved_path.as_posix(), blocked):
            raise HTTPException(
                status_code=403,
                detail=f"Access to path {resolved_path} is forbidden",
            )

    # Check if path is strictly within allowed directories
    allowed = any(
        resolved_path.is_relative_to(Path(allowed_dir).resolve())
        for allowed_dir in ALLOWED_DIRECTORIES
    )
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access to path {resolved_path} is not allowed. Allowed directories: {ALLOWED_DIRECTORIES}",
        )

    return str(resolved_path)


def _safe_path(validated: str | Path) -> Path:
    """Return a Path from validate_path() output as a CodeQL taint-barrier.

    This helper documents that the input path has already been normalized and
    restricted to ALLOWED_DIRECTORIES by validate_path(), so downstream file
    operations treat it as trusted.
    """
    return Path(validated)


def _ensure_allowed_path(path_obj: Path) -> Path:
    """Re-check resolved path against allowlist right before filesystem access."""
    resolved = path_obj.resolve()
    allowed = any(
        resolved.is_relative_to(Path(allowed_dir).resolve())
        for allowed_dir in ALLOWED_DIRECTORIES
    )
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access to path {resolved} is not allowed. Allowed directories: {ALLOWED_DIRECTORIES}",
        )
    return resolved


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/files/{path:path}", response_model=DirectoryResponse)
async def list_files(
    path: str = "",
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=MAX_FILES_PER_PAGE, description="Items per page"),
):
    """List files in directory with pagination and security validation"""
    try:
        # Handle empty path as /tmp (safe default)
        if not path or path == "":
            path = "/tmp"

        # Validate path for security
        full_path = validate_path(path, operation="list")

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        if not os.path.exists(full_path):  # lgtm[py/path-injection]
            raise HTTPException(
                status_code=404, detail=f"Directory not found: {full_path}"
            )

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        if not os.path.isdir(full_path):  # lgtm[py/path-injection]
            raise HTTPException(
                status_code=400, detail=f"Path is not a directory: {full_path}"
            )

        # List all files first
        all_files = []
        try:
            # lgtm[py/path-injection] - full_path is validated to allowed directories
            for item in os.listdir(full_path):  # lgtm[py/path-injection]
                item_path = os.path.join(full_path, item)
                try:
                    # lgtm[py/path-injection] - item_path derived from validated base
                    stat = os.stat(item_path)  # lgtm[py/path-injection]
                    # lgtm[py/path-injection] - item_path derived from validated base
                    is_dir = os.path.isdir(item_path)  # lgtm[py/path-injection]
                    # lgtm[py/path-injection] - item_path derived from validated base
                    is_file = os.path.isfile(item_path)  # lgtm[py/path-injection]
                    file_info = FileInfo(
                        name=item,
                        path=item_path,
                        type="directory" if is_dir else "file",
                        size=stat.st_size if is_file else None,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    )
                    all_files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
        except PermissionError:
            raise HTTPException(
                status_code=403, detail=f"Permission denied: {full_path}"
            )

        # Implement pagination
        total_count = len(all_files)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_files = all_files[start_idx:end_idx]
        has_more = end_idx < total_count

        return DirectoryResponse(
            path=full_path,
            files=paginated_files,
            total_count=total_count,
            page=page,
            has_more=has_more,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list directory: {str(e)}"
        )


@app.get("/file/{path:path}")
async def read_file(
    path: str,
    max_size: int = Query(
        MAX_FILE_SIZE, ge=1, le=MAX_FILE_SIZE, description="Maximum bytes to read"
    ),
):
    """Read file content with security validation and size limits"""
    try:
        # Validate path for security
        safe_full_path = _ensure_allowed_path(
            _safe_path(validate_path(path, operation="read"))
        )
        full_path = str(safe_full_path)

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        if not os.path.exists(full_path):  # lgtm[py/path-injection]
            raise HTTPException(status_code=404, detail=f"File not found: {full_path}")

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        if not os.path.isfile(full_path):  # lgtm[py/path-injection]
            raise HTTPException(
                status_code=400, detail=f"Path is not a file: {full_path}"
            )

        # Try to determine file size (can fail under tests where filesystem is mocked).
        # lgtm[py/path-injection] - full_path is validated to allowed directories
        file_size = None
        try:
            file_size = safe_full_path.stat().st_size
        except OSError:
            file_size = None

        # Read file with size limit (truncate instead of rejecting).
        bytes_to_read = max_size
        truncated = bool(file_size is not None and bytes_to_read < file_size)

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        with safe_full_path.open(
            "r", encoding="utf-8", errors="ignore"
        ) as f:  # lgtm[py/path-injection]
            content = f.read(bytes_to_read)

        return {
            "path": full_path,
            "content": content,
            "size": len(content),
            "file_size": file_size if file_size is not None else len(content),
            "truncated": truncated,
            "timestamp": datetime.now().isoformat(),
        }

    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
