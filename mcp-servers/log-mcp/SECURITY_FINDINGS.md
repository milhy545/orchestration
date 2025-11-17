# Security Scan Report - Log MCP Service

**Service:** Log MCP
**Port:** 8010
**Scan Date:** 2025-11-17
**Status:** ⚠️ CRITICAL ISSUES FOUND

## Executive Summary
Found **2 CRITICAL** and **1 HIGH** severity vulnerabilities that require immediate attention.

## Critical Vulnerabilities

### 1. ⚠️ CRITICAL - Command Injection
- **Location:** `main.py:119-124`
- **Function:** `log_analysis_tool()`
- **Severity:** CRITICAL
- **CWE:** CWE-78 (OS Command Injection)

**Vulnerable Code:**
```python
elif request.log_source == "command":
    try:
        result = subprocess.run(
            request.source_value.split(),  # ❌ Direct command execution
            capture_output=True,
            text=True,
            timeout=30
        )
```

**Risk:** Attackers can execute arbitrary system commands
**Attack Vector:**
```bash
curl -X POST http://localhost:8010/tools/log_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "log_source": "command",
    "source_value": "cat /etc/passwd",
    "analysis_type": "pattern"
  }'
```

**Fix Required:**
- Implement command whitelist
- Use shlex.quote() for argument sanitization
- Remove direct command execution or restrict to safe commands only

---

### 2. ⚠️ CRITICAL - Path Traversal
- **Location:** `main.py:106-115`
- **Function:** `log_analysis_tool()`
- **Severity:** CRITICAL
- **CWE:** CWE-22 (Path Traversal)

**Vulnerable Code:**
```python
if request.log_source == "file_path":
    log_path = Path(request.source_value)  # ❌ No path validation
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    # Handle compressed files
    if log_path.suffix == '.gz':
        with gzip.open(log_path, 'rt') as f:
            log_lines = f.readlines()
    else:
        log_lines = log_path.read_text().splitlines()
```

**Risk:** Read any file on the system
**Attack Vector:**
```bash
curl -X POST http://localhost:8010/tools/log_analysis \
  -H "Content-Type: application/json" \
  -d '{
    "log_source": "file_path",
    "source_value": "/etc/shadow",
    "analysis_type": "pattern"
  }'
```

**Fix Required:**
- Implement base directory restriction (chroot-like)
- Validate path with resolve() and check if within allowed directory
- Use whitelist of allowed log directories

## High Severity Issues

### 3. 🔴 HIGH - Unrestricted File Access
- **Location:** `main.py:371-380` (log_search_tool)
- **Severity:** HIGH
- **CWE:** CWE-22 (Path Traversal)

**Vulnerable Code:**
```python
for source in request.sources:
    source_path = Path(source)  # ❌ No path validation
    if not source_path.exists():
        continue

    # Read file content
    if source_path.suffix == '.gz':
        with gzip.open(source_path, 'rt') as f:
            lines = f.readlines()
    else:
        lines = source_path.read_text().splitlines()
```

**Risk:** Multiple file reads without path validation
**Fix Required:** Same as vulnerability #2

## Medium Severity Issues

### 4. 🟡 MEDIUM - ReDoS Potential
- **Location:** `main.py:195, 211, 386`
- **Severity:** MEDIUM
- **CWE:** CWE-1333 (ReDoS)

**Issue:** User-supplied regex patterns without complexity limits
```python
regex_pattern = re.compile(pattern)  # User-controlled pattern
```

**Fix Required:**
- Add regex complexity validation
- Implement timeout for regex operations
- Consider using re2 library for safer regex

### 5. 🟡 MEDIUM - Resource Exhaustion
- **Location:** `main.py:138-166`
- **Severity:** MEDIUM

**Issue:** No limits on log file size or line count before filtering
**Fix Required:**
- Add max file size check before reading
- Implement streaming for large files
- Add memory usage limits

## Low Severity Issues

### 6. 🟢 LOW - Information Disclosure
- **Location:** Error messages throughout
- **Severity:** LOW

**Issue:** Detailed error messages may leak system information
**Fix Required:** Implement generic error messages for production

## Recommendations

### Immediate Actions Required:
1. ✅ Fix command injection (CRITICAL)
2. ✅ Fix path traversal (CRITICAL)
3. ✅ Implement path whitelist (HIGH)

### Security Enhancements:
1. Add authentication/authorization
2. Implement rate limiting
3. Add input validation for all user inputs
4. Add audit logging for all file access and command execution
5. Use principle of least privilege

### Code Example - Secure Path Validation:
```python
import os
from pathlib import Path

# Define allowed log directories
ALLOWED_LOG_DIRS = [
    "/var/log",
    "/app/logs",
    "/tmp/logs"
]

def validate_log_path(user_path: str) -> Path:
    """Validate and sanitize log file path"""
    try:
        # Resolve to absolute path
        path = Path(user_path).resolve()

        # Check if path is within allowed directories
        for allowed_dir in ALLOWED_LOG_DIRS:
            allowed_path = Path(allowed_dir).resolve()
            try:
                path.relative_to(allowed_path)
                return path  # Path is valid
            except ValueError:
                continue

        raise HTTPException(
            status_code=403,
            detail="Access denied: Path not in allowed directories"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid path")
```

### Code Example - Secure Command Execution:
```python
import shlex
from typing import List

# Whitelist of allowed commands
ALLOWED_COMMANDS = {
    "journalctl": ["-n", "-u", "--since", "--until"],
    "tail": ["-n", "-f"],
    "grep": ["-i", "-v", "-E"]
}

def validate_command(command_str: str) -> List[str]:
    """Validate and sanitize command"""
    parts = shlex.split(command_str)

    if not parts or parts[0] not in ALLOWED_COMMANDS:
        raise HTTPException(
            status_code=403,
            detail=f"Command not allowed. Allowed: {list(ALLOWED_COMMANDS.keys())}"
        )

    cmd = parts[0]
    args = parts[1:]

    # Validate arguments
    allowed_args = ALLOWED_COMMANDS[cmd]
    for arg in args:
        if arg.startswith('-') and arg not in allowed_args:
            raise HTTPException(
                status_code=403,
                detail=f"Argument {arg} not allowed for {cmd}"
            )

    return parts
```

## Compliance Notes
- **OWASP Top 10:** A03:2021 – Injection, A01:2021 – Broken Access Control
- **CIS Controls:** Control 3.3 - Configure Data Access Control Lists

## Next Steps
1. Review and apply fixes for CRITICAL vulnerabilities
2. Implement comprehensive input validation
3. Add security testing to CI/CD pipeline
4. Schedule follow-up security audit after fixes

---
**Auditor Notes:**
This service requires immediate remediation before production deployment. The command injection and path traversal vulnerabilities present severe security risks.
