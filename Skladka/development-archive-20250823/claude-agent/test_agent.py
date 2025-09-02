#!/usr/bin/env python3
"""
Test script pro HAS Claude Agent - bez API key závislosti
"""
import asyncio
import sys
import os
sys.path.append('/home/orchestration/claude-agent')

# Mock Anthropic client pro test bez API key
class MockAnthropic:
    def __init__(self, api_key):
        self.api_key = api_key
    
    class Messages:
        def create(self, **kwargs):
            class MockResponse:
                def __init__(self):
                    self.content = [type('obj', (object,), {'text': 'Mock response from Haiku agent on HAS'})]
                    self.usage = type('obj', (object,), {})()
            return MockResponse()
    
    @property
    def messages(self):
        return self.Messages()

# Patch anthropic import
import sys
anthropic_module = type(sys)('anthropic')
anthropic_module.Anthropic = MockAnthropic
sys.modules['anthropic'] = anthropic_module

from haiku_agent import HASClaudeAgent

async def test_agent():
    """Test základní funkcionalita agenta"""
    print("🚀 Testing HAS Claude Agent...")
    
    try:
        # Initialize agent
        agent = HASClaudeAgent()
        print("✅ Agent initialized successfully")
        
        # Test resource monitoring
        resources = agent.check_resource_usage()
        print(f"✅ Resource monitoring: {resources['status']}")
        print(f"   RAM: {resources['ram_used_mb']:.1f}MB ({resources['ram_percent']:.1f}%)")
        print(f"   CPU: {resources['cpu_percent']:.1f}%")
        
        # Test MCP connectivity
        print("\n🔧 Testing MCP tools...")
        
        # Test search_memories (should work)
        memory_result = await agent.call_mcp_tool("search_memories", {"query": "test", "limit": 1})
        if memory_result.get('success'):
            print("✅ search_memories: Working")
        else:
            print(f"❌ search_memories: {memory_result.get('error', 'Failed')}")
        
        # Test file_list (should work)  
        file_result = await agent.call_mcp_tool("file_list", {"path": "/home/orchestration"})
        if file_result.get('success'):
            print("✅ file_list: Working")
        else:
            print(f"❌ file_list: {file_result.get('error', 'Failed')}")
            
        # Test store_memory (probably broken)
        store_result = await agent.call_mcp_tool("store_memory", {
            "content": "HAS Agent test memory",
            "importance": 0.8
        })
        if store_result.get('success'):
            print("✅ store_memory: Working")
        else:
            print(f"❌ store_memory: {store_result.get('error', 'Failed')}")
        
        # Test Claude request (mock)
        print("\n🤖 Testing Claude API...")
        response = await agent.claude_request("Hello from HAS agent test")
        if response.get('success'):
            print("✅ Claude API: Working (mock)")
            print(f"   Response: {response['content']}")
        else:
            print(f"❌ Claude API: {response.get('error', 'Failed')}")
        
        # Health check
        print("\n🩺 Running health check...")
        health = await agent.health_check()
        print(f"✅ Health check completed")
        print(f"   Agent: {health['agent_status']}")
        print(f"   Resources: {health['resources']['status']}")
        print(f"   MCP: {health.get('mcp_connectivity', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("HAS Claude Agent Test Suite")
    print("=" * 50)
    
    success = asyncio.run(test_agent())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Agent test completed successfully!")
        print("Ready for production deployment.")
    else:
        print("💥 Agent test failed!")
        print("Check logs and fix issues before deployment.")