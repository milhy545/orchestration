#!/usr/bin/env python3
"""Code Graph MCP Server — parses Python code with tree-sitter, stores in Neo4j.

Node types: Module, Class, Function, Variable
Relationship types: IMPORTS, DEFINES, CALLS, INHERITS, DECORATES
"""

import ast
import json
import logging
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Code Graph MCP Server", version="1.0.0")
logger = logging.getLogger("code-graph-mcp")

WORKSPACE = os.getenv("WORKSPACE_PATH", "/workspace")
NEO4J_URL = os.getenv("NEO4J_URL", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j_password")

# ---------------------------------------------------------------------------
# Neo4j driver (lazy init)
# ---------------------------------------------------------------------------
_driver = None


def _get_driver():
    global _driver
    if _driver is None:
        try:
            from neo4j import GraphDatabase
            _driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        except Exception as exc:
            logger.warning(f"Neo4j connection failed: {exc}")
            return None
    return _driver


def _run_cypher(query: str, params: Optional[Dict] = None) -> List[Dict]:
    driver = _get_driver()
    if not driver:
        raise RuntimeError("Neo4j is not available")
    with driver.session() as session:
        result = session.run(query, params or {})
        return [dict(record) for record in result]


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


# ---------------------------------------------------------------------------
# Python AST-based code analysis (fallback when tree-sitter unavailable)
# ---------------------------------------------------------------------------

def _parse_python_file(filepath: Path) -> Dict[str, Any]:
    """Parse a Python file and extract structural information."""
    source = filepath.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as exc:
        return {"file": str(filepath), "error": str(exc)}

    module_name = filepath.stem
    classes = []
    functions = []
    imports = []
    variables = []
    calls = []
    decorators = []

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = []
            for b in node.bases:
                if isinstance(b, ast.Name):
                    bases.append(b.id)
                elif isinstance(b, ast.Attribute):
                    bases.append(ast.dump(b))
            classes.append({"name": node.name, "bases": bases, "line": node.lineno})
            for dec in node.decorator_list:
                dec_name = getattr(dec, "id", None) or getattr(getattr(dec, "func", None), "id", None) or "unknown"
                decorators.append({"target": node.name, "decorator": str(dec_name)})

        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append({"name": node.name, "line": node.lineno})
            for dec in node.decorator_list:
                dec_name = getattr(dec, "id", None) or getattr(getattr(dec, "func", None), "id", None) or "unknown"
                decorators.append({"target": node.name, "decorator": str(dec_name)})

        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "alias": alias.asname})

        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append({"module": f"{mod}.{alias.name}", "alias": alias.asname})

        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)

    # Top-level variables
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    variables.append(t.id)

    return {
        "file": str(filepath),
        "module": module_name,
        "classes": classes,
        "functions": functions,
        "imports": imports,
        "variables": variables,
        "calls": list(set(calls)),
        "decorators": decorators,
    }


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def index_python_project(path: str) -> Dict[str, Any]:
    """Index all .py files under path into Neo4j."""
    resolved = Path(path) if Path(path).is_absolute() else Path(WORKSPACE) / path
    resolved = resolved.resolve()
    py_files = sorted(resolved.rglob("*.py"))
    if not py_files:
        return {"path": str(resolved), "message": "No Python files found"}

    analyses = []
    for f in py_files[:500]:
        analyses.append(_parse_python_file(f))

    # Try to store in Neo4j
    stored = False
    try:
        driver = _get_driver()
        if driver:
            with driver.session() as session:
                # Clear previous data for this path
                session.run("MATCH (n {project: $project}) DETACH DELETE n", {"project": str(resolved)})

                for a in analyses:
                    if "error" in a:
                        continue
                    # Create Module node
                    session.run(
                        "MERGE (m:Module {name: $name, project: $project, file: $file})",
                        {"name": a["module"], "project": str(resolved), "file": a["file"]},
                    )
                    # Classes
                    for cls in a["classes"]:
                        session.run(
                            "MERGE (c:Class {name: $name, project: $project}) "
                            "WITH c "
                            "MATCH (m:Module {name: $module, project: $project}) "
                            "MERGE (m)-[:DEFINES]->(c)",
                            {"name": cls["name"], "project": str(resolved), "module": a["module"]},
                        )
                        for base in cls["bases"]:
                            session.run(
                                "MERGE (parent:Class {name: $base, project: $project}) "
                                "WITH parent "
                                "MATCH (child:Class {name: $name, project: $project}) "
                                "MERGE (child)-[:INHERITS]->(parent)",
                                {"base": base, "name": cls["name"], "project": str(resolved)},
                            )
                    # Functions
                    for func in a["functions"]:
                        session.run(
                            "MERGE (f:Function {name: $name, project: $project}) "
                            "WITH f "
                            "MATCH (m:Module {name: $module, project: $project}) "
                            "MERGE (m)-[:DEFINES]->(f)",
                            {"name": func["name"], "project": str(resolved), "module": a["module"]},
                        )
                    # Imports
                    for imp in a["imports"]:
                        session.run(
                            "MATCH (m:Module {name: $module, project: $project}) "
                            "MERGE (target:Module {name: $imported, project: $project}) "
                            "MERGE (m)-[:IMPORTS]->(target)",
                            {"module": a["module"], "imported": imp["module"].split(".")[0], "project": str(resolved)},
                        )
                    # Decorators
                    for dec in a.get("decorators", []):
                        session.run(
                            "MATCH (t {name: $target, project: $project}) "
                            "MERGE (d:Function {name: $decorator, project: $project}) "
                            "MERGE (d)-[:DECORATES]->(t)",
                            {"target": dec["target"], "decorator": dec["decorator"], "project": str(resolved)},
                        )
            stored = True
    except Exception as exc:
        logger.warning(f"Neo4j storage failed: {exc}")

    return {
        "path": str(resolved),
        "files_indexed": len(analyses),
        "stored_in_neo4j": stored,
        "summary": {
            "modules": len([a for a in analyses if "error" not in a]),
            "errors": len([a for a in analyses if "error" in a]),
            "classes": sum(len(a.get("classes", [])) for a in analyses),
            "functions": sum(len(a.get("functions", [])) for a in analyses),
        },
    }


