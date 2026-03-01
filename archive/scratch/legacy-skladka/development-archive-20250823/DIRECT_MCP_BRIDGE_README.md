# Direct MCP Bridge - New Architecture

## Problem Solved
ZEN Coordinator had routing issues with MCP protocol adaptation. Direct MCP Bridge bypasses this by connecting directly to MCP services.

## Architecture Change
```
OLD: Claude/Gemini → ZEN Coordinator → MCP Services (routing problems)
NEW: Claude/Gemini → Direct MCP Bridge → MCP Services (direct connection)
```

## Verified Working Tools
- ✅ terminal_exec - executes commands, returns JSON with stdout/stderr
- ✅ file_read - reads files with metadata (size, timestamp)  
- ✅ file_list - lists directories with details
- ✅ git_status - Git operations (API endpoint works)
- ✅ search_memories - works with David Strejc patterns
- ✅ 36 memories from Claude Master Archive accessible

## Usage
```bash
python direct_mcp_bridge.py call <tool> '{"args":"value"}'

# Examples:
python direct_mcp_bridge.py call file_read '{"path":"/etc/hosts"}'
python direct_mcp_bridge.py call terminal_exec '{"command":"ls /"}'
python direct_mcp_bridge.py call search_memories '{"query":"Claude","limit":3}'
```

## Security
- Communication only via LAN (192.168.0.58)
- No new external ports
- Same network isolation as ZEN Coordinator

## Result
Instead of problematic ZEN Coordinator proxy, we have direct, fast and verified access to MCP services.

## Testing Results
Tested with Claude-Gemini coordinated debugging. All core MCP tools verified functional.