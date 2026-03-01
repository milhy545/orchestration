#\!/usr/bin/env python3
"""
ZEN Coordinator pro organizovanou MCP architekturu
Bezpečný proxy pro MCP servery s PostgreSQL integrací a Redis cachingem
"""

import json
import socket
import urllib.parse
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging
import uuid
import psycopg2
import redis

# Konfigurace organizovaných MCP serverů
MCP_SERVICES = {
    "filesystem": {
        "description": "Enhanced Filesystem MCP (Organized)",
        "tools": ["file_read", "file_write", "file_list", "file_search", "file_analyze"],
        "internal_port": 8001,
        "status": "unknown",
        "container": "mcp-filesystem"
    },
    "git": {
        "description": "Git Operations MCP (Organized)",
        "tools": ["git_status", "git_commit", "git_push", "git_log", "git_diff"],
        "internal_port": 8002,
        "status": "unknown", 
        "container": "mcp-git"
    },
    "terminal": {
        "description": "Terminal Operations MCP (Organized)",
        "tools": ["terminal_exec", "shell_command", "system_info"],
        "internal_port": 8003,
        "status": "unknown",
        "container": "mcp-terminal"
    },
    "database": {
        "description": "Database Operations MCP (Organized)",
        "tools": ["db_query", "db_connect", "db_schema", "db_backup"],
        "internal_port": 8004,
        "status": "unknown",
        "container": "mcp-database"
    },
    "memory": {
        "description": "Memory & Context MCP (Organized)", 
        "tools": ["store_memory", "search_memories", "get_context", "memory_stats"],
        "internal_port": 8007,
        "status": "unknown",
        "container": "mcp-memory"
    },
    "transcriber": {
        "description": "WebM Transcriber MCP (Organized)",
        "tools": ["transcribe_webm", "transcribe_url", "audio_convert"],
        "internal_port": 8008,
        "status": "unknown",
        "container": "mcp-transcriber"
    },
    "research": {
        "description": "Research & Perplexity MCP (Organized)",
        "tools": ["research_query", "perplexity_search", "web_search"],
        "internal_port": 8011,
        "status": "unknown",
        "container": "mcp-research"
    }
}

# Database a cache konfigurace
POSTGRES_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "mcp_unified",
    "user": "mcp_admin",
    "password": "mcp_secure_2024"
}

REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0
}

def get_redis_client():
    """Get Redis client for caching"""
    try:
        return redis.Redis(**REDIS_CONFIG)
    except:
        return None

def log_mcp_request(service, tool, success, response_time=None):
    """Log MCP request to PostgreSQL"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO mcp_request_logs (service, tool, success, response_time, timestamp)
            VALUES (%s, %s, %s, %s, NOW())
        """, (service, tool, success, response_time))
        
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logging.warning(f"Failed to log request: {e}")

