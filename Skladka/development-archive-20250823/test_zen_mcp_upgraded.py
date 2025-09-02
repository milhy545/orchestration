#!/usr/bin/env python3
import json
import sys
import subprocess

def test_zen_mcp():
    # Prepare test inputs
    discovery_test = json.dumps({method: tools/list, id: test_discovery, params: {}})
    single_tool_test = json.dumps({
        'method': 'tools/call', 
        'id': 'test_single_tool', 
        'params': {
            'name': 'system_info', 
            'arguments': {}
        }
    })
    
    # Function to run MCP command
    def run_mcp_command(input_json):
        cmd = [
            'python3', '/home/orchestration/zen_mcp_server_updated.py'
        ]
        
        try:
            result = subprocess.run(
                cmd, 
                input=input_json + '\n', 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.stdout, result.stderr
        except Exception as e:
            return None, str(e)
    
    # Tool Discovery Test
    stdout, stderr = run_mcp_command(discovery_test)
    print('Tool Discovery Test Raw Output:')
    print(stdout)
    print('Errors:', stderr)
    
    # Single Tool Call Test
    stdout, stderr = run_mcp_command(single_tool_test)
    print('\nSingle Tool Call Test Raw Output:')
    print(stdout)
    print('Errors:', stderr)

def main():
    test_zen_mcp()

if __name__ == '__main__':
    main()
