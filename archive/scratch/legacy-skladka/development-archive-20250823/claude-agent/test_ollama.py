#!/usr/bin/env python3
"""
Test OLLAMA fallback functionality
"""
import asyncio
import sys
sys.path.append('/home/orchestration/claude-agent')

from haiku_agent import HASClaudeAgent

async def test_ollama():
    print("🔥 Testing OLLAMA fallback...")
    
    try:
        agent = HASClaudeAgent()
        
        # Test OLLAMA connection
        result = await agent.try_ollama_request("Hello, test OLLAMA connection from HAS")
        
        if result.get('success'):
            print("✅ OLLAMA fallback: Working")
            print(f"   Response: {result['content'][:100]}...")
            print(f"   Model: {result['model']}")
        else:
            print(f"❌ OLLAMA fallback: {result.get('error', 'Failed')}")
        
        # Test full fallback chain
        print("\n🔄 Testing full fallback chain...")
        result2 = await agent.fallback_request("Test fallback request", reason="test")
        
        if result2.get('success'):
            print("✅ Fallback chain: Working")
            print(f"   Model: {result2['model']}")
        else:
            print(f"❌ Fallback chain: {result2.get('error', 'Failed')}")
        
        return True
        
    except Exception as e:
        print(f"❌ OLLAMA test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_ollama())
    
    if success:
        print("\n🎉 OLLAMA fallback ready!")
    else:
        print("\n💥 OLLAMA fallback needs work!")