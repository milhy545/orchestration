from mega_orchestrator.mcp_tooling import MCP_TOOL_DEFINITIONS, build_mcp_tools


def test_search_chat_history_schema_is_exposed():
    tools = build_mcp_tools(["search_chat_history"])

    assert tools[0]["name"] == "search_chat_history"
    assert tools[0]["inputSchema"]["required"] == ["query"]
    assert tools[0]["inputSchema"]["properties"]["mode"]["default"] == "hybrid"


def test_audit_chat_recall_schema_is_exposed():
    schema = MCP_TOOL_DEFINITIONS["audit_chat_recall"]["inputSchema"]

    assert schema["type"] == "object"


def test_agent_welcome_schema_is_exposed():
    tools = build_mcp_tools(["agent_welcome"])

    assert tools[0]["name"] == "agent_welcome"
    assert tools[0]["inputSchema"]["required"] == ["agent_name"]
    assert "current_hw_data" in tools[0]["inputSchema"]["properties"]
