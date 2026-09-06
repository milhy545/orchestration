from mega_orchestrator.mcp_tooling import MCP_TOOL_DEFINITIONS, build_mcp_tools


def test_catalog_validate_schema_matches_runtime():
    schema = MCP_TOOL_DEFINITIONS["catalog_validate"]["inputSchema"]
    assert "verify_artifacts" in schema["properties"]
    assert "archive_url" not in schema["properties"]


def test_speak_generate_is_exposed():
    tools = build_mcp_tools(["speak_generate"])
    assert tools[0]["name"] == "speak_generate"
    assert tools[0]["inputSchema"]["required"] == ["text"]
