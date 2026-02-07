#!/usr/bin/env python3
"""
Config MCP Service - Environment variables, configuration management
Port: 7009
"""

import configparser
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Config MCP Service",
    description="Environment variables and configuration file management",
    version="1.0.0",
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Configuration storage paths
CONFIG_BASE_PATH = Path(os.environ.get("CONFIG_BASE_PATH", "/app/configs"))
try:
    CONFIG_BASE_PATH.mkdir(parents=True, exist_ok=True)
except OSError as exc:
    fallback_path = Path(os.environ.get("CONFIG_BASE_PATH_FALLBACK", "/tmp/configs"))
    fallback_path.mkdir(parents=True, exist_ok=True)
    logger.warning(
        "CONFIG_BASE_PATH not writable (%s). Falling back to %s",
        exc,
        fallback_path,
    )
    CONFIG_BASE_PATH = fallback_path


def resolve_config_path(user_path: str) -> Path:
    """Resolve a user-provided path safely within CONFIG_BASE_PATH."""
    if not user_path:
        raise HTTPException(status_code=400, detail="file_path is required")

    candidate = Path(user_path)
    if candidate.is_absolute():
        raise HTTPException(status_code=403, detail="Path outside allowed directory")

    resolved = (CONFIG_BASE_PATH / candidate).resolve()  # lgtm[py/path-injection]
    try:
        resolved.relative_to(CONFIG_BASE_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path outside allowed directory")

    return resolved


def validate_backup_name(backup_name: str) -> str:
    if not backup_name:
        raise HTTPException(status_code=400, detail="Backup name required")
    if ".." in backup_name or "/" in backup_name or "\\" in backup_name:
        raise HTTPException(status_code=400, detail="Invalid backup name")
    return backup_name


def validate_backup_patterns(patterns: List[str]) -> List[str]:
    sanitized = []
    for pattern in patterns:
        if ".." in pattern or "/" in pattern or "\\" in pattern:
            raise HTTPException(status_code=400, detail="Invalid file pattern")
        sanitized.append(pattern)
    return sanitized


# Request/Response Models


class EnvVarRequest(BaseModel):
    """Environment variable operation request"""

    operation: str = Field(..., description="get, set, list, delete")
    key: Optional[str] = None
    value: Optional[str] = None
    prefix: Optional[str] = None  # For listing with prefix filter


class ConfigFileRequest(BaseModel):
    """Configuration file operation request"""

    operation: str = Field(..., description="read, write, create, delete, list")
    file_path: str
    format: Optional[str] = "json"  # json, yaml, ini, env
    content: Optional[Dict[str, Any]] = None
    section: Optional[str] = None  # For INI files


class ConfigValidateRequest(BaseModel):
    """Configuration validation request"""

    config_data: Dict[str, Any]
    schema: Optional[Dict[str, Any]] = None
    required_keys: Optional[List[str]] = []
    value_types: Optional[Dict[str, str]] = {}  # key -> type mapping


class ConfigBackupRequest(BaseModel):
    """Configuration backup request"""

    operation: str = Field(..., description="create, restore, list, delete")
    backup_name: Optional[str] = None
    file_patterns: Optional[List[str]] = ["*.json", "*.yaml", "*.yml", "*.ini", "*.env"]


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Config MCP",
        "port": 7009,
        "timestamp": datetime.now().isoformat(),
        "features": ["env_vars", "config_files", "validation", "backup"],
        "storage": {
            "config_path": str(CONFIG_BASE_PATH),
            "writable": os.access(CONFIG_BASE_PATH, os.W_OK),
        },
    }


