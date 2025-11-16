# Database MCP Security Improvements

## CRITICAL Security Vulnerabilities Fixed

### 1. SQL Injection in Table Names (CRITICAL)
**Before:**
```python
cursor.execute(f"PRAGMA table_info({table_name});")  # VULNERABLE!
cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit};")  # VULNERABLE!
```

**After:**
```python
validated_table = validate_table_name(table_name)  # Regex validation
cursor.execute(f"PRAGMA table_info({validated_table});")  # SAFE
cursor.execute(f"SELECT * FROM {validated_table} LIMIT ?;", (limit,))  # SAFE
```

**Impact:** Prevented SQL injection attacks like:
- `table_name = "users); DROP TABLE users; --"`
- `table_name = "users UNION SELECT * FROM passwords"`

### 2. Unrestricted Query Execution (CRITICAL)
**Before:**
```python
# ANY SQL query could be executed!
cursor.execute(query, params)
```

**After:**
```python
def validate_query(query: str):
    # Block dangerous operations
    DANGEROUS_OPERATIONS = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE"}
    # Allow only SELECT and PRAGMA
    ALLOWED_OPERATIONS = {"SELECT", "PRAGMA"}
```

**Impact:** Blocked dangerous operations:
- `DROP TABLE users`
- `DELETE FROM users`
- `UPDATE users SET password = 'hacked'`

### 3. Connection Management
**Before:**
```python
conn = get_db_connection()
# ... operations ...
conn.close()  # Might not close on error!
```

**After:**
```python
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DATABASE_FILE, timeout=10.0)
    try:
        yield conn
    finally:
        conn.close()  # Always closes!

# Usage
with get_db_connection() as conn:
    # operations
```

**Impact:** Ensures connections are always properly closed

### 4. Result Set Limits
**Added:** Maximum rows to prevent memory exhaustion
```python
MAX_QUERY_RESULTS = 10000
MAX_SAMPLE_LIMIT = 1000
```

**Impact:** Prevents DoS attacks through huge result sets

## Additional Security Measures

### Table Name Validation
```python
def validate_table_name(table_name: str) -> str:
    # Only alphanumeric and underscores
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise HTTPException(400, "Invalid table name")

    # Block SQLite system tables
    if table_name.startswith('sqlite_'):
        raise HTTPException(403, "System table access forbidden")
```

### Query Validation
- Whitelist of allowed operations (SELECT, PRAGMA)
- Blacklist of dangerous operations (DROP, DELETE, etc.)
- Query must start with allowed operation

## Performance Improvements

### 1. Connection Pooling (via Context Manager)
- Guaranteed connection cleanup
- Timeout configuration (10 seconds)

### 2. Result Pagination
- Maximum rows configurable per query
- Truncation indication in response

### 3. Database Timeout
- 10-second connection timeout
- Prevents hanging connections

## API Changes

### Health Endpoint
**Added:**
```bash
GET /health
```
Returns database status and connectivity

### QueryResult Model
**Added fields:**
- `row_count: int` - Total rows returned
- `truncated: bool` - Indicates if results were truncated

### Execute Query Endpoint
**Added parameters:**
- `max_rows: int` - Maximum rows to return (default: 1000, max: 10000)

**Restrictions:**
- Only SELECT and PRAGMA queries allowed
- All dangerous operations blocked

### Sample Data Endpoint
**Added parameter:**
- `limit: int` - Rows to return (default: 10, max: 1000)

## Testing

Run security tests:
```bash
cd mcp-servers/database-mcp
pytest tests/test_main.py::TestSecurityVulnerabilities -v
```

## Configuration

To customize security settings, modify these constants in `main.py`:
- `MAX_QUERY_RESULTS` - Maximum rows per query
- `DEFAULT_SAMPLE_LIMIT` - Default sample size
- `MAX_SAMPLE_LIMIT` - Maximum sample size
- `ALLOWED_OPERATIONS` - Set of allowed SQL keywords
- `DANGEROUS_OPERATIONS` - Set of blocked SQL keywords

## Usage Examples

### Execute safe SELECT query
```bash
POST /db/execute?query=SELECT * FROM users WHERE id = ?&params=[1]&max_rows=100
```

### Get table schema
```bash
GET /db/schema/users
```

### Get sample data
```bash
GET /db/sample/users?limit=50
```

## Breaking Changes

⚠️ **Warning:** This update includes breaking changes:

1. **Only SELECT and PRAGMA queries allowed** - All modification queries (INSERT, UPDATE, DELETE, DROP, etc.) are blocked
2. **Table names must be valid identifiers** - Only alphanumeric characters and underscores
3. **System tables blocked** - Cannot access tables starting with `sqlite_`
4. **Result limits enforced** - Maximum 10,000 rows per query, 1,000 per sample
5. **Queries must be parameterized** - Use `?` placeholders for values

## Migration Guide

If you need write operations:
1. Create a separate endpoint with proper authentication
2. Implement role-based access control
3. Use transaction management
4. Add audit logging

Example secure write endpoint:
```python
@app.post("/db/insert")
async def insert_data(table: str, data: Dict, auth: str = Header(...)):
    # 1. Authenticate user
    # 2. Validate permissions
    # 3. Validate table name
    # 4. Use parameterized query
    # 5. Log operation
    pass
```

## Security Recommendations

1. **Add Authentication** - Implement API keys or JWT tokens
2. **Add Authorization** - Role-based access control
3. **Add Audit Logging** - Log all database operations
4. **Use Read Replicas** - For read-only operations
5. **Implement Rate Limiting** - Prevent abuse
6. **Regular Backups** - Automated backup strategy