def check_mcp_service_health(port):
    """Check if MCP service is healthy using socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("localhost", port))
        sock.close()
        return result == 0
    except:
        return False

def call_mcp_service(port, method, params=None):
    """Call MCP service using proper JSON-RPC 2.0 protocol with caching"""
    import time
    start_time = time.time()
    
    try:
        # Check Redis cache first for read operations
        redis_client = get_redis_client()
        cache_key = f"mcp:{port}:{method}:{json.dumps(params, sort_keys=True)}"
        
        if redis_client and method in ["tools/list", "health"]:
            cached = redis_client.get(cache_key)
            if cached:
                return {
                    "success": True,
                    "data": json.loads(cached),
                    "method": "cached"
                }
        
        # MCP JSON-RPC 2.0 request
        request_id = str(uuid.uuid4())
        
        mcp_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        # Try direct HTTP first
        try:
            data = json.dumps(mcp_request).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Content-Length": str(len(data))
            }
            
            req = urllib.request.Request(
                f"http://localhost:{port}/mcp",
                data=data,
                headers=headers,
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                
                # Cache successful responses
                if redis_client and method in ["tools/list", "health"]:
                    redis_client.setex(cache_key, 300, json.dumps(response_data))  # 5min cache
                
                response_time = time.time() - start_time
                return {
                    "success": True,
                    "data": response_data,
                    "method": "http",
                    "response_time": response_time
                }
        except Exception as e:
            # Try alternative endpoints as fallback
            return adapt_to_native_api(port, method, params)
        
    except Exception as e:
        response_time = time.time() - start_time
        return {
            "success": False,
            "error": f"MCP service call failed: {str(e)}",
            "response_time": response_time
        }

def adapt_to_native_api(port, method, params=None):
    """Adapt MCP calls to native FastAPI endpoints as fallback"""
    try:
        # Implement service-specific adaptations here
        return {
            "success": False,
            "error": f"Service on port {port} requires MCP protocol adaptation"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"API adaptation failed: {str(e)}"
        }

class ZENCoordinator(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Custom log format"""
        logging.info(f"ZEN Coordinator (Organized) - {self.address_string()} - {format % args}")
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/services":
            self.handle_services_list()
        elif parsed_path.path == "/health":
            self.handle_health_check()
        elif parsed_path.path == "/tools/list":
            self.handle_tools_list()
        elif parsed_path.path == "/stats":
            self.handle_stats()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == "/mcp":
            self.handle_mcp_request()
        elif parsed_path.path == "/tools/call":
            self.handle_tools_call()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_services_list(self):
        """GET /services - seznam MCP služeb s organizovanou architekturou"""
        # Update service status
        for service_name, config in MCP_SERVICES.items():
            config["status"] = "running" if check_mcp_service_health(config["internal_port"]) else "offline"
        
        response_data = {
            "zen_coordinator": {
                "status": "running",
                "port": 8020,
                "protocol": "MCP over HTTP",
                "architecture": "organized",
                "security": "Services accessible only through coordinator",
                "database": "PostgreSQL unified storage",
                "cache": "Redis caching enabled",
                "services": MCP_SERVICES
            },
            "infrastructure": {
                "postgresql": {"host": "localhost", "port": 5432, "database": "mcp_unified"},
                "redis": {"host": "localhost", "port": 6379},
                "organization": "/home/orchestration/"
            }
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2).encode())
    
    def handle_health_check(self):
        """GET /health - health check koordinátor s database stavem"""
        running_services = sum(1 for config in MCP_SERVICES.values() 
                             if check_mcp_service_health(config["internal_port"]))
        total_services = len(MCP_SERVICES)
        
        # Check database connection
        db_healthy = True
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            conn.close()
        except:
            db_healthy = False
        
        # Check Redis connection
        redis_healthy = True
        try:
            redis_client = get_redis_client()
            if redis_client:
                redis_client.ping()
        except:
            redis_healthy = False
        
        health_status = "healthy" if (running_services == total_services and db_healthy and redis_healthy) else "degraded"
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": health_status,
            "service": "ZEN Coordinator (Organized)",
            "port": 8020,
            "services_running": running_services,
            "services_total": total_services,
            "database_healthy": db_healthy,
            "redis_healthy": redis_healthy,
            "architecture": "organized PostgreSQL + Redis"
        }).encode())
    
    def handle_tools_list(self):
        """GET /tools/list - seznam všech dostupných MCP tools z organizované architektury"""
        all_tools = []
        
        for service_name, config in MCP_SERVICES.items():
            if check_mcp_service_health(config["internal_port"]):
                for tool in config["tools"]:
                    all_tools.append({
                        "name": tool,
                        "service": service_name,
                        "description": f"{tool} via {config[description]}",
                        "container": config["container"]
                    })
        
        response_data = {
            "jsonrpc": "2.0",
            "result": {
                "tools": all_tools,
                "total_tools": len(all_tools),
                "architecture": "organized"
            }
        }
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(response_data, indent=2).encode())
    
    def handle_stats(self):
        """GET /stats - statistiky použití z PostgreSQL"""
        try:
            conn = psycopg2.connect(**POSTGRES_CONFIG)
            cursor = conn.cursor()
            
            # Get request statistics
            cursor.execute("""
                SELECT service, tool, COUNT(*) as count,
                       AVG(response_time) as avg_time,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM mcp_request_logs
                WHERE timestamp >= NOW() - INTERVAL 24 hours
                GROUP BY service, tool
                ORDER BY count DESC
            """)
            
            stats = cursor.fetchall()
            cursor.close()
            conn.close()
            
            response_data = {
                "stats": [
                    {
                        "service": row[0],
                        "tool": row[1], 
                        "requests": row[2],
                        "avg_response_time": float(row[3]) if row[3] else 0,
                        "success_rate": (row[4] / row[2] * 100) if row[2] > 0 else 0
                    }
                    for row in stats
                ]
            }
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            self.send_error(500, f"Stats error: {str(e)}")
    
    def handle_mcp_request(self):
        """POST /mcp - hlavní MCP proxy endpoint pro organizovanou architekturu"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in MCP request")
                return
            
            tool_name = request_data.get("tool", "")
            if not tool_name:
                self.send_error(400, "Missing tool parameter in request")
                return
            
            # Route to appropriate service
            target_service, target_port = self.route_tool_to_service(tool_name)
            
            if not target_service:
                self.send_error(400, f"Unknown tool: {tool_name}")
                return
            
            if not check_mcp_service_health(target_port):
                self.send_error(502, f"Service {target_service} (port {target_port}) is offline")
                return
            
            # Convert to proper MCP format
            mcp_params = {
                "name": tool_name,
                "arguments": request_data.get("arguments", {})
            }
            
            # Call MCP service
            result = call_mcp_service(target_port, "tools/call", mcp_params)
            
            # Log request
            log_mcp_request(target_service, tool_name, result["success"], 
                          result.get("response_time"))
            
            if result["success"]:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                
                response_json = json.dumps(result["data"], indent=2)
                self.wfile.write(response_json.encode())
            else:
                self.send_error(502, f"Service {target_service} error: {result.get(error, Unknown error)}")
                
        except Exception as e:
            self.send_error(500, f"Coordinator internal error: {str(e)}")
    
    def handle_tools_call(self):
        """POST /tools/call - MCP tools/call endpoint pro organizovanou architekturu"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            
            try:
                request_data = json.loads(post_data.decode("utf-8"))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON in tools/call request")
                return
            
            params = request_data.get("params", {})
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            
            if not tool_name:
                self.send_error(400, "Missing tool name in tools/call request")
                return
            
            # Route and execute
            target_service, target_port = self.route_tool_to_service(tool_name)
            
            if not target_service:
                self.send_error(400, f"Unknown tool: {tool_name}")
                return
            
            if not check_mcp_service_health(target_port):
                self.send_error(502, f"Service {target_service} is offline")
                return
            
            # Execute tool call
            result = call_mcp_service(target_port, "tools/call", {
                "name": tool_name,
                "arguments": tool_args
            })
            
            # Log request
            log_mcp_request(target_service, tool_name, result["success"],
                          result.get("response_time"))
            
            if result["success"]:
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(result["data"], indent=2).encode())
            else:
                self.send_error(502, f"Tool execution failed: {result.get(error, Unknown error)}")
                
        except Exception as e:
            self.send_error(500, f"Tools/call handler error: {str(e)}")
    
    def route_tool_to_service(self, tool_name):
        """Route tool name to appropriate MCP service"""
        # Direct tool mapping
        for service_name, config in MCP_SERVICES.items():
            if tool_name in config["tools"]:
                return service_name, config["internal_port"]
        
        # Prefix-based routing
        routing_prefixes = {
            "file_": ("filesystem", 8001),
            "git_": ("git", 8002),
            "terminal_": ("terminal", 8003),
            "shell_": ("terminal", 8003),
            "db_": ("database", 8004),
            "store_": ("memory", 8007),
            "search_": ("memory", 8007),
            "memory_": ("memory", 8007),
            "transcribe_": ("transcriber", 8008),
            "audio_": ("transcriber", 8008),
            "research_": ("research", 8011),
            "web_": ("research", 8011)
        }
        
        for prefix, (service, port) in routing_prefixes.items():
            if tool_name.startswith(prefix):
                return service, port
        
        return None, None

