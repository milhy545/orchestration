#!/usr/bin/env python3
"""
🚀 MEGA ORCHESTRATOR - COMPLETE HYBRID ARCHITECTURE
Enhanced ZEN Coordinator s David Strejc patterns

Combines:
- Original MCP orchestration (HTTP proxy routing)
- Provider Registry System (auto API key detection)
- SAGE Mode Routing (intelligent task routing)
- Conversation Memory (cross-MCP threading)
- Enhanced File Processing (token-aware handling)
- Backup Coordinator integration
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
from aiohttp import web
import redis.asyncio as aioredis
import asyncpg

# Import our enhanced components
from mega_orchestrator.providers.registry import ModelProviderRegistry, initialize_provider_registry
from mega_orchestrator.modes.sage_router import SAGEModeRouter, SAGEMode
from mega_orchestrator.utils.conversation_memory import ConversationMemory
from mega_orchestrator.utils.file_storage import FileStorage, FileHandlingMode

# Version and build info
VERSION = "1.0.0"
BUILD_DATE = "2025-09-02"

@dataclass
class MCPServiceConfig:
    name: str
    port: int
    health_endpoint: str = "/health"
    tools: List[str] = None
    sage_modes: List[SAGEMode] = None
    priority: int = 1
    timeout: int = 30
    retry_count: int = 3

class MegaOrchestrator:
    """
    🚀 MEGA ORCHESTRATOR - Complete hybrid architecture
    
    Features:
    - Enhanced MCP service orchestration (port 7000-7030)
    - David Strejc's coordination patterns
    - SAGE mode-based intelligent routing
    - Cross-service conversation memory
    - Advanced file processing with deduplication
    - Provider registry with automatic fallbacks
    - Backup coordinator integration
    - Comprehensive health monitoring
    """
    
    def __init__(self, port: int = 7000, backup_mode: bool = False):
        self.port = port
        self.backup_mode = backup_mode
        self.version = VERSION
        self.build_date = BUILD_DATE
        
        # Core components
        self.services = self._init_mcp_services()
        self.provider_registry = None
        self.conversation_memory = ConversationMemory()
        self.file_storage = FileStorage()
        self.sage_router = SAGEModeRouter()
        
        # Infrastructure
        self.redis = None
        self.db_pool = None
        self.app = None
        
        # Statistics
        self.stats = {
            "startup_time": time.time(),
            "requests_processed": 0,
            "mode_switches": 0,
            "provider_fallbacks": 0,
            "memory_contexts": 0,
            "file_operations": 0
        }
        
    def _init_mcp_services(self) -> Dict[str, MCPServiceConfig]:
        """Initialize MCP services with new port mapping"""
        return {
            "filesystem": MCPServiceConfig(
                name="Filesystem MCP",
                port=7001,
                tools=["file_read", "file_write", "file_list", "file_search", "file_analyze"],
                sage_modes=[SAGEMode.FILESYSTEM, SAGEMode.CODE, SAGEMode.DOCS],
                priority=1
            ),
            "git": MCPServiceConfig(
                name="Git MCP", 
                port=7002,
                tools=["git_status", "git_commit", "git_push", "git_log", "git_diff"],
                sage_modes=[SAGEMode.CODE],
                priority=1
            ),
            "terminal": MCPServiceConfig(
                name="Terminal MCP",
                port=7003,
                tools=["terminal_exec", "shell_command", "system_info", "create_terminal", "execute_command"],
                sage_modes=[SAGEMode.DEBUG, SAGEMode.TERMINAL],
                priority=1
            ),
            "database": MCPServiceConfig(
                name="Database MCP",
                port=7004,
                tools=["db_query", "db_connect", "db_schema", "db_backup"],
                sage_modes=[SAGEMode.ANALYZE],
                priority=1
            ),
            "memory": MCPServiceConfig(
                name="Memory MCP",
                port=7005,
                tools=["store_memory", "search_memories", "get_context", "memory_stats", "list_memories"],
                sage_modes=[SAGEMode.MEMORY, SAGEMode.CHAT],
                priority=1
            ),
            "research": MCPServiceConfig(
                name="Research MCP",
                port=7011,
                tools=["research_query", "perplexity_search", "web_search", "search_web"],
                sage_modes=[SAGEMode.ANALYZE, SAGEMode.DOCS],
                priority=1
            ),
            "advanced_memory": MCPServiceConfig(
                name="Advanced Memory MCP",
                port=7012,
                tools=["vector_search", "semantic_similarity"],
                sage_modes=[SAGEMode.MEMORY, SAGEMode.ANALYZE],
                priority=2
            ),
            "advanced_memory_v2": MCPServiceConfig(
                name="Advanced Memory v2",
                port=7015,
                tools=["conversation_thread", "file_deduplication", "context_continuation"],
                sage_modes=[SAGEMode.MEMORY, SAGEMode.CHAT],
                priority=3
            ),
            "transcriber": MCPServiceConfig(
                name="Transcriber MCP",
                port=7013,
                tools=["transcribe_webm", "transcribe_url", "audio_convert"],
                sage_modes=[SAGEMode.ANALYZE],
                priority=2,
                timeout=60  # Longer timeout for transcription
            ),
            "video_processing": MCPServiceConfig(
                name="Video Processing MCP",
                port=7016,
                tools=["process_video", "extract_frames", "video_analysis"],
                sage_modes=[SAGEMode.ANALYZE],
                priority=2,
                timeout=120
            )
        }

    async def initialize(self):
        """Initialize Mega Orchestrator with all components"""
        logging.info(f"🚀 Initializing Mega Orchestrator v{self.version} ({'BACKUP' if self.backup_mode else 'PRIMARY'})")
        
        try:
            # Initialize infrastructure
            await self._init_infrastructure()
            
            # Initialize core components
            await self._init_components()
            
            # Initialize web application
            self._init_web_app()
            
            # Start background tasks
            await self._start_background_tasks()
            
            # Health check all services
            await self._initial_health_check()
            
            logging.info(f"✅ Mega Orchestrator initialized successfully on port {self.port}")
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize Mega Orchestrator: {e}")
            raise
            
    async def _init_infrastructure(self):
        """Initialize Redis and PostgreSQL connections"""
        # Connect to Redis
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        self.redis = aioredis.from_url(redis_url)
        await self.redis.ping()
        logging.info(f"✅ Redis connection established: {redis_url}")
        
        # Connect to PostgreSQL
        db_url = os.getenv("MCP_DATABASE_URL", "postgresql://mcp_admin:change_me_in_production@postgresql:5432/mcp_unified")
        
        self.db_pool = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
        logging.info("✅ PostgreSQL connection pool established")
        
    async def _init_components(self):
        """Initialize all core components"""
        # Initialize Provider Registry
        self.provider_registry = await initialize_provider_registry()
        available_providers = self.provider_registry.get_available_providers_with_keys()
        logging.info(f"✅ Provider Registry: {len(available_providers)} providers available: {available_providers}")
        
        # Initialize Conversation Memory
        await self.conversation_memory.initialize(self.db_pool, self.redis)
        logging.info("✅ Conversation Memory System initialized")
        
        logging.info("✅ File Storage System initialized")
        logging.info("✅ SAGE Mode Router initialized")
        
    def _init_web_app(self):
        """Initialize web application with all routes"""
        self.app = web.Application()
        
        # Core MCP routes
        self.app.router.add_post('/mcp', self._handle_mcp_request)
        self.app.router.add_post('/mcp/{service}', self._handle_direct_service_request)
        
        # Information routes
        self.app.router.add_get('/health', self._handle_health)
        self.app.router.add_get('/services', self._handle_services)
        self.app.router.add_get('/tools/list', self._handle_tools_list)
        self.app.router.add_get('/status', self._handle_status)
        self.app.router.add_get('/stats', self._handle_stats)
        
        # Management routes
        self.app.router.add_get('/providers', self._handle_providers)
        self.app.router.add_get('/modes', self._handle_modes)
        self.app.router.add_get('/memory/stats', self._handle_memory_stats)
        self.app.router.add_get('/files/stats', self._handle_file_stats)
        
        # Debug routes
        self.app.router.add_get('/debug/cache', self._handle_debug_cache)
        self.app.router.add_get('/debug/contexts/{session_id}', self._handle_debug_contexts)
        
        logging.info("✅ Web application routes initialized")
        
    async def _start_background_tasks(self):
        """Start background maintenance tasks"""
        # Statistics update task
        asyncio.create_task(self._update_stats_task())
        
        # Health monitoring task
        asyncio.create_task(self._health_monitoring_task())
        
        logging.info("✅ Background tasks started")
        
    async def _initial_health_check(self):
        """Perform initial health check of all services"""
        health_results = await self._check_all_services_health()
        
        healthy_count = sum(1 for status in health_results.values() if status.get("status") == "healthy")
        total_count = len(self.services)
        
        logging.info(f"🔍 Initial health check: {healthy_count}/{total_count} services healthy")
        
        if healthy_count < total_count // 2:
            logging.warning("⚠️ Less than 50% of services are healthy!")
            
    # ============================================================================
    # CORE REQUEST HANDLING
    # ============================================================================
            
    async def _handle_mcp_request(self, request):
        """Handle intelligent MCP request with SAGE routing"""
        try:
            data = await request.json()
            tool = data.get("tool")
            arguments = data.get("arguments", {})
            mode = data.get("mode")
            session_id = data.get("session_id")
            context_id = data.get("context_id")
            
            if not tool:
                return web.json_response({"error": "Tool name required"}, status=400)
                
            # Detect SAGE mode if not provided
            if mode:
                try:
                    sage_mode = SAGEMode(mode)
                except ValueError:
                    sage_mode = self.sage_router.detect_mode(tool, arguments)
            else:
                sage_mode = self.sage_router.detect_mode(tool, arguments)
                
            # Route request with enhanced processing
            result = await self._route_enhanced_request(
                tool=tool,
                arguments=arguments,
                mode=sage_mode,
                session_id=session_id,
                context_id=context_id
            )
            
            self.stats["requests_processed"] += 1
            
            return web.json_response(result)
            
        except Exception as e:
            logging.error(f"Error handling MCP request: {e}")
            return web.json_response({"error": str(e)}, status=500)
            
    async def _route_enhanced_request(self, tool: str, arguments: Dict[str, Any],
                                    mode: SAGEMode, session_id: Optional[str] = None,
                                    context_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced request routing with full integration"""
        
        # Store request in conversation memory
        if not context_id:
            service_name = self._get_service_for_tool(tool, mode)
            context_id = await self.conversation_memory.store_request(
                tool=tool,
                args=arguments,
                mode=mode.value,
                service=service_name or "unknown",
                session_id=session_id
            )
            self.stats["memory_contexts"] += 1
            
        # Process file content if present
        arguments = await self._process_file_arguments(arguments)
        
        # Get service with fallback logic
        service_name = self._get_service_for_tool(tool, mode)
        if not service_name:
            return {"error": f"No service found for tool: {tool} in mode: {mode.value}"}
            
        service = self.services[service_name]
        
        # Attempt primary service call
        result = await self._call_mcp_service_with_retry(service, tool, arguments, context_id)
        
        # If primary failed, try fallback services
        if "error" in result and service.priority == 1:
            fallback_services = [s for s in self.services.values() 
                               if tool in (s.tools or []) and s.priority > 1]
            
            for fallback_service in sorted(fallback_services, key=lambda x: x.priority):
                logging.info(f"Trying fallback service: {fallback_service.name}")
                fallback_result = await self._call_mcp_service_with_retry(
                    fallback_service, tool, arguments, context_id)
                
                if "error" not in fallback_result:
                    result = fallback_result
                    self.stats["provider_fallbacks"] += 1
                    break
                    
        # Store response in conversation memory
        await self.conversation_memory.store_response(context_id, result)
        
        # Add metadata to response
        result["_meta"] = {
            "context_id": context_id,
            "mode": mode.value,
            "service": service_name,
            "timestamp": time.time(),
            "orchestrator": "mega",
            "version": self.version
        }
        
        return result
        
    def _get_service_for_tool(self, tool: str, mode: SAGEMode) -> Optional[str]:
        """Find appropriate service based on tool and SAGE mode"""
        # Primary: tool + mode match
        for service_name, config in self.services.items():
            if tool in (config.tools or []) and mode in (config.sage_modes or []):
                return service_name
                
        # Fallback: tool match only
        for service_name, config in self.services.items():
            if tool in (config.tools or []):
                return service_name
                
        return None
        
    async def _process_file_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Process file-related arguments with enhanced file handling"""
        processed_args = arguments.copy()
        
        # Check for file_path argument
        if "file_path" in arguments:
            try:
                file_path = arguments["file_path"]
                processed_file = await self.file_storage.process_file(
                    file_path, 
                    FileHandlingMode.AUTO,
                    max_tokens=4000
                )
                
                # Replace or enhance arguments based on processing mode
                processed_args["_file_metadata"] = asdict(processed_file.metadata)
                
                if processed_file.content:
                    processed_args["file_content"] = processed_file.content
                elif processed_file.summary:
                    processed_args["file_summary"] = processed_file.summary
                elif processed_file.references:
                    processed_args["file_references"] = processed_file.references
                    
                self.stats["file_operations"] += 1
                
            except Exception as e:
                logging.warning(f"File processing error: {e}")
                processed_args["_file_error"] = str(e)
                
        return processed_args
        
    async def _call_mcp_service_with_retry(self, service: MCPServiceConfig, 
                                         tool: str, arguments: Dict[str, Any],
                                         context_id: str) -> Dict[str, Any]:
        """Call MCP service with retry logic and enhanced error handling"""
        
        for attempt in range(service.retry_count):
            try:
                url = f"http://localhost:{service.port}/mcp"
                payload = {
                    "tool": tool,
                    "arguments": arguments,
                    "context_id": context_id,
                    "_orchestrator": "mega",
                    "_version": self.version
                }
                
                timeout = aiohttp.ClientTimeout(total=service.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, json=payload) as response:
                        if response.status == 200:
                            result = await response.json()
                            return result
                        else:
                            error_text = await response.text()
                            error_msg = f"Service {service.name} returned {response.status}: {error_text}"
                            
                            if attempt < service.retry_count - 1:
                                logging.warning(f"{error_msg} (attempt {attempt + 1}/{service.retry_count})")
                                await asyncio.sleep(0.5 * (attempt + 1))  # Exponential backoff
                                continue
                            else:
                                return {"error": error_msg, "service": service.name}
                                
            except asyncio.TimeoutError:
                error_msg = f"Service {service.name} timeout after {service.timeout}s"
                if attempt < service.retry_count - 1:
                    logging.warning(f"{error_msg} (attempt {attempt + 1}/{service.retry_count})")
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                else:
                    return {"error": error_msg, "service": service.name}
                    
            except Exception as e:
                error_msg = f"Service {service.name} error: {str(e)}"
                if attempt < service.retry_count - 1:
                    logging.warning(f"{error_msg} (attempt {attempt + 1}/{service.retry_count})")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                else:
                    return {"error": error_msg, "service": service.name}
                    
        return {"error": f"Service {service.name} failed after {service.retry_count} attempts"}

    # ============================================================================
    # WEB ROUTE HANDLERS  
    # ============================================================================
    
    async def _handle_direct_service_request(self, request):
        """Handle direct service request bypass"""
        service_name = request.match_info['service']
        
        if service_name not in self.services:
            return web.json_response({"error": f"Service {service_name} not found"}, status=404)
            
        try:
            data = await request.json()
            service = self.services[service_name]
            
            result = await self._call_mcp_service_with_retry(
                service, 
                data.get("tool"), 
                data.get("arguments", {}),
                data.get("context_id", "direct")
            )
            
            return web.json_response(result)
            
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)
            
    async def _handle_health(self, request):
        """Enhanced health check with detailed service status"""
        health_data = {
            "orchestrator": "mega",
            "version": self.version,
            "build_date": self.build_date,
            "status": "healthy",
            "port": self.port,
            "backup_mode": self.backup_mode,
            "timestamp": time.time(),
            "uptime": time.time() - self.stats["startup_time"]
        }
        
        # Check infrastructure
        try:
            await self.redis.ping()
            health_data["redis"] = "healthy"
        except:
            health_data["redis"] = "unhealthy"
            health_data["status"] = "degraded"
            
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            health_data["database"] = "healthy" 
        except:
            health_data["database"] = "unhealthy"
            health_data["status"] = "degraded"
            
        # Check MCP services
        service_health = await self._check_all_services_health()
        health_data["services"] = service_health
        
        healthy_services = sum(1 for s in service_health.values() if s.get("status") == "healthy")
        total_services = len(service_health)
        
        health_data["service_summary"] = {
            "healthy": healthy_services,
            "total": total_services,
            "percentage": round((healthy_services / total_services) * 100, 1) if total_services > 0 else 0
        }
        
        if healthy_services < total_services * 0.7:
            health_data["status"] = "degraded"
            
        # Add component status
        health_data["components"] = {
            "provider_registry": len(self.provider_registry.get_available_providers_with_keys()) > 0,
            "conversation_memory": True,  # Always available if DB is up
            "file_storage": True,
            "sage_router": True
        }
        
        return web.json_response(health_data)
        
    async def _check_all_services_health(self) -> Dict[str, Dict[str, Any]]:
        """Check health of all MCP services"""
        health_results = {}
        
        for name, service in self.services.items():
            try:
                url = f"http://localhost:{service.port}{service.health_endpoint}"
                timeout = aiohttp.ClientTimeout(total=5)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            health_results[name] = {
                                "status": "healthy",
                                "port": service.port,
                                "response_time": response.headers.get("response-time", "unknown")
                            }
                        else:
                            health_results[name] = {
                                "status": "unhealthy",
                                "port": service.port,
                                "error": f"HTTP {response.status}"
                            }
            except Exception as e:
                health_results[name] = {
                    "status": "unreachable", 
                    "port": service.port,
                    "error": str(e)
                }
                
        return health_results
        
    async def _handle_services(self, request):
        """Return service information"""
        services_info = {}
        
        for name, config in self.services.items():
            services_info[name] = {
                "name": config.name,
                "port": config.port,
                "tools": config.tools or [],
                "sage_modes": [mode.value for mode in (config.sage_modes or [])],
                "priority": config.priority,
                "timeout": config.timeout
            }
            
        return web.json_response({
            "orchestrator": "mega",
            "version": self.version,
            "services": services_info,
            "total_services": len(services_info)
        })
        
    async def _handle_tools_list(self, request):
        """Return comprehensive tools list"""
        all_tools = {}
        
        for service_name, config in self.services.items():
            for tool in (config.tools or []):
                if tool not in all_tools:
                    all_tools[tool] = []
                    
                all_tools[tool].append({
                    "service": service_name,
                    "port": config.port,
                    "modes": [mode.value for mode in (config.sage_modes or [])],
                    "priority": config.priority
                })
                
        return web.json_response({
            "orchestrator": "mega",
            "version": self.version,
            "tools": all_tools,
            "total_tools": len(all_tools)
        })
        
    async def _handle_status(self, request):
        """Return comprehensive orchestrator status"""
        status = {
            "orchestrator": "mega",
            "version": self.version,
            "build_date": self.build_date,
            "port": self.port,
            "backup_mode": self.backup_mode,
            "uptime": time.time() - self.stats["startup_time"],
            "stats": self.stats.copy()
        }
        
        # Add component status
        status["components"] = {
            "provider_registry": self.provider_registry.get_status() if self.provider_registry else {},
            "conversation_memory": await self.conversation_memory.get_stats(),
            "file_storage": self.file_storage.get_cache_stats(),
            "sage_router": self.sage_router.get_mode_stats()
        }
        
        return web.json_response(status)
        
    async def _handle_stats(self, request):
        """Return detailed statistics"""
        return web.json_response(self.stats)
        
    async def _handle_providers(self, request):
        """Return provider registry information"""
        if self.provider_registry:
            return web.json_response(self.provider_registry.get_status())
        else:
            return web.json_response({"error": "Provider registry not initialized"})
            
    async def _handle_modes(self, request):
        """Return SAGE mode information"""
        modes_info = {}
        
        for mode in SAGEMode:
            config = self.sage_router.get_mode_config(mode)
            modes_info[mode.value] = {
                "name": config.name,
                "description": config.description,
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "preferred_providers": config.preferred_providers,
                "tool_patterns": config.tool_patterns
            }
            
        return web.json_response({
            "modes": modes_info,
            "stats": self.sage_router.get_mode_stats()
        })
        
    async def _handle_memory_stats(self, request):
        """Return conversation memory statistics"""
        return web.json_response(await self.conversation_memory.get_stats())
        
    async def _handle_file_stats(self, request):
        """Return file storage statistics"""
        return web.json_response(self.file_storage.get_cache_stats())
        
    async def _handle_debug_cache(self, request):
        """Return debug cache information"""
        return web.json_response({
            "conversation_contexts": len(self.conversation_memory.contexts),
            "file_cache": len(self.file_storage.cache),
            "service_count": len(self.services),
            "provider_count": len(self.provider_registry.providers) if self.provider_registry else 0
        })
        
    async def _handle_debug_contexts(self, request):
        """Return conversation contexts for session"""
        session_id = request.match_info['session_id']
        
        contexts = await self.conversation_memory.get_conversation_thread(session_id, limit=20)
        
        return web.json_response({
            "session_id": session_id,
            "context_count": len(contexts),
            "contexts": [asdict(ctx) for ctx in contexts]
        })

    # ============================================================================
    # BACKGROUND TASKS
    # ============================================================================
    
    async def _update_stats_task(self):
        """Background task to update statistics"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                
                # Update memory context count
                self.stats["memory_contexts"] = len(self.conversation_memory.contexts)
                
            except Exception as e:
                logging.error(f"Error updating stats: {e}")
                
    async def _health_monitoring_task(self):
        """Background task for health monitoring"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                health_results = await self._check_all_services_health()
                unhealthy_services = [name for name, status in health_results.items() 
                                    if status.get("status") != "healthy"]
                
                if unhealthy_services:
                    logging.warning(f"Unhealthy services detected: {unhealthy_services}")
                    
            except Exception as e:
                logging.error(f"Error in health monitoring: {e}")

    async def run(self):
        """Run the Mega Orchestrator"""
        await self.initialize()
        
        logging.info(f"🚀 Starting Mega Orchestrator on port {self.port}")
        logging.info(f"📊 Health check: http://localhost:{self.port}/health")
        logging.info(f"🛠️  Services: http://localhost:{self.port}/services")
        logging.info(f"📋 Tools: http://localhost:{self.port}/tools/list")
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logging.info(f"✅ Mega Orchestrator running on port {self.port}")
        
        # Keep running
        try:
            while True:
                await asyncio.sleep(3600)
        except KeyboardInterrupt:
            logging.info("🛑 Shutting down Mega Orchestrator...")
            await runner.cleanup()

async def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Check if running in backup mode
    backup_mode = os.getenv("BACKUP_MODE", "false").lower() == "true"
    port = 7999 if backup_mode else 7000
    
    orchestrator = MegaOrchestrator(port=port, backup_mode=backup_mode)
    await orchestrator.run()

if __name__ == "__main__":
    asyncio.run(main())
