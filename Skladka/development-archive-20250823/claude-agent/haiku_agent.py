#!/usr/bin/env python3
"""
HAS Claude Agent - Haiku Model
Lightweight agent pro Home Automation Server s resource monitoring a fallback strategies
"""

import asyncio
import json
import logging
import os
import sys
import time
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import anthropic
import requests
import psutil
import aiohttp

class HASClaudeAgent:
    """Claude Agent optimalizovaný pro HAS environment s Haiku modelem"""
    
    def __init__(self, config_path: str = "/home/orchestration/claude-agent/config/agent_config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.setup_logging()
        
        # Anthropic client - OAuth mode (Pro subscription)
        try:
            self.anthropic_client = anthropic.Anthropic()  # OAuth will be handled automatically
        except Exception as e:
            self.logger.warning(f"Anthropic client init failed (OAuth): {e}")
            self.anthropic_client = None
        
        # Resource monitoring
        self.resource_limits = self.config['resource_limits']
        self.last_health_check = time.time()
        
        # MCP integration
        self.mcp_base_url = self.config['mcp']['base_url']
        self.mcp_tools = self.config['mcp']['tools']
        
        # Fallback configuration
        self.ollama_url = self.config['fallback']['ollama_url']
        self.workstation_url = self.config['fallback']['workstation_url']
        
        self.logger.info("HAS Claude Agent initialized with Haiku model")
    
    def load_config(self) -> Dict[str, Any]:
        """Load agent configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Default configuration
            return {
                'anthropic': {
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 4096
                },
                'resource_limits': {
                    'ram_warn_mb': 3200,      # 80% of 4GB
                    'ram_critical_mb': 3600,   # 90% of 4GB  
                    'cpu_warn_percent': 70,
                    'cpu_critical_percent': 85
                },
                'mcp': {
                    'base_url': 'http://localhost:8020',
                    'tools': [
                        'file_list', 'file_read', 'file_write', 'file_search',
                        'terminal_exec', 'shell_command', 'system_info',
                        'git_status', 'git_commit', 'git_push', 'git_log',
                        'store_memory', 'search_memories', 'memory_stats',
                        'research_query', 'web_search'
                    ]
                },
                'fallback': {
                    'ollama_url': 'http://192.168.0.41:5000',
                    'ollama_model': 'deepseek-coder:1.3b',
                    'workstation_url': 'http://192.168.0.10:8000'
                },
                'logging': {
                    'level': 'INFO',
                    'file': '/home/orchestration/claude-agent/logs/agent.log'
                }
            }
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', '/home/orchestration/claude-agent/logs/agent.log')
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('HASClaudeAgent')
    
    def check_resource_usage(self) -> Dict[str, Any]:
        """Monitor system resources and trigger fallbacks if needed"""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            ram_used_mb = memory.used / (1024 * 1024)
            ram_percent = memory.percent
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Load average
            load_avg = os.getloadavg()
            
            resource_status = {
                'ram_used_mb': ram_used_mb,
                'ram_percent': ram_percent,
                'cpu_percent': cpu_percent,
                'load_avg': load_avg[0],
                'timestamp': datetime.now().isoformat()
            }
            
            # Check thresholds
            resource_status['status'] = 'ok'
            resource_status['fallback_recommended'] = False
            
            if ram_used_mb > self.resource_limits['ram_critical_mb']:
                resource_status['status'] = 'critical'
                resource_status['fallback_recommended'] = True
                self.logger.warning(f"Critical RAM usage: {ram_used_mb:.1f}MB")
            elif ram_used_mb > self.resource_limits['ram_warn_mb']:
                resource_status['status'] = 'warning'
                self.logger.warning(f"High RAM usage: {ram_used_mb:.1f}MB")
            
            if cpu_percent > self.resource_limits['cpu_critical_percent']:
                resource_status['status'] = 'critical'
                resource_status['fallback_recommended'] = True
                self.logger.warning(f"Critical CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > self.resource_limits['cpu_warn_percent']:
                resource_status['status'] = 'warning'
                self.logger.warning(f"High CPU usage: {cpu_percent:.1f}%")
            
            return resource_status
            
        except Exception as e:
            self.logger.error(f"Resource monitoring error: {e}")
            return {'status': 'error', 'error': str(e)}
    
    async def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call MCP tool via direct local connection"""
        if arguments is None:
            arguments = {}
            
        try:
            # Use local direct_mcp_bridge.py
            import subprocess
            import tempfile
            
            # Prepare arguments
            args_json = json.dumps(arguments)
            
            # Call direct MCP bridge
            cmd = [
                'python3', 
                '/home/orchestration/direct_mcp_bridge.py',
                'call',
                tool_name,
                args_json
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                response = json.loads(result.stdout)
                self.logger.info(f"MCP tool {tool_name} executed successfully")
                return response
            else:
                error_msg = f"MCP tool {tool_name} failed: {result.stderr}"
                self.logger.error(error_msg)
                return {"success": False, "error": error_msg}
                
        except Exception as e:
            error_msg = f"MCP tool {tool_name} exception: {str(e)}"
            self.logger.error(error_msg)
            return {"success": False, "error": error_msg}
    
    async def claude_request(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Make request to Claude Haiku with resource awareness"""
        
        # Check local resources before making request
        resources = self.check_resource_usage()
        
        if resources.get('fallback_recommended'):
            self.logger.warning("Local resource limits exceeded, considering fallback")
            return await self.fallback_request(prompt, system_prompt, reason="local_resource_limits")
        
        # Check if Anthropic client is available (OAuth)
        if not self.anthropic_client:
            self.logger.warning("Anthropic client not available, using fallback")
            return await self.fallback_request(prompt, system_prompt, reason="oauth_unavailable")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": self.config['anthropic']['model'],
                "max_tokens": self.config['anthropic']['max_tokens'],
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            response = self.anthropic_client.messages.create(**kwargs)
            
            return {
                "success": True,
                "content": response.content[0].text,
                "usage": response.usage.dict() if hasattr(response.usage, 'dict') else None,
                "model": "haiku",
                "resources": resources
            }
            
        except Exception as e:
            error_msg = f"Claude Haiku request failed: {str(e)}"
            self.logger.error(error_msg)
            
            # Check if it's rate limit error
            if "rate_limit" in str(e).lower() or "429" in str(e) or "quota" in str(e).lower():
                self.logger.warning("Anthropic API rate limit exceeded - using OLLAMA fallback")
                return await self.fallback_request(prompt, system_prompt, reason="anthropic_rate_limit")
            else:
                # Other API errors
                return await self.fallback_request(prompt, system_prompt, reason="api_error")
    
    async def fallback_request(self, prompt: str, system_prompt: str = None, reason: str = "unknown") -> Dict[str, Any]:
        """Handle fallback - OLLAMA for Anthropic rate limits to complete work"""
        self.logger.info(f"Initiating fallback request, reason: {reason}")
        
        # For Anthropic rate limits - use OLLAMA to complete the work (even if slow)
        if reason == "anthropic_rate_limit":
            self.logger.warning("Anthropic API rate limit exceeded - using OLLAMA to complete work (may take long time)")
            try:
                ollama_response = await self.try_ollama_request(prompt, system_prompt)
                if ollama_response.get('success'):
                    self.logger.info("OLLAMA successfully completed work despite Anthropic rate limits")
                    return ollama_response
            except Exception as e:
                self.logger.error(f"OLLAMA fallback failed: {e}")
                # Still try to give some response
                return {
                    "success": True,
                    "content": f"Anthropic rate limit exceeded, OLLAMA fallback failed: {str(e)}. Task could not be completed.",
                    "model": "rate_limit_error",
                    "fallback_reason": reason
                }
        
        # For local resource limits - also use OLLAMA but with warning
        if reason == "local_resource_limits":
            self.logger.warning("Local resource limits exceeded - using OLLAMA")
            try:
                ollama_response = await self.try_ollama_request(prompt, system_prompt)
                if ollama_response.get('success'):
                    return ollama_response
            except Exception as e:
                self.logger.error(f"OLLAMA fallback failed: {e}")
        
        # For other issues (OAuth, API errors) - try workstation first
        try:
            workstation_response = await self.try_workstation_request(prompt, system_prompt)
            if workstation_response.get('success'):
                return workstation_response
        except Exception as e:
            self.logger.warning(f"Workstation fallback failed: {e}")
        
        # All fallbacks failed
        return {
            "success": False,
            "error": f"All fallback methods failed, reason: {reason}",
            "model": "fallback_failed"
        }
    
    async def try_ollama_request(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Try request to OLLAMA server"""
        try:
            # OLLAMA webserver API call - optimized for quick responses
            full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            full_prompt += "\n\nProsím krátkou a stručnou odpověď v 1-2 větách."
            
            payload = {
                "model": self.config['fallback'].get('ollama_model', 'deepseek-coder:1.3b'),
                "prompt": full_prompt,
                "max_tokens": 200  # Shorter responses for faster processing
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=300  # 5 minutes timeout - enough to complete work
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get('success'):
                            return {
                                "success": True,
                                "content": result.get('response', ''),
                                "model": f"ollama-{result.get('model', 'unknown')}",
                                "fallback_reason": "resource_limits"
                            }
                        else:
                            return {"success": False, "error": f"OLLAMA API error: {result.get('error', 'Unknown')}"}
                    else:
                        return {"success": False, "error": f"OLLAMA HTTP {response.status}"}
                        
        except Exception as e:
            return {"success": False, "error": f"OLLAMA error: {str(e)}"}
    
    async def try_workstation_request(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """Try request to workstation (emergency fallback)"""
        # TODO: Implement workstation delegation via SSH or API
        return {"success": False, "error": "Workstation fallback not implemented yet"}
    
    async def process_user_input(self, user_input: str) -> str:
        """Process user input and return response"""
        try:
            # System prompt for HAS agent
            system_prompt = """You are a Claude agent running on a Home Automation Server (HAS) with limited resources. 
            You have access to MCP tools for filesystem, git, memory, terminal operations.
            You should be concise and efficient in your responses.
            Monitor resource usage and prefer lightweight operations."""
            
            # Get Claude response
            response = await self.claude_request(user_input, system_prompt)
            
            if response.get('success'):
                return response['content']
            else:
                return f"Error: {response.get('error', 'Unknown error occurred')}"
                
        except Exception as e:
            self.logger.error(f"Processing error: {e}")
            return f"Processing error: {str(e)}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "agent_status": "running",
            "resources": self.check_resource_usage()
        }
        
        # Test MCP connectivity
        try:
            mcp_test = await self.call_mcp_tool("search_memories", {"query": "test", "limit": 1})
            health_status["mcp_connectivity"] = "ok" if mcp_test.get('success') else "error"
        except:
            health_status["mcp_connectivity"] = "error"
        
        # Test Claude API
        try:
            test_response = await self.claude_request("test")
            health_status["claude_api"] = "ok" if test_response.get('success') else "error"
        except:
            health_status["claude_api"] = "error"
        
        return health_status
    
    async def run_interactive(self):
        """Run interactive mode"""
        print("HAS Claude Agent - Interactive Mode")
        print("Type 'quit' to exit, 'health' for health check")
        print("-" * 50)
        
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print("Shutting down HAS Claude Agent...")
                    break
                elif user_input.lower() == 'health':
                    health = await self.health_check()
                    print(json.dumps(health, indent=2))
                elif user_input.lower().startswith('mcp '):
                    # Direct MCP tool call: mcp tool_name {"args": "value"}
                    parts = user_input[4:].split(' ', 1)
                    tool_name = parts[0]
                    args = json.loads(parts[1]) if len(parts) > 1 else {}
                    result = await self.call_mcp_tool(tool_name, args)
                    print(json.dumps(result, indent=2))
                elif user_input:
                    response = await self.process_user_input(user_input)
                    print(f"\nResponse: {response}")
                    
            except KeyboardInterrupt:
                print("\nShutting down HAS Claude Agent...")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main entry point"""
    agent = HASClaudeAgent()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'health':
            # Health check mode
            loop = asyncio.get_event_loop()
            health = loop.run_until_complete(agent.health_check())
            print(json.dumps(health, indent=2))
        elif sys.argv[1] == 'test':
            # Test mode
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(agent.process_user_input("Hello, test the HAS agent"))
            print(response)
    else:
        # Interactive mode
        loop = asyncio.get_event_loop()
        loop.run_until_complete(agent.run_interactive())

if __name__ == "__main__":
    main()