# Terminal MCP Security Improvements

## Security Vulnerabilities Fixed

### 1. Command Injection Prevention (CRITICAL)
**Before:**
```python
subprocess.run(request.command, shell=True, ...)  # VULNERABLE!
```

**After:**
```python
cmd_parts = shlex.split(request.command)
subprocess.run(cmd_parts, shell=False, ...)  # SECURE
```

**Impact:** Prevents arbitrary command execution through shell metacharacters (`;`, `&&`, `|`, etc.)

### 2. Command Whitelist
**Added:** Whitelist of allowed commands
```python
ALLOWED_COMMANDS = {
    "ls", "echo", "cat", "pwd", "whoami", "date", "ps", "df", "du",
    "grep", "find", "wc", "head", "tail", "sort", "uniq", "cut",
    "python3", "node", "npm", "git", "docker", "curl", "wget"
}
```

**Impact:** Only pre-approved commands can be executed

### 3. Directory Access Control
**Added:** Sandbox for working directories
```python
ALLOWED_WORKING_DIRS = ["/tmp", "/data", "/workspace", "/home"]
```

**Impact:** Prevents path traversal attacks and access to sensitive directories like `/etc`, `/root`

### 4. Output Size Limits
**Added:** Maximum output size (10MB)
```python
MAX_OUTPUT_SIZE = 10 * 1024 * 1024
```

**Impact:** Prevents memory exhaustion from commands with large output

### 5. Timeout Limits
**Added:** Maximum timeout (5 minutes)
```python
MAX_TIMEOUT = 300  # 5 minutes
```

**Impact:** Prevents long-running commands from consuming resources

## API Changes

### CommandRequest Model
**Added fields:**
- `args: Optional[List[str]]` - Additional command arguments

### CommandResponse Model
**Added fields:**
- `truncated: bool` - Indicates if output was truncated

## Testing

Run security tests:
```bash
cd mcp-servers/terminal-mcp
pytest tests/test_main.py::TestSecurityVulnerabilities -v
```

## Configuration

To customize security settings, modify these constants in `main.py`:
- `MAX_OUTPUT_SIZE` - Maximum output size in bytes
- `MAX_TIMEOUT` - Maximum command timeout in seconds
- `ALLOWED_WORKING_DIRS` - List of allowed working directories
- `ALLOWED_COMMANDS` - Set of allowed commands

## Breaking Changes

⚠️ **Warning:** This update includes breaking changes:

1. Commands not in the whitelist will be rejected with 403 error
2. Access to directories outside `ALLOWED_WORKING_DIRS` will be rejected
3. Timeouts exceeding `MAX_TIMEOUT` will be rejected
4. Shell features (pipes, redirects, command chaining) no longer work

To enable additional commands, add them to `ALLOWED_COMMANDS` set.
