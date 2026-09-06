"""Authenticated, least-privilege MCP gateway for Mega-Orchestrator."""

from .app import GatewayConfig, create_app

__all__ = ["GatewayConfig", "create_app"]
