#!/usr/bin/env python3
import json
import os
import sys
import subprocess
import time
import uuid
from typing import Dict, List, Any, Optional

class ToolRoutingError(Exception):
    """Custom exception for tool routing failures"""
    pass

class ZENMCPServerV2:
    def __init__(self):
        self.services = {
            # Core MCP Services
            'filesystem': {'port': 7001, 'methods': ['read', 'write', 'list', 'search']},
            'git': {'port': 7002, 'methods': ['status', 'commit', 'push', 'log']},
            'terminal': {'port': 7003, 'methods': ['execute', 'info', 'shell']},
            'database': {'port': 7004, 'methods': ['query', 'execute', 'schema']},
            'memory': {'port': 7005, 'methods': ['store', 'search', 'retrieve']},
            'advanced_memory': {'port': 7012, 'methods': ['semantic_store', 'vector_search', 'analyze']},
            'research': {'port': 7011, 'methods': ['query', 'web_search', 'perplexity']},
            'transcriber': {'port': 7013, 'methods': ['audio', 'video', 'convert']},
            'marketplace': {'port': 7034, 'methods': ['skills_list', 'skills_resolve', 'registry_search', 'registry_get_server', 'catalog_validate']},
        }
        
        self.tool_service_mapping = {
            # Comprehensive tool-to-service mapping
            'file_read': {'service': 'filesystem', 'method': 'read'},
            'file_write': {'service': 'filesystem', 'method': 'write'},
            'file_list': {'service': 'filesystem', 'method': 'list'},
            'terminal_exec': {'service': 'terminal', 'method': 'execute'},
            'git_status': {'service': 'git', 'method': 'status'},
            'git_commit': {'service': 'git', 'method': 'commit'},
            'system_info': {'service': 'terminal', 'method': 'info'},
            'database_query': {'service': 'database', 'method': 'query'},
            'store_memory': {'service': 'memory', 'method': 'store'},
            'search_memories': {'service': 'memory', 'method': 'search'},
            'research_query': {'service': 'research', 'method': 'query'},
            'transcribe_audio': {'service': 'transcriber', 'method': 'audio'},
            'semantic_store': {'service': 'advanced_memory', 'method': 'semantic_store'},
            'skills_list': {'service': 'marketplace', 'method': 'skills_list'},
            'skills_resolve': {'service': 'marketplace', 'method': 'skills_resolve'},
            'registry_search': {'service': 'marketplace', 'method': 'registry_search'},
            'registry_get_server': {'service': 'marketplace', 'method': 'registry_get_server'},
            'catalog_validate': {'service': 'marketplace', 'method': 'catalog_validate'},
        }

    def call_mcp_service(self, service: str, method: str, params: Dict = None) -> Dict:
        """
        Centralized method for calling MCP services with enhanced error handling
        """
        if service not in self.services:
            raise ToolRoutingError(f"Unknown service: {service}")
        
        if method not in self.services[service]['methods']:
            raise ToolRoutingError(f"Invalid method {method} for service {service}")
        
        url = f"http://localhost:{self.services[service]['port']}/mcp"
        
        payload = {
            'jsonrpc': '2.0',
            'id': str(uuid.uuid4()),
            'method': method,
            'params': params or {}
        }
        
        try:
            curl_cmd = [
                'curl', '-s', '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '--max-time', '15',
            ]
            if service == 'marketplace':
                token = os.getenv('MARKETPLACE_JWT_TOKEN', '').strip()
                if token:
                    curl_cmd.extend(['-H', f'Authorization: Bearer {token}'])

            curl_cmd.extend(['-d', json.dumps(payload), url])
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=20)
            
            if result.returncode == 0:
                try:
                    response = json.loads(result.stdout)
                    return response.get('result', {})
                except json.JSONDecodeError:
                    raise ToolRoutingError(f"Invalid JSON response: {result.stdout}")
            else:
                raise ToolRoutingError(f"Service call failed: {result.stderr or result.stdout}")
                
        except subprocess.TimeoutExpired:
            raise ToolRoutingError(f"Service {service} call timeout")
        except Exception as e:
            raise ToolRoutingError(f"Service call error: {str(e)}")

    def route_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Advanced tool routing with fallback and error handling
        """
        if tool_name not in self.tool_service_mapping:
            # Implement fuzzy matching or error correction
            raise ToolRoutingError(f"Tool {tool_name} not mapped to any service")
        
        mapping = self.tool_service_mapping[tool_name]
        
        try:
            result = self.call_mcp_service(
                service=mapping['service'], 
                method=mapping['method'], 
                params=params
            )
            
            return {
                'tool_name': tool_name,
                'service': mapping['service'],
                'method': mapping['method'],
                'result': result,
                'timestamp': time.time()
            }
        except ToolRoutingError as e:
            return {
                'tool_name': tool_name,
                'error': str(e),
                'error_type': 'ToolRoutingError',
                'timestamp': time.time()
            }

    def handle_discovery(self) -> Dict:
        """
        Comprehensive tool and service discovery
        """
        return {
            'services': list(self.services.keys()),
            'tools': list(self.tool_service_mapping.keys()),
            'mcp_version': 'v2.optimized',
            'timestamp': time.time()
        }

    def handle_batch_operation(self, tools: List[Dict]) -> List[Dict]:
        """
        Handle batch tool execution with error isolation
        """
        results = []
        for tool_request in tools:
            tool_name = tool_request.get('name')
            tool_params = tool_request.get('arguments', {})
            
            try:
                result = self.route_tool(tool_name, tool_params)
                results.append(result)
            except Exception as e:
                results.append({
                    'tool_name': tool_name,
                    'error': str(e),
                    'error_type': 'UnhandledError',
                    'timestamp': time.time()
                })
        
        return results

    def handle_request(self, request: Dict) -> Dict:
        """
        Advanced request handler with JSON-RPC 2.0 compatibility
        """
        method = request.get('method', '')
        params = request.get('params', {})
        request_id = request.get('id')
        
        try:
            if method == 'tools/list':
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': self.handle_discovery()
                }
            
            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_params = params.get('arguments', {})
                
                result = self.route_tool(tool_name, tool_params)
                
                return {
                    'jsonrpc': '2.0', 
                    'id': request_id,
                    'result': {
                        'content': [{
                            'type': 'text', 
                            'text': json.dumps(result, indent=2)
                        }]
                    }
                }
            
            elif method == 'tools/batch':
                tools = params.get('tools', [])
                results = self.handle_batch_operation(tools)
                
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'result': {
                        'content': [{
                            'type': 'text',
                            'text': json.dumps(results, indent=2)
                        }]
                    }
                }
            
            else:
                return {
                    'jsonrpc': '2.0',
                    'id': request_id,
                    'error': {
                        'code': -32601, 
                        'message': f'Method not found: {method}'
                    }
                }
        
        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'error': {
                    'code': -32603,
                    'message': f'Internal error: {str(e)}'
                }
            }

def main():
    """Main MCP server loop with advanced error handling"""
    server = ZENMCPServerV2()
    
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
                
            try:
                request = json.loads(line.strip())
                response = server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                error_response = {
                    'jsonrpc': '2.0',
                    'id': None,
                    'error': {
                        'code': -32700, 
                        'message': 'Parse error: Invalid JSON'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    'jsonrpc': '2.0',
                    'id': None,
                    'error': {
                        'code': -32000, 
                        'message': f'Unhandled server error: {str(e)}'
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    
    except KeyboardInterrupt:
        sys.stderr.write("ZEN MCP Server shutting down gracefully...\n")

if __name__ == '__main__':
    main()
