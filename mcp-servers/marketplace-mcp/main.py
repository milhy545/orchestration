#!/usr/bin/env python3
"""
Marketplace MCP Service - Hybrid Skills Catalog + MCP Subregistry
Port: 7034 (host mapping), 8000 in-container
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from packaging.version import InvalidVersion, Version
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Marketplace MCP Service",
    description="Private skills catalog and MCP subregistry for LAN orchestration",
    version="1.0.0",
)
Instrumentator().instrument(app).expose(app)

CATALOG_PATH = Path(os.environ.get("MARKET_CATALOG_PATH", "/app/catalog"))
MARKET_BASE_URL = os.environ.get("MARKET_BASE_URL", "http://localhost:7034").rstrip("/")
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")


class SkillCompat(BaseModel):
    clients: List[str] = Field(default_factory=lambda: ["codex-cli"])
    min_version: str = "0.0.0"


class SkillPackageEntry(BaseModel):
    name: str
    version: str
    description: str = ""
    archive_url: str
    sha256: str = ""
    tags: List[str] = Field(default_factory=list)
    source: str = "internal"
    compat: SkillCompat = Field(default_factory=SkillCompat)


class InstallSkillSpec(BaseModel):
    name: str
    version: Optional[str] = None


class InstallPlanRequest(BaseModel):
    client: str = "codex-cli"
    install_root: str = "~/.codex/skills"
    skills: List[InstallSkillSpec]


class RegistryServerVersion(BaseModel):
    version: str
    transport: str = "streamable_http"
    endpoint: str
    auth: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class RegistryServerEntry(BaseModel):
    id: str
    name: str
    description: str = ""
    source: str = "internal"
    tags: List[str] = Field(default_factory=list)
    versions: List[RegistryServerVersion] = Field(default_factory=list)


class ToolRequest(BaseModel):
    arguments: Dict[str, Any] = Field(default_factory=dict)


class LegacyMCPRequest(BaseModel):
    tool: Optional[str] = None
    arguments: Dict[str, Any] = Field(default_factory=dict)


def _read_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        logger.warning("Catalog file missing: %s", path)
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.error("Invalid catalog JSON: %s (%s)", path, exc)
        return default


def _catalog() -> Dict[str, Any]:
    return {
        "skills": _read_json(CATALOG_PATH / "skills-index.json", {"skills": []}),
        "servers": _read_json(CATALOG_PATH / "servers-index.json", {"servers": []}),
        "trust": _read_json(CATALOG_PATH / "trust-policy.json", {"policy": "none"}),
    }


def _extract_scopes(payload: Dict[str, Any]) -> Set[str]:
    scopes: Set[str] = set()
    for key in ("scope", "scopes", "permissions"):
        value = payload.get(key)
        if isinstance(value, str):
            for item in value.replace(",", " ").split():
                if item:
                    scopes.add(item)
        elif isinstance(value, list):
            scopes.update(str(item) for item in value if str(item).strip())
    return scopes


def _require_scopes(required: List[str]):
    async def _dep(
        authorization: Optional[str] = Header(default=None),
    ) -> Dict[str, Any]:
        if not JWT_SECRET:
            raise HTTPException(status_code=500, detail="JWT_SECRET is not configured")
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing bearer token")

        token = authorization.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                options={"require": ["sub", "exp"]},
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

        scopes = _extract_scopes(payload)
        if any(scope not in scopes for scope in required):
            raise HTTPException(
                status_code=403, detail=f"Missing required scopes: {required}"
            )

        return payload

    return _dep


def _all_skill_entries() -> List[SkillPackageEntry]:
    payload = _catalog()["skills"]
    out: List[SkillPackageEntry] = []
    for entry in payload.get("skills", []):
        try:
            out.append(SkillPackageEntry(**entry))
        except Exception as exc:
            logger.warning("Ignoring invalid skill entry: %s (%s)", entry, exc)
    return out


def _all_servers() -> List[RegistryServerEntry]:
    payload = _catalog()["servers"]
    out: List[RegistryServerEntry] = []
    for entry in payload.get("servers", []):
        try:
            out.append(RegistryServerEntry(**entry))
        except Exception as exc:
            logger.warning("Ignoring invalid server entry: %s (%s)", entry, exc)
    return out


def _skill_versions(name: str) -> List[SkillPackageEntry]:
    return [s for s in _all_skill_entries() if s.name == name]


def _select_latest(entries: List[SkillPackageEntry]) -> SkillPackageEntry:
    def _version_key(item: SkillPackageEntry):
        try:
            return Version(item.version)
        except InvalidVersion:
            return Version("0")

    return sorted(entries, key=_version_key, reverse=True)[0]


def _find_skill(name: str, version: str) -> SkillPackageEntry:
    for entry in _all_skill_entries():
        if entry.name == name and entry.version == version:
            return entry
    raise HTTPException(status_code=404, detail=f"Skill {name}@{version} not found")


def _local_artifact_path(archive_url: str) -> Optional[Path]:
    if archive_url.startswith("http://") or archive_url.startswith("https://"):
        return None
    resolved = (CATALOG_PATH / archive_url).resolve()
    try:
        resolved.relative_to(CATALOG_PATH.resolve())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact path in catalog")
    return resolved


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _latest_server_version(
    server: RegistryServerEntry,
) -> Optional[RegistryServerVersion]:
    if not server.versions:
        return None

    def _version_key(item: RegistryServerVersion):
        try:
            return Version(item.version)
        except InvalidVersion:
            return Version("0")

    return sorted(server.versions, key=_version_key, reverse=True)[0]


async def _tool_skills_list(arguments: Dict[str, Any]) -> Dict[str, Any]:
    name = arguments.get("name")
    tag = arguments.get("tag")
    compat_client = arguments.get("compat_client")

    entries = _all_skill_entries()
    if name:
        entries = [e for e in entries if e.name == name]
    if tag:
        entries = [e for e in entries if tag in e.tags]
    if compat_client:
        entries = [e for e in entries if compat_client in e.compat.clients]

    return {
        "skills": [e.model_dump() for e in entries],
        "count": len(entries),
    }


async def _tool_skills_resolve(arguments: Dict[str, Any]) -> Dict[str, Any]:
    name = arguments.get("name")
    version = arguments.get("version")
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    if version:
        entry = _find_skill(name, version)
    else:
        versions = _skill_versions(name)
        if not versions:
            raise HTTPException(status_code=404, detail=f"Skill {name} not found")
        entry = _select_latest(versions)

    return entry.model_dump()


async def _tool_registry_search(arguments: Dict[str, Any]) -> Dict[str, Any]:
    tag = arguments.get("tag")
    source = arguments.get("source")

    servers = _all_servers()
    if tag:
        servers = [s for s in servers if tag in s.tags]
    if source:
        servers = [s for s in servers if s.source == source]

    return {
        "servers": [s.model_dump() for s in servers],
        "count": len(servers),
    }


async def _tool_registry_get_server(arguments: Dict[str, Any]) -> Dict[str, Any]:
    server_id = arguments.get("server_id")
    if not server_id:
        raise HTTPException(status_code=400, detail="server_id is required")

    for server in _all_servers():
        if server.id == server_id:
            latest = _latest_server_version(server)
            return {
                **server.model_dump(),
                "latest_version": latest.version if latest else None,
            }

    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


async def _tool_catalog_validate(arguments: Dict[str, Any]) -> Dict[str, Any]:
    verify_artifacts = bool(arguments.get("verify_artifacts", True))

    errors: List[str] = []
    checked = 0

    for entry in _all_skill_entries():
        checked += 1
        if verify_artifacts:
            local_path = _local_artifact_path(entry.archive_url)
            if local_path is not None:
                if not local_path.exists():
                    errors.append(f"Missing artifact: {local_path}")
                    continue
                if entry.sha256:
                    actual = _sha256_file(local_path)
                    if actual != entry.sha256:
                        errors.append(f"SHA mismatch for {entry.name}@{entry.version}")

    return {
        "valid": len(errors) == 0,
        "checked_skills": checked,
        "errors": errors,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


TOOL_HANDLERS = {
    "skills_list": _tool_skills_list,
    "skills_resolve": _tool_skills_resolve,
    "registry_search": _tool_registry_search,
    "registry_get_server": _tool_registry_get_server,
    "catalog_validate": _tool_catalog_validate,
}


def _tool_specs() -> List[Dict[str, Any]]:
    return [
        {
            "name": "skills_list",
            "description": "List skills from private catalog",
            "parameters": {
                "name": "string (optional)",
                "tag": "string (optional)",
                "compat_client": "string (optional)",
            },
        },
        {
            "name": "skills_resolve",
            "description": "Resolve one skill and latest version fallback",
            "parameters": {
                "name": "string (required)",
                "version": "string (optional)",
            },
        },
        {
            "name": "registry_search",
            "description": "Search MCP subregistry server entries",
            "parameters": {
                "tag": "string (optional)",
                "source": "string (optional)",
            },
        },
        {
            "name": "registry_get_server",
            "description": "Get MCP server metadata by id",
            "parameters": {
                "server_id": "string (required)",
            },
        },
        {
            "name": "catalog_validate",
            "description": "Validate catalog and optional artifact checksums",
            "parameters": {
                "verify_artifacts": "boolean (optional, default true)",
            },
        },
    ]


async def _dispatch_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    handler = TOOL_HANDLERS.get(tool_name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
    return await handler(arguments)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "marketplace-mcp",
        "port": 8000,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "catalog_path": str(CATALOG_PATH),
        "jwt_configured": bool(JWT_SECRET),
    }


@app.get("/tools/list")
async def list_tools(
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    return {"tools": _tool_specs()}


@app.post("/tools/{tool_name}")
async def call_tool(
    tool_name: str,
    request: ToolRequest,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    return await _dispatch_tool(tool_name, request.arguments)


@app.get("/skills/v1/index")
async def skills_index(
    name: Optional[str] = None,
    tag: Optional[str] = None,
    compat_client: Optional[str] = None,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    return await _tool_skills_list(
        {"name": name, "tag": tag, "compat_client": compat_client}
    )


@app.get("/skills/v1/packages/{name}/{version}")
async def skill_package(
    name: str,
    version: str,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    return _find_skill(name, version).model_dump()


@app.get("/skills/v1/packages/{name}/{version}/download")
async def skill_download(
    name: str,
    version: str,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
):
    pkg = _find_skill(name, version)
    local_path = _local_artifact_path(pkg.archive_url)

    if local_path is None:
        return RedirectResponse(url=pkg.archive_url)

    if not local_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")

    if pkg.sha256:
        actual = _sha256_file(local_path)
        if actual != pkg.sha256:
            raise HTTPException(status_code=500, detail="Artifact checksum mismatch")

    return FileResponse(
        path=local_path, filename=local_path.name, media_type="application/gzip"
    )


@app.post("/skills/v1/install-plan")
async def install_plan(
    request: InstallPlanRequest,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    if not request.skills:
        raise HTTPException(status_code=400, detail="At least one skill is required")

    resolved: List[SkillPackageEntry] = []
    for spec in sorted(
        request.skills, key=lambda item: (item.name, item.version or "")
    ):
        if spec.version:
            item = _find_skill(spec.name, spec.version)
        else:
            versions = _skill_versions(spec.name)
            if not versions:
                raise HTTPException(
                    status_code=404, detail=f"Skill {spec.name} not found"
                )
            item = _select_latest(versions)
        resolved.append(item)

    steps: List[Dict[str, Any]] = []
    step_order = 1
    for pkg in resolved:
        download_path = (
            f"{MARKET_BASE_URL}/skills/v1/packages/{pkg.name}/{pkg.version}/download"
        )
        install_target = f"{request.install_root.rstrip('/')}/{pkg.name}"

        steps.extend(
            [
                {
                    "order": step_order,
                    "action": "download",
                    "skill": pkg.name,
                    "version": pkg.version,
                    "url": download_path,
                },
                {
                    "order": step_order + 1,
                    "action": "verify_sha256",
                    "skill": pkg.name,
                    "sha256": pkg.sha256,
                },
                {
                    "order": step_order + 2,
                    "action": "extract",
                    "skill": pkg.name,
                    "target": install_target,
                },
                {
                    "order": step_order + 3,
                    "action": "activate",
                    "skill": pkg.name,
                    "client": request.client,
                },
            ]
        )
        step_order += 4

    return {
        "client": request.client,
        "install_root": request.install_root,
        "resolved_packages": [pkg.model_dump() for pkg in resolved],
        "steps": steps,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/registry/v0.1/servers")
async def registry_servers(
    tag: Optional[str] = None,
    source: Optional[str] = None,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    out = await _tool_registry_search({"tag": tag, "source": source})
    return out


@app.get("/registry/v0.1/servers/{server_id}")
async def registry_server(
    server_id: str,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    return await _tool_registry_get_server({"server_id": server_id})


@app.get("/registry/v0.1/servers/{server_id}/versions")
async def registry_server_versions(
    server_id: str,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    for server in _all_servers():
        if server.id == server_id:
            return {
                "server_id": server_id,
                "versions": [item.model_dump() for item in server.versions],
            }
    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


@app.get("/registry/v0.1/servers/{server_id}/latest")
async def registry_server_latest(
    server_id: str,
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    for server in _all_servers():
        if server.id == server_id:
            latest = _latest_server_version(server)
            if latest is None:
                raise HTTPException(status_code=404, detail="No versions available")
            return {
                "server_id": server_id,
                "latest": latest.model_dump(),
            }
    raise HTTPException(status_code=404, detail=f"Server {server_id} not found")


@app.post("/mcp")
async def mcp_handler(
    body: Dict[str, Any],
    _token: Dict[str, Any] = Depends(_require_scopes(["market:read"])),
) -> Dict[str, Any]:
    # JSON-RPC 2.0 branch
    if "jsonrpc" in body:
        request_id = body.get("id")
        method = body.get("method")
        params = body.get("params", {})

        if body.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32600, "message": "Invalid Request"},
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"tools": _tool_specs()},
            }

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result = await _dispatch_tool(tool_name, arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }
            except HTTPException as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": exc.detail},
                }

        # Compatibility mode: direct JSON-RPC method name equals tool name.
        if method in TOOL_HANDLERS:
            try:
                result = await _dispatch_tool(method, params or {})
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result,
                }
            except HTTPException as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": exc.detail},
                }

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    # Legacy orchestrator payload branch: {tool, arguments}
    tool_name = body.get("tool")
    arguments = body.get("arguments", {})
    if not tool_name:
        raise HTTPException(status_code=400, detail="tool is required")

    return await _dispatch_tool(tool_name, arguments)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
