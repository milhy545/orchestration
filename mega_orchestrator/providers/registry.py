#!/usr/bin/env python3
"""
🚀 MEGA ORCHESTRATOR - PROVIDER REGISTRY SYSTEM
Adaptace David Strejc's ModelProviderRegistry pro náš MCP systém

Features:
- Automatická detekce API klíčů
- Priority routing: Native APIs -> Custom -> OpenRouter  
- Smart fallback při nedostupnosti providerů
- Model restrictions pro cost control
- Singleton pattern pro provider management
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
import asyncpg
from mega_orchestrator.utils.secrets import load_secret

class ProviderType(Enum):
    """Types of AI providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai" 
    GOOGLE = "google"
    OPENROUTER = "openrouter"
    OLLAMA = "ollama"
    CUSTOM = "custom"

@dataclass
class ProviderConfig:
    """Configuration for AI provider"""
    name: str
    type: ProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: List[str] = None
    priority: int = 0
    restrictions: Dict[str, Any] = None
    health_endpoint: Optional[str] = None
    
class ModelProviderRegistry:
    """
    Singleton registry for AI model providers s automatickou detekcí
    
    Inspirováno David Strejc's zen-mcp-server Provider Registry
    Adaptováno pro naše MCP orchestration potřeby
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.providers: Dict[str, ProviderConfig] = {}
            self.fallback_chains: Dict[str, List[str]] = {}
            self.model_restrictions: Dict[str, Dict[str, Any]] = {}
            self.initialized = False
            
    async def initialize(self):
        """Initialize provider registry with auto-detection"""
        if self.initialized:
            return
            
        logging.info("🔍 Auto-detecting available AI providers...")
        
        # Auto-detect API keys from environment
        await self._detect_provider_keys()
        
        # Setup fallback chains
        self._setup_fallback_chains()
        
        # Load model restrictions
        await self._load_model_restrictions()
        
        # Test provider availability
        await self._test_provider_health()
        
        self.initialized = True
        logging.info(f"✅ Provider Registry initialized with {len(self.providers)} providers")
        
    async def _detect_provider_keys(self):
        """Automatická detekce API klíčů z prostředí"""

        def _is_real_secret(value: Optional[str]) -> bool:
            if not value:
                return False
            normalized = value.strip().lower()
            return normalized != "" and not normalized.startswith("your_")
        
        # Anthropic detection
        anthropic_key = load_secret("ANTHROPIC_API_KEY")
        if _is_real_secret(anthropic_key):
            self.providers["anthropic"] = ProviderConfig(
                name="Anthropic",
                type=ProviderType.ANTHROPIC,
                api_key=anthropic_key,
                base_url="https://api.anthropic.com/v1",
                models=["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
                priority=1,
                restrictions={"max_tokens": 4096, "cost_per_1k": 0.015}
            )
            
        # OpenAI detection  
        openai_key = load_secret("OPENAI_API_KEY")
        if _is_real_secret(openai_key):
            self.providers["openai"] = ProviderConfig(
                name="OpenAI",
                type=ProviderType.OPENAI,
                api_key=openai_key,
                base_url="https://api.openai.com/v1",
                models=["gpt-4", "gpt-4-turbo-preview", "gpt-3.5-turbo"],
                priority=1,
                restrictions={"max_tokens": 4096, "cost_per_1k": 0.02}
            )
            
        # Google/Gemini detection
        gemini_key = load_secret("GEMINI_API_KEY") or load_secret("GOOGLE_API_KEY")
        if _is_real_secret(gemini_key):
            self.providers["google"] = ProviderConfig(
                name="Google",
                type=ProviderType.GOOGLE,
                api_key=gemini_key,
                base_url="https://generativelanguage.googleapis.com/v1beta",
                models=["gemini-pro", "gemini-pro-vision"],
                priority=1,
                restrictions={"max_tokens": 2048, "cost_per_1k": 0.01}
            )
            
        # OpenRouter detection (fallback provider)
        openrouter_key = load_secret("OPENROUTER_API_KEY")
        if _is_real_secret(openrouter_key):
            self.providers["openrouter"] = ProviderConfig(
                name="OpenRouter", 
                type=ProviderType.OPENROUTER,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                models=["anthropic/claude-3-sonnet", "openai/gpt-4", "google/gemini-pro"],
                priority=3,  # Lower priority = fallback
                restrictions={"max_tokens": 4096, "cost_per_1k": 0.025}
            )
            
        # OLLAMA detection (local models)
        if await self._test_ollama_connection():
            self.providers["ollama"] = ProviderConfig(
                name="OLLAMA Local",
                type=ProviderType.OLLAMA,
                base_url="http://192.168.0.41:11434/api",
                models=["llama2", "codellama", "mistral"],
                priority=2,
                restrictions={"max_tokens": 2048, "cost_per_1k": 0.0},
                health_endpoint="http://192.168.0.41:11434/api/tags"
            )
            
    async def _test_ollama_connection(self) -> bool:
        """Test OLLAMA server connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://192.168.0.41:11434/api/tags", timeout=5) as response:
                    return response.status == 200
        except:
            return False
            
    def _setup_fallback_chains(self):
        """Setup provider fallback chains"""
        self.fallback_chains = {
            "chat": ["anthropic", "openai", "google", "openrouter", "ollama"],
            "code": ["anthropic", "openai", "ollama", "openrouter"],
            "analyze": ["anthropic", "google", "openai", "openrouter"],
            "debug": ["anthropic", "openai", "ollama"],
            "memory": ["anthropic", "openai", "google"],
            "docs": ["anthropic", "google", "openai", "openrouter"]
        }
        
    async def _load_model_restrictions(self):
        """Load model restrictions pro cost control"""
        self.model_restrictions = {
            "claude-3-opus-20240229": {
                "max_requests_per_hour": 50,
                "max_tokens_per_request": 4096,
                "cost_alert_threshold": 10.0
            },
            "gpt-4": {
                "max_requests_per_hour": 100,
                "max_tokens_per_request": 4096,
                "cost_alert_threshold": 15.0
            },
            "gemini-pro": {
                "max_requests_per_hour": 200,
                "max_tokens_per_request": 2048,
                "cost_alert_threshold": 5.0
            }
        }
        
    async def _test_provider_health(self):
        """Test health of all providers"""
        for name, provider in self.providers.items():
            try:
                if provider.health_endpoint:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(provider.health_endpoint, timeout=5) as response:
                            if response.status == 200:
                                logging.info(f"✅ {provider.name} provider healthy")
                            else:
                                logging.warning(f"⚠️ {provider.name} provider unhealthy")
                else:
                    # Test with simple request for providers without health endpoint
                    if await self._test_provider_request(provider):
                        logging.info(f"✅ {provider.name} provider healthy")
                    else:
                        logging.warning(f"⚠️ {provider.name} provider unhealthy")
            except Exception as e:
                logging.error(f"❌ {provider.name} provider failed: {e}")
                
    async def _test_provider_request(self, provider: ProviderConfig) -> bool:
        """Test provider with simple request"""
        # Implementation would depend on provider type
        # For now, just return True if we have API key
        return provider.api_key is not None
        
    def get_available_providers_with_keys(self) -> List[str]:
        """Get list of providers with valid API keys"""
        return [name for name, provider in self.providers.items() 
                if provider.api_key or provider.type == ProviderType.OLLAMA]
                
    def get_provider_for_mode(self, mode: str, exclude: List[str] = None) -> Optional[ProviderConfig]:
        """Get best provider for SAGE mode s fallback logic"""
        exclude = exclude or []
        
        fallback_chain = self.fallback_chains.get(mode, 
                        ["anthropic", "openai", "google", "openrouter", "ollama"])
        
        for provider_name in fallback_chain:
            if provider_name not in exclude and provider_name in self.providers:
                provider = self.providers[provider_name]
                if provider.api_key or provider.type == ProviderType.OLLAMA:
                    return provider
                    
        return None
        
    def get_status(self) -> Dict[str, Any]:
        """Get provider registry status"""
        return {
            "total_providers": len(self.providers),
            "available_providers": self.get_available_providers_with_keys(),
            "fallback_chains": self.fallback_chains,
            "restrictions": len(self.model_restrictions)
        }
        
    def check_model_restrictions(self, model: str, request_count: int = 1, 
                               tokens: int = 0) -> Tuple[bool, Optional[str]]:
        """Check if model request violates restrictions"""
        if model not in self.model_restrictions:
            return True, None
            
        restrictions = self.model_restrictions[model]
        
        # Check token limit
        if tokens > restrictions.get("max_tokens_per_request", float('inf')):
            return False, f"Token limit exceeded: {tokens} > {restrictions['max_tokens_per_request']}"
            
        # Additional checks could be implemented here
        return True, None
        
    async def route_request(self, mode: str, model: Optional[str] = None, 
                          exclude_providers: List[str] = None) -> Optional[ProviderConfig]:
        """
        Route request to best available provider
        s ohledem na mode, model preferences, a restrictions
        """
        exclude_providers = exclude_providers or []
        
        # If specific model requested, find provider that supports it
        if model:
            for provider in self.providers.values():
                if (model in provider.models and 
                    provider.name.lower() not in [p.lower() for p in exclude_providers]):
                    
                    # Check restrictions
                    allowed, reason = self.check_model_restrictions(model)
                    if allowed:
                        return provider
                    else:
                        logging.warning(f"Model {model} restricted: {reason}")
                        
        # Fallback to mode-based routing
        return self.get_provider_for_mode(mode, exclude_providers)

# Singleton instance
provider_registry = ModelProviderRegistry()

# Async initialization function
async def initialize_provider_registry():
    """Initialize the global provider registry"""
    await provider_registry.initialize()
    return provider_registry
