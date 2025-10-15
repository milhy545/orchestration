#!/usr/bin/env python3
"""
Test rychlé fallback strategie
"""
import asyncio
import sys
sys.path.append('/home/orchestration/claude-agent')

from haiku_agent import HASClaudeAgent

async def test_fast_fallback():
    print("⚡ Testing fast fallback strategies...")
    
    try:
        agent = HASClaudeAgent()
        
        # Test resource limits fallback (should be instant)
        print("\n1. Testing resource limits fallback...")
        start_time = asyncio.get_event_loop().time()
        result1 = await agent.fallback_request("Test message", reason="resource_limits")
        end_time = asyncio.get_event_loop().time()
        
        print(f"✅ Resource fallback: {result1['model']} ({end_time - start_time:.2f}s)")
        print(f"   Response: {result1['content'][:80]}...")
        
        # Test OAuth fallback (should try workstation, then timeout OLLAMA)
        print("\n2. Testing OAuth fallback...")
        start_time = asyncio.get_event_loop().time()
        result2 = await agent.fallback_request("Test OAuth fallback", reason="oauth_unavailable")
        end_time = asyncio.get_event_loop().time()
        
        print(f"✅ OAuth fallback: {result2['model']} ({end_time - start_time:.2f}s)")
        print(f"   Response: {result2['content'][:80]}...")
        
        # Test resource monitoring
        print("\n3. Testing resource monitoring...")
        resources = agent.check_resource_usage()
        print(f"✅ Resources: RAM {resources['ram_used_mb']:.1f}MB, CPU {resources['cpu_percent']:.1f}%")
        print(f"   Status: {resources['status']}, Fallback: {resources.get('fallback_recommended', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fast fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_fast_fallback())
    
    if success:
        print("\n⚡ Fast fallback strategies ready!")
    else:
        print("\n💥 Fast fallback needs work!")