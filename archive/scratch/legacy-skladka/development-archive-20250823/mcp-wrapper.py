#!/usr/bin/env python3
"""
MCP Server Wrapper for ZEN Coordinator
Provides MCP protocol interface to ZEN Coordinator HTTP API
"""

import json
import sys
import asyncio
import aiohttp
from contextlib import asynccontextmanager

class ZenMCPWrapper:
    def __init__(self, zen_url="http://localhost:8020"):
        self.zen_url = zen_url
        
    async def handle_mcp_request(self, request):
        """Handle MCP request and forward to ZEN Coordinator"""
        try:
            if request.get("method") == "tools/list":
                # Get actual tools from ZEN Coordinator
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.zen_url}/tools/list") as response:
                        if response.status == 200:
                            tools_data = await response.json()
                            # ZEN returns nested structure: {"result": {"tools": [...]}}
                            tools = tools_data.get("result", {}).get("tools", [])
                            # Simplify tool format for MCP protocol
                            simple_tools = []
                            for tool in tools:
                                simple_tools.append({
                                    "name": tool["name"],
                                    "description": tool["description"]
                                })
                            return {"tools": simple_tools}
                
                # Fallback to static list
                return {
                    "tools": [
                        {"name": "terminal_exec", "description": "Execute terminal command"},
                        {"name": "shell_command", "description": "Execute shell command"},
                        {"name": "system_info", "description": "Get system information"},
                        {"name": "file_read", "description": "Read file contents"}, 
                        {"name": "file_write", "description": "Write file contents"},
                        {"name": "file_list", "description": "List directory contents"},
                        {"name": "file_search", "description": "Search files"},
                        {"name": "file_analyze", "description": "Analyze files"},
                        {"name": "git_status", "description": "Get git repository status"},
                        {"name": "git_log", "description": "Get git commit history"},
                        {"name": "git_diff", "description": "Get git diff"},
                        {"name": "store_memory", "description": "Store memory/context"},
                        {"name": "search_memories", "description": "Search stored memories"},
                        {"name": "list_memories", "description": "List stored memories"},
                        {"name": "memory_stats", "description": "Get memory statistics"},
                        {"name": "transcribe_webm", "description": "Transcribe WebM audio"},
                        {"name": "transcribe_url", "description": "Transcribe audio from URL"},
                        {"name": "research_query", "description": "Perform research query"},
                        {"name": "perplexity_search", "description": "Search using Perplexity"},
                        {"name": "db_query", "description": "Execute database query"},
                        {"name": "db_schema", "description": "Get database schema"}
                    ]
                }
            
            elif request.get("method") == "tools/call":
                # Forward tool call to ZEN Coordinator
                tool_name = request["params"]["name"]
                arguments = request["params"].get("arguments", {})
                
                zen_request = {
                    "tool": tool_name,
                    "arguments": arguments
                }
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.zen_url}/mcp",
                        json=zen_request,
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result, indent=2)
                                    }
                                ]
                            }
                        else:
                            error_text = await response.text()
                            return {
                                "content": [
                                    {
                                        "type": "text", 
                                        "text": f"Error: {response.status} - {error_text}"
                                    }
                                ]
                            }
                            
            elif request.get("method") == "initialize":
                return {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "zen-orchestration",
                        "version": "1.0.0"
                    }
                }
                
            else:
                return {"error": f"Unknown method: {request.get('method')}"}
                
        except Exception as e:
            return {"error": str(e)}

async def main():
    """Main MCP server loop"""
    wrapper = ZenMCPWrapper()
    
    # Read from stdin, write to stdout (MCP protocol)
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
                
            request = json.loads(line.strip())
            response = await wrapper.handle_mcp_request(request)
            
            # Send response
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {"error": str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == "__main__":
    asyncio.run(main())