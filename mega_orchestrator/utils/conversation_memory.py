#!/usr/bin/env python3
"""
🚀 MEGA ORCHESTRATOR - CONVERSATION MEMORY SYSTEM
Adaptace David Strejc's conversation memory pro náš MCP systém

Features:
- Cross-tool conversation threading
- File deduplication across tools
- Conversation persistence & timeout
- Thread continuation capabilities
- Memory across MCP service calls
"""

import asyncio
import logging
import hashlib
import secrets
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncpg
import redis.asyncio as aioredis
from pathlib import Path

@dataclass
class ConversationContext:
    """Context for conversation thread"""
    context_id: str
    session_id: str
    tool: str
    service: str
    mode: str
    timestamp: float
    request_data: Dict[str, Any]
    response_data: Optional[Dict[str, Any]] = None
    file_hashes: List[str] = None
    parent_context: Optional[str] = None
    
@dataclass
class FileReference:
    """Reference to file content with deduplication"""
    file_hash: str
    file_path: str
    content_snippet: str
    full_content_available: bool
    last_accessed: float
    access_count: int
    
class ConversationMemory:
    """
    Cross-MCP conversation memory system
    
    Inspirováno David Strejc's conversation_memory.py
    Rozšířeno pro MCP orchestration needs
    """
    
    def __init__(self):
        self.db_pool: Optional[asyncpg.Pool] = None
        self.redis: Optional[aioredis.Redis] = None
        self.contexts: Dict[str, ConversationContext] = {}
        self.file_cache: Dict[str, FileReference] = {}
        self.session_threads: Dict[str, List[str]] = {}
        self.cleanup_interval = 3600  # 1 hour
        
    async def initialize(self, db_pool: asyncpg.Pool, redis: aioredis.Redis):
        """Initialize conversation memory system"""
        self.db_pool = db_pool
        self.redis = redis
        
        await self._create_tables()
        await self._load_active_contexts()
        
        # Start cleanup task
        asyncio.create_task(self._cleanup_expired_contexts())
        
        logging.info("✅ Conversation Memory System initialized")
        
    async def _create_tables(self):
        """Create necessary database tables"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS conversation_contexts (
                    context_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    tool TEXT NOT NULL,
                    service TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    request_data JSONB NOT NULL,
                    response_data JSONB,
                    file_hashes TEXT[],
                    parent_context TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS file_references (
                    file_hash TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    content_snippet TEXT NOT NULL,
                    full_content_available BOOLEAN DEFAULT TRUE,
                    last_accessed REAL NOT NULL,
                    access_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_contexts_session 
                ON conversation_contexts(session_id, timestamp)
            ''')
            
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_contexts_tool 
                ON conversation_contexts(tool, timestamp)
            ''')
            
    async def _load_active_contexts(self):
        """Load active contexts from database"""
        async with self.db_pool.acquire() as conn:
            # Load contexts from last 24 hours
            cutoff_time = time.time() - 86400
            
            rows = await conn.fetch('''
                SELECT * FROM conversation_contexts 
                WHERE timestamp > $1 
                ORDER BY timestamp DESC
            ''', cutoff_time)
            
            for row in rows:
                context = ConversationContext(
                    context_id=row['context_id'],
                    session_id=row['session_id'],
                    tool=row['tool'],
                    service=row['service'],
                    mode=row['mode'],
                    timestamp=row['timestamp'],
                    request_data=dict(row['request_data']),
                    response_data=dict(row['response_data']) if row['response_data'] else None,
                    file_hashes=list(row['file_hashes']) if row['file_hashes'] else [],
                    parent_context=row['parent_context']
                )
                
                self.contexts[context.context_id] = context
                
                # Update session threads
                if context.session_id not in self.session_threads:
                    self.session_threads[context.session_id] = []
                self.session_threads[context.session_id].append(context.context_id)
                
        logging.info(f"Loaded {len(self.contexts)} active conversation contexts")
        
    async def store_request(self, tool: str, args: Dict[str, Any], 
                          mode: str, service: str, 
                          session_id: Optional[str] = None) -> str:
        """
        Store request context and return context_id
        """
        # Generate context ID
        context_id = self._generate_context_id(tool, args, session_id)
        
        # Use session_id or generate one
        if not session_id:
            session_id = self._generate_session_id()
            
        # Check for file content and deduplicate
        file_hashes = await self._process_file_content(args)
        
        # Find parent context (last context in session)
        parent_context = None
        if session_id in self.session_threads and self.session_threads[session_id]:
            parent_context = self.session_threads[session_id][-1]
            
        # Create context
        context = ConversationContext(
            context_id=context_id,
            session_id=session_id,
            tool=tool,
            service=service,
            mode=mode,
            timestamp=time.time(),
            request_data=args,
            file_hashes=file_hashes,
            parent_context=parent_context
        )
        
        # Store in memory and database
        self.contexts[context_id] = context
        await self._persist_context(context)
        
        # Update session threads
        if session_id not in self.session_threads:
            self.session_threads[session_id] = []
        self.session_threads[session_id].append(context_id)
        
        # Store in Redis for quick access
        await self.redis.setex(
            f"context:{context_id}",
            3600,  # 1 hour TTL
            json.dumps(asdict(context), default=str)
        )
        
        logging.debug(f"Stored request context: {context_id}")
        return context_id
        
    async def store_response(self, context_id: str, response_data: Dict[str, Any]):
        """Store response data for context"""
        if context_id not in self.contexts:
            logging.warning(f"Context {context_id} not found for response storage")
            return
            
        context = self.contexts[context_id]
        context.response_data = response_data
        
        # Update database
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                UPDATE conversation_contexts 
                SET response_data = $1 
                WHERE context_id = $2
            ''', json.dumps(response_data), context_id)
            
        # Update Redis
        await self.redis.setex(
            f"context:{context_id}",
            3600,
            json.dumps(asdict(context), default=str)
        )
        
        logging.debug(f"Stored response for context: {context_id}")
        
    async def get_conversation_thread(self, session_id: str, 
                                    limit: int = 10) -> List[ConversationContext]:
        """Get conversation thread for session"""
        if session_id not in self.session_threads:
            return []
            
        context_ids = self.session_threads[session_id][-limit:]
        contexts = []
        
        for context_id in context_ids:
            if context_id in self.contexts:
                contexts.append(self.contexts[context_id])
            else:
                # Try to load from database
                context = await self._load_context_from_db(context_id)
                if context:
                    contexts.append(context)
                    self.contexts[context_id] = context
                    
        return contexts
        
    async def get_related_contexts(self, tool: str, mode: str, 
                                 limit: int = 5) -> List[ConversationContext]:
        """Get contexts related by tool and mode"""
        related = []
        
        for context in self.contexts.values():
            if context.tool == tool or context.mode == mode:
                related.append(context)
                
        # Sort by timestamp (most recent first)
        related.sort(key=lambda x: x.timestamp, reverse=True)
        return related[:limit]
        
    async def deduplicate_file_content(self, file_path: str, 
                                     content: str) -> Tuple[str, bool]:
        """
        Deduplicate file content and return hash + whether it's new
        """
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        
        if file_hash in self.file_cache:
            # Update access statistics
            self.file_cache[file_hash].last_accessed = time.time()
            self.file_cache[file_hash].access_count += 1
            
            # Update database
            async with self.db_pool.acquire() as conn:
                await conn.execute('''
                    UPDATE file_references 
                    SET last_accessed = $1, access_count = access_count + 1
                    WHERE file_hash = $2
                ''', time.time(), file_hash)
                
            return file_hash, False
            
        # New content - store reference
        snippet = content[:500] + "..." if len(content) > 500 else content
        
        file_ref = FileReference(
            file_hash=file_hash,
            file_path=file_path,
            content_snippet=snippet,
            full_content_available=True,
            last_accessed=time.time(),
            access_count=1
        )
        
        self.file_cache[file_hash] = file_ref
        
        # Store in database
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO file_references 
                (file_hash, file_path, content_snippet, full_content_available, 
                 last_accessed, access_count)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (file_hash) DO NOTHING
            ''', file_hash, file_path, snippet, True, time.time(), 1)
            
        return file_hash, True
        
    async def _process_file_content(self, args: Dict[str, Any]) -> List[str]:
        """Process and deduplicate file content from arguments"""
        file_hashes = []
        
        # Look for file content in various argument patterns
        content_keys = ['content', 'file_content', 'data', 'text']
        path_keys = ['file_path', 'path', 'filename']
        
        for content_key in content_keys:
            if content_key in args and isinstance(args[content_key], str):
                content = args[content_key]
                
                # Try to find corresponding path
                file_path = "unknown"
                for path_key in path_keys:
                    if path_key in args:
                        file_path = args[path_key]
                        break
                        
                file_hash, is_new = await self.deduplicate_file_content(file_path, content)
                file_hashes.append(file_hash)
                
                if not is_new:
                    # Replace content with hash reference to save space
                    args[f"{content_key}_hash"] = file_hash
                    args[content_key] = f"[DEDUPLICATED:{file_hash[:8]}...]"
                    
        return file_hashes
        
    def _generate_context_id(self, tool: str, args: Dict[str, Any], 
                           session_id: Optional[str] = None) -> str:
        """Generate unique context ID"""
        return secrets.token_hex(16)
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        return secrets.token_hex(8)
        
    async def _persist_context(self, context: ConversationContext):
        """Persist context to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO conversation_contexts
                (context_id, session_id, tool, service, mode, timestamp,
                 request_data, response_data, file_hashes, parent_context)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (context_id) DO NOTHING
            ''', context.context_id, context.session_id, context.tool,
                 context.service, context.mode, context.timestamp,
                 json.dumps(context.request_data), 
                 json.dumps(context.response_data) if context.response_data else None,
                 context.file_hashes, context.parent_context)
                 
    async def _load_context_from_db(self, context_id: str) -> Optional[ConversationContext]:
        """Load context from database"""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM conversation_contexts WHERE context_id = $1
            ''', context_id)
            
            if row:
                return ConversationContext(
                    context_id=row['context_id'],
                    session_id=row['session_id'],
                    tool=row['tool'],
                    service=row['service'],
                    mode=row['mode'],
                    timestamp=row['timestamp'],
                    request_data=dict(row['request_data']),
                    response_data=dict(row['response_data']) if row['response_data'] else None,
                    file_hashes=list(row['file_hashes']) if row['file_hashes'] else [],
                    parent_context=row['parent_context']
                )
        return None
        
    async def _cleanup_expired_contexts(self):
        """Periodic cleanup of expired contexts"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                cutoff_time = time.time() - 86400  # 24 hours
                expired_contexts = [
                    cid for cid, ctx in self.contexts.items()
                    if ctx.timestamp < cutoff_time
                ]
                
                # Remove from memory
                for context_id in expired_contexts:
                    del self.contexts[context_id]
                    
                # Clean Redis
                if expired_contexts:
                    redis_keys = [f"context:{cid}" for cid in expired_contexts]
                    await self.redis.delete(*redis_keys)
                    
                # Clean database (keep for longer term)
                async with self.db_pool.acquire() as conn:
                    deleted_count = await conn.execute('''
                        DELETE FROM conversation_contexts 
                        WHERE timestamp < $1
                    ''', time.time() - 604800)  # 7 days
                    
                logging.info(f"Cleaned up {len(expired_contexts)} expired contexts")
                
            except Exception as e:
                logging.error(f"Error in context cleanup: {e}")
                
    async def get_stats(self) -> Dict[str, Any]:
        """Get conversation memory statistics"""
        return {
            "active_contexts": len(self.contexts),
            "active_sessions": len(self.session_threads),
            "file_cache_size": len(self.file_cache),
            "total_file_accesses": sum(ref.access_count for ref in self.file_cache.values()),
            "oldest_context": min((ctx.timestamp for ctx in self.contexts.values()), default=0),
            "newest_context": max((ctx.timestamp for ctx in self.contexts.values()), default=0)
        }
