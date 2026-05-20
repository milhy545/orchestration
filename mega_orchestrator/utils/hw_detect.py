"""Hardware detection utility for the Welcome Service.

Reads CPU, RAM, GPU, OS and network topology from the local machine and returns
a dict compatible with :meth:`WelcomeService.welcome` ``current_hw_data``.

Safe to call on any Linux host; unknown fields are returned as ``"unknown"``
rather than raising.
"""

from __future__ import annotations

import os
import platform
import re
import socket
import subprocess
from typing import Any, Dict


def detect_hardware() -> Dict[str, Any]:
    """Return a hardware snapshot for the current host.

    Returns:
        dict with keys: ``hostname``, ``os``, ``cpu``, ``cpu_cores``,
        ``ram_gb``, ``gpu``, ``ip``.
    """
    return {
        "hostname": platform.node(),
        "os": platform.platform(),
        "cpu": _detect_cpu(),
        "cpu_cores": _detect_cpu_cores(),
        "ram_gb": _detect_ram_gb(),
        "gpu": _detect_gpu(),
        "ip": _detect_ip(),
    }


# Paths to pseudo-files — defined as module constants so tests can patch them.
_PROC_CPUINFO = "/proc/cpuinfo"
_PROC_MEMINFO = "/proc/meminfo"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _detect_cpu(cpuinfo_path: str = _PROC_CPUINFO) -> str:
    """Return the CPU model name from /proc/cpuinfo, falling back to platform."""
    try:
        with open(cpuinfo_path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def _detect_cpu_cores() -> int:
    """Return the number of logical CPU cores."""
    try:
        return os.cpu_count() or 0
    except Exception:
        return 0


def _detect_ram_gb(meminfo_path: str = _PROC_MEMINFO) -> float:
    """Return total RAM in GB from /proc/meminfo."""
    try:
        with open(meminfo_path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("MemTotal"):
                    kb = int(line.split()[1])
                    return round(kb / 1_048_576, 1)
    except (OSError, ValueError, IndexError):
        pass
    return 0.0


def _detect_gpu() -> str:
    """Return GPU name, trying nvidia-smi first, then lspci."""
    # Try nvidia-smi (fast, precise)
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="replace")
        first = out.strip().splitlines()[0].strip()
        if first:
            return first
    except Exception:
        pass

    # Fall back to lspci
    try:
        out = subprocess.check_output(
            ["lspci"],
            stderr=subprocess.DEVNULL,
            timeout=5,
        ).decode("utf-8", errors="replace")
        for line in out.splitlines():
            if re.search(r"VGA|3D controller|Display", line, re.IGNORECASE):
                # Strip the PCI address prefix and return the description
                parts = line.split(":", 2)
                return parts[-1].strip() if len(parts) >= 2 else line.strip()
    except Exception:
        pass

    return "unknown"


def _detect_ip() -> str:
    """Return the primary non-loopback IP address."""
    try:
        # Connect to an external address without sending data to get the local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "unknown"