@app.post("/tools/env_vars")
async def env_vars_tool(request: EnvVarRequest) -> Dict[str, Any]:
    """
    Manage environment variables

    Tool: env_vars
    Description: Get, set, list, or delete environment variables
    """
    try:
        if request.operation == "get":
            if not request.key:
                raise HTTPException(
                    status_code=400, detail="Key required for get operation"
                )

            value = os.environ.get(request.key)
            return {
                "operation": "get",
                "key": request.key,
                "value": value,
                "found": value is not None,
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "set":
            if not request.key or request.value is None:
                raise HTTPException(
                    status_code=400, detail="Key and value required for set operation"
                )

            old_value = os.environ.get(request.key)
            os.environ[request.key] = request.value

            return {
                "operation": "set",
                "key": request.key,
                "new_value": request.value,
                "old_value": old_value,
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "list":
            env_vars = dict(os.environ)

            if request.prefix:
                env_vars = {
                    k: v for k, v in env_vars.items() if k.startswith(request.prefix)
                }

            return {
                "operation": "list",
                "count": len(env_vars),
                "prefix_filter": request.prefix,
                "variables": env_vars,
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "delete":
            if not request.key:
                raise HTTPException(
                    status_code=400, detail="Key required for delete operation"
                )

            old_value = os.environ.get(request.key)
            if old_value is not None:
                del os.environ[request.key]

            return {
                "operation": "delete",
                "key": request.key,
                "deleted": old_value is not None,
                "old_value": old_value,
                "timestamp": datetime.now().isoformat(),
            }

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown operation: {request.operation}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Environment variable operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Env var operation failed")


@app.post("/tools/config_file")
async def config_file_tool(request: ConfigFileRequest) -> Dict[str, Any]:
    """
    Manage configuration files

    Tool: config_file
    Description: Read, write, create, delete, or list configuration files
    """
    try:
        if request.operation == "list":
            if not CONFIG_BASE_PATH.exists():
                return {
                    "operation": "list",
                    "files": [],
                    "count": 0,
                    "timestamp": datetime.now().isoformat(),
                }

            files = []
            for file_path in CONFIG_BASE_PATH.rglob("*"):
                if file_path.is_file():
                    relative_path = file_path.relative_to(CONFIG_BASE_PATH)
                    files.append(
                        {
                            "path": str(relative_path),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat(),
                            "extension": file_path.suffix,
                        }
                    )

            return {
                "operation": "list",
                "files": files,
                "count": len(files),
                "base_path": str(CONFIG_BASE_PATH),
                "timestamp": datetime.now().isoformat(),
            }

        file_path = resolve_config_path(request.file_path)

        if request.operation == "read":
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            # lgtm[py/path-injection] - file_path is resolved within CONFIG_BASE_PATH
            content = file_path.read_text()

            # Parse based on format
            parsed_content = None
            if request.format == "json":
                parsed_content = json.loads(content)
            elif request.format in ["yaml", "yml"]:
                parsed_content = yaml.safe_load(content)
            elif request.format == "ini":
                config = configparser.ConfigParser()
                config.read_string(content)
                parsed_content = {
                    section: dict(config[section]) for section in config.sections()
                }
            elif request.format == "env":
                parsed_content = {}
                for line in content.strip().split("\n"):
                    if "=" in line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        parsed_content[key.strip()] = value.strip().strip("\"'")

            return {
                "operation": "read",
                "file_path": request.file_path,
                "format": request.format,
                "raw_content": content,
                "parsed_content": parsed_content,
                "file_size": file_path.stat().st_size,
                "modified_time": datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat(),
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "write":
            if request.content is None:
                raise HTTPException(
                    status_code=400, detail="Content required for write operation"
                )

            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Format content based on format
            if request.format == "json":
                content = json.dumps(request.content, indent=2)
            elif request.format in ["yaml", "yml"]:
                content = yaml.dump(request.content, default_flow_style=False)
            elif request.format == "ini":
                config = configparser.ConfigParser()
                for section, values in request.content.items():
                    config[section] = values
                with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp:
                    config.write(tmp)
                    tmp.flush()
                    content = Path(tmp.name).read_text()
                Path(tmp.name).unlink()
            elif request.format == "env":
                content = "\n".join([f"{k}={v}" for k, v in request.content.items()])
            else:
                content = str(request.content)

            # lgtm[py/path-injection] - file_path is resolved within CONFIG_BASE_PATH
            file_path.write_text(content)

            return {
                "operation": "write",
                "file_path": request.file_path,
                "format": request.format,
                "bytes_written": len(content),
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "create":
            if file_path.exists():
                raise HTTPException(status_code=409, detail="File already exists")

            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Create empty file with appropriate format
            if request.format == "json":
                initial_content = "{}"
            elif request.format in ["yaml", "yml"]:
                initial_content = ""
            elif request.format == "ini":
                initial_content = ""
            elif request.format == "env":
                initial_content = ""
            else:
                initial_content = ""

            # lgtm[py/path-injection] - file_path is resolved within CONFIG_BASE_PATH
            file_path.write_text(initial_content)

            return {
                "operation": "create",
                "file_path": request.file_path,
                "format": request.format,
                "created": True,
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "delete":
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            file_size = file_path.stat().st_size
            # lgtm[py/path-injection] - file_path is resolved within CONFIG_BASE_PATH
            file_path.unlink()

            return {
                "operation": "delete",
                "file_path": request.file_path,
                "deleted": True,
                "file_size": file_size,
                "timestamp": datetime.now().isoformat(),
            }

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown operation: {request.operation}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Config file operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Config file operation failed")


@app.post("/tools/validate")
async def validate_tool(request: ConfigValidateRequest) -> Dict[str, Any]:
    """
    Validate configuration data

    Tool: validate
    Description: Validate configuration data against schema or rules
    """
    try:
        validation_errors = []
        warnings = []

        # Check required keys
        missing_keys = []
        for key in request.required_keys:
            if key not in request.config_data:
                missing_keys.append(key)
                validation_errors.append(f"Required key '{key}' is missing")

        # Check value types
        type_errors = []
        for key, expected_type in request.value_types.items():
            if key in request.config_data:
                value = request.config_data[key]

                if expected_type == "string" and not isinstance(value, str):
                    type_errors.append(
                        f"Key '{key}' should be string, got {type(value).__name__}"
                    )
                elif expected_type == "integer" and not isinstance(value, int):
                    type_errors.append(
                        f"Key '{key}' should be integer, got {type(value).__name__}"
                    )
                elif expected_type == "float" and not isinstance(value, (int, float)):
                    type_errors.append(
                        f"Key '{key}' should be float, got {type(value).__name__}"
                    )
                elif expected_type == "boolean" and not isinstance(value, bool):
                    type_errors.append(
                        f"Key '{key}' should be boolean, got {type(value).__name__}"
                    )
                elif expected_type == "list" and not isinstance(value, list):
                    type_errors.append(
                        f"Key '{key}' should be list, got {type(value).__name__}"
                    )
                elif expected_type == "dict" and not isinstance(value, dict):
                    type_errors.append(
                        f"Key '{key}' should be dict, got {type(value).__name__}"
                    )

        validation_errors.extend(type_errors)

        # Basic value checks
        for key, value in request.config_data.items():
            if isinstance(value, str):
                if len(value.strip()) == 0:
                    warnings.append(f"Key '{key}' has empty string value")
                if value != value.strip():
                    warnings.append(f"Key '{key}' has leading/trailing whitespace")
            elif isinstance(value, (int, float)):
                if value < 0 and key.lower().endswith(
                    ("_port", "_timeout", "_count", "_size")
                ):
                    validation_errors.append(
                        f"Key '{key}' should be positive, got {value}"
                    )

        # Schema validation if provided
        schema_errors = []
        if request.schema:
            # Basic schema validation (simplified)
            for schema_key, schema_def in request.schema.items():
                if isinstance(schema_def, dict) and "required" in schema_def:
                    if schema_def["required"] and schema_key not in request.config_data:
                        schema_errors.append(f"Schema requires key '{schema_key}'")

        validation_errors.extend(schema_errors)

        is_valid = len(validation_errors) == 0

        return {
            "is_valid": is_valid,
            "validation_errors": validation_errors,
            "warnings": warnings,
            "summary": {
                "total_keys": len(request.config_data),
                "missing_required": len(missing_keys),
                "type_errors": len(type_errors),
                "schema_errors": len(schema_errors),
                "warning_count": len(warnings),
            },
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Config validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Validation failed")


@app.post("/tools/backup")
async def backup_tool(request: ConfigBackupRequest) -> Dict[str, Any]:
    """
    Backup and restore configuration files

    Tool: backup
    Description: Create, restore, list, or delete configuration backups
    """
    try:
        backup_dir = CONFIG_BASE_PATH / "backups"
        backup_dir.mkdir(exist_ok=True)

        if request.operation == "create":
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = validate_backup_name(
                request.backup_name or f"backup_{timestamp}"
            )
            backup_path = backup_dir / backup_name  # lgtm[py/path-injection]

            if backup_path.exists():  # lgtm[py/path-injection]
                raise HTTPException(status_code=409, detail="Backup already exists")

            backup_path.mkdir()  # lgtm[py/path-injection]
            backed_up_files = []

            # Copy files matching patterns
            for pattern in validate_backup_patterns(request.file_patterns or []):
                for file_path in CONFIG_BASE_PATH.glob(
                    pattern
                ):  # lgtm[py/path-injection]
                    if file_path.is_file() and not file_path.is_relative_to(backup_dir):
                        relative_path = file_path.relative_to(CONFIG_BASE_PATH)
                        backup_file_path = backup_path / relative_path
                        backup_file_path.parent.mkdir(
                            parents=True, exist_ok=True
                        )  # lgtm[py/path-injection]
                        shutil.copy2(
                            file_path, backup_file_path
                        )  # lgtm[py/path-injection]
                        backed_up_files.append(str(relative_path))

            return {
                "operation": "create",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "files_backed_up": backed_up_files,
                "file_count": len(backed_up_files),
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "list":
            backups = []
            if backup_dir.exists():
                for backup_path in backup_dir.iterdir():
                    if backup_path.is_dir():
                        file_count = len(list(backup_path.rglob("*")))
                        backups.append(
                            {
                                "name": backup_path.name,
                                "created": datetime.fromtimestamp(
                                    backup_path.stat().st_mtime
                                ).isoformat(),
                                "file_count": file_count,
                                "size_mb": round(
                                    sum(
                                        f.stat().st_size
                                        for f in backup_path.rglob("*")
                                        if f.is_file()
                                    )
                                    / 1024
                                    / 1024,
                                    2,
                                ),
                            }
                        )

            return {
                "operation": "list",
                "backups": backups,
                "backup_count": len(backups),
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "restore":
            backup_name = validate_backup_name(request.backup_name)
            backup_path = backup_dir / backup_name  # lgtm[py/path-injection]
            if not backup_path.exists():  # lgtm[py/path-injection]
                raise HTTPException(status_code=404, detail="Backup not found")

            restored_files = []
            for backup_file in backup_path.rglob("*"):  # lgtm[py/path-injection]
                if backup_file.is_file():
                    relative_path = backup_file.relative_to(backup_path)
                    target_path = (
                        CONFIG_BASE_PATH / relative_path
                    ).resolve()  # lgtm[py/path-injection]
                    try:
                        target_path.relative_to(CONFIG_BASE_PATH.resolve())
                    except ValueError:
                        raise HTTPException(
                            status_code=403, detail="Path outside allowed directory"
                        )
                    target_path.parent.mkdir(
                        parents=True, exist_ok=True
                    )  # lgtm[py/path-injection]
                    shutil.copy2(backup_file, target_path)  # lgtm[py/path-injection]
                    restored_files.append(str(relative_path))

            return {
                "operation": "restore",
                "backup_name": request.backup_name,
                "files_restored": restored_files,
                "file_count": len(restored_files),
                "timestamp": datetime.now().isoformat(),
            }

        elif request.operation == "delete":
            backup_name = validate_backup_name(request.backup_name)
            backup_path = backup_dir / backup_name  # lgtm[py/path-injection]
            if not backup_path.exists():  # lgtm[py/path-injection]
                raise HTTPException(status_code=404, detail="Backup not found")

            file_count = len(list(backup_path.rglob("*")))  # lgtm[py/path-injection]
            shutil.rmtree(backup_path)  # lgtm[py/path-injection]

            return {
                "operation": "delete",
                "backup_name": request.backup_name,
                "deleted": True,
                "deleted_file_count": file_count,
                "timestamp": datetime.now().isoformat(),
            }

        else:
            raise HTTPException(
                status_code=400, detail=f"Unknown operation: {request.operation}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Backup operation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Backup operation failed")


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "env_vars",
                "description": "Get, set, list, or delete environment variables",
                "parameters": {
                    "operation": "string (required: get|set|list|delete)",
                    "key": "string (optional, variable name)",
                    "value": "string (optional, variable value for set)",
                    "prefix": "string (optional, prefix filter for list)",
                },
            },
            {
                "name": "config_file",
                "description": "Read, write, create, delete, or list configuration files",
                "parameters": {
                    "operation": "string (required: read|write|create|delete|list)",
                    "file_path": "string (required, file path relative to config dir)",
                    "format": "string (optional: json|yaml|ini|env, default json)",
                    "content": "object (optional, content for write operation)",
                    "section": "string (optional, section for INI files)",
                },
            },
            {
                "name": "validate",
                "description": "Validate configuration data against schema or rules",
                "parameters": {
                    "config_data": "object (required, configuration data to validate)",
                    "schema": "object (optional, validation schema)",
                    "required_keys": "array (optional, list of required keys)",
                    "value_types": "object (optional, key->type mappings)",
                },
            },
            {
                "name": "backup",
                "description": "Create, restore, list, or delete configuration backups",
                "parameters": {
                    "operation": "string (required: create|restore|list|delete)",
                    "backup_name": "string (optional, backup name)",
                    "file_patterns": "array (optional, file patterns to backup)",
                },
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
