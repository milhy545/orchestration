#\!/usr/bin/env python3
"""
Enhanced ZEN Coordinator with Multi-Model Orchestration
Based on BeehiveInnovations ZEN MCP architecture
"""

import json
import urllib.request
import urllib.parse
import logging
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Multi-Model Configuration
AI_PROVIDERS = {
    'gemini': {
        'api_key': os.getenv('GEMINI_API_KEY', ''),
        'models': ['gemini-pro', 'gemini-pro-vision'],
        'strengths': ['reasoning', 'analysis', 'multilingual']
    },
    'openai': {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
        'models': ['gpt-4', 'gpt-3.5-turbo'],
        'strengths': ['coding', 'conversation', 'creativity']
    },
    'claude': {
        'api_key': os.getenv('ANTHROPIC_API_KEY', ''),
        'models': ['claude-3-sonnet', 'claude-3-haiku'], 
        'strengths': ['analysis', 'safety', 'reasoning']
    }
}

# Enhanced MCP Services with AI capabilities
MCP_SERVICES = {
    'cldmemory': {
        'port': 8006,
        'container': 'mcp-cldmemory',
        'tools': ['store_memory', 'search_memories', 'memory_stats'],
        'ai_enhanced': True
    },
    'filesystem': {
        'port': 8001,
        'container': 'mcp-filesystem', 
        'tools': ['file_read', 'file_write', 'file_list'],
        'ai_enhanced': False
    },
    'terminal': {
        'port': 8003,
        'container': 'mcp-terminal',
        'tools': ['terminal_exec', 'shell_command'],
        'ai_enhanced': False
    },
    'research': {
        'port': 8011,
        'container': 'mcp-research',
        'tools': ['research_query', 'web_search'],
        'ai_enhanced': True
    }
}

# ZEN Workflow Tools (BeehiveInnovations inspired)
ZEN_TOOLS = {
    'chat': {
        'description': 'Multi-model conversation with context preservation',
        'models': ['gemini', 'claude', 'openai'],
        'auto_select': True
    },
    'thinkdeep': {
        'description': 'Deep analysis using multiple AI perspectives',
        'models': ['claude', 'gemini'],
        'sequential': True
    },
    'codereview': {
        'description': 'Comprehensive code review with multiple models',
        'models': ['openai', 'claude'],
        'parallel': True
    },
    'debug': {
        'description': 'Multi-model debugging assistance',
        'models': ['openai', 'gemini'],
        'auto_select': True
    },
    'orchestrate': {
        'description': 'Coordinate MCP services with AI decision making',
        'models': ['claude'],
        'mcp_integration': True
    }
}

class EnhancedZENCoordinator(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/health':
            self.handle_health()
        elif parsed_path.path == '/tools':
            self.handle_tools_list()
        elif parsed_path.path == '/models':
            self.handle_models_list()
        elif parsed_path.path == '/services':
            self.handle_services_list()
        else:
            self.send_error(404, 'Endpoint not found')

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/mcp':
            self.handle_mcp_request()
        elif parsed_path.path == '/zen':
            self.handle_zen_orchestration()
        elif parsed_path.path == '/multi-model':
            self.handle_multi_model()
        else:
            self.send_error(404, 'Endpoint not found')

    def handle_health(self):
        """Enhanced health check"""
        try:
            # Check MCP services
            healthy_services = 0
            for service, config in MCP_SERVICES.items():
                try:
                    response = urllib.request.urlopen(
                        f"http://{config['container']}:{config['port']}/health", 
                        timeout=2
                    )
                    if response.getcode() == 200:
                        healthy_services += 1
                except:
                    pass

            # Check AI providers (basic check)
            available_models = []
            for provider, config in AI_PROVIDERS.items():
                if config['api_key']:
                    available_models.append(provider)

            health_data = {
                'status': 'healthy',
                'service': 'Enhanced ZEN Coordinator',
                'port': 8025,
                'mcp_services': {
                    'healthy': healthy_services,
                    'total': len(MCP_SERVICES)
                },
                'ai_providers': {
                    'available': available_models,
                    'total': len(AI_PROVIDERS)
                },
                'zen_tools': list(ZEN_TOOLS.keys()),
                'features': ['multi_model_orchestration', 'mcp_integration', 'context_preservation']
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(health_data, indent=2)
            self.wfile.write(response_json.encode())

        except Exception as e:
            self.send_error(500, f'Health check failed: {str(e)}')

    def handle_tools_list(self):
        """List all available ZEN tools"""
        tools_data = {
            'zen_tools': ZEN_TOOLS,
            'mcp_tools': {service: config['tools'] for service, config in MCP_SERVICES.items()},
            'total_tools': len(ZEN_TOOLS) + sum(len(config['tools']) for config in MCP_SERVICES.values())
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(tools_data, indent=2)
        self.wfile.write(response_json.encode())

    def handle_models_list(self):
        """List available AI models"""
        models_data = {
            'providers': AI_PROVIDERS,
            'available_models': sum([config['models'] for config in AI_PROVIDERS.values()], []),
            'model_strengths': {provider: config['strengths'] for provider, config in AI_PROVIDERS.items()}
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response_json = json.dumps(models_data, indent=2)
        self.wfile.write(response_json.encode())

    def handle_zen_orchestration(self):
        """Handle ZEN workflow orchestration"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            tool = request_data.get('tool', '')
            args = request_data.get('arguments', {})
            
            if tool not in ZEN_TOOLS:
                self.send_error(400, f'Unknown ZEN tool: {tool}')
                return

            # For now, return success with tool info (implement actual orchestration later)
            result = {
                'success': True,
                'tool': tool,
                'config': ZEN_TOOLS[tool],
                'message': f'ZEN {tool} orchestration initiated',
                'next_steps': ['model_selection', 'context_preparation', 'execution']
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            response_json = json.dumps(result, indent=2)
            self.wfile.write(response_json.encode())

        except Exception as e:
            self.send_error(500, f'ZEN orchestration failed: {str(e)}')

    def handle_mcp_request(self):
        """Handle MCP requests (legacy compatibility)"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            tool = request_data.get('tool', '')
            args = request_data.get('arguments', {})
            
            # Route to appropriate MCP service
            for service, config in MCP_SERVICES.items():
                if tool in config['tools']:
                    try:
                        # Direct MCP call to service
                        mcp_request = {
                            'jsonrpc': '2.0',
                            'id': 'mega-orchestrator',
                            'method': 'tools/call',
                            'params': {'name': tool, 'arguments': args}
                        }
                        
                        data = json.dumps(mcp_request).encode('utf-8')
                        req = urllib.request.Request(
                            f"http://{config['container']}:8000/mcp",
                            data=data,
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        with urllib.request.urlopen(req, timeout=10) as response:
                            result = json.loads(response.read().decode('utf-8'))
                        
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        response_json = json.dumps(result, indent=2)
                        self.wfile.write(response_json.encode())
                        return
                        
                    except Exception as e:
                        self.send_error(502, f'MCP service {service} error: {str(e)}')
                        return
            
            self.send_error(400, f'Unknown tool: {tool}')

        except Exception as e:
            self.send_error(500, f'MCP request failed: {str(e)}')

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    server = HTTPServer(('0.0.0.0', 8025), EnhancedZENCoordinator)
    print('🚀 Enhanced ZEN Coordinator with Multi-Model Orchestration')
    print('📊 Features: MCP Integration + AI Provider Support')
    print('🎯 ZEN Tools:', list(ZEN_TOOLS.keys()))
    print('🤖 AI Providers:', list(AI_PROVIDERS.keys()))
    server.serve_forever()
