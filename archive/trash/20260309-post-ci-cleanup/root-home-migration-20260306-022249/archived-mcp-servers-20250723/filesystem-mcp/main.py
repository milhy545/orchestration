#\!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

app = FastAPI(title="Filesystem MCP API", version="1.0.0")

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

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/files/{path:path}", response_model=DirectoryResponse)
async def list_files(path: str = ""):
    """List files in directory"""
    # Handle empty path as root
    if not path or path == "" or path == "/":
        full_path = "/"
    else:
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path
        full_path = path
    
    try:
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"Directory not found: {full_path}")
        
        if not os.path.isdir(full_path):
            raise HTTPException(status_code=400, detail=f"Path is not a directory: {full_path}")
        
        files = []
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
                    files.append(file_info)
                except (OSError, PermissionError):
                    # Skip files we can't access
                    continue
        except PermissionError:
            raise HTTPException(status_code=403, detail=f"Permission denied: {full_path}")
        
        return DirectoryResponse(
            path=full_path,
            files=files,
            total_count=len(files)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/file/{path:path}")
async def read_file(path: str):
    """Read file content"""
    if not path.startswith("/"):
        path = "/" + path
    
    try:
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        
        if not os.path.isfile(path):
            raise HTTPException(status_code=400, detail=f"Path is not a file: {path}")
        
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(10000)  # Limit to 10KB
        
        return {
            "path": path,
            "content": content,
            "size": len(content),
            "timestamp": datetime.now().isoformat()
        }
    
    except PermissionError:
        raise HTTPException(status_code=403, detail=f"Permission denied: {path}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
