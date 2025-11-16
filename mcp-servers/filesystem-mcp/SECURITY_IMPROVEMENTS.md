# Filesystem MCP Security Improvements

## Security Vulnerabilities Fixed

### 1. Path Traversal Prevention (CRITICAL)
**Before:**
```python
# No validation!
if not path.startswith("/"):
    path = "/" + path
# Direct file access allowed
```

**After:**
```python
def validate_path(path: str, operation: str = "read") -> str:
    # Resolve and normalize path
    abs_path = os.path.abspath(path)
    resolved_path = str(Path(abs_path).resolve())

    # Check against allowed directories
    # Check against blocked paths
    # Detect path traversal attempts
```

**Impact:** Prevents unauthorized file system access through:
- Path traversal (`../../../../etc/passwd`)
- Access to sensitive system files
- Directory breakout attempts

### 2. Directory Sandboxing
**Added:** Whitelist of allowed directories
```python
ALLOWED_DIRECTORIES = ["/tmp", "/data", "/workspace", "/home", "/var/log"]
```

**Impact:** Restricts file operations to safe directories only

### 3. Blocked Sensitive Paths
**Added:** Explicit blacklist for sensitive files
```python
BLOCKED_PATHS = [
    "/etc/passwd", "/etc/shadow", "/etc/sudoers",
    "/root/.ssh", "/home/*/.ssh/id_rsa",
    "/proc", "/sys"
]
```

**Impact:** Prevents access to critical system files

### 4. File Size Limits
**Added:** Maximum file size for reading (10MB)
```python
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
```

**Impact:** Prevents memory exhaustion from reading large files

### 5. Pagination for Large Directories
**Added:** Pagination support with limits
```python
MAX_FILES_PER_PAGE = 1000
```

**Impact:** Prevents performance issues with large directory listings

## Performance Improvements

### 1. Paginated Directory Listings
- Added `page` and `limit` query parameters
- Default: 100 files per page
- Maximum: 1000 files per page

### 2. File Size Pre-check
- Check file size before reading
- Return 413 error if file exceeds limit
- Configurable max_size parameter

## API Changes

### DirectoryResponse Model
**Added fields:**
- `page: int` - Current page number
- `has_more: bool` - Indicates if more files exist

### File Read Endpoint
**Added parameters:**
- `max_size: int` - Maximum bytes to read (default: 10MB)

**Added response fields:**
- `file_size: int` - Total file size
- `truncated: bool` - Indicates if content was truncated

## Testing

Run security tests:
```bash
cd mcp-servers/filesystem-mcp
pytest tests/test_main.py::TestSecurityVulnerabilities -v
```

## Configuration

To customize security settings, modify these constants in `main.py`:
- `MAX_FILE_SIZE` - Maximum file size for reading
- `MAX_FILES_PER_PAGE` - Maximum files per page
- `ALLOWED_DIRECTORIES` - List of allowed base directories
- `BLOCKED_PATHS` - List of explicitly blocked paths

## Usage Examples

### List directory with pagination
```bash
# First page (default 100 items)
GET /files/tmp

# Specific page with custom limit
GET /files/tmp?page=2&limit=50
```

### Read file with size limit
```bash
# Read with default limit (10MB)
GET /file/tmp/test.txt

# Read with custom limit (1MB)
GET /file/tmp/large.txt?max_size=1048576
```

## Breaking Changes

⚠️ **Warning:** This update includes breaking changes:

1. Access to directories outside `ALLOWED_DIRECTORIES` will be rejected with 403 error
2. Access to paths in `BLOCKED_PATHS` will be rejected with 403 error
3. Path traversal attempts (`..`) will be rejected
4. Files exceeding `MAX_FILE_SIZE` cannot be read
5. Directory listings are now paginated

To enable access to additional directories, add them to `ALLOWED_DIRECTORIES` list.
