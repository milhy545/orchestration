#!/usr/bin/env python3
"""
MQTT MCP Service Tests
"""

import sys
import importlib.util
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
import types

if "gmqtt" not in sys.modules:
    gmqtt_stub = types.ModuleType("gmqtt")

    class Client:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def set_auth_credentials(self, *args, **kwargs):
            return None

        async def connect(self, *args, **kwargs):
            return None

        async def publish(self, *args, **kwargs):
            return None

        async def subscribe(self, *args, **kwargs):
            return None

    gmqtt_stub.Client = Client
    sys.modules["gmqtt"] = gmqtt_stub

module_path = Path(__file__).resolve().parents[1] / "main.py"
MODULE_NAME = "mqtt_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(
        module.mqtt_server, "connect_mqtt", AsyncMock(return_value=None)
    )
    with TestClient(app) as test_client:
        yield test_client


class TestMqttMCPHealth:
    def test_health_endpoint(self, client):
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "mqtt-mcp"
        assert data["status"] in {"healthy", "degraded"}
        assert "checks" in data
        assert "broker_connected" in data["checks"]

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        payload = response.json()
        assert payload["service"] == "MQTT MCP Server"
        assert payload["status"] == "running"

    def test_tools_list(self, client):
        response = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        )
        assert response.status_code == 200
        payload = response.json()
        tool_names = {tool["name"] for tool in payload["result"]["tools"]}
        assert {
            "publish_message",
            "subscribe_topic",
            "get_mqtt_status",
            "list_messages",
        }.issubset(tool_names)

    def test_invalid_jsonrpc_request(self, client):
        response = client.post(
            "/mcp", json={"jsonrpc": "1.0", "method": "tools/list", "id": 2}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32600

    def test_unknown_method(self, client):
        response = client.post(
            "/mcp", json={"jsonrpc": "2.0", "method": "missing", "id": 3}
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32601

    def test_unknown_tool(self, client):
        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "missing", "arguments": {}},
                "id": 4,
            },
        )
        assert response.status_code == 400
        assert response.json()["error"]["code"] == -32601

    def test_publish_message_tool(self, monkeypatch, client):
        publish = AsyncMock(return_value={"success": True, "topic": "demo"})
        monkeypatch.setattr(module.mqtt_server, "publish_message", publish)

        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "publish_message",
                    "arguments": {"topic": "demo", "message": "hello", "qos": 1},
                },
                "id": 5,
            },
        )

        assert response.status_code == 200
        publish.assert_awaited_once()
        assert (
            '"success": true' in response.json()["result"]["content"][0]["text"].lower()
        )

    def test_subscribe_and_list_messages_tools(self, monkeypatch, client):
        subscribe = AsyncMock(return_value={"success": True, "topic": "demo"})
        list_messages = AsyncMock(
            return_value={"topic": "demo", "messages": [{"message": "hi"}], "count": 1}
        )
        monkeypatch.setattr(module.mqtt_server, "subscribe_topic", subscribe)
        monkeypatch.setattr(module.mqtt_server, "list_messages", list_messages)

        subscribe_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "subscribe_topic", "arguments": {"topic": "demo"}},
                "id": 6,
            },
        )
        list_response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "list_messages",
                    "arguments": {"topic": "demo", "limit": 10},
                },
                "id": 7,
            },
        )

        assert subscribe_response.status_code == 200
        assert list_response.status_code == 200
        subscribe.assert_awaited_once()
        list_messages.assert_awaited_once()

    def test_get_mqtt_status_tool(self, monkeypatch, client):
        get_status = AsyncMock(
            return_value={"connected": False, "broker": "mqtt-broker:1883"}
        )
        monkeypatch.setattr(module.mqtt_server, "get_mqtt_status", get_status)

        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "get_mqtt_status", "arguments": {}},
                "id": 8,
            },
        )

        assert response.status_code == 200
        get_status.assert_awaited_once()

    def test_internal_error_returns_jsonrpc_error(self, monkeypatch, client):
        async def boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(module.mqtt_server, "get_mqtt_status", boom)

        response = client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "get_mqtt_status", "arguments": {}},
                "id": 9,
            },
        )

        assert response.status_code == 500
        assert response.json()["error"]["code"] == -32603

    @pytest.mark.asyncio
    async def test_server_tracks_messages_and_lists_them(self):
        server = module.MQTTMCPServer()

        await server.on_mqtt_message(None, "demo/topic", b"hello", 1, None)

        topic_payload = await server.list_messages(topic="demo/topic", limit=10)
        all_payload = await server.list_messages(limit=10)
        status_payload = await server.get_mqtt_status()

        assert topic_payload["count"] == 1
        assert topic_payload["messages"][0]["message"] == "hello"
        assert all_payload["total_topics"] == 1
        assert status_payload["total_messages"] == 1

    @pytest.mark.asyncio
    async def test_publish_and_subscribe_fail_when_broker_unavailable(self):
        server = module.MQTTMCPServer()
        server.connect_mqtt = AsyncMock(return_value=None)

        publish_payload = await server.publish_message("demo/topic", "hello")
        subscribe_payload = await server.subscribe_topic("demo/topic")

        assert publish_payload["success"] is False
        assert subscribe_payload["success"] is False
        server.connect_mqtt.assert_awaited()
