# \!/usr/bin/env python3
import fnmatch
import json
import mimetypes
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

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


class FileWriteRequest(BaseModel):
    path: str
    content: str
    overwrite: bool = False
    create_dirs: bool = False


class FileWriteResponse(BaseModel):
    path: str
    bytes_written: int
    created: bool
    overwritten: bool
    timestamp: str


class SearchMatch(BaseModel):
    name: str
    path: str
    type: str
    size: Optional[int] = None
    modified: Optional[str] = None
    snippet: Optional[str] = None


class FileSearchResponse(BaseModel):
    root: str
    matches: List[SearchMatch]
    count: int
    truncated: bool = False


class FileAnalyzeResponse(BaseModel):
    path: str
    exists: bool
    type: str
    size: int
    extension: str = ""
    line_count: Optional[int] = None
    mime_guess: Optional[str] = None
    preview: Optional[str] = None
    truncated: bool = False
    timestamp: str


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


def _build_file_info(item_path: Path) -> FileInfo:
    """Build file metadata for a validated path."""
    stat = item_path.stat()
    return FileInfo(
        name=item_path.name,
        path=str(item_path),
        type="directory" if item_path.is_dir() else "file",
        size=stat.st_size if item_path.is_file() else None,
        modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
    )


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
            file_size = os.path.getsize(full_path)  # lgtm[py/path-injection]
        except OSError:
            file_size = None

        # Read file with size limit (truncate instead of rejecting).
        bytes_to_read = max_size
        truncated = bool(file_size is not None and bytes_to_read < file_size)

        # lgtm[py/path-injection] - full_path is validated to allowed directories
        with open(
            full_path, "r", encoding="utf-8", errors="ignore"
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


@app.post("/file/write", response_model=FileWriteResponse)
async def write_file(request: FileWriteRequest):
    """Write a UTF-8 text file within the allowed directory sandbox."""
    try:
        safe_path = _ensure_allowed_path(
            _safe_path(validate_path(request.path, operation="write"))
        )
        parent = _ensure_allowed_path(safe_path.parent)

        if not parent.exists():
            if not request.create_dirs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parent directory does not exist: {parent}",
                )
            parent.mkdir(parents=True, exist_ok=True)
            _ensure_allowed_path(parent)

        existed = safe_path.exists()
        if existed and safe_path.is_dir():
            raise HTTPException(
                status_code=400, detail=f"Path is a directory: {safe_path}"
            )
        if existed and not request.overwrite:
            raise HTTPException(
                status_code=409, detail=f"File already exists: {safe_path}"
            )

        safe_path.write_text(request.content, encoding="utf-8")

        return FileWriteResponse(
            path=str(safe_path),
            bytes_written=len(request.content.encode("utf-8")),
            created=not existed,
            overwritten=existed,
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(
            status_code=403, detail=f"Permission denied: {request.path}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")


@app.get("/search/files", response_model=FileSearchResponse)
async def search_files(
    root: str = Query(..., description="Root directory to search"),
    pattern: str = Query("*", min_length=1, description="Glob pattern"),
    limit: int = Query(100, ge=1, le=MAX_FILES_PER_PAGE, description="Maximum matches"),
    content_query: Optional[str] = Query(
        None, description="Optional text to search inside files"
    ),
    include_hidden: bool = Query(False, description="Include dotfiles and dotdirs"),
):
    """Search files by name and optionally by content."""
    try:
        safe_root = _ensure_allowed_path(
            _safe_path(validate_path(root, operation="list"))
        )
        if not safe_root.exists():
            raise HTTPException(
                status_code=404, detail=f"Directory not found: {safe_root}"
            )
        if not safe_root.is_dir():
            raise HTTPException(
                status_code=400, detail=f"Path is not a directory: {safe_root}"
            )

        matches: List[SearchMatch] = []
        truncated = False

        for current_root, dirnames, filenames in os.walk(safe_root):
            current_path = _ensure_allowed_path(Path(current_root))

            if not include_hidden:
                dirnames[:] = [name for name in dirnames if not name.startswith(".")]
                filenames = [name for name in filenames if not name.startswith(".")]

            for name in filenames:
                if not fnmatch.fnmatch(name, pattern):
                    continue

                file_path = current_path / name
                snippet = None
                if content_query:
                    try:
                        if file_path.stat().st_size > MAX_FILE_SIZE:
                            continue
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                    except (OSError, PermissionError):
                        continue
                    if content_query not in content:
                        continue
                    match_index = content.find(content_query)
                    start = max(0, match_index - 40)
                    end = min(len(content), match_index + len(content_query) + 40)
                    snippet = content[start:end]

                info = _build_file_info(file_path)
                matches.append(
                    SearchMatch(
                        name=info.name,
                        path=info.path,
                        type=info.type,
                        size=info.size,
                        modified=info.modified,
                        snippet=snippet,
                    )
                )

                if len(matches) >= limit:
                    truncated = True
                    return FileSearchResponse(
                        root=str(safe_root),
                        matches=matches,
                        count=len(matches),
                        truncated=truncated,
                    )

        return FileSearchResponse(
            root=str(safe_root),
            matches=matches,
            count=len(matches),
            truncated=truncated,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search files: {str(e)}")


@app.get("/analyze/{path:path}", response_model=FileAnalyzeResponse)
async def analyze_file(
    path: str,
    max_preview: int = Query(4000, ge=1, le=10000, description="Maximum preview size"),
):
    """Return basic metadata and a bounded preview for a file or directory."""
    try:
        safe_path = _ensure_allowed_path(
            _safe_path(validate_path(path, operation="read"))
        )
        if not safe_path.exists():
            raise HTTPException(status_code=404, detail=f"Path not found: {safe_path}")

        stat = safe_path.stat()
        file_type = "directory" if safe_path.is_dir() else "file"
        mime_guess, _ = mimetypes.guess_type(str(safe_path))
        preview = None
        line_count = None
        truncated = False

        if safe_path.is_file():
            content = safe_path.read_text(encoding="utf-8", errors="ignore")
            line_count = content.count("\n") + (
                1 if content and not content.endswith("\n") else 0
            )
            preview = content[:max_preview]
            truncated = len(content) > max_preview

        return FileAnalyzeResponse(
            path=str(safe_path),
            exists=True,
            type=file_type,
            size=stat.st_size,
            extension=safe_path.suffix,
            line_count=line_count,
            mime_guess=mime_guess,
            preview=preview,
            truncated=truncated,
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze file: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
