#!/usr/bin/env python3
"""
ASGI entry point for Vercel deployment.
Wraps MegaOrchestrator as ASGI application.
"""

import asyncio
import logging
import os
from aiohttp import web

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Import the orchestrator
from mega_orchestrator.mega_orchestrator_complete import MegaOrchestrator


class ASGIOrchestratorWrapper:
    """Wraps MegaOrchestrator for ASGI/Vercel compatibility."""
    
    def __init__(self):
        self.orchestrator = None
        self.app = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize orchestrator and aiohttp app."""
        if self._initialized:
            return
        
        backup_mode = os.getenv("BACKUP_MODE", "false").lower() == "true"
        port = 7999 if backup_mode else 7000
        
        self.orchestrator = MegaOrchestrator(port=port, backup_mode=backup_mode)
        await self.orchestrator.initialize()
        
        # Return the app object for ASGI servers
        self.app = self.orchestrator.app
        self._initialized = True
        
        logging.info("✅ Orchestrator initialized for Vercel deployment")
    
    async def __call__(self, scope, receive, send):
        """ASGI interface."""
        if not self._initialized:
            await self.initialize()
        
        # Delegate to aiohttp app handler
        await self.app(scope, receive, send)


# Create wrapper instance
_wrapper = ASGIOrchestratorWrapper()


async def app(scope, receive, send):
    """ASGI application entry point for Vercel."""
    await _wrapper(scope, receive, send)


# For local testing with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
