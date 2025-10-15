#!/usr/bin/env python3
"""
🚀 BACKUP COORDINATOR - Emergency Fallback System
Port 7999 - Emergency coordinator pro disaster recovery

Features:
- Lightweight fallback coordinator
- Basic MCP service routing without advanced features
- Health monitoring and primary coordinator detection
- Automatic primary/backup switching
- Emergency service restoration
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import aiohttp
from aiohttp import web
import aioredis
import asyncpg

@dataclass 
class BasicMCPService:
    name: str
    port: int
    tools: List[str]
    priority: int = 1

class BackupCoordinator:
    """
    🔧 BACKUP COORDINATOR - Emergency fallback system
    
    Minimal coordinator pro emergency situations:
    - Základní MCP routing bez advanced features
    - Health monitoring primary coordinatoru
    - Automatic failover detection
    - Essential service orchestration
    """
    
    def __init__(self):
        self.port = 7999
        self.is_primary = False  # Start as backup
        self.primary_coordinator_url = "http://localhost:7000"
        self.version = "1.0.0-backup"
        
        # Basic services without advanced routing
        self.services = self._init_basic_services()
        
        # Minimal infrastructure
        self.redis = None
        self.db_pool = None
        self.app = None
        
        # Monitoring
        self.primary_health_failures = 0
        self.failover_threshold = 3
        self.last_primary_check = 0
        
        # Statistics
        self.stats = {
            "startup_time": time.time(),
            "requests_processed": 0,
            "failover_activations": 0,
            "primary_restored": 0,
            "emergency_mode": False
        }
        
    def _init_basic_services(self) -> Dict[str, BasicMCPService]:
        """Initialize basic MCP services for emergency routing"""
        return {
            "filesystem": BasicMCPService(
                name="Filesystem MCP", 
                port=7001,
                tools=["file_read", "file_write", "file_list"]
            ),
            "terminal": BasicMCPService(
                name="Terminal MCP",
                port=7003, 
                tools=["terminal_exec", "shell_command"]
            ),
            "memory": BasicMCPService(
                name="Memory MCP",
                port=7005,
                tools=["store_memory", "search_memories"]
            ),
            "research": BasicMCPService(
                name="Research MCP",
                port=7011,
                tools=["web_search", "search_web"]
            )
        }
        
    async def initialize(self):
        """Initialize backup coordinator"""
        logging.info("🔧 Initializing Backup Coordinator...")
        
        try:
            # Minimal infrastructure initialization
            await self._init_minimal_infrastructure()
            
            # Initialize web app
            self._init_web_app()
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            # Check if should start as primary (if main coordinator is down)
            await self._check_failover_status()
            
            logging.info(f"✅ Backup Coordinator initialized {'(PRIMARY MODE)' if self.is_primary else '(BACKUP MODE)'}")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Backup Coordinator: {e}")
            raise
            
    async def _init_minimal_infrastructure(self):
        """Initialize minimal Redis/DB connections with fallbacks"""
        try:
            # Try Redis connection
            self.redis = aioredis.from_url("redis://localhost:7022")
            await self.redis.ping()
            logging.info("✅ Redis connection established")
        except Exception as e:
            logging.warning(f"⚠️ Redis connection failed: {e} (continuing without Redis)")
            self.redis = None
            
        try:
            # Try PostgreSQL connection
            self.db_pool = await asyncpg.create_pool(
                "postgresql://mcp_admin:change_me_in_production@localhost:7021/mcp_unified",
                min_size=1, max_size=3
            )
            logging.info("✅ PostgreSQL connection established")
        except Exception as e:
            logging.warning(f"⚠️ PostgreSQL connection failed: {e} (continuing without DB)")
            self.db_pool = None
            
    def _init_web_app(self):
        """Initialize web application with emergency routes"""
        self.app = web.Application()
        
        # Core routes
        self.app.router.add_post('/mcp', self._handle_mcp_request)
        self.app.router.add_get('/health', self._handle_health)
        self.app.router.add_get('/services', self._handle_services)
        self.app.router.add_get('/status', self._handle_status)
        
        # Emergency management routes
        self.app.router.add_post('/emergency/activate', self._handle_emergency_activate)
        self.app.router.add_post('/emergency/deactivate', self._handle_emergency_deactivate)
        self.app.router.add_get('/primary/status', self._handle_primary_status)
        
        logging.info("✅ Backup Coordinator web routes initialized")
        
    async def _start_monitoring_tasks(self):
        """Start monitoring and failover tasks"""
        asyncio.create_task(self._primary_health_monitor())
        asyncio.create_task(self._failover_detection_task())
        
        logging.info("✅ Monitoring tasks started")
        
    async def _check_failover_status(self):
        """Check if backup should immediately become primary"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.primary_coordinator_url}/health", timeout=5) as response:
                    if response.status == 200:
                        logging.info("✅ Primary coordinator is healthy - remaining in backup mode")
                        return
        except:
            pass
            
        # Primary is down - activate as primary
        logging.warning("⚠️ Primary coordinator unreachable - activating as PRIMARY")
        await self._activate_as_primary()
        
    # ============================================================================
    # REQUEST HANDLING
    # ============================================================================
    
    async def _handle_mcp_request(self, request):
        """Handle basic MCP request routing"""
        try:
            # If not primary, check if primary is available to forward
            if not self.is_primary and not self.stats["emergency_mode"]:
                try:
                    # Try forwarding to primary
                    data = await request.json()
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            f"{self.primary_coordinator_url}/mcp", 
                            json=data,
                            timeout=10
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                return web.json_response(result)
                            else:
                                # Primary failed - handle locally
                                logging.warning("Primary coordinator failed - handling request locally")
                                self.stats["emergency_mode"] = True
                                
                except Exception as e:
                    logging.warning(f"Failed to forward to primary: {e} - handling locally")
                    self.stats["emergency_mode"] = True
                    
            # Handle request locally
            data = await request.json()
            result = await self._route_basic_request(
                data.get("tool"),
                data.get("arguments", {})
            )
            
            self.stats["requests_processed"] += 1
            return web.json_response(result)
            
        except Exception as e:
            logging.error(f"Error handling backup MCP request: {e}")
            return web.json_response({"error": str(e)}, status=500)
            
    async def _route_basic_request(self, tool: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Basic request routing without advanced features"""
        if not tool:
            return {"error": "Tool name required"}
            
        # Find service for tool
        service_name = None
        for name, service in self.services.items():
            if tool in service.tools:
                service_name = name
                break
                
        if not service_name:
            return {"error": f"No service found for tool: {tool}"}
            
        service = self.services[service_name]
        
        # Simple service call without retry logic
        try:
            url = f"http://localhost:{service.port}/mcp"
            payload = {
                "tool": tool,
                "arguments": arguments,
                "_orchestrator": "backup",
                "_emergency_mode": self.stats["emergency_mode"]
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        result["_backup_coordinator"] = True
                        return result
                    else:
                        return {
                            "error": f"Service {service.name} returned {response.status}",
                            "backup_coordinator": True
                        }
                        
        except Exception as e:
            return {
                "error": f"Service {service.name} error: {str(e)}",
                "backup_coordinator": True
            }
            
    # ============================================================================
    # WEB ROUTE HANDLERS
    # ============================================================================
    
    async def _handle_health(self, request):
        """Health check for backup coordinator"""
        health_data = {
            "orchestrator": "backup",
            "version": self.version,
            "status": "healthy",
            "port": self.port,
            "is_primary": self.is_primary,
            "emergency_mode": self.stats["emergency_mode"],
            "timestamp": time.time(),
            "uptime": time.time() - self.stats["startup_time"]
        }
        
        # Check infrastructure
        if self.redis:
            try:
                await self.redis.ping()
                health_data["redis"] = "healthy"
            except:
                health_data["redis"] = "unhealthy"
                
        if self.db_pool:
            try:
                async with self.db_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                health_data["database"] = "healthy"
            except:
                health_data["database"] = "unhealthy"
        
        # Check primary coordinator status
        health_data["primary_coordinator"] = await self._check_primary_health()
        
        return web.json_response(health_data)
        
    async def _handle_services(self, request):
        """Return basic service information"""
        services_info = {}
        
        for name, service in self.services.items():
            services_info[name] = {
                "name": service.name,
                "port": service.port,
                "tools": service.tools,
                "priority": service.priority
            }
            
        return web.json_response({
            "orchestrator": "backup",
            "version": self.version,
            "services": services_info,
            "is_primary": self.is_primary,
            "emergency_mode": self.stats["emergency_mode"]
        })
        
    async def _handle_status(self, request):
        """Return backup coordinator status"""
        status = {
            "orchestrator": "backup",
            "version": self.version,
            "port": self.port,
            "is_primary": self.is_primary,
            "uptime": time.time() - self.stats["startup_time"],
            "stats": self.stats.copy()
        }
        
        status["primary_coordinator"] = {
            "url": self.primary_coordinator_url,
            "health_failures": self.primary_health_failures,
            "last_check": self.last_primary_check
        }
        
        return web.json_response(status)
        
    async def _handle_emergency_activate(self, request):
        """Manually activate emergency mode"""
        await self._activate_as_primary()
        self.stats["emergency_mode"] = True
        
        return web.json_response({
            "status": "activated",
            "message": "Backup coordinator activated as primary",
            "timestamp": time.time()
        })
        
    async def _handle_emergency_deactivate(self, request):
        """Manually deactivate emergency mode"""
        self.is_primary = False
        self.stats["emergency_mode"] = False
        self.primary_health_failures = 0
        
        return web.json_response({
            "status": "deactivated", 
            "message": "Backup coordinator returned to backup mode",
            "timestamp": time.time()
        })
        
    async def _handle_primary_status(self, request):
        """Return primary coordinator status"""
        primary_status = await self._check_primary_health()
        
        return web.json_response({
            "primary_coordinator": {
                "url": self.primary_coordinator_url,
                "status": primary_status,
                "health_failures": self.primary_health_failures,
                "last_check": self.last_primary_check
            },
            "backup_status": {
                "is_primary": self.is_primary,
                "emergency_mode": self.stats["emergency_mode"]
            }
        })
        
    # ============================================================================
    # MONITORING AND FAILOVER
    # ============================================================================
    
    async def _primary_health_monitor(self):
        """Monitor primary coordinator health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                primary_healthy = await self._check_primary_health() == "healthy"
                self.last_primary_check = time.time()
                
                if primary_healthy:
                    self.primary_health_failures = 0
                    
                    # If we're primary and real primary is back, step down
                    if self.is_primary and not self.stats["emergency_mode"]:
                        logging.info("✅ Primary coordinator restored - stepping down")
                        await self._step_down_from_primary()
                        self.stats["primary_restored"] += 1
                        
                else:
                    self.primary_health_failures += 1
                    logging.warning(f"⚠️ Primary coordinator health failure #{self.primary_health_failures}")
                    
            except Exception as e:
                logging.error(f"Error in primary health monitor: {e}")
                
    async def _failover_detection_task(self):
        """Detect when failover should be activated"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                # Activate failover if threshold reached
                if (self.primary_health_failures >= self.failover_threshold and 
                    not self.is_primary):
                    
                    logging.warning(f"🚨 Failover threshold reached ({self.primary_health_failures} failures) - activating as PRIMARY")
                    await self._activate_as_primary()
                    self.stats["failover_activations"] += 1
                    
            except Exception as e:
                logging.error(f"Error in failover detection: {e}")
                
    async def _check_primary_health(self) -> str:
        """Check primary coordinator health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.primary_coordinator_url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status", "unknown")
                    else:
                        return "unhealthy"
        except:
            return "unreachable"
            
    async def _activate_as_primary(self):
        """Activate backup as primary coordinator"""
        self.is_primary = True
        logging.info("🔥 BACKUP COORDINATOR ACTIVATED AS PRIMARY")
        
    async def _step_down_from_primary(self):
        """Step down from primary role"""
        self.is_primary = False
        self.stats["emergency_mode"] = False
        logging.info("🔄 Stepped down from primary - returning to backup mode")

    async def run(self):
        """Run the backup coordinator"""
        await self.initialize()
        
        logging.info(f"🔧 Starting Backup Coordinator on port {self.port}")
        logging.info(f"📊 Health check: http://localhost:{self.port}/health")
        logging.info(f"🛠️  Emergency activate: http://localhost:{self.port}/emergency/activate")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logging.info(f"✅ Backup Coordinator running on port {self.port}")
        
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logging.info("🛑 Shutting down Backup Coordinator...")
            await runner.cleanup()

async def main():
    """Main entry point for backup coordinator"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    backup_coordinator = BackupCoordinator()
    await backup_coordinator.run()

if __name__ == "__main__":
    asyncio.run(main())