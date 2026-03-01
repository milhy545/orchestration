#!/usr/bin/env python3
"""
Direct MCP Bridge - Nová architektura
Přímé spojení mezi AI systémy a MCP services bez problematického ZEN proxy
"""

import json
import requests
import sys
from typing import Dict, Any, List, Optional

class DirectMCPBridge:
    """
    Přímé spojení s MCP services - obchází ZEN Coordinator problémy
    """
    def __init__(self):
        # Přímé porty MCP services na HAS
        self.services = {
            'filesystem': {'host': '192.168.0.58', 'port': 8001, 'active': True},
            'git': {'host': '192.168.0.58', 'port': 8002, 'active': True}, 
            'terminal': {'host': '192.168.0.58', 'port': 8003, 'active': True},
            'database': {'host': '192.168.0.58', 'port': 8004, 'active': True},
            'memory': {'host': '192.168.0.58', 'port': 8005, 'active': True},  # Fixed port
            'transcriber': {'host': '192.168.0.58', 'port': 8010, 'active': True},
            'research': {'host': '192.168.0.58', 'port': 8011, 'active': True}
        }
        
        # Tool-to-service mapping
        self.tool_mapping = {
            # Filesystem
            'file_list': 'filesystem',
            'file_read': 'filesystem', 
            'file_write': 'filesystem',
            'file_search': 'filesystem',
            'file_analyze': 'filesystem',
            
            # Terminal
            'terminal_exec': 'terminal',
            'shell_command': 'terminal',
            'system_info': 'terminal',
            
            # Git
            'git_status': 'git',
            'git_commit': 'git',
            'git_push': 'git',
            'git_log': 'git', 
            'git_diff': 'git',
            
            # Memory
            'search_memories': 'memory',
            'store_memory': 'memory',
            'get_context': 'memory',
            'memory_stats': 'memory',
            'list_memories': 'memory',
            
            # Research
            'research_query': 'research',
            'perplexity_search': 'research', 
            'web_search': 'research',
            
            # Transcriber
            'transcribe_webm': 'transcriber',
            'transcribe_url': 'transcriber',
            'audio_convert': 'transcriber'
        }
    
    def call_direct(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Přímé volání MCP service bez ZEN proxy"""
        if arguments is None:
            arguments = {}
            
        # Najdi service pro tool
        if tool_name not in self.tool_mapping:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
            
        service_name = self.tool_mapping[tool_name]
        service = self.services.get(service_name)
        
        if not service or not service['active']:
            return {"success": False, "error": f"Service {service_name} not available"}
        
        # Kompletní API endpoint mapping pro všechny MCP nástroje
        api_routes = {
            # Filesystem (port 8001)
            'file_list': {'method': 'GET', 'url': lambda args: f"/files/{args.get('path', '/').lstrip('/')}"},
            'file_read': {'method': 'GET', 'url': lambda args: f"/file/{args.get('path', '').lstrip('/')}"},
            'file_write': {'method': 'POST', 'url': lambda args: f"/file/{args.get('path', '').lstrip('/')}"},
            
            # Terminal (port 8003)  
            'terminal_exec': {'method': 'POST', 'url': lambda args: '/command'},
            'shell_command': {'method': 'POST', 'url': lambda args: '/command'},
            'system_info': {'method': 'GET', 'url': lambda args: '/processes'},
            
            # Git (port 8002)
            'git_status': {'method': 'GET', 'url': lambda args: f"/git/{args.get('path', '.').lstrip('/')}/status"},
            'git_log': {'method': 'GET', 'url': lambda args: f"/git/{args.get('path', '.').lstrip('/')}/log"},
            'git_diff': {'method': 'GET', 'url': lambda args: f"/git/{args.get('path', '.').lstrip('/')}/diff"},
            
            # Memory (port 8005)
            'search_memories': {'method': 'GET', 'url': lambda args: f"/memory/search?query={args.get('query', '')}&limit={args.get('limit', 5)}"},
            'store_memory': {'method': 'POST', 'url': lambda args: '/memory/store'},
            'list_memories': {'method': 'GET', 'url': lambda args: '/memory/list'},
            'memory_stats': {'method': 'GET', 'url': lambda args: '/memory/stats'},
        }
        
        if tool_name not in api_routes:
            return {"success": False, "error": f"No API route defined for tool: {tool_name}"}
            
        route = api_routes[tool_name]
        url = f"http://{service['host']}:{service['port']}{route['url'](arguments)}"
        method = route['method']
        
        try:
            # Použij správnou HTTP metodu podle API route
            if method == 'GET':
                response = requests.get(url, timeout=10)
            elif method == 'POST':
                response = requests.post(
                    url, 
                    json=arguments,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
            else:
                return {"success": False, "error": f"Unsupported HTTP method: {method}"}
            
            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {
                    "success": False, 
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "service": service_name,
                    "tool": tool_name
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Direct call failed: {str(e)}",
                "service": service_name,
                "tool": tool_name
            }
    
    def health_check_all(self) -> Dict[str, Any]:
        """Health check všech MCP services přímo"""
        results = {}
        for name, service in self.services.items():
            try:
                url = f"http://{service['host']}:{service['port']}/health"
                response = requests.get(url, timeout=5)
                results[name] = {
                    "status": "healthy" if response.status_code == 200 else "error",
                    "port": service['port'],
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                results[name] = {
                    "status": "unreachable",
                    "port": service['port'], 
                    "error": str(e)
                }
        return results
    
    def list_tools(self) -> List[str]:
        """Seznam všech dostupných nástrojů"""
        return list(self.tool_mapping.keys())

def main():
    """CLI interface pro Direct MCP Bridge"""
    bridge = DirectMCPBridge()
    
    if len(sys.argv) < 2:
        print("Usage: python direct_mcp_bridge.py <command> [args...]")
        print("Commands: health, tools, call <tool_name> [json_args]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "health":
        health = bridge.health_check_all()
        print(json.dumps(health, indent=2))
        
    elif command == "tools":
        tools = bridge.list_tools()
        print(json.dumps({"tools": tools, "count": len(tools)}, indent=2))
        
    elif command == "call" and len(sys.argv) > 2:
        tool_name = sys.argv[2]
        args = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = bridge.call_direct(tool_name, args)
        print(json.dumps(result, indent=2))
        
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()