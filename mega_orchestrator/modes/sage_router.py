#!/usr/bin/env python3
"""
🚀 MEGA ORCHESTRATOR - SAGE MODE ROUTER
Adaptace David Strejc's SAGE-MCP mode-based routing pro náš MCP systém

SAGE Modes:
- CHAT: Konverzační AI s vysokou kreativitou
- DEBUG: Debugování s precizní analýzou
- ANALYZE: Analýza dat a dokumentů
- MEMORY: Práce s pamětí a kontextem  
- CODE: Programování a refactoring
- DOCS: Dokumentace a vysvětlování
"""

import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class SAGEMode(Enum):
    """SAGE Mode types for intelligent routing"""
    CHAT = "chat"
    DEBUG = "debug" 
    ANALYZE = "analyze"
    MEMORY = "memory"
    CODE = "code"
    DOCS = "docs"
    TERMINAL = "terminal"
    FILESYSTEM = "filesystem"

@dataclass
class SAGEModeConfig:
    """Configuration for each SAGE mode"""
    name: str
    description: str
    temperature: float
    max_tokens: int
    preferred_providers: List[str]
    tool_patterns: List[str]
    keywords: List[str]
    
class SAGEModeRouter:
    """
    Intelligent mode-based routing system
    
    Inspirováno David Strejc's SAGE-MCP mode switching
    Adaptováno pro naše MCP orchestration
    """
    
    def __init__(self):
        self.modes = self._initialize_modes()
        self.mode_history: Dict[str, List[SAGEMode]] = {}
        self.tool_mode_cache: Dict[str, SAGEMode] = {}
        
    def _initialize_modes(self) -> Dict[SAGEMode, SAGEModeConfig]:
        """Initialize SAGE mode configurations"""
        return {
            SAGEMode.CHAT: SAGEModeConfig(
                name="Chat Mode",
                description="Conversational AI with high creativity",
                temperature=0.7,
                max_tokens=2048,
                preferred_providers=["anthropic", "openai", "google"],
                tool_patterns=["store_memory", "search_memories", "conversation"],
                keywords=["chat", "talk", "discuss", "conversation", "explain"]
            ),
            
            SAGEMode.DEBUG: SAGEModeConfig(
                name="Debug Mode", 
                description="Debugging with precise analysis",
                temperature=0.1,
                max_tokens=4096,
                preferred_providers=["anthropic", "openai", "ollama"],
                tool_patterns=["terminal_exec", "system_info", "shell_command", "debug"],
                keywords=["debug", "error", "bug", "fix", "troubleshoot", "analyze"]
            ),
            
            SAGEMode.ANALYZE: SAGEModeConfig(
                name="Analyze Mode",
                description="Data and document analysis", 
                temperature=0.3,
                max_tokens=4096,
                preferred_providers=["anthropic", "google", "openai"],
                tool_patterns=["file_read", "file_search", "research_query", "db_query"],
                keywords=["analyze", "research", "study", "examine", "investigate"]
            ),
            
            SAGEMode.MEMORY: SAGEModeConfig(
                name="Memory Mode",
                description="Working with memory and context",
                temperature=0.4,
                max_tokens=3072,
                preferred_providers=["anthropic", "openai", "google"],
                tool_patterns=["store_memory", "search_memories", "vector_search", "get_context"],
                keywords=["remember", "recall", "memory", "context", "history"]
            ),
            
            SAGEMode.CODE: SAGEModeConfig(
                name="Code Mode",
                description="Programming and refactoring",
                temperature=0.2,
                max_tokens=4096,
                preferred_providers=["anthropic", "openai", "ollama"],
                tool_patterns=["file_write", "git_commit", "git_push", "file_analyze"],
                keywords=["code", "program", "develop", "implement", "refactor"]
            ),
            
            SAGEMode.DOCS: SAGEModeConfig(
                name="Docs Mode", 
                description="Documentation and explanation",
                temperature=0.5,
                max_tokens=3072,
                preferred_providers=["anthropic", "google", "openai"],
                tool_patterns=["file_write", "file_read", "research_query"],
                keywords=["document", "explain", "describe", "manual", "guide"]
            ),
            
            SAGEMode.TERMINAL: SAGEModeConfig(
                name="Terminal Mode",
                description="Command execution and system operations",
                temperature=0.1,
                max_tokens=2048, 
                preferred_providers=["anthropic", "openai", "ollama"],
                tool_patterns=["terminal_exec", "shell_command", "system_info"],
                keywords=["command", "execute", "run", "terminal", "shell"]
            ),
            
            SAGEMode.FILESYSTEM: SAGEModeConfig(
                name="Filesystem Mode",
                description="File operations and management", 
                temperature=0.2,
                max_tokens=3072,
                preferred_providers=["anthropic", "openai"],
                tool_patterns=["file_read", "file_write", "file_list", "file_search"],
                keywords=["file", "directory", "folder", "path", "filesystem"]
            )
        }
        
    def detect_mode(self, tool: str, args: Dict[str, Any], 
                   context: Optional[str] = None) -> SAGEMode:
        """
        Detect appropriate SAGE mode based on tool and context
        """
        # Check cache first
        if tool in self.tool_mode_cache:
            return self.tool_mode_cache[tool]
            
        # Primary tool-based detection
        for mode, config in self.modes.items():
            for pattern in config.tool_patterns:
                if pattern in tool:
                    self.tool_mode_cache[tool] = mode
                    return mode
                    
        # Context-based detection
        if context:
            detected_mode = self._detect_mode_from_context(context)
            if detected_mode:
                return detected_mode
                
        # Argument-based detection
        detected_mode = self._detect_mode_from_args(args)
        if detected_mode:
            return detected_mode
            
        # Default fallback
        return SAGEMode.CHAT
        
    def _detect_mode_from_context(self, context: str) -> Optional[SAGEMode]:
        """Detect mode from context string"""
        context_lower = context.lower()
        
        mode_scores = {}
        for mode, config in self.modes.items():
            score = 0
            for keyword in config.keywords:
                if keyword in context_lower:
                    score += 1
            if score > 0:
                mode_scores[mode] = score
                
        if mode_scores:
            return max(mode_scores, key=mode_scores.get)
        return None
        
    def _detect_mode_from_args(self, args: Dict[str, Any]) -> Optional[SAGEMode]:
        """Detect mode from arguments"""
        # Convert args to searchable text
        args_text = json.dumps(args, default=str).lower()
        
        for mode, config in self.modes.items():
            for keyword in config.keywords:
                if keyword in args_text:
                    return mode
                    
        return None
        
    def get_mode_config(self, mode: SAGEMode) -> SAGEModeConfig:
        """Get configuration for specific mode"""
        return self.modes.get(mode, self.modes[SAGEMode.CHAT])
        
    def get_provider_preferences(self, mode: SAGEMode) -> List[str]:
        """Get provider preferences for mode"""
        config = self.get_mode_config(mode)
        return config.preferred_providers
        
    def get_temperature(self, mode: SAGEMode) -> float:
        """Get temperature setting for mode"""
        config = self.get_mode_config(mode)
        return config.temperature
        
    def get_max_tokens(self, mode: SAGEMode) -> int:
        """Get max tokens for mode"""
        config = self.get_mode_config(mode)
        return config.max_tokens
        
    def should_switch_mode(self, current_mode: SAGEMode, tool: str, 
                          context: str = None) -> Tuple[bool, Optional[SAGEMode]]:
        """
        Determine if mode should be switched based on new context
        """
        suggested_mode = self.detect_mode(tool, {}, context)
        
        # Don't switch for similar modes  
        similar_modes = {
            SAGEMode.TERMINAL: [SAGEMode.DEBUG],
            SAGEMode.FILESYSTEM: [SAGEMode.CODE],
            SAGEMode.MEMORY: [SAGEMode.ANALYZE],
        }
        
        if current_mode in similar_modes:
            if suggested_mode in similar_modes[current_mode]:
                return False, None
                
        # Switch if significantly different
        if suggested_mode != current_mode:
            return True, suggested_mode
            
        return False, None
        
    def track_mode_usage(self, session_id: str, mode: SAGEMode):
        """Track mode usage for session"""
        if session_id not in self.mode_history:
            self.mode_history[session_id] = []
        self.mode_history[session_id].append(mode)
        
    def get_mode_stats(self, session_id: str = None) -> Dict[str, Any]:
        """Get mode usage statistics"""
        if session_id:
            modes = self.mode_history.get(session_id, [])
            return {
                "session_modes": [mode.value for mode in modes],
                "most_used": max(set(modes), key=modes.count).value if modes else None,
                "mode_switches": len(set(modes))
            }
        else:
            all_modes = []
            for session_modes in self.mode_history.values():
                all_modes.extend(session_modes)
            
            return {
                "total_sessions": len(self.mode_history),
                "total_mode_uses": len(all_modes),
                "mode_distribution": {
                    mode.value: all_modes.count(mode) for mode in SAGEMode
                }
            }
            
    def create_mode_prompt(self, mode: SAGEMode, base_prompt: str) -> str:
        """
        Create mode-specific prompt enhancement
        """
        config = self.get_mode_config(mode)
        
        mode_prompts = {
            SAGEMode.CHAT: "You are in conversational mode. Be friendly, creative, and engaging.",
            SAGEMode.DEBUG: "You are in debug mode. Be precise, analytical, and thorough in your analysis.",
            SAGEMode.ANALYZE: "You are in analysis mode. Focus on data interpretation and insights.",
            SAGEMode.MEMORY: "You are in memory mode. Consider context and conversation history.",
            SAGEMode.CODE: "You are in code mode. Focus on programming best practices and clean code.",
            SAGEMode.DOCS: "You are in documentation mode. Be clear, comprehensive, and educational.",
            SAGEMode.TERMINAL: "You are in terminal mode. Focus on command execution and system operations.",
            SAGEMode.FILESYSTEM: "You are in filesystem mode. Focus on file operations and management."
        }
        
        mode_enhancement = mode_prompts.get(mode, "")
        
        return f"{mode_enhancement}\n\n{base_prompt}"
        
    def optimize_for_mode(self, mode: SAGEMode, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimize request data based on SAGE mode
        """
        config = self.get_mode_config(mode)
        
        # Apply mode-specific optimizations
        optimized = request_data.copy()
        optimized["temperature"] = config.temperature
        optimized["max_tokens"] = config.max_tokens
        optimized["mode"] = mode.value
        optimized["preferred_providers"] = config.preferred_providers
        
        return optimized

# Global instance
sage_router = SAGEModeRouter()