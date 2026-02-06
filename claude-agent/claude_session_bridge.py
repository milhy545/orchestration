#!/usr/bin/env python3
"""
Bridge pro použití Claude Code session credentials s HAS agentem
"""
import os
import sys
import json
import asyncio
from pathlib import Path

# Add claude-agent to path
sys.path.append('/home/orchestration/claude-agent')

def find_claude_credentials():
    """Najdi Claude credentials na systému"""
    
    # Check environment variables first
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        return {'api_key': api_key}

    # Check OS keyring if available
    try:
        import keyring  # type: ignore

        keyring_key = keyring.get_password("anthropic", "api_key")
        if keyring_key:
            return {'api_key': keyring_key}
    except Exception:
        pass
    
    # Check various config locations
    possible_paths = [
        Path.home() / '.anthropic' / 'config.json',
        Path.home() / '.claude' / 'config.json',
        Path('/root/.anthropic/config.json'),
        Path('/root/.claude/config.json')
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path) as f:
                    config = json.load(f)
                    if 'api_key' in config:
                        return config
            except:
                continue
    
    return None

async def run_has_agent_with_auth():
    """Spusť HAS agent s dostupnými credentials"""
    
    # Try to find credentials
    creds = find_claude_credentials()
    
    if creds and 'api_key' in creds:
        # Set environment variable for this session (avoid logging secrets)
        os.environ['ANTHROPIC_API_KEY'] = creds['api_key']
        masked = f"{creds['api_key'][:4]}...{creds['api_key'][-4:]}" if len(creds['api_key']) >= 8 else "***"
        print(f"✅ Using API key: {masked}")
    else:
        print("⚠️ No API key found, testing fallback mode")
    
    # Import and run agent
    from haiku_agent import HASClaudeAgent
    
    agent = HASClaudeAgent()
    
    # Test resource monitoring
    resources = agent.check_resource_usage()
    print(f"📊 Resources: RAM {resources['ram_used_mb']:.1f}MB ({resources['ram_percent']:.1f}%), CPU {resources['cpu_percent']:.1f}%")
    
    # Test MCP tools
    print("🔧 Testing MCP tools...")
    mcp_result = await agent.call_mcp_tool("search_memories", {"query": "test", "limit": 1})
    if mcp_result.get('success'):
        print("✅ MCP tools working")
    else:
        print(f"❌ MCP tools failed: {mcp_result.get('error')}")
    
    # Test Claude API (will use fallback if no auth)
    print("🤖 Testing Claude API...")
    try:
        response = await agent.claude_request("Hello from HAS agent test")
        if response.get('success'):
            print(f"✅ Claude API working with {response.get('model', 'unknown')} model")
            print(f"   Response: {response['content'][:80]}...")
        else:
            print(f"⚠️ Claude API fallback: {response.get('model', 'unknown')}")
            if response.get('content'):
                print(f"   Response: {response['content'][:80]}...")
    except Exception as e:
        print(f"❌ Claude API error: {e}")
    
    # Health check
    print("🩺 Health check...")
    health = await agent.health_check()
    print(f"   Agent: {health['agent_status']}")
    print(f"   Resources: {health['resources']['status']}")
    print(f"   MCP: {health.get('mcp_connectivity', 'unknown')}")
    print(f"   Claude API: {health.get('claude_api', 'unknown')}")

if __name__ == "__main__":
    print("🔗 HAS Claude Agent with Session Bridge")
    print("=" * 50)
    asyncio.run(run_has_agent_with_auth())
