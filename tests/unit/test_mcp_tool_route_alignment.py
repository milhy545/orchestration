from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ORCHESTRATOR_PATH = PROJECT_ROOT / "mega_orchestrator" / "mega_orchestrator_complete.py"


def _tool_routes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    routes = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr not in {"get", "post"} or not decorator.args:
                continue
            route = decorator.args[0]
            if isinstance(route, ast.Constant) and isinstance(route.value, str):
                if route.value.startswith("/tools/") and route.value != "/tools/list":
                    routes.add(route.value.rsplit("/", 1)[-1])
    return routes


def _listed_tools(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    list_tools = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "list_tools"
    )
    names = set()
    for node in ast.walk(list_tools):
        if not isinstance(node, ast.Dict):
            continue
        for key, value in zip(node.keys, node.values):
            if (
                isinstance(key, ast.Constant)
                and key.value == "name"
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                names.add(value.value)
    return names


def _orchestrator_tools(service_name: str) -> set[str]:
    tree = ast.parse(ORCHESTRATOR_PATH.read_text(encoding="utf-8"))
    init_services = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_init_mcp_services"
    )
    returned_dict = next(
        node.value
        for node in ast.walk(init_services)
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict)
    )

    for key, value in zip(returned_dict.keys, returned_dict.values):
        if not isinstance(key, ast.Constant) or key.value != service_name:
            continue
        assert isinstance(value, ast.Call)
        tools_arg = next(keyword.value for keyword in value.keywords if keyword.arg == "tools")
        return set(ast.literal_eval(tools_arg))
    raise AssertionError(f"No orchestrator config found for service {service_name}")


def test_security_mcp_tools_match_routes() -> None:
    service_path = PROJECT_ROOT / "mcp-servers" / "security-mcp" / "main.py"
    routes = _tool_routes(service_path)

    assert _listed_tools(service_path) == routes
    assert _orchestrator_tools("security") == routes


def test_log_mcp_tools_match_routes() -> None:
    service_path = PROJECT_ROOT / "mcp-servers" / "log-mcp" / "main.py"
    routes = _tool_routes(service_path)

    assert _listed_tools(service_path) == routes
    assert _orchestrator_tools("log") == routes
