#!/usr/bin/env python3
import json
import sys
import subprocess
import time
from typing import Dict, List, Any

# NEW OPTIMIZED MCP Services Configuration  
MCP_SERVICES = {
    # 8001-8010: Core MCP Services (Základní služby)
    'filesystem': {'port': 8001, 'path': ''},      # File Operations
    'git': {'port': 8002, 'path': ''},             # Version Control  
    'terminal': {'port': 8003, 'path': ''},        # Command Execution
    'database': {'port': 8004, 'path': ''},        # Data Operations
    'memory': {'port': 8005, 'path': ''},          # Simple Storage
    'network': {'port': 8006, 'path': '/health'},  # Network Operations
    'system': {'port': 8007, 'path': '/health'},   # System Info
    'security': {'port': 8008, 'path': '/health'}, # Security Operations
    'config': {'port': 8009, 'path': '/health'},   # Configuration Management
    'log': {'port': 8010, 'path': '/health'},      # Logging Operations
    
    # 8011-8020: AI/Enhanced Services (Pokročilé AI služby)
    'research': {'port': 8011, 'path': ''},        # AI Research
    'advanced_memory': {'port': 8012, 'path': ''}, # AI Memory (vector search)
    'transcriber': {'port': 8013, 'path': ''},     # Audio Processing
    'vision': {'port': 8014, 'path': '/health'},   # Image Processing (placeholder)
    
    # 8020: ZEN Coordinator
    'coordinator': {'port': 8020, 'path': '/health'}, # Master Controller
    
    # 8021-8023: Support Services 
    'postgresql': {'port': 8021, 'path': ''},      # Primary Database
    'redis': {'port': 8022, 'path': ''},           # Cache/Sessions
    'qdrant': {'port': 8023, 'path': ''},          # Vector Database
    
    # 8028-8030: Management Services
    'monitoring': {'port': 8028, 'path': ''},      # Health Checks & Metrics
    'backup': {'port': 8029, 'path': '/health'},   # Automated backups
    'message_queue': {'port': 8030, 'path': ''}    # Task queuing
}

# ZEN Enhanced Tools
ZEN_TOOLS = {
    'orchestrate': {
        'description': 'Coordinate multiple MCP services for complex tasks',
        'parameters': {
            'type': 'object',
            'properties': {
                'task': {'type': 'string', 'description': 'The complex task to orchestrate'},
                'services': {'type': 'array', 'items': {'type': 'string'}, 'description': 'MCP services to coordinate'}
            },
            'required': ['task']
        }
    },
    'memory_workflow': {
        'description': 'Execute memory operations with semantic search and storage',
        'parameters': {
            'type': 'object',
            'properties': {
                'action': {'type': 'string', 'enum': ['store', 'search', 'recall', 'analyze']},
                'content': {'type': 'string', 'description': 'Content to process'},
                'memory_type': {'type': 'string', 'enum': ['episodic', 'semantic', 'procedural', 'emotional']}
            },
            'required': ['action', 'content']
        }
    },
    'system_status': {
        'description': 'Get comprehensive system status across all MCP services',
        'parameters': {
            'type': 'object',
            'properties': {
                'detailed': {'type': 'boolean', 'default': False}
            }
        }
    },
    'docker_status': {
        'description': 'Get Docker containers status for MCP services',
        'parameters': {
            'type': 'object',
            'properties': {
                'service_filter': {'type': 'string', 'description': 'Filter containers by service name'}
            }
        }
    },
    'service_health': {
        'description': 'Get health status of specific MCP service',
        'parameters': {
            'type': 'object',
            'properties': {
                'service': {'type': 'string', 'description': 'Service name to check'},
                'include_logs': {'type': 'boolean', 'default': False}
            },
            'required': ['service']
        }
    }
}

