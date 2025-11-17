#\!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

app = FastAPI(title="Filesystem MCP API", version="1.0.0")
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Security configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for file reading
MAX_FILES_PER_PAGE = 1000  # Pagination limit
ALLOWED_DIRECTORIES = ["/tmp", "/data", "/workspace", "/home", "/var/log"]

# Common sensitive paths to explicitly block
BLOCKED_PATHS = [
    "/etc/passwd", "/etc/shadow", "/etc/sudoers",
    "/root/.ssh", "/home/*/.ssh/id_rsa",
    "/proc", "/sys"
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
        abs_path = os.path.abspath(path)
        resolved_path = str(Path(abs_path).resolve())
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid path: {str(e)}")

    # Check against blocked paths
    for blocked in BLOCKED_PATHS:
        if "*" in blocked:
            # Handle wildcards
            blocked_pattern = blocked.replace("*", "")
            if blocked_pattern in resolved_path:
                raise HTTPException(
                    status_code=403,
                    detail=f"Access to path {resolved_path} is forbidden"
                )
        elif resolved_path.startswith(blocked) or resolved_path == blocked:
            raise HTTPException(
                status_code=403,
                detail=f"Access to path {resolved_path} is forbidden"
            )

    # Check if path is strictly within allowed directories (not just prefix match)
    allowed = any(os.path.commonpath([resolved_path, allowed_dir]) == allowed_dir for allowed_dir in ALLOWED_DIRECTORIES)
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access to path {resolved_path} is not allowed. Allowed directories: {ALLOWED_DIRECTORIES}"
        )

    # Additional check: ensure no path traversal happened
    if ".." in path:
        raise HTTPException(
            status_code=403,
            detail="Path traversal detected (..). Please use absolute paths only."
        )

    return resolved_path


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/files/{path:path}", response_model=DirectoryResponse)
async def list_files(
    path: str = "",
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(100, ge=1, le=MAX_FILES_PER_PAGE, description="Items per page")
):
    """List files in directory with pagination and security validation"""
    try:
        # Handle empty path as /tmp (safe default)
        if not path or path == "":
            path = "/tmp"

        # Validate path for security
        full_path = validate_path(path, operation="list")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"Directory not found: {full_path}")

        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {full_path}")

        # List all files first
        all_files = []
        try:
            for item in os.listdir(full_path):
                item_path = os.path.join(full_path, item)
                try:
                    stat = os.stat(item_path)
                    file_info = FileInfo(
                        name=item,
                        path=item_path,
                        type="directory" if os.path.isdir(item_path) else "file",
                        size=stat.st_size if os.path.isfile(item_path) else None,
                        modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
                    )
                    all_files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Permission denied: {full_path}")

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
            has_more=has_more
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list directory: {str(e)}")

@app.get("/file/{path:path}")
async def read_file(
    path: str,
    max_size: int = Query(MAX_FILE_SIZE, ge=1, le=MAX_FILE_SIZE, description="Maximum bytes to read")
):
    """Read file content with security validation and size limits"""
    try:
        # Validate path for security
        full_path = validate_path(path, operation="read")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"File not found: {full_path}")

        if not os.path.isfile(full_path):
            raise HTTPException(status_code=400, detail=f"Path is not a file: {full_path}")

        # Check file size before reading
        file_size = os.path.getsize(full_path)
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large ({file_size} bytes). Maximum allowed: {MAX_FILE_SIZE} bytes"
            )

        # Read file with size limit
        bytes_to_read = min(max_size, file_size)
        truncated = bytes_to_read < file_size

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(bytes_to_read)

        return {
            "path": full_path,
            "content": content,
            "size": len(content),
            "file_size": file_size,
            "truncated": truncated,
            "timestamp": datetime.now().isoformat()
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
