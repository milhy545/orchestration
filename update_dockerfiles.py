import os
import re

dockerfiles = [
    "mcp-servers/redis-mcp/Dockerfile",
    "mcp-servers/qdrant-mcp/Dockerfile",
    "mcp-servers/system-mcp/Dockerfile",
    "mcp-servers/security-mcp/Dockerfile",
    "mcp-servers/memory-mcp/Dockerfile",
    "mcp-servers/network-mcp/Dockerfile",
    "mcp-servers/webm-transcriber/Dockerfile",
    "mcp-servers/forai-mcp/Dockerfile",
    "mcp-servers/postgresql-mcp/Dockerfile",
    "mcp-servers/terminal-mcp/Dockerfile",
    "mcp-servers/gmail-mcp/Dockerfile",
    "mcp-servers/advanced-memory-mcp/Dockerfile",
    "mcp-servers/research-mcp/Dockerfile",
    "mcp-servers/database-mcp/Dockerfile",
    "mcp-servers/config-mcp/Dockerfile",
    "mcp-servers/marketplace-mcp/Dockerfile",
    "mcp-servers/mqtt-mcp/Dockerfile",
    "mcp-servers/filesystem-mcp/Dockerfile",
    "mcp-servers/code-graph-mcp/Dockerfile",
    "mcp-servers/git-mcp/Dockerfile",
    "mcp-servers/zen-mcp/Dockerfile",
    "mcp-servers/log-mcp/Dockerfile",
    "config/Dockerfile",
    "orchestrator-cli/Dockerfile"
]

uv_copy_line = "COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/\n"

for file_path in dockerfiles:
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        continue
    
    with open(file_path, "r") as f:
        lines = f.readlines()
    
    new_lines = []
    workdir_found = False
    
    for line in lines:
        new_lines.append(line)
        if not workdir_found and line.strip().startswith("WORKDIR"):
            new_lines.append(uv_copy_line)
            workdir_found = True
        
        # Replace RUN pip install ... with uv pip install
        if "RUN pip install" in line:
            # Check if it installs from requirements.txt
            # Most cases seem to be `RUN pip install --no-cache-dir -r requirements.txt`
            # or `RUN pip install --no-cache-dir ...`
            # The instruction says: Nahraď příkazy `RUN pip install ...` moderním příkazem `RUN uv pip install --system --no-cache -r requirements.txt`
            # We should probably be careful to preserve the requirements file if it is different.
            
            match = re.search(r"-r\s+([^\s&|]+)", line)
            req_file = "requirements.txt"
            if match:
                req_file = match.group(1)
            
            # Construct the new command
            # The prompt says: RUN uv pip install --system --no-cache -r requirements.txt
            # I will follow exactly as requested but use req_file if found.
            new_lines[-1] = f"RUN uv pip install --system --no-cache -r {req_file}\n"

    with open(file_path, "w") as f:
        f.writelines(new_lines)
    print(f"Updated: {file_path}")
