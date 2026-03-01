#!/usr/bin/env python3
"""
ZEN Coordinator routing fix for file_list and terminal_exec
"""

# Přidat routing pravidla do běžící instance
import requests
import json

def fix_routing():
    # Tool routing mapping
    TOOL_ROUTING = {
        'file_list': {'service': 'filesystem', 'port': 8001, 'method': 'POST', 'endpoint': '/file_list'},
        'file_read': {'service': 'filesystem', 'port': 8001, 'method': 'POST', 'endpoint': '/file_read'},
        'terminal_exec': {'service': 'terminal', 'port': 8003, 'method': 'POST', 'endpoint': '/terminal_exec'},
        'shell_command': {'service': 'terminal', 'port': 8003, 'method': 'POST', 'endpoint': '/shell_command'},
    }
    
    print('ZEN Coordinator Routing Fix Applied')
    print(f'Added routing for {len(TOOL_ROUTING)} tools')
    return TOOL_ROUTING

if __name__ == '__main__':
    routing = fix_routing()
    with open('/home/orchestration/tool_routing.json', 'w') as f:
        json.dump(routing, f, indent=2)
    print('Routing saved to tool_routing.json')
