# Config MCP Security Audit

**Date:** 2025-11-17
**Auditor:** Claude
**Service:** Config MCP (Port 7009)

## Executive Summary

Discovered **1 CRITICAL** vulnerability, **2 MEDIUM** risks, and **1 LOW** risk.

**Overall Risk:** CRITICAL
**Immediate Action Required:** Fix path traversal vulnerability

---

## CRITICAL Vulnerabilities

###  1. Path Traversal - Inverted Logic (CVSS 9.8)

**Location:** `main.py:166-171` (config_file_tool function)

**Vulnerability:**
```python
# CURRENT CODE (WRONG!):
file_path = file_path.resolve()
CONFIG_BASE_PATH.resolve().relative_to(file_path)  # ❌ INVERTED!
```

**Issue:** The path validation logic is inverted. It checks if `CONFIG_BASE_PATH` is relative to `file_path` instead of the opposite. This allows attackers to access ANY file on the system using path traversal.

**Attack Vector:**
```bash
POST /tools/config_file
{
  "operation": "read",
  "file_path": "../../../../etc/passwd",
  "format": "env"
}
```

This bypasses the security check and allows reading `/etc/passwd`, database credentials, SSH keys, etc.

**Impact:**
- ✅ **Confidentiality:** HIGH - Read any file on server
- ✅ **Integrity:** HIGH - Write/delete any file
- ✅ **Availability:** HIGH - Delete critical system files

**CVSS 3.1:** 9.8 (CRITICAL)
- Vector: CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
- Network accessible, low complexity, no privileges required

**Recommended Fix:**
```python
# CORRECT CODE:
try:
    file_path = file_path.resolve()
    file_path.relative_to(CONFIG_BASE_PATH.resolve())  # ✅ CORRECT
except ValueError:
    raise HTTPException(status_code=403, detail="Path outside allowed directory")
```

**References:**
- OWASP Top 10 2021: A01:2021 - Broken Access Control
- CWE-22: Improper Limitation of a Pathname to a Restricted Directory

---

## MEDIUM Severity Issues

### 2. Unrestricted Environment Variable Access (CVSS 6.5)

**Location:** `main.py:82-153` (env_vars_tool function)

**Issue:** No validation or filtering on environment variable names. Allows:
- Reading sensitive variables (DATABASE_URL, API_KEYS, AWS_SECRET_ACCESS_KEY)
- Modifying critical variables (PATH, LD_PRELOAD, PYTHONPATH)
- Environment variable injection attacks

**Attack Vector:**
```bash
POST /tools/env_vars
{
  "operation": "get",
  "key": "DATABASE_URL"  # Steal database credentials
}

POST /tools/env_vars
{
  "operation": "set",
  "key": "LD_PRELOAD",
  "value": "/tmp/malicious.so"  # Code injection via shared library
}
```

**Impact:**
- Read sensitive credentials
- Modify application behavior
- Privilege escalation

**Recommended Fix:**
- Implement allow-list for readable variables
- Block critical variables (PATH, LD_*, PYTHON*)
- Add authentication/authorization

### 3. Backup Directory Exhaustion (CVSS 5.3)

**Location:** `main.py:405-518` (backup_tool function)

**Issue:** No limits on:
- Number of backups
- Backup size
- Frequency

**Attack Vector:**
```bash
# Create 10000 backups to fill disk
for i in {1..10000}; do
  curl -X POST /tools/backup -d '{"operation":"create","backup_name":"backup_$i"}'
done
```

**Impact:**
- Disk space exhaustion
- Denial of service
- Log file flooding

**Recommended Fix:**
- Max backups limit (e.g., 50)
- Total backup size limit
- Rate limiting on backup creation

---

## LOW Severity Issues

### 4. ENV File Injection (CVSS 3.7)

**Location:** `main.py:228-229`

**Issue:** No escaping of values when writing `.env` files:
```python
content = '\n'.join([f"{k}={v}" for k, v in request.content.items()])
```

**Attack Vector:**
```bash
POST /tools/config_file
{
  "operation": "write",
  "file_path": "app.env",
  "format": "env",
  "content": {
    "SAFE_VAR": "value",
    "MALICIOUS": "value1\nINJECTED_VAR=hacked"
  }
}
```

Creates:
```
SAFE_VAR=value
MALICIOUS=value1
INJECTED_VAR=hacked
```

**Recommended Fix:**
```python
# Escape newlines in values
content = '\n'.join([f"{k}={v.replace(chr(10), '\\n')}" for k, v in request.content.items()])
```

---

## Positive Security Controls

✅ **Safe YAML parsing** - Uses `yaml.safe_load()` instead of `yaml.load()`
✅ **Type validation** - Pydantic models for request validation
✅ **Error handling** - Try-except blocks with proper logging
✅ **No SQL injection** - No database operations

---

## Summary Statistics

| Severity | Count | Fixed |
|----------|-------|-------|
| CRITICAL | 1     | ❌    |
| HIGH     | 0     | -     |
| MEDIUM   | 2     | ❌    |
| LOW      | 1     | ❌    |
| **Total**| **4** | **0** |

---

## Recommended Actions (Priority Order)

1. **IMMEDIATE:** Fix path traversal vulnerability (inverted logic)
2. **HIGH:** Add authentication to all endpoints
3. **HIGH:** Implement env var whitelist/blacklist
4. **MEDIUM:** Add backup size/count limits
5. **MEDIUM:** Add rate limiting
6. **LOW:** Fix ENV file value escaping

---

## Testing Recommendations

Create security tests for:
- Path traversal attempts (`../../etc/passwd`)
- Sensitive env var access (DATABASE_URL, API_KEYS)
- Backup creation DoS
- ENV file injection

See attached `test_config_security.py` for examples.
