# Git MCP Security Improvements

## Security Enhancements

### 1. Repository Path Validation
**Added:** Comprehensive path validation
```python
def validate_repository_path(path: str) -> str:
    # Normalize and resolve path
    # Check against allowed locations
    # Detect path traversal
    # Verify git repository exists
```

**Impact:** Prevents unauthorized repository access:
- Path traversal attempts blocked
- Access restricted to whitelisted locations
- Verifies `.git` directory exists

### 2. Repository Sandboxing
**Added:** Whitelist of allowed repository locations
```python
ALLOWED_REPOSITORIES = ["/data", "/workspace", "/tmp", "/home"]
```

**Impact:** Restricts git operations to approved directories only

### 3. Command Timeouts
**Added:** Timeout for all git operations
```python
GIT_TIMEOUT = 30  # seconds
```

**Impact:** Prevents hanging git operations from consuming resources

### 4. Resource Limits
**Added:** Limits for output size and log entries
```python
MAX_LOG_ENTRIES = 1000  # Maximum commits to fetch
MAX_DIFF_SIZE = 10 * 1024 * 1024  # 10MB maximum diff size
```

**Impact:** Prevents memory exhaustion from large git operations

## Positive Aspects (Already Secure)

### ✅ Safe Subprocess Usage
The code already used safe subprocess practices:
```python
# Good: Uses list of arguments, not shell=True
subprocess.run(["git", "-C", path, "status", "--porcelain"], ...)
```

### ✅ Proper Command Construction
Uses `-C` flag instead of changing directories, which is safer

## Performance Improvements

### 1. Enforced Limits
- Maximum log entries: 1000
- Maximum diff size: 10MB
- Command timeout: 30 seconds

### 2. Diff Truncation
Large diffs are automatically truncated with indication

### 3. Health Check
Git availability verified through health endpoint

## API Changes

### All Models Enhanced
**Added fields:**
- `repository: str` - Shows validated repository path

### GitLog Model
**Added fields:**
- `count: int` - Number of log entries returned

### GitDiff Model
**Added fields:**
- `truncated: bool` - Indicates if diff was truncated

### Log Endpoint
**Added parameter:**
- `limit: int` - Number of commits (default: 5, max: 1000)

### Health Endpoint
**Added:**
```bash
GET /health
```
Returns git version and availability status

## Testing

Run tests:
```bash
cd mcp-servers/git-mcp
pytest tests/test_main.py -v
```

## Configuration

To customize security settings, modify these constants in `main.py`:
- `GIT_TIMEOUT` - Command timeout in seconds
- `MAX_LOG_ENTRIES` - Maximum commits to fetch
- `MAX_DIFF_SIZE` - Maximum diff output size
- `ALLOWED_REPOSITORIES` - List of allowed repository locations

## Usage Examples

### Check repository status
```bash
GET /git/data/my-repo/status
```

### Get commit log
```bash
# Default 5 commits
GET /git/data/my-repo/log

# Custom limit
GET /git/data/my-repo/log?limit=20
```

### Get diff
```bash
GET /git/data/my-repo/diff
```

## Breaking Changes

⚠️ **Warning:** This update includes breaking changes:

1. **Repository path validation** - Only repositories in allowed locations can be accessed
2. **Git repository verification** - Path must contain `.git` directory
3. **Path traversal blocked** - Paths containing `..` are rejected
4. **Response format changed** - Added `repository` field to all responses
5. **GitLog limit enforced** - Maximum 1000 commits
6. **GitDiff may truncate** - Large diffs truncated at 10MB

## Migration Guide

### Update allowed repositories
Add your repository locations to `ALLOWED_REPOSITORIES`:
```python
ALLOWED_REPOSITORIES = ["/data", "/workspace", "/your/custom/path"]
```

### Handle new response fields
Update API clients to handle new fields:
```python
# Old
{"status": "M file.txt"}

# New
{"status": "M file.txt", "repository": "/data/my-repo"}
```

### Handle truncation
Check `truncated` field in diff responses:
```python
response = get_diff()
if response["truncated"]:
    print("Warning: Diff was truncated")
```

## Security Recommendations

1. **Add Authentication** - Implement API keys or JWT tokens
2. **Add Authorization** - Per-repository access control
3. **Add Audit Logging** - Log all git operations
4. **Limit Repository List** - Only expose necessary repositories
5. **Use Read-Only Access** - Mount repositories read-only where possible