class ZENMCPServer:
    def __init__(self):
        self.services = MCP_SERVICES
        self.tools = ZEN_TOOLS

    def call_mcp_service_curl(self, service_name: str, method: str, params: Dict = None) -> Dict:
        """Call MCP service using curl"""
        if service_name not in self.services:
            return {'error': f'Unknown service: {service_name}'}
            
        service_config = self.services[service_name]
        url = f"http://localhost:{service_config['port']}{service_config['path']}"
        
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': method,
            'params': params or {}
        }
        
        try:
            curl_cmd = [
                'curl', '-s', '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps(payload),
                '--max-time', '10',
                url
            ]
            
            result = subprocess.run(curl_cmd, capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'error': f'Invalid JSON response: {result.stdout}'}
            else:
                return {'error': f'Curl failed: {result.stderr or result.stdout}'}
                
        except subprocess.TimeoutExpired:
            return {'error': 'Service call timeout'}
        except Exception as e:
            return {'error': f'Service call failed: {str(e)}'}

    def handle_orchestrate(self, params: Dict) -> Dict:
        """Handle orchestration requests"""
        task = params.get('task', '')
        services = params.get('services', ['filesystem', 'memory', 'research'])
        
        results = {}
        
        # Memory workflow
        if 'memory' in task.lower() or 'remember' in task.lower():
            memory_result = self.call_mcp_service_curl('advanced_memory', 'search', {'query': task})
            results['advanced_memory'] = memory_result
            
        # Research workflow  
        if 'research' in task.lower() or 'find' in task.lower():
            research_result = self.call_mcp_service_curl('research', 'search', {'query': task})
            results['research'] = research_result
            
        # Service status check
        for service in services:
            if service in self.services:
                result = self.call_mcp_service_curl(service, 'status', {})
                results[f'{service}_status'] = result
                
        return {
            'task': task,
            'orchestration_results': results,
            'timestamp': time.time(),
            'services_checked': services,
            'architecture': 'optimized_30_services'
        }

    def handle_memory_workflow(self, params: Dict) -> Dict:
        """Handle memory workflow operations"""
        action = params.get('action', 'search')
        content = params.get('content', '')
        memory_type = params.get('memory_type', 'semantic')
        
        if action == 'store':
            result = self.call_mcp_service_curl('advanced_memory', 'store', {
                'content': content,
                'memory_type': memory_type,
                'metadata': {'source': 'zen_orchestrator', 'timestamp': time.time()}
            })
        elif action == 'search':
            result = self.call_mcp_service_curl('advanced_memory', 'search', {
                'query': content,
                'memory_type': memory_type,
                'limit': 10
            })
        elif action == 'recall':
            result = self.call_mcp_service_curl('advanced_memory', 'recall', {
                'context': content,
                'memory_type': memory_type
            })
        elif action == 'analyze':
            result = self.call_mcp_service_curl('advanced_memory', 'analyze', {
                'content': content,
                'analysis_type': memory_type
            })
        else:
            result = {'error': f'Unknown memory action: {action}'}
            
        return result

    def handle_system_status(self, params: Dict) -> Dict:
        """Get comprehensive system status - NEW OPTIMIZED VERSION"""
        detailed = params.get('detailed', False)
        status = {}
        
        # Count services by category
        categories = {
            'core_services': ['filesystem', 'git', 'terminal', 'database', 'memory', 'network', 'system', 'security', 'config', 'log'],
            'ai_services': ['research', 'advanced_memory', 'transcriber', 'vision'],
            'support_services': ['postgresql', 'redis', 'qdrant'],
            'management_services': ['monitoring', 'backup', 'message_queue'],
            'coordinator': ['coordinator']
        }
        
        category_status = {}
        
        for category, service_list in categories.items():
            category_status[category] = {
                'services': {},
                'healthy_count': 0,
                'total_count': len(service_list)
            }
            
            for service_name in service_list:
                if service_name in self.services:
                    try:
                        result = self.call_mcp_service_curl(service_name, 'health', {})
                        is_healthy = 'error' not in result
                        category_status[category]['services'][service_name] = {
                            'status': 'healthy' if is_healthy else 'error',
                            'port': self.services[service_name]['port'],
                            'details': result if detailed else None
                        }
                        if is_healthy:
                            category_status[category]['healthy_count'] += 1
                    except Exception as e:
                        category_status[category]['services'][service_name] = {
                            'status': 'error',
                            'port': self.services[service_name]['port'],
                            'error': str(e)
                        }
        
        # Overall statistics
        total_services = sum(cat['total_count'] for cat in category_status.values())
        healthy_services = sum(cat['healthy_count'] for cat in category_status.values())
        
        return {
            'architecture': 'optimized_30_services',
            'categories': category_status,
            'total_services': total_services,
            'healthy_services': healthy_services,
            'system_health': 'excellent' if healthy_services >= total_services * 0.9 else 
                           'good' if healthy_services >= total_services * 0.7 else 'degraded',
            'timestamp': time.time()
        }

    def handle_service_health(self, params: Dict) -> Dict:
        """Get health status of specific service"""
        service = params.get('service', '')
        include_logs = params.get('include_logs', False)
        
        if service not in self.services:
            return {'error': f'Unknown service: {service}'}
            
        # Get service health
        result = self.call_mcp_service_curl(service, 'health', {})
        
        response = {
            'service': service,
            'port': self.services[service]['port'],
            'path': self.services[service]['path'],
            'health': result,
            'timestamp': time.time()
        }
        
        # Add Docker logs if requested
        if include_logs:
            try:
                logs_cmd = ['docker', 'logs', f'mcp-{service.replace("_", "-")}', '--tail', '10']
                logs_result = subprocess.run(logs_cmd, capture_output=True, text=True, timeout=5)
                response['logs'] = logs_result.stdout if logs_result.returncode == 0 else logs_result.stderr
            except Exception as e:
                response['logs_error'] = str(e)
                
        return response

    def handle_docker_status(self, params: Dict) -> Dict:
        """Get Docker container status"""
        service_filter = params.get('service_filter', '')
        
        try:
            if service_filter:
                cmd = ['docker', 'ps', '--format', 'json', '--filter', f'name={service_filter}']
            else:
                cmd = ['docker', 'ps', '--format', 'json', '--filter', 'name=mcp-']
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            containers = []
            if result.returncode == 0 and result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            containers.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
            
            return {
                'containers': containers,
                'total_containers': len(containers),
                'mcp_services_running': len([c for c in containers if 'mcp-' in c.get('Names', '')]),
                'architecture': 'optimized_30_services',
                'timestamp': time.time()
            }
            
        except Exception as e:
            return {'error': f'Docker status failed: {str(e)}'}

    def handle_request(self, request: Dict) -> Dict:
        """Handle MCP tool requests"""
        method = request.get('method', '')
        params = request.get('params', {})
        
        if method == 'tools/list':
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {
                    'tools': [
                        {
                            'name': name,
                            'description': tool['description'],
                            'inputSchema': tool['parameters']
                        }
                        for name, tool in self.tools.items()
                    ]
                }
            }
        elif method == 'tools/call':
            tool_name = params.get('name', '')
            tool_params = params.get('arguments', {})
            
            if tool_name == 'orchestrate':
                result = self.handle_orchestrate(tool_params)
            elif tool_name == 'memory_workflow':
                result = self.handle_memory_workflow(tool_params)
            elif tool_name == 'system_status':
                result = self.handle_system_status(tool_params)
            elif tool_name == 'docker_status':
                result = self.handle_docker_status(tool_params)
            elif tool_name == 'service_health':
                result = self.handle_service_health(tool_params)
            else:
                result = {'error': f'Unknown tool: {tool_name}'}
                
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'result': {'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}]}
            }
        else:
            return {
                'jsonrpc': '2.0',
                'id': request.get('id'),
                'error': {'code': -32601, 'message': f'Method not found: {method}'}
            }

def main():
    """Main MCP server loop"""
    server = ZENMCPServer()
    
    try:
        # MCP stdio protocol
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
                    'error': {'code': -32700, 'message': 'Parse error'}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
            except Exception as e:
                error_response = {
                    'jsonrpc': '2.0',
                    'id': None,
                    'error': {'code': -32603, 'message': f'Internal error: {str(e)}'}
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()