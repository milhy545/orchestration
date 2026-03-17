# Správné mapování MCP nástrojů pro ZEN Coordinator
TOOL_MAPPING = {
    # Filesystem tools - správné názvy
    'list_files': {'service': 'filesystem', 'tool': 'file_list', 'port': 7001},
    'read_file': {'service': 'filesystem', 'tool': 'file_read', 'port': 7001},
    'write_file': {'service': 'filesystem', 'tool': 'file_write', 'port': 7001},
    
    # Terminal tools - správné názvy  
    'execute_command': {'service': 'terminal', 'tool': 'terminal_exec', 'port': 7003},
    'shell_command': {'service': 'terminal', 'tool': 'shell_command', 'port': 7003},
    
    # Git tools - správné názvy
    'git_execute': {'service': 'git', 'tool': 'git_status', 'port': 7002},
    'git_status': {'service': 'git', 'tool': 'git_status', 'port': 7002},
    
    # Memory tools - basic (SQL)
    'search_memories': {'service': 'memory', 'tool': 'search_memories', 'port': 7005},
    'store_memory': {'service': 'memory', 'tool': 'store_memory', 'port': 7005},
    
    # Advanced Memory tools (Semantic/Vector)
    'semantic_search': {'service': 'advanced-memory', 'tool': 'semantic_similarity', 'port': 7012},
    'store_semantic_memory': {'service': 'advanced-memory', 'tool': 'store_memory', 'port': 7012},
    'vector_search': {'service': 'advanced-memory', 'tool': 'vector_search', 'port': 7012},
}
