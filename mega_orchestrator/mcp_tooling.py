#!/usr/bin/env python3
"""Shared MCP tool metadata for Mega Orchestrator compatibility layers."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List


MCP_TOOL_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "file_read": {
        "description": "Read a file from an allowed path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path to read."},
                "max_size": {"type": "integer", "description": "Maximum bytes to return.", "default": 1000000},
            },
            "required": ["path"],
        },
    },
    "file_write": {
        "description": "Write UTF-8 text to a file in an allowed path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Absolute file path to write."},
                "content": {"type": "string", "description": "Text content to write."},
                "overwrite": {"type": "boolean", "default": False},
                "create_dirs": {"type": "boolean", "default": False},
            },
            "required": ["path", "content"],
        },
    },
    "file_list": {
        "description": "List files in a directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Absolute directory path."},
                "page": {"type": "integer", "default": 1},
                "limit": {"type": "integer", "default": 100},
            },
            "required": ["directory"],
        },
    },
    "file_search": {
        "description": "Search for files under a root path by pattern and optional content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "root": {"type": "string", "description": "Root directory to search."},
                "pattern": {"type": "string", "default": "*"},
                "content_query": {"type": "string"},
                "limit": {"type": "integer", "default": 100},
                "include_hidden": {"type": "boolean", "default": False},
            },
            "required": ["root"],
        },
    },
    "file_analyze": {
        "description": "Return metadata and preview for a file or directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File or directory path."},
                "max_preview": {"type": "integer", "default": 4000},
            },
            "required": ["path"],
        },
    },
    "git_status": {
        "description": "Return git status for a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path."},
            },
        },
    },
    "git_commit": {
        "description": "Create a commit in a repository using the configured user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path."},
                "message": {"type": "string", "description": "Commit message."},
            },
            "required": ["message"],
        },
    },
    "git_push": {
        "description": "Push the current branch to its configured upstream.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path."},
            },
        },
    },
    "git_log": {
        "description": "Read recent commit history from a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path."},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    "git_diff": {
        "description": "Show diff output for a repository.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Repository path."},
                "target": {"type": "string", "description": "Optional ref or file target."},
            },
        },
    },
    "terminal_exec": {
        "description": "Execute a shell command in the terminal MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
    },
    "shell_command": {
        "description": "Execute a shell command and return stdout/stderr.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
    },
    "system_info": {
        "description": "Return system and process information.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "create_terminal": {
        "description": "Create a logical terminal session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "cwd": {"type": "string"},
            },
        },
    },
    "execute_command": {
        "description": "Execute a command in an existing or implicit terminal session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {"type": "string"},
                "cwd": {"type": "string"},
                "timeout": {"type": "integer", "default": 30},
            },
            "required": ["command"],
        },
    },
    "db_query": {
        "description": "Run a database query via the database MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "connection": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    "db_connect": {
        "description": "Validate database connectivity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "connection": {"type": "string"},
            },
        },
    },
    "db_schema": {
        "description": "Inspect database schema metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "connection": {"type": "string"},
            },
        },
    },
    "db_backup": {
        "description": "Export sample backup data from the database MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "connection": {"type": "string"},
            },
        },
    },
    "store_memory": {
        "description": "Store a memory item.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
                "metadata": {"type": "object"},
            },
            "required": ["content"],
        },
    },
    "search_memories": {
        "description": "Search stored memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
    },
    "get_context": {
        "description": "Fetch contextual memories for a topic or session.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    "memory_stats": {
        "description": "Return memory system statistics.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "list_memories": {
        "description": "List recent memories.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
            },
        },
    },
    "research_query": {
        "description": "Run a web research query through the research MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "model": {"type": "string", "default": "sonar-pro"},
            },
            "required": ["query"],
        },
    },
    "perplexity_search": {
        "description": "Run a Perplexity-backed search query.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "model": {"type": "string", "default": "sonar-pro"},
            },
            "required": ["query"],
        },
    },
    "web_search": {
        "description": "Run a web search query via the research MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "model": {"type": "string", "default": "sonar-pro"},
            },
            "required": ["query"],
        },
    },
    "search_web": {
        "description": "Alias for web search via the research MCP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "model": {"type": "string", "default": "sonar-pro"},
            },
            "required": ["query"],
        },
    },
    "skills_list": {
        "description": "List skills from the marketplace registry.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    "skills_resolve": {
        "description": "Resolve a specific skill from the marketplace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "version": {"type": "string"},
            },
            "required": ["name"],
        },
    },
    "registry_search": {
        "description": "Search marketplace registry metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    "registry_get_server": {
        "description": "Return registry metadata for a server.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "server_id": {"type": "string"},
            },
            "required": ["server_id"],
        },
    },
    "catalog_validate": {
        "description": "Validate a marketplace catalog artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "archive_url": {"type": "string"},
                "sha256": {"type": "string"},
            },
            "required": ["archive_url", "sha256"],
        },
    },
}


def build_mcp_tools(available_tools: Iterable[str]) -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []
    for name in sorted(set(available_tools)):
        spec = MCP_TOOL_DEFINITIONS.get(name)
        if not spec:
            continue
        tools.append(
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["inputSchema"],
            }
        )
    return tools
