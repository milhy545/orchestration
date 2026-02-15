#!/usr/bin/env python3
"""FORAI MCP Server — wraps forai preprocessing tool as an MCP service.

Provides tools to analyze Python source files, extract imports/definitions,
and generate machine-readable FORAI headers.
"""

import ast
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="FORAI MCP Server", version="1.0.0")

WORKSPACE = os.getenv("WORKSPACE_PATH", "/workspace")


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    success: bool
    result: Any = None
    error: Optional[str] = None


class ForaiHeader(BaseModel):
    file: str
    imports: List[str]
    classes: List[str]
    functions: List[str]
    variables: List[str]
    exports: List[str]


# ---------------------------------------------------------------------------
# Core FORAI logic (inline — forai may not be pip-installable)
# ---------------------------------------------------------------------------

def _analyze_python_file(filepath: str) -> Dict[str, Any]:
    """Parse a single Python file and extract FORAI metadata."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if not path.suffix == ".py":
        return {"file": str(path), "error": "Not a Python file"}

    source = path.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return {"file": str(path), "error": f"SyntaxError: {exc}"}

    imports: List[str] = []
    classes: List[str] = []
    functions: List[str] = []
    variables: List[str] = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")
        elif isinstance(node, ast.ClassDef):
            bases = [
                getattr(b, "id", None) or getattr(getattr(b, "attr", None), "__str__", lambda: "?")()
                for b in node.bases
            ]
            classes.append({"name": node.name, "bases": bases, "line": node.lineno})
        elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            functions.append({"name": node.name, "line": node.lineno, "async": isinstance(node, ast.AsyncFunctionDef)})
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables.append(target.id)

    # __all__ as exports
    exports: List[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                exports.append(elt.value)

    return {
        "file": str(path),
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "variables": variables,
        "exports": exports,
    }


def _generate_forai_header(analysis: Dict[str, Any]) -> str:
    """Generate a FORAI-format header comment block."""
    lines = ["# FORAI:START"]
    lines.append(f"#   file: {analysis['file']}")
    if analysis.get("imports"):
        lines.append(f"#   imports: {', '.join(str(i) for i in analysis['imports'])}")
    if analysis.get("classes"):
        names = [c["name"] if isinstance(c, dict) else c for c in analysis["classes"]]
        lines.append(f"#   classes: {', '.join(names)}")
    if analysis.get("functions"):
        names = [f["name"] if isinstance(f, dict) else f for f in analysis["functions"]]
        lines.append(f"#   functions: {', '.join(names)}")
    if analysis.get("exports"):
        lines.append(f"#   exports: {', '.join(analysis['exports'])}")
    lines.append("# FORAI:END")
    return "\n".join(lines)


def _resolve_path(path: str) -> Path:
    """Resolve a path relative to WORKSPACE."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(WORKSPACE) / p
    return p.resolve()


def _collect_py_files(path: Path, recursive: bool = True) -> List[Path]:
    if path.is_file():
        return [path] if path.suffix == ".py" else []
    if recursive:
        return sorted(path.rglob("*.py"))
    return sorted(path.glob("*.py"))


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def forai_analyze(path: str) -> Dict[str, Any]:
    """Analyze file(s) and return FORAI metadata."""
    resolved = _resolve_path(path)
    files = _collect_py_files(resolved)
    if not files:
        return {"path": str(resolved), "files": [], "message": "No Python files found"}
    results = [_analyze_python_file(str(f)) for f in files[:200]]  # cap
    return {"path": str(resolved), "files_analyzed": len(results), "results": results}


def forai_process(path: str, recursive: bool = True) -> Dict[str, Any]:
    """Process files and inject FORAI headers."""
    resolved = _resolve_path(path)
    files = _collect_py_files(resolved, recursive)
    processed = []
    for f in files[:200]:
        analysis = _analyze_python_file(str(f))
        if "error" in analysis:
            processed.append({"file": str(f), "status": "skipped", "error": analysis["error"]})
            continue
        header = _generate_forai_header(analysis)
        content = f.read_text(encoding="utf-8", errors="replace")
        # Remove existing FORAI header
        import re
        content = re.sub(r"# FORAI:START.*?# FORAI:END\n?", "", content, flags=re.DOTALL)
        new_content = header + "\n\n" + content.lstrip("\n")
        f.write_text(new_content, encoding="utf-8")
        processed.append({"file": str(f), "status": "processed"})
    return {"files_processed": len(processed), "details": processed}


def forai_query(path: str, query: str) -> Dict[str, Any]:
    """Query file dependencies/relationships from FORAI analysis."""
    resolved = _resolve_path(path)
    files = _collect_py_files(resolved)
    analyses = [_analyze_python_file(str(f)) for f in files[:200]]

    query_lower = query.lower()

    if "import" in query_lower or "depend" in query_lower:
        dep_map = {}
        for a in analyses:
            if "error" not in a:
                dep_map[a["file"]] = a["imports"]
        return {"query": query, "type": "dependencies", "results": dep_map}

    if "class" in query_lower:
        classes = {}
        for a in analyses:
            if "error" not in a and a.get("classes"):
                classes[a["file"]] = a["classes"]
        return {"query": query, "type": "classes", "results": classes}

    if "function" in query_lower or "def" in query_lower:
        funcs = {}
        for a in analyses:
            if "error" not in a and a.get("functions"):
                funcs[a["file"]] = a["functions"]
        return {"query": query, "type": "functions", "results": funcs}

    # Default: return all analyses
    return {"query": query, "type": "full", "results": analyses}


# ---------------------------------------------------------------------------
# MCP Endpoints
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "forai_analyze",
        "description": "Analyze Python file(s) and return FORAI metadata (imports, classes, functions, exports)",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to analyze"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "forai_process",
        "description": "Process Python files and inject FORAI machine-readable headers",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to process"},
                "recursive": {"type": "boolean", "description": "Process subdirectories recursively", "default": True},
            },
            "required": ["path"],
        },
    },
    {
        "name": "forai_query",
        "description": "Query file dependencies and relationships from FORAI analysis",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path to query"},
                "query": {"type": "string", "description": "Query string (e.g. 'imports', 'classes', 'functions')"},
            },
            "required": ["path", "query"],
        },
    },
]

TOOL_DISPATCH = {
    "forai_analyze": lambda args: forai_analyze(args["path"]),
    "forai_process": lambda args: forai_process(args["path"], args.get("recursive", True)),
    "forai_query": lambda args: forai_query(args["path"], args["query"]),
}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "forai-mcp", "timestamp": datetime.utcnow().isoformat()}


@app.get("/tools/list")
async def tools_list():
    return {"tools": TOOLS}


@app.post("/tools/call")
async def tools_call(request: ToolCallRequest):
    handler = TOOL_DISPATCH.get(request.name)
    if not handler:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {request.name}")
    try:
        result = handler(request.arguments)
        return ToolCallResponse(success=True, result=result)
    except Exception as exc:
        return ToolCallResponse(success=False, error=str(exc))
