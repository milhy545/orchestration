import os
import re

def update_dockerfile(file_path):
    with open(file_path, "r") as f:
        content = f.read()
    
    # 1. Add uv copy after each WORKDIR
    # We use a lambda to avoid adding it multiple times if there are multiple WORKDIRs
    # or if it's already there (though we already reverted).
    uv_copy = "COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/"
    
    lines = content.splitlines()
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if line.strip().startswith("WORKDIR"):
            # Check if the next line is already the uv copy (unlikely after checkout)
            new_lines.append(uv_copy)
            
    content = "\n".join(new_lines)
    
    # 2. Replace RUN pip install ...
    # This is trickier because of multiline and multiple commands.
    
    # Let's handle the specific case of zen-mcp multiline
    # RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    #     pip install --no-cache-dir -r requirements.txt
    zen_pattern = r"RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \\\n\s+pip install --no-cache-dir -r requirements\.txt"
    content = re.sub(zen_pattern, "RUN uv pip install --system --no-cache -r requirements.txt", content)
    
    # General replacement for other cases
    # We want to replace "RUN pip install [options] [targets]"
    # with "RUN uv pip install --system --no-cache [targets]"
    # but the prompt says specifically to use "-r requirements.txt" in the replacement.
    
    # If the original had a different -r file, we should probably keep it?
    # Or should we literally follow the prompt?
    # Prompt: Nahraď příkazy `RUN pip install ...` moderním příkazem `RUN uv pip install --system --no-cache -r requirements.txt`
    
    # I'll try to find the -r filename if it exists, otherwise default to requirements.txt
    
    def pip_replace(match):
        full_command = match.group(0)
        # Find -r something
        r_match = re.search(r"-r\s+([^\s&|;]+)", full_command)
        req_file = "requirements.txt"
        if r_match:
            req_file = r_match.group(1)
        
        # If it was a git install like in forai-mcp
        if "git+" in full_command:
            # Maybe we should keep the git URL?
            git_match = re.search(r'["\'](git\+[^\s"\'&|;]+)["\']', full_command)
            if git_match:
                return f"RUN uv pip install --system --no-cache {git_match.group(1)}"
            else:
                git_match = re.search(r'(git\+[^\s&|;]+)', full_command)
                if git_match:
                    return f"RUN uv pip install --system --no-cache {git_match.group(1)}"

        return f"RUN uv pip install --system --no-cache -r {req_file}"

    # Replace single line RUN pip install ...
    # We avoid matching if it's already "uv pip"
    content = re.sub(r"RUN pip install\s+.*", pip_replace, content)
    
    with open(file_path, "w") as f:
        f.write(content + "\n")

# Find all Dockerfiles again
import subprocess
result = subprocess.run(["find", "mcp-servers/", "config/", "orchestrator-cli/", "-name", "Dockerfile"], capture_output=True, text=True)
dockerfiles = result.stdout.splitlines()

for df in dockerfiles:
    print(f"Updating {df}...")
    update_dockerfile(df)