def setup_database():
    """Setup database tables for logging"""
    try:
        conn = psycopg2.connect(**POSTGRES_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mcp_request_logs (
                id SERIAL PRIMARY KEY,
                service VARCHAR(50),
                tool VARCHAR(100),
                success BOOLEAN,
                response_time FLOAT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mcp_logs_timestamp 
            ON mcp_request_logs(timestamp);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database tables created/verified")
        
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")

def main():
    """Start ZEN Coordinator with organized architecture"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - ZEN Coordinator (Organized) - %(levelname)s - %(message)s"
    )
    
    # Setup database
    setup_database()
    
    # Start HTTP server
    server = HTTPServer(("0.0.0.0", 8020), ZENCoordinator)
    
    print("🎯 ZEN Coordinator (Organized Architecture) started on http://0.0.0.0:8020")
    print("🏗️ Architecture: PostgreSQL + Redis + Docker Compose")
    print("🔒 Security: MCP services accessible only through coordinator")
    print("📊 Endpoints:")
    print("  GET  /services    - List MCP services")
    print("  GET  /health      - Health check")
    print("  GET  /tools/list  - List all MCP tools")
    print("  GET  /stats       - Usage statistics")
    print("  POST /mcp         - MCP tool proxy (legacy)")
    print("  POST /tools/call  - MCP tools/call (standard)")
    print()
    print("🔗 Protected MCP Services (Organized):")
    for name, config in MCP_SERVICES.items():
        status = "🟢" if check_mcp_service_health(config["internal_port"]) else "🔴"
        print(f"  {status} {name}: localhost:{config[internal_port]} - {config[description]}")
    print()
    print("✅ Ready for secure organized MCP communication...")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\n🛑 ZEN Coordinator shutting down...")
        server.server_close()

if __name__ == "__main__":
    main()
