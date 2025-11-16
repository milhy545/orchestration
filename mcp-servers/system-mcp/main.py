#!/usr/bin/env python3
"""
System MCP Service - Resources monitoring, processes, system info
Port: 8007
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psutil
import platform
import shutil
import subprocess
import time
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="System MCP Service",
    description="System resources monitoring, process management, and system information",
    version="1.0.0"
)

# Request/Response Models
class ResourceMonitorRequest(BaseModel):
    """Resource monitoring configuration"""
    interval: Optional[int] = 1  # seconds
    duration: Optional[int] = 60  # seconds
    include_per_core: Optional[bool] = False

class ProcessListRequest(BaseModel):
    """Process list filtering"""
    name_filter: Optional[str] = None
    user_filter: Optional[str] = None
    sort_by: Optional[str] = "memory"  # memory, cpu, pid, name
    limit: Optional[int] = Field(50, ge=1, le=1000, description="Maximum processes to return")

class ProcessInfo(BaseModel):
    """Process information"""
    pid: int
    name: str
    username: str
    status: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    create_time: str
    cmdline: List[str]

class SystemInfo(BaseModel):
    """System information"""
    hostname: str
    platform: str
    platform_release: str
    platform_version: str
    architecture: str
    processor: str
    cpu_count: int
    boot_time: str
    uptime_seconds: float

class DiskUsage(BaseModel):
    """Disk usage information"""
    mountpoint: str
    device: str
    filesystem: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent_used: float

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "System MCP",
        "port": 8007,
        "timestamp": datetime.now().isoformat(),
        "features": ["resource_monitor", "process_list", "disk_usage", "system_info"],
        "system": {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "disk_count": len(psutil.disk_partitions())
        }
    }

@app.post("/tools/resource_monitor")
async def resource_monitor_tool(request: ResourceMonitorRequest) -> Dict[str, Any]:
    """
    Monitor system resources over time
    
    Tool: resource_monitor
    Description: Monitor CPU, memory, disk, and network usage over specified duration
    """
    try:
        samples = []
        start_time = time.time()
        
        # Limit duration to prevent long-running requests
        duration = min(request.duration, 300)  # Max 5 minutes
        
        while time.time() - start_time < duration:
            sample_time = time.time()
            
            # CPU usage
            if request.include_per_core:
                cpu_percent = psutil.cpu_percent(interval=request.interval, percpu=True)
                cpu_avg = sum(cpu_percent) / len(cpu_percent)
            else:
                cpu_percent = psutil.cpu_percent(interval=request.interval)
                cpu_avg = cpu_percent
            
            # Memory usage
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            
            # Network I/O
            network_io = psutil.net_io_counters()
            
            sample = {
                "timestamp": datetime.fromtimestamp(sample_time).isoformat(),
                "cpu": {
                    "percent": cpu_avg,
                    "per_core": cpu_percent if request.include_per_core else None
                },
                "memory": {
                    "percent": memory.percent,
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "total_gb": round(memory.total / (1024**3), 2)
                },
                "disk_io": {
                    "read_bytes": disk_io.read_bytes if disk_io else 0,
                    "write_bytes": disk_io.write_bytes if disk_io else 0,
                    "read_count": disk_io.read_count if disk_io else 0,
                    "write_count": disk_io.write_count if disk_io else 0
                } if disk_io else None,
                "network_io": {
                    "bytes_sent": network_io.bytes_sent if network_io else 0,
                    "bytes_recv": network_io.bytes_recv if network_io else 0,
                    "packets_sent": network_io.packets_sent if network_io else 0,
                    "packets_recv": network_io.packets_recv if network_io else 0
                } if network_io else None
            }
            
            samples.append(sample)
            
            # Break if we have enough samples or duration exceeded
            if len(samples) >= 60:  # Max 60 samples
                break
        
        # Calculate averages
        avg_cpu = sum(s["cpu"]["percent"] for s in samples) / len(samples)
        avg_memory = sum(s["memory"]["percent"] for s in samples) / len(samples)
        
        return {
            "monitoring_duration": time.time() - start_time,
            "sample_count": len(samples),
            "interval_seconds": request.interval,
            "averages": {
                "cpu_percent": round(avg_cpu, 2),
                "memory_percent": round(avg_memory, 2)
            },
            "samples": samples[-20:],  # Return last 20 samples to limit response size
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Resource monitoring failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resource monitoring failed: {str(e)}")

@app.post("/tools/process_list")
async def process_list_tool(request: ProcessListRequest) -> Dict[str, Any]:
    """
    List and filter system processes
    
    Tool: process_list
    Description: Get list of running processes with filtering and sorting options
    """
    try:
        processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'username', 'status', 'create_time', 'cmdline']):
            try:
                # Get process info
                pinfo = proc.info
                
                # Apply name filter
                if request.name_filter and request.name_filter.lower() not in pinfo['name'].lower():
                    continue
                
                # Apply user filter
                if request.user_filter and request.user_filter != pinfo['username']:
                    continue
                
                # Get CPU and memory usage
                cpu_percent = proc.cpu_percent()
                memory_info = proc.memory_info()
                memory_percent = proc.memory_percent()
                
                process_info = ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo['name'],
                    username=pinfo['username'] or 'unknown',
                    status=pinfo['status'],
                    cpu_percent=round(cpu_percent, 2),
                    memory_percent=round(memory_percent, 2),
                    memory_mb=round(memory_info.rss / (1024**2), 2),
                    create_time=datetime.fromtimestamp(pinfo['create_time']).isoformat(),
                    cmdline=pinfo['cmdline'] or []
                )
                
                processes.append(process_info)
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have disappeared or no access
                continue
        
        # Sort processes
        if request.sort_by == "memory":
            processes.sort(key=lambda x: x.memory_percent, reverse=True)
        elif request.sort_by == "cpu":
            processes.sort(key=lambda x: x.cpu_percent, reverse=True)
        elif request.sort_by == "pid":
            processes.sort(key=lambda x: x.pid)
        elif request.sort_by == "name":
            processes.sort(key=lambda x: x.name.lower())
        
        # Limit results
        limited_processes = processes[:request.limit]
        
        return {
            "total_processes": len(processes),
            "returned_processes": len(limited_processes),
            "filters": {
                "name_filter": request.name_filter,
                "user_filter": request.user_filter,
                "sort_by": request.sort_by,
                "limit": request.limit
            },
            "processes": [proc.dict() for proc in limited_processes],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Process listing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Process listing failed: {str(e)}")

@app.post("/tools/disk_usage")
async def disk_usage_tool() -> Dict[str, Any]:
    """
    Get disk usage information for all mounted filesystems
    
    Tool: disk_usage
    Description: Get disk space usage for all mounted filesystems
    """
    try:
        disk_info = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                
                disk_usage = DiskUsage(
                    mountpoint=partition.mountpoint,
                    device=partition.device,
                    filesystem=partition.fstype,
                    total_gb=round(usage.total / (1024**3), 2),
                    used_gb=round(usage.used / (1024**3), 2),
                    free_gb=round(usage.free / (1024**3), 2),
                    percent_used=round((usage.used / usage.total) * 100, 2)
                )
                
                disk_info.append(disk_usage)
                
            except (PermissionError, FileNotFoundError):
                # Skip inaccessible filesystems
                continue
        
        # Sort by percent used (highest first)
        disk_info.sort(key=lambda x: x.percent_used, reverse=True)
        
        # Calculate totals
        total_size = sum(d.total_gb for d in disk_info)
        total_used = sum(d.used_gb for d in disk_info)
        total_free = sum(d.free_gb for d in disk_info)
        
        return {
            "filesystem_count": len(disk_info),
            "total_storage": {
                "total_gb": round(total_size, 2),
                "used_gb": round(total_used, 2),
                "free_gb": round(total_free, 2),
                "percent_used": round((total_used / total_size) * 100, 2) if total_size > 0 else 0
            },
            "filesystems": [disk.dict() for disk in disk_info],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Disk usage check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Disk usage check failed: {str(e)}")

@app.post("/tools/system_info")
async def system_info_tool() -> Dict[str, Any]:
    """
    Get comprehensive system information
    
    Tool: system_info
    Description: Get detailed system information including platform, hardware, and uptime
    """
    try:
        # Boot time
        boot_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_timestamp)
        uptime_seconds = time.time() - boot_timestamp
        
        # CPU info
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "max_frequency": f"{psutil.cpu_freq().max:.2f} MHz" if psutil.cpu_freq() else "Unknown",
            "current_frequency": f"{psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "Unknown"
        }
        
        # Memory info
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        memory_info = {
            "total_gb": round(memory.total / (1024**3), 2),
            "available_gb": round(memory.available / (1024**3), 2),
            "percent": memory.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
            "swap_percent": swap.percent
        }
        
        # Network interfaces
        network_interfaces = []
        for interface, addresses in psutil.net_if_addrs().items():
            interface_info = {
                "name": interface,
                "addresses": []
            }
            
            for addr in addresses:
                interface_info["addresses"].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast
                })
            
            network_interfaces.append(interface_info)
        
        system_info = SystemInfo(
            hostname=platform.node(),
            platform=platform.system(),
            platform_release=platform.release(),
            platform_version=platform.version(),
            architecture=platform.machine(),
            processor=platform.processor() or "Unknown",
            cpu_count=psutil.cpu_count(),
            boot_time=boot_time.isoformat(),
            uptime_seconds=round(uptime_seconds, 2)
        )
        
        return {
            "system": system_info.dict(),
            "cpu": cpu_info,
            "memory": memory_info,
            "network_interfaces": network_interfaces,
            "users": [{"name": user.name, "terminal": user.terminal, "host": user.host, "started": datetime.fromtimestamp(user.started).isoformat()} for user in psutil.users()],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"System info retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"System info retrieval failed: {str(e)}")

@app.get("/tools/list")
async def list_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {
                "name": "resource_monitor",
                "description": "Monitor CPU, memory, disk, and network usage over specified duration",
                "parameters": {
                    "interval": "integer (default: 1, seconds between samples)",
                    "duration": "integer (default: 60, total monitoring duration)",
                    "include_per_core": "boolean (default: false, include per-core CPU stats)"
                }
            },
            {
                "name": "process_list",
                "description": "Get list of running processes with filtering and sorting options",
                "parameters": {
                    "name_filter": "string (optional, filter by process name)",
                    "user_filter": "string (optional, filter by username)",
                    "sort_by": "string (default: memory, options: memory|cpu|pid|name)",
                    "limit": "integer (default: 50, max processes to return)"
                }
            },
            {
                "name": "disk_usage",
                "description": "Get disk space usage for all mounted filesystems",
                "parameters": {}
            },
            {
                "name": "system_info",
                "description": "Get detailed system information including platform, hardware, and uptime",
                "parameters": {}
            }
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)