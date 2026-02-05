#!/usr/bin/env python3
"""
Log MCP Service - Log aggregation, analysis, and monitoring
Port: 7010
"""
import gzip
import json
import logging
import os
import re
import shlex
import subprocess
import tempfile
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
ALLOWED_LOG_DIRS = ["/var/log", "/app/logs", "/tmp/logs"]

# Whitelist of allowed commands
ALLOWED_COMMANDS = {
    "journalctl": ["-n", "-u", "--since", "--until", "-f", "-x", "-e"],
    "tail": ["-n", "-f"],
    "grep": ["-i", "-v", "-E", "-A", "-B", "-C"],
}


def validate_log_path(user_path: str) -> Path:
    """Validate and sanitize log file path to prevent path traversal"""
    try:
        # Resolve to absolute path
        path = Path(user_path).resolve()

        # Check if path is within allowed directories
        for allowed_dir in ALLOWED_LOG_DIRS:
            allowed_path = Path(allowed_dir).resolve()
            try:
                path.relative_to(allowed_path)
                # Path is valid and within allowed directory
                if not path.exists():
                    raise HTTPException(status_code=404, detail="Log file not found")
                if not path.is_file():
                    raise HTTPException(status_code=400, detail="Path is not a file")
                return path
            except ValueError:
                continue

        # Path not in any allowed directory
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Path not in allowed directories {ALLOWED_LOG_DIRS}",
        )
    except Exception as e:
        logger.error(f"Path validation failed: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid path")


def validate_command(command_str: str) -> List[str]:
    """Validate and sanitize command to prevent command injection"""
    try:
        parts = shlex.split(command_str)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid command syntax: {str(e)}")

    if not parts:
        raise HTTPException(status_code=400, detail="Empty command")

    cmd = parts[0]

    # Check if command is in whitelist
    if cmd not in ALLOWED_COMMANDS:
        raise HTTPException(
            status_code=403,
            detail=f"Command not allowed. Allowed commands: {list(ALLOWED_COMMANDS.keys())}",
        )

    # Validate arguments
    allowed_args = ALLOWED_COMMANDS[cmd]
    for arg in parts[1:]:
        if arg.startswith("-"):
            # Check if flag is allowed
            flag_valid = False
            for allowed_arg in allowed_args:
                if arg.startswith(allowed_arg):
                    flag_valid = True
                    break

            if not flag_valid:
                raise HTTPException(
                    status_code=403, detail=f"Argument {arg} not allowed for {cmd}"
                )

    return parts


app = FastAPI(
    title="Log MCP Service",
    description="Log aggregation, analysis, and monitoring tools",
    version="1.0.0",
)
# Prometheus metrics instrumentation
Instrumentator().instrument(app).expose(app)


# Common log patterns
LOG_PATTERNS = {
    "apache_access": r'(\S+) \S+ \S+ \[([\w:/]+\s[+\-]\d{4})\] "(\S+) (\S+) (\S+)" (\d{3}) (\d+|-)',
    "nginx_access": r'(\S+) - (\S+) \[([\w:/]+\s[+\-]\d{4})\] "(\w+) ([^"]+) ([^"]+)" (\d+) (\d+) "([^"]*)" "([^"]*)"',
    "syslog": r"(\w+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\S+):\s+(.*)",
    "json": r"^\{.*\}$",
    "timestamp": r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}",
    "ip_address": r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
    "error_level": r"\b(ERROR|WARN|INFO|DEBUG|FATAL|CRITICAL)\b",
}

# Request/Response Models


class LogAnalysisRequest(BaseModel):
    """Log analysis request"""

    log_source: str = Field(..., description="file_path, command, or direct_text")
    source_value: str
    analysis_type: str = Field(..., description="pattern, stats, errors, timeline")
    pattern: Optional[str] = None
    log_format: Optional[str] = "auto"  # auto, apache, nginx, syslog, json
    time_range: Optional[Dict[str, str]] = (
        None  # {"start": "2024-01-01", "end": "2024-01-02"}
    )
    filters: Optional[Dict[str, str]] = {}  # {"level": "ERROR", "source": "app"}
    limit: Optional[int] = 1000


class LogMonitorRequest(BaseModel):
    """Log monitoring request"""

    operation: str = Field(..., description="start, stop, status, alerts")
    log_file: Optional[str] = None
    patterns: Optional[List[str]] = []
    alert_threshold: Optional[int] = 10  # alerts per minute
    monitor_duration: Optional[int] = 300  # seconds


class LogAggregateRequest(BaseModel):
    """Log aggregation request"""

    sources: List[str]
    output_format: str = "json"  # json, csv, text
    group_by: Optional[str] = "timestamp"  # timestamp, level, source, ip
    time_window: Optional[str] = "1h"  # 1m, 5m, 1h, 1d
    merge_strategy: str = "chronological"  # chronological, by_source


class LogSearchRequest(BaseModel):
    """Log search request"""

    query: str
    sources: List[str]
    search_type: str = "regex"  # regex, text, fuzzy
    context_lines: Optional[int] = 3
    max_results: Optional[int] = 100
    case_sensitive: Optional[bool] = False


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Log MCP",
        "port": 7010,
        "timestamp": datetime.now().isoformat(),
        "features": ["log_analysis", "log_monitor", "log_aggregate", "log_search"],
        "patterns": list(LOG_PATTERNS.keys()),
    }


@app.post("/tools/log_analysis")
async def log_analysis_tool(request: LogAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze log files or text

    Tool: log_analysis
    Description: Analyze logs for patterns, statistics, errors, and timeline
    """
    try:
        # Get log content
        log_lines = []

        if request.log_source == "file_path":
            # Validate path to prevent path traversal
            log_path = validate_log_path(request.source_value)

            # Handle compressed files
            if log_path.suffix == ".gz":
                with gzip.open(log_path, "rt") as f:
                    log_lines = f.readlines()
            else:
                log_lines = log_path.read_text().splitlines()

        elif request.log_source == "command":
            # Validate command to prevent command injection
            validated_command = validate_command(request.source_value)

            try:
                result = subprocess.run(
                    validated_command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    shell=False,  # Explicitly disable shell
                )
                log_lines = result.stdout.splitlines()
            except subprocess.TimeoutExpired:
                raise HTTPException(status_code=408, detail="Command timeout")
            except Exception as e:
                logger.error(f"Command execution failed: {str(e)}")
                raise HTTPException(status_code=500, detail="Command execution failed")

        elif request.log_source == "direct_text":
            log_lines = request.source_value.splitlines()
        else:
            raise HTTPException(status_code=400, detail="Invalid log_source")

        # Apply filters and time range
        filtered_lines = []
        for line in log_lines:
            # Time range filter
            if request.time_range:
                timestamps = re.findall(LOG_PATTERNS["timestamp"], line)
                if timestamps:
                    try:
                        line_time = datetime.strptime(
                            timestamps[0], "%Y-%m-%d %H:%M:%S"
                        )
                        start_time = datetime.fromisoformat(
                            request.time_range.get("start", "1900-01-01")
                        )
                        end_time = datetime.fromisoformat(
                            request.time_range.get("end", "2100-01-01")
                        )
                        if not (start_time <= line_time <= end_time):
                            continue
                    except ValueError:
                        pass

            # Other filters
            include_line = True
            for filter_key, filter_value in request.filters.items():
                if filter_key == "level" and filter_value.upper() not in line.upper():
                    include_line = False
                elif filter_key == "source" and filter_value not in line:
                    include_line = False
                elif filter_key == "ip":
                    ips = re.findall(LOG_PATTERNS["ip_address"], line)
                    if filter_value not in ips:
                        include_line = False

            if include_line:
                filtered_lines.append(line)

        # Apply limit
        if len(filtered_lines) > request.limit:
            filtered_lines = filtered_lines[: request.limit]

        # Perform analysis based on type
        if request.analysis_type == "pattern":
            return await _analyze_patterns(
                filtered_lines, request.pattern, request.log_format
            )
        elif request.analysis_type == "stats":
            return await _analyze_stats(filtered_lines)
        elif request.analysis_type == "errors":
            return await _analyze_errors(filtered_lines)
        elif request.analysis_type == "timeline":
            return await _analyze_timeline(filtered_lines)
        else:
            raise HTTPException(status_code=400, detail="Invalid analysis_type")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Log analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Log analysis failed: {str(e)}")


async def _analyze_patterns(
    lines: List[str], pattern: str, log_format: str
) -> Dict[str, Any]:
    """Analyze log lines for patterns"""
    matches = []

    if pattern:
        # Custom pattern
        regex_pattern = re.compile(pattern)
        for i, line in enumerate(lines):
            match = regex_pattern.search(line)
            if match:
                matches.append(
                    {
                        "line_number": i + 1,
                        "line": line.strip(),
                        "match": match.group(),
                        "groups": match.groups() if match.groups() else [],
                    }
                )
    else:
        # Auto-detect format and extract patterns
        if log_format == "auto":
            log_format = _detect_log_format(lines[:10])

        if log_format in LOG_PATTERNS:
            regex_pattern = re.compile(LOG_PATTERNS[log_format])
            for i, line in enumerate(lines):
                match = regex_pattern.search(line)
                if match:
                    matches.append(
                        {
                            "line_number": i + 1,
                            "line": line.strip(),
                            "parsed_groups": match.groups(),
                        }
                    )

    return {
        "analysis_type": "pattern",
        "total_lines": len(lines),
        "matches": matches,
        "match_count": len(matches),
        "detected_format": log_format,
        "timestamp": datetime.now().isoformat(),
    }


async def _analyze_stats(lines: List[str]) -> Dict[str, Any]:
    """Generate statistics from log lines"""
    # Count error levels
    level_counts = Counter()
    ip_counts = Counter()
    hourly_counts = defaultdict(int)

    for line in lines:
        # Error levels
        levels = re.findall(LOG_PATTERNS["error_level"], line.upper())
        for level in levels:
            level_counts[level] += 1

        # IP addresses
        ips = re.findall(LOG_PATTERNS["ip_address"], line)
        for ip in ips:
            ip_counts[ip] += 1

        # Timestamps for hourly distribution
        timestamps = re.findall(LOG_PATTERNS["timestamp"], line)
        if timestamps:
            try:
                dt = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                hourly_counts[hour_key] += 1
            except ValueError:
                pass

    return {
        "analysis_type": "stats",
        "total_lines": len(lines),
        "log_levels": dict(level_counts.most_common()),
        "top_ips": dict(ip_counts.most_common(10)),
        "hourly_distribution": dict(hourly_counts),
        "unique_ips": len(ip_counts),
        "timestamp": datetime.now().isoformat(),
    }


async def _analyze_errors(lines: List[str]) -> Dict[str, Any]:
    """Analyze error patterns and frequency"""
    errors = []
    error_patterns = Counter()

    for i, line in enumerate(lines):
        line_upper = line.upper()
        if any(
            level in line_upper for level in ["ERROR", "FATAL", "CRITICAL", "EXCEPTION"]
        ):
            errors.append(
                {
                    "line_number": i + 1,
                    "line": line.strip(),
                    "timestamp": _extract_timestamp(line),
                }
            )

            # Extract error pattern (remove specific details like IDs, timestamps)
            clean_pattern = re.sub(
                r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}", "[TIMESTAMP]", line
            )
            clean_pattern = re.sub(r"\b\d+\b", "[NUMBER]", clean_pattern)
            clean_pattern = re.sub(
                r"\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b",
                "[UUID]",
                clean_pattern,
            )
            error_patterns[clean_pattern] += 1

    return {
        "analysis_type": "errors",
        "total_lines": len(lines),
        "error_count": len(errors),
        "errors": errors[:50],  # Limit to first 50
        "common_error_patterns": dict(error_patterns.most_common(10)),
        "timestamp": datetime.now().isoformat(),
    }


async def _analyze_timeline(lines: List[str]) -> Dict[str, Any]:
    """Create timeline analysis"""
    events = []
    timeline = defaultdict(list)

    for i, line in enumerate(lines):
        timestamp = _extract_timestamp(line)
        if timestamp:
            events.append(
                {
                    "timestamp": timestamp,
                    "line_number": i + 1,
                    "content": line.strip()[:100],  # Truncate for display
                }
            )

            # Group by hour
            try:
                dt = datetime.fromisoformat(timestamp)
                hour_key = dt.strftime("%Y-%m-%d %H:00")
                timeline[hour_key].append(line.strip()[:50])
            except ValueError:
                pass

    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"])

    return {
        "analysis_type": "timeline",
        "total_lines": len(lines),
        "events_with_timestamps": len(events),
        "first_event": events[0]["timestamp"] if events else None,
        "last_event": events[-1]["timestamp"] if events else None,
        "recent_events": events[-20:],  # Last 20 events
        "hourly_timeline": {k: len(v) for k, v in timeline.items()},
        "timestamp": datetime.now().isoformat(),
    }


def _detect_log_format(sample_lines: List[str]) -> str:
    """Auto-detect log format from sample lines"""
    for format_name, pattern in LOG_PATTERNS.items():
        if format_name in ["timestamp", "ip_address", "error_level"]:
            continue

        regex = re.compile(pattern)
        matches = sum(1 for line in sample_lines if regex.search(line))
        if matches >= len(sample_lines) * 0.5:  # 50% match rate
            return format_name

    return "unknown"


def _extract_timestamp(line: str) -> Optional[str]:
    """Extract timestamp from log line"""
    timestamps = re.findall(LOG_PATTERNS["timestamp"], line)
    if timestamps:
        try:
            # Try to parse and return in ISO format
            dt = datetime.strptime(timestamps[0], "%Y-%m-%d %H:%M:%S")
            return dt.isoformat()
        except ValueError:
            return timestamps[0]  # Return as-is if parsing fails
    return None


@app.post("/tools/log_search")
async def log_search_tool(request: LogSearchRequest) -> Dict[str, Any]:
    """
    Search through log files

    Tool: log_search
    Description: Search for patterns in multiple log sources
    """
    try:
        results = []
        total_matches = 0

        for source in request.sources:
            try:
                # Validate path to prevent path traversal
                source_path = validate_log_path(source)

                # Read file content
                if source_path.suffix == ".gz":
                    with gzip.open(source_path, "rt") as f:
                        lines = f.readlines()
                else:
                    lines = source_path.read_text().splitlines()
            except HTTPException:
                # Skip files that fail validation
                continue

            # Search based on type
            source_matches = []
            if request.search_type == "regex":
                try:
                    pattern = re.compile(
                        request.query,
                        re.IGNORECASE if not request.case_sensitive else 0,
                    )
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            context_start = max(0, i - request.context_lines)
                            context_end = min(len(lines), i + request.context_lines + 1)
                            source_matches.append(
                                {
                                    "line_number": i + 1,
                                    "matched_line": line.strip(),
                                    "context": lines[context_start:context_end],
                                }
                            )
                except re.error as e:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid regex: {str(e)}"
                    )

            elif request.search_type == "text":
                query = (
                    request.query.lower()
                    if not request.case_sensitive
                    else request.query
                )
                for i, line in enumerate(lines):
                    line_to_search = (
                        line.lower() if not request.case_sensitive else line
                    )
                    if query in line_to_search:
                        context_start = max(0, i - request.context_lines)
                        context_end = min(len(lines), i + request.context_lines + 1)
                        source_matches.append(
                            {
                                "line_number": i + 1,
                                "matched_line": line.strip(),
                                "context": lines[context_start:context_end],
                            }
                        )

            # Apply result limit per source
            if len(source_matches) > request.max_results // len(request.sources):
                source_matches = source_matches[
                    : request.max_results // len(request.sources)
                ]

            if source_matches:
                results.append(
                    {
                        "source": str(source_path),
                        "matches": source_matches,
                        "match_count": len(source_matches),
                    }
                )
                total_matches += len(source_matches)

        return {
            "query": request.query,
            "search_type": request.search_type,
            "sources_searched": len(request.sources),
            "sources_with_matches": len(results),
            "total_matches": total_matches,
            "results": results,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Log search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Log search failed: {str(e)}")


@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "log_analysis",
                "description": "Analyze logs for patterns, statistics, errors, and timeline",
                "parameters": {
                    "log_source": "string (required: file_path|command|direct_text)",
                    "source_value": "string (required, file path, command, or log text)",
                    "analysis_type": "string (required: pattern|stats|errors|timeline)",
                    "pattern": "string (optional, regex pattern for pattern analysis)",
                    "log_format": "string (optional: auto|apache|nginx|syslog|json)",
                    "time_range": "object (optional, {start, end} timestamps)",
                    "filters": "object (optional, filter criteria)",
                    "limit": "integer (optional, max lines to process)",
                },
            },
            {
                "name": "log_search",
                "description": "Search for patterns in multiple log sources",
                "parameters": {
                    "query": "string (required, search query)",
                    "sources": "array (required, list of log file paths)",
                    "search_type": "string (optional: regex|text|fuzzy, default regex)",
                    "context_lines": "integer (optional, lines of context, default 3)",
                    "max_results": "integer (optional, max results, default 100)",
                    "case_sensitive": "boolean (optional, default false)",
                },
            },
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
