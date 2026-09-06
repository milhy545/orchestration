from mega_orchestrator.mcp_stdio_bridge import _handle_request
from mega_orchestrator.mcp_tooling import build_mcp_tools


def test_catalog_validate_schema_matches_marketplace_api():
    tool = build_mcp_tools(["catalog_validate"])[0]
    assert tool["name"] == "catalog_validate"
    assert tool["inputSchema"]["properties"] == {
        "verify_artifacts": {"type": "boolean", "default": True}
    }
    assert "required" not in tool["inputSchema"]


def test_stdio_initialize_reports_resources_capability():
    response = _handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    capabilities = response["result"]["capabilities"]
    assert capabilities["tools"]["listChanged"] is False
    assert capabilities["resources"] == {"subscribe": False, "listChanged": False}
