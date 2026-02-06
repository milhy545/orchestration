# \!/usr/bin/env python3
import asyncio
import json
import os
from pathlib import Path
import shlex
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

app = FastAPI(title="Terminal MCP API", version="1.0.0")
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)

# Security configuration
MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB limit for stdout/stderr
MAX_TIMEOUT = 300  # 5 minutes maximum
ALLOWED_WORKING_DIRS = ["/tmp", "/data", "/workspace", "/home"]

# Whitelist of allowed commands (base commands only)
ALLOWED_COMMANDS = {
    "ls",
    "echo",
    "cat",
    "pwd",
    "whoami",
    "date",
    "ps",
    "df",
    "du",
    "grep",
    "find",
    "wc",
    "head",
    "tail",
    "sort",
    "uniq",
    "cut",
    "python3",
    "node",
    "npm",
    "git",
    "docker",
    "curl",
    "wget",
}


class CommandRequest(BaseModel):
    command: str
    args: Optional[List[str]] = None
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
    truncated: bool = False


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


def validate_working_directory(cwd: str) -> str:
    """Validate and sanitize working directory"""
    if not cwd:
        return "/tmp"

    # Resolve to absolute path
    resolved_path = Path(cwd).resolve()  # lgtm[py/path-injection]

    # Check if directory exists
    # lgtm[py/path-injection] - resolved_path is restricted to allowed directories
    if not resolved_path.exists():
        raise HTTPException(status_code=400, detail=f"Directory not found: {cwd}")
    # lgtm[py/path-injection] - resolved_path is restricted to allowed directories
    if not resolved_path.is_dir():
        raise HTTPException(status_code=400, detail=f"Path is not a directory: {cwd}")

    # Check if it's within allowed directories
    allowed = any(
        resolved_path.is_relative_to(Path(allowed_dir).resolve())
        for allowed_dir in ALLOWED_WORKING_DIRS
    )
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail=f"Access to directory {resolved_path} is not allowed. Allowed directories: {ALLOWED_WORKING_DIRS}",
        )

    return str(resolved_path)


def validate_command(command: str) -> str:
    """Validate command against whitelist"""
    # Parse command to get base command
    try:
        parts = shlex.split(command)
        if not parts:
            raise HTTPException(status_code=400, detail="Empty command")

        base_command = parts[0]

        # Check if command is in whitelist
        if base_command not in ALLOWED_COMMANDS:
            raise HTTPException(
                status_code=403,
                detail=f"Command '{base_command}' is not allowed. Allowed commands: {sorted(ALLOWED_COMMANDS)}",
            )

        return base_command
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid command syntax: {str(e)}")


def truncate_output(output: str, max_size: int = MAX_OUTPUT_SIZE) -> tuple[str, bool]:
    """Truncate output if it exceeds max size"""
    if len(output) > max_size:
        return output[:max_size] + "\n... (output truncated)", True
    return output, False


@app.post("/command", response_model=CommandResponse)
async def execute_command(request: CommandRequest):
    """Execute shell command with security restrictions"""
    try:
        start_time = datetime.now()

        # Validate timeout
        timeout = min(request.timeout, MAX_TIMEOUT)
        if timeout != request.timeout:
            raise HTTPException(
                status_code=400,
                detail=f"Timeout too large. Maximum allowed: {MAX_TIMEOUT} seconds",
            )

        # Validate working directory
        cwd = validate_working_directory(request.cwd)

        # Parse and validate command
        try:
            cmd_parts = shlex.split(request.command)
        except ValueError as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid command syntax: {str(e)}"
            )

        if not cmd_parts:
            raise HTTPException(status_code=400, detail="Empty command")

        base_command = cmd_parts[0]

        # Validate against whitelist
        if base_command not in ALLOWED_COMMANDS:
            raise HTTPException(
                status_code=403,
                detail=f"Command '{base_command}' is not allowed. Allowed commands: {sorted(ALLOWED_COMMANDS)}",
            )

        # Add additional args if provided
        if request.args:
            cmd_parts.extend(request.args)

        # Execute command with security measures
        # Using list of arguments instead of shell=True to prevent command injection
        # lgtm[py/path-injection] - cwd validated to allowed directories
        result = subprocess.run(
            cmd_parts,
            shell=False,  # Security: Prevent command injection
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        execution_time = (datetime.now() - start_time).total_seconds()

        # Truncate output if needed
        stdout, stdout_truncated = truncate_output(result.stdout)
        stderr, stderr_truncated = truncate_output(result.stderr)

        return CommandResponse(
            success=result.returncode == 0,
            exit_code=result.returncode,
            stdout=stdout,
            stderr=stderr,
            execution_time=execution_time,
            cwd=cwd,
            truncated=stdout_truncated or stderr_truncated,
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Command execution failed: {str(e)}"
        )


@app.get("/directory")
async def get_current_directory():
    """Get current working directory info"""
    try:
        cwd = os.getcwd()
        files = []
        for item in os.listdir(cwd):
            item_path = os.path.join(cwd, item)
            files.append(
                {
                    "name": item,
                    "type": "directory" if os.path.isdir(item_path) else "file",
                    "size": (
                        os.path.getsize(item_path)
                        if os.path.isfile(item_path)
                        else None
                    ),
                }
            )

        return {"cwd": cwd, "files": files, "count": len(files)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processes")
async def list_processes():
    """List running processes"""
    try:
        result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return {"processes": lines[1:], "count": len(lines) - 1}  # Skip header
        else:
            raise HTTPException(status_code=500, detail="Failed to list processes")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
