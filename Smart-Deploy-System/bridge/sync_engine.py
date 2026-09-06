import os
import hashlib
import subprocess
import difflib
import socket
from pathlib import Path

class SyncEngine:
    def __init__(self, remote_host="HAS", remote_root="/home/orchestration/Smart-Deploy-System/unified-truth"):
        self.remote_host = remote_host
        self.remote_root = remote_root
        self.hostname = socket.gethostname()
        
        # Base files (GLOBAL)
        self.files_to_sync = {
            "AGENTS.md": Path("~/AGENTS.md").expanduser(),
            "GEMINI.md": Path("~/.gemini/GEMINI.md").expanduser(),
            "MEMORY.md": Path("~/.codex/memories/MEMORY.md").expanduser()
        }
        
        # Hardware-specific files (LOCAL)
        self.hw_files = {
            ".zshrc": Path("~/.zshrc").expanduser(),
            ".bash_aliases": Path("~/.bash_aliases").expanduser()
        }

    def get_local_content(self, file_path):
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_remote_content(self, filename, is_hw=False):
        remote_path = f"{self.remote_root}/{filename}"
        if is_hw:
            remote_path = f"{self.remote_root}/hw-profiles/{self.hostname}/{filename}"
            
        cmd = f"ssh {self.remote_host} 'cat {remote_path}'"
        try:
            return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
        except:
            return None

    def get_diff(self, filename, is_hw=False):
        local_path = self.files_to_sync.get(filename) or self.hw_files.get(filename)
        l_content = self.get_local_content(local_path)
        r_content = self.get_remote_content(filename, is_hw)
        
        if l_content is None or r_content is None:
            return "File missing on one side."
            
        diff = difflib.unified_diff(
            r_content.splitlines(),
            l_content.splitlines(),
            fromfile='HAS (Source)',
            tofile='Local (Agent)',
            lineterm=''
        )
        return "\n".join(list(diff))

    def check_status(self):
        status = {}
        # Check Global Files
        for filename, local_path in self.files_to_sync.items():
            status[filename] = self._compare(filename, local_path, is_hw=False)
            
        # Check HW Files
        for filename, local_path in self.hw_files.items():
            status[f"HW:{filename}"] = self._compare(filename, local_path, is_hw=True)
            
        return status

    def _compare(self, filename, local_path, is_hw):
        l_content = self.get_local_content(local_path)
        r_content = self.get_remote_content(filename, is_hw)
        
        if not l_content and not r_content: return "MISSING"
        if not l_content: return "REMOTE_ONLY"
        if not r_content: return "LOCAL_ONLY"
        
        l_hash = hashlib.sha256(l_content.encode()).hexdigest()
        r_hash = hashlib.sha256(r_content.encode()).hexdigest()
        
        return "SYNCED" if l_hash == r_hash else "OUT_OF_SYNC"

    def pull(self, filename, is_hw=False):
        local_path = self.files_to_sync.get(filename) or self.hw_files.get(filename)
        remote_path = f"{self.remote_root}/{filename}"
        if is_hw:
            remote_path = f"{self.remote_root}/hw-profiles/{self.hostname}/{filename}"
            
        local_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = f"scp {self.remote_host}:{remote_path} {local_path}"
        subprocess.check_call(cmd, shell=True)

    def push(self, filename, is_hw=False):
        local_path = self.files_to_sync.get(filename) or self.hw_files.get(filename)
        remote_path = f"{self.remote_root}/{filename}"
        if is_hw:
            # Ensure HW directory exists on HAS
            ssh_cmd = f"ssh {self.remote_host} 'mkdir -p {self.remote_root}/hw-profiles/{self.hostname}'"
            subprocess.check_call(ssh_cmd, shell=True)
            remote_path = f"{self.remote_root}/hw-profiles/{self.hostname}/{filename}"
            
        cmd = f"scp {local_path} {self.remote_host}:{remote_path}"
        subprocess.check_call(cmd, shell=True)

if __name__ == "__main__":
    engine = SyncEngine()
    print(engine.check_status())
