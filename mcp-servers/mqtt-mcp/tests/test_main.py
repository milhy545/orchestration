#!/usr/bin/env python3
"""
MQTT MCP Service Tests
"""
from fastapi.testclient import TestClient

# Import the main app
import sys
import importlib.util
from pathlib import Path

module_path = Path(__file__).resolve().parents[1] / "main.py"
MODULE_NAME = "mqtt_mcp_main"
spec = importlib.util.spec_from_file_location(MODULE_NAME, module_path)
module = importlib.util.module_from_spec(spec)
sys.modules[MODULE_NAME] = module
assert spec.loader is not None
spec.loader.exec_module(module)

app = module.app
client = TestClient(app)


class TestMqttMCPHealth:
    def test_health_endpoint(self):
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["service"] == "mqtt-mcp"
        assert data["status"] in {"healthy", "degraded"}
        assert "checks" in data
        assert "broker_connected" in data["checks"]
