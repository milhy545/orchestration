#!/usr/bin/env python3
"""
MQTT MCP Server - Model Context Protocol compliant MQTT broker interface
Port: 8015 (external) -> 8000 (internal)
Broker: mqtt-broker:1883 (internal Docker network)

Provides JSON-RPC 2.0 tools for MQTT operations
"""

import json
import sys
import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback

# MQTT client library
try:
    import gmqtt
except ImportError:
    print("gmqtt not installed, install with: pip install gmqtt", file=sys.stderr)
    sys.exit(1)

# FastAPI for HTTP interface
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("FastAPI not installed, install with: pip install fastapi uvicorn", file=sys.stderr)
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mqtt-mcp")

class MQTTMCPServer:
    def __init__(self):
        self.mqtt_client = None
        self.mqtt_broker = os.getenv("MQTT_BROKER", "mqtt-broker")  # Docker service name
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.mqtt_username = os.getenv("MQTT_USERNAME", "mcp_admin")
        # lgtm[py/hardcoded-credentials] - Default for development; use MQTT_PASSWORD env var in production
        self.mqtt_password = os.getenv("MQTT_PASSWORD", "mcp_secure_mqtt_2024")
        self.subscribed_topics = {}
        self.connected = False
        
    async def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client = gmqtt.Client("mcp-mqtt-server")
            self.mqtt_client.set_auth_credentials(self.mqtt_username, self.mqtt_password)
            
            # Set event handlers
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.on_message = self.on_mqtt_message
            self.mqtt_client.on_disconnect = self.on_mqtt_disconnect
            
            await self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port)
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}")
            self.connected = True
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            
    async def on_mqtt_connect(self, client, flags, rc, properties):
        """MQTT connection callback"""
        logger.info(f"MQTT connected with result code {rc}")
        
    async def on_mqtt_message(self, client, topic, payload, qos, properties):
        """MQTT message received callback"""
        try:
            message = payload.decode("utf-8")
            timestamp = datetime.now().isoformat()
            logger.info(f"Received message on {topic}: {message}")
            
            # Store message for retrieval
            if topic not in self.subscribed_topics:
                self.subscribed_topics[topic] = []
            self.subscribed_topics[topic].append({
                "timestamp": timestamp,
                "message": message,
                "qos": qos
            })
            
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
            
    async def on_mqtt_disconnect(self, client, packet, exc=None):
        """MQTT disconnection callback"""
        logger.warning("MQTT disconnected")
        self.connected = False

    # MCP Tools Implementation
    async def publish_message(self, topic: str, message: str, qos: int = 0, retain: bool = False) -> Dict[str, Any]:
        """Publish message to MQTT topic"""
        try:
            if not self.connected or not self.mqtt_client:
                await self.connect_mqtt()
                
            if not self.connected:
                return {"success": False, "error": "MQTT broker not available"}
                
            await self.mqtt_client.publish(topic, message, qos=qos, retain=retain)
            
            return {
                "success": True,
                "topic": topic,
                "message": message,
                "qos": qos,
                "retain": retain,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return {"success": False, "error": str(e)}
            
    async def subscribe_topic(self, topic: str, qos: int = 0) -> Dict[str, Any]:
        """Subscribe to MQTT topic"""
        try:
            if not self.connected or not self.mqtt_client:
                await self.connect_mqtt()
                
            if not self.connected:
                return {"success": False, "error": "MQTT broker not available"}
                
            await self.mqtt_client.subscribe(topic, qos=qos)
            
            if topic not in self.subscribed_topics:
                self.subscribed_topics[topic] = []
                
            return {
                "success": True,
                "topic": topic,
                "qos": qos,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error subscribing to topic: {e}")
            return {"success": False, "error": str(e)}
            
    async def get_mqtt_status(self) -> Dict[str, Any]:
        """Get MQTT broker connection status"""
        return {
            "connected": self.connected,
            "broker": f"{self.mqtt_broker}:{self.mqtt_port}",
            "subscribed_topics": list(self.subscribed_topics.keys()),
            "total_messages": sum(len(messages) for messages in self.subscribed_topics.values()),
            "timestamp": datetime.now().isoformat()
        }
        
    async def list_messages(self, topic: str = None, limit: int = 50) -> Dict[str, Any]:
        """List received messages from topics"""
        try:
            if topic:
                messages = self.subscribed_topics.get(topic, [])[-limit:]
                return {"topic": topic, "messages": messages, "count": len(messages)}
            else:
                all_messages = {}
                for t, msgs in self.subscribed_topics.items():
                    all_messages[t] = msgs[-limit:]
                return {"all_topics": all_messages, "total_topics": len(all_messages)}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

# Create FastAPI app
app = FastAPI(title="MQTT MCP Server", version="1.0.0")
mqtt_server = MQTTMCPServer()

@app.on_event("startup")
async def startup_event():
    """Initialize MQTT connection on startup"""
    await mqtt_server.connect_mqtt()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"service": "MQTT MCP Server", "status": "running", "connected": mqtt_server.connected}

@app.post("/mcp")
async def mcp_handler(request: Dict[str, Any]):
    """Main MCP JSON-RPC 2.0 handler"""
    try:
        jsonrpc = request.get("jsonrpc")
        method = request.get("method")
        params = request.get("params", {})
        id_val = request.get("id")
        
        if jsonrpc != "2.0":
            return JSONResponse(
                content={
                    "jsonrpc": "2.0", 
                    "error": {"code": -32600, "message": "Invalid Request"}, 
                    "id": id_val
                },
                status_code=400
            )
            
        # Route to appropriate tool
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "result": {
                    "tools": [
                        {
                            "name": "publish_message",
                            "description": "Publish message to MQTT topic",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "topic": {"type": "string", "description": "MQTT topic"},
                                    "message": {"type": "string", "description": "Message content"},
                                    "qos": {"type": "integer", "default": 0, "description": "QoS level (0-2)"},
                                    "retain": {"type": "boolean", "default": False, "description": "Retain message"}
                                },
                                "required": ["topic", "message"]
                            }
                        },
                        {
                            "name": "subscribe_topic",
                            "description": "Subscribe to MQTT topic",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "topic": {"type": "string", "description": "MQTT topic to subscribe"},
                                    "qos": {"type": "integer", "default": 0, "description": "QoS level (0-2)"}
                                },
                                "required": ["topic"]
                            }
                        },
                        {
                            "name": "get_mqtt_status",
                            "description": "Get MQTT broker connection status",
                            "inputSchema": {"type": "object", "properties": {}}
                        },
                        {
                            "name": "list_messages",
                            "description": "List received messages from subscribed topics",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "topic": {"type": "string", "description": "Specific topic (optional)"},
                                    "limit": {"type": "integer", "default": 50, "description": "Message limit"}
                                }
                            }
                        }
                    ]
                },
                "id": id_val
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name == "publish_message":
                result = await mqtt_server.publish_message(**arguments)
            elif tool_name == "subscribe_topic":
                result = await mqtt_server.subscribe_topic(**arguments)
            elif tool_name == "get_mqtt_status":
                result = await mqtt_server.get_mqtt_status()
            elif tool_name == "list_messages":
                result = await mqtt_server.list_messages(**arguments)
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                        "id": id_val
                    },
                    status_code=400
                )
                
            return {"jsonrpc": "2.0", "result": {"content": [{"type": "text", "text": json.dumps(result)}]}, "id": id_val}
            
        else:
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Unknown method: {method}"},
                    "id": id_val
                },
                status_code=400
            )
            
    except Exception as e:
        logger.error(f"MCP handler error: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": "Internal error"},
                "id": request.get("id")
            },
            status_code=500
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