def query_code_graph(cypher_query: str) -> Dict[str, Any]:
    """Execute a raw Cypher query against Neo4j."""
    results = _run_cypher(cypher_query)
    serializable = []
    for record in results:
        row = {}
        for k, v in record.items():
            try:
                json.dumps(v)
                row[k] = v
            except (TypeError, ValueError):
                row[k] = str(v)
        serializable.append(row)
    return {"query": cypher_query, "results": serializable, "count": len(serializable)}


def find_dependencies(module: str) -> Dict[str, Any]:
    """Find what a module imports."""
    try:
        results = _run_cypher(
            "MATCH (m:Module {name: $name})-[:IMPORTS]->(dep) RETURN dep.name AS dependency",
            {"name": module},
        )
        return {"module": module, "dependencies": [r["dependency"] for r in results]}
    except RuntimeError:
        return {"module": module, "error": "Neo4j unavailable", "dependencies": []}


def find_callers(function: str) -> Dict[str, Any]:
    """Find who calls a function (via CALLS relationships)."""
    try:
        results = _run_cypher(
            "MATCH (caller)-[:CALLS]->(f:Function {name: $name}) RETURN caller.name AS caller, labels(caller) AS labels",
            {"name": function},
        )
        return {"function": function, "callers": [r["caller"] for r in results]}
    except RuntimeError:
        return {"function": function, "error": "Neo4j unavailable", "callers": []}


def detect_circular_imports(path: str) -> Dict[str, Any]:
    """Detect circular import chains using AST analysis."""
    resolved = Path(path) if Path(path).is_absolute() else Path(WORKSPACE) / path
    resolved = resolved.resolve()
    py_files = sorted(resolved.rglob("*.py"))

    # Build import graph
    import_graph: Dict[str, List[str]] = defaultdict(list)
    for f in py_files[:500]:
        analysis = _parse_python_file(f)
        if "error" in analysis:
            continue
        for imp in analysis["imports"]:
            import_graph[analysis["module"]].append(imp["module"].split(".")[0])

    # Detect cycles with DFS
    cycles = []
    visited = set()
    rec_stack = set()

    def _dfs(node: str, path_so_far: List[str]):
        visited.add(node)
        rec_stack.add(node)
        for neighbor in import_graph.get(node, []):
            if neighbor not in visited:
                _dfs(neighbor, path_so_far + [neighbor])
            elif neighbor in rec_stack:
                cycle_start = path_so_far.index(neighbor) if neighbor in path_so_far else -1
                if cycle_start >= 0:
                    cycles.append(path_so_far[cycle_start:] + [neighbor])
                else:
                    cycles.append([neighbor, node, neighbor])

        rec_stack.discard(node)

    for module in import_graph:
        if module not in visited:
            _dfs(module, [module])

    return {
        "path": str(resolved),
        "modules_scanned": len(import_graph),
        "circular_imports": cycles[:50],
        "has_circular": len(cycles) > 0,
    }


# ---------------------------------------------------------------------------
# MCP Endpoints
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "index_python_project",
        "description": "Parse all .py files and store classes/functions/imports in Neo4j graph",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project directory path"},
            },
            "required": ["path"],
        },
    },
    {
        "name": "query_code_graph",
        "description": "Execute a raw Cypher query against the code graph in Neo4j",
        "parameters": {
            "type": "object",
            "properties": {
                "cypher_query": {"type": "string", "description": "Cypher query string"},
            },
            "required": ["cypher_query"],
        },
    },
    {
        "name": "find_dependencies",
        "description": "Find all imports/dependencies of a given module",
        "parameters": {
            "type": "object",
            "properties": {
                "module": {"type": "string", "description": "Module name to look up"},
            },
            "required": ["module"],
        },
    },
    {
        "name": "find_callers",
        "description": "Find all callers of a given function",
        "parameters": {
            "type": "object",
            "properties": {
                "function": {"type": "string", "description": "Function name to look up"},
            },
            "required": ["function"],
        },
    },
    {
        "name": "detect_circular_imports",
        "description": "Detect circular import chains in a Python project",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Project directory path"},
            },
            "required": ["path"],
        },
    },
]

TOOL_DISPATCH = {
    "index_python_project": lambda args: index_python_project(args["path"]),
    "query_code_graph": lambda args: query_code_graph(args["cypher_query"]),
    "find_dependencies": lambda args: find_dependencies(args["module"]),
    "find_callers": lambda args: find_callers(args["function"]),
    "detect_circular_imports": lambda args: detect_circular_imports(args["path"]),
}


@app.get("/health")
async def health():
    neo4j_ok = False
    try:
        driver = _get_driver()
        if driver:
            driver.verify_connectivity()
            neo4j_ok = True
    except Exception:
        pass
    return {
        "status": "healthy" if neo4j_ok else "degraded",
        "service": "code-graph-mcp",
        "neo4j": "connected" if neo4j_ok else "unavailable",
        "timestamp": datetime.utcnow().isoformat(),
    }


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
