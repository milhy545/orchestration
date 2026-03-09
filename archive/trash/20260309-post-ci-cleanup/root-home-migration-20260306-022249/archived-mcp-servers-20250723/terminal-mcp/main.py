#\!/usr/bin/env python3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import subprocess
import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio

app = FastAPI(title="Terminal MCP API", version="1.0.0")

class CommandRequest(BaseModel):
    command: str
    cwd: Optional[str] = None
    timeout: Optional[int] = 30
    user_id: Optional[str] = "default"

class CommandResponse(BaseModel):
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time: float
    cwd: str

@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Execute shell command"""
    try:
        start_time = datetime.now()
        
        # Set working directory
        cwd = request.cwd or "/"
        if not os.path.exists(cwd):
            raise HTTPException(status_code=400, detail=f"Directory not found: {cwd}")
        
        # Execute command
        result = subprocess.run(
            request.command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=request.timeout
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return CommandResponse(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=execution_time,
            cwd=cwd
        )
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/directory")
async def get_current_directory():
    """Get current working directory info"""
    try:
        cwd = os.getcwd()
        files = []
        for item in os.listdir(cwd):
            item_path = os.path.join(cwd, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else None
            })
        
        return {
            "cwd": cwd,
            "files": files,
            "count": len(files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/processes")
async def list_processes():
    """List running processes"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            return {
                "processes": lines[1:],  # Skip header
                "count": len(lines) - 1
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to list processes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
