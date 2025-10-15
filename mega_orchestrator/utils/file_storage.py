#!/usr/bin/env python3
"""
🚀 MEGA ORCHESTRATOR - ENHANCED FILE STORAGE SYSTEM
Adaptace David Strejc's file handling pro náš MCP systém

Features:
- Inteligentní file chunking
- Token-aware content processing
- Multiple file handling modes (embedded/summary/reference)
- Secure path validation
- File deduplication and caching
"""

import os
import hashlib
import logging
import mimetypes
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import asyncio
import aiofiles
import json

class FileHandlingMode(Enum):
    """File processing modes"""
    EMBEDDED = "embedded"      # Full content embedded
    SUMMARY = "summary"        # Summarized content
    REFERENCE = "reference"    # Reference only
    AUTO = "auto"             # Automatic based on size

@dataclass
class FileMetadata:
    """File metadata with processing info"""
    path: str
    hash: str
    size: int
    mime_type: str
    encoding: str
    last_modified: float
    processing_mode: FileHandlingMode
    token_count: Optional[int] = None
    chunk_count: Optional[int] = None
    
@dataclass
class FileChunk:
    """File content chunk"""
    chunk_id: str
    file_hash: str
    sequence: int
    content: str
    token_count: int
    start_line: Optional[int] = None
    end_line: Optional[int] = None

@dataclass
class ProcessedFile:
    """Processed file with metadata and content"""
    metadata: FileMetadata
    content: Optional[str] = None
    summary: Optional[str] = None
    chunks: List[FileChunk] = None
    references: List[str] = None

class FileStorage:
    """
    Enhanced file storage system
    
    Inspirováno David Strejc's file_storage.py a file_utils.py
    Rozšířeno pro MCP orchestration needs
    """
    
    def __init__(self):
        self.max_embed_size = 50000  # Max size for embedded content
        self.max_chunk_size = 4000   # Max tokens per chunk
        self.supported_text_types = {
            'text/plain', 'text/markdown', 'text/x-python', 
            'text/javascript', 'application/json', 'text/html',
            'text/css', 'text/yaml', 'text/xml'
        }
        self.cache: Dict[str, ProcessedFile] = {}
        self.chunk_cache: Dict[str, List[FileChunk]] = {}
        
    async def process_file(self, file_path: str, 
                         mode: FileHandlingMode = FileHandlingMode.AUTO,
                         max_tokens: Optional[int] = None) -> ProcessedFile:
        """
        Process file according to specified mode
        """
        try:
            # Validate and normalize path
            normalized_path = await self._validate_path(file_path)
            if not normalized_path:
                raise ValueError(f"Invalid or inaccessible path: {file_path}")
                
            # Get file metadata
            metadata = await self._get_file_metadata(normalized_path, mode)
            
            # Check cache
            if metadata.hash in self.cache:
                cached = self.cache[metadata.hash]
                if cached.metadata.processing_mode == mode or mode == FileHandlingMode.AUTO:
                    return cached
                    
            # Determine processing mode
            if mode == FileHandlingMode.AUTO:
                mode = self._determine_auto_mode(metadata, max_tokens)
                metadata.processing_mode = mode
                
            # Process according to mode
            processed = await self._process_by_mode(normalized_path, metadata, mode, max_tokens)
            
            # Cache result
            self.cache[metadata.hash] = processed
            
            return processed
            
        except Exception as e:
            logging.error(f"Error processing file {file_path}: {e}")
            raise
            
    async def _validate_path(self, file_path: str) -> Optional[str]:
        """Validate and normalize file path for security"""
        try:
            path = Path(file_path).resolve()
            
            # Security checks
            if not path.exists():
                return None
                
            if not path.is_file():
                return None
                
            # Check if path is within allowed directories
            allowed_dirs = [
                Path("/home/milhy777"),
                Path("/tmp"),
                Path("/home/orchestration/data")
            ]
            
            if not any(str(path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
                logging.warning(f"Path outside allowed directories: {path}")
                return None
                
            return str(path)
            
        except Exception as e:
            logging.error(f"Path validation error: {e}")
            return None
            
    async def _get_file_metadata(self, file_path: str, 
                               mode: FileHandlingMode) -> FileMetadata:
        """Get comprehensive file metadata"""
        path = Path(file_path)
        stat = path.stat()
        
        # Calculate file hash
        file_hash = await self._calculate_file_hash(file_path)
        
        # Detect MIME type and encoding
        mime_type, encoding = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = await self._detect_mime_type(file_path)
            
        if not encoding:
            encoding = "utf-8"
            
        return FileMetadata(
            path=file_path,
            hash=file_hash,
            size=stat.st_size,
            mime_type=mime_type or "application/octet-stream",
            encoding=encoding,
            last_modified=stat.st_mtime,
            processing_mode=mode
        )
        
    async def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
                
        return hash_sha256.hexdigest()
        
    async def _detect_mime_type(self, file_path: str) -> str:
        """Detect MIME type by reading file content"""
        try:
            async with aiofiles.open(file_path, 'rb') as f:
                header = await f.read(1024)
                
            # Simple text detection
            try:
                header.decode('utf-8')
                return 'text/plain'
            except UnicodeDecodeError:
                return 'application/octet-stream'
                
        except Exception:
            return 'application/octet-stream'
            
    def _determine_auto_mode(self, metadata: FileMetadata, 
                           max_tokens: Optional[int] = None) -> FileHandlingMode:
        """Automatically determine processing mode"""
        # Binary files -> reference only
        if not self._is_text_file(metadata.mime_type):
            return FileHandlingMode.REFERENCE
            
        # Large files -> summary or chunking
        if metadata.size > self.max_embed_size:
            return FileHandlingMode.SUMMARY
            
        # Token limit considerations
        if max_tokens and metadata.size > max_tokens * 4:  # Rough tokens estimation
            return FileHandlingMode.SUMMARY
            
        return FileHandlingMode.EMBEDDED
        
    def _is_text_file(self, mime_type: str) -> bool:
        """Check if file is text-based"""
        return (
            mime_type in self.supported_text_types or
            mime_type.startswith('text/') or
            mime_type in ['application/json', 'application/javascript', 'application/xml']
        )
        
    async def _process_by_mode(self, file_path: str, metadata: FileMetadata,
                             mode: FileHandlingMode, max_tokens: Optional[int]) -> ProcessedFile:
        """Process file according to specified mode"""
        
        if mode == FileHandlingMode.EMBEDDED:
            return await self._process_embedded(file_path, metadata)
            
        elif mode == FileHandlingMode.SUMMARY:
            return await self._process_summary(file_path, metadata, max_tokens)
            
        elif mode == FileHandlingMode.REFERENCE:
            return await self._process_reference(file_path, metadata)
            
        else:
            raise ValueError(f"Unsupported processing mode: {mode}")
            
    async def _process_embedded(self, file_path: str, 
                              metadata: FileMetadata) -> ProcessedFile:
        """Process file with full content embedded"""
        if not self._is_text_file(metadata.mime_type):
            raise ValueError("Cannot embed binary file")
            
        async with aiofiles.open(file_path, 'r', encoding=metadata.encoding) as f:
            content = await f.read()
            
        # Estimate token count
        token_count = self._estimate_tokens(content)
        metadata.token_count = token_count
        
        return ProcessedFile(
            metadata=metadata,
            content=content
        )
        
    async def _process_summary(self, file_path: str, metadata: FileMetadata,
                             max_tokens: Optional[int]) -> ProcessedFile:
        """Process file with summarized content"""
        if not self._is_text_file(metadata.mime_type):
            return await self._process_reference(file_path, metadata)
            
        # Read and chunk content
        chunks = await self._create_chunks(file_path, metadata)
        
        # Create summary
        summary = await self._create_file_summary(file_path, metadata, chunks[:3])  # First 3 chunks
        
        metadata.chunk_count = len(chunks)
        metadata.token_count = sum(chunk.token_count for chunk in chunks)
        
        # Cache chunks
        self.chunk_cache[metadata.hash] = chunks
        
        return ProcessedFile(
            metadata=metadata,
            summary=summary,
            chunks=chunks if len(chunks) <= 5 else chunks[:5]  # Limit chunks in response
        )
        
    async def _process_reference(self, file_path: str, 
                               metadata: FileMetadata) -> ProcessedFile:
        """Process file as reference only"""
        # Generate file info without content
        references = [
            f"File: {metadata.path}",
            f"Size: {metadata.size:,} bytes",
            f"Type: {metadata.mime_type}",
            f"Modified: {metadata.last_modified}"
        ]
        
        if self._is_text_file(metadata.mime_type) and metadata.size < 10000:
            # Add snippet for small text files
            try:
                async with aiofiles.open(file_path, 'r', encoding=metadata.encoding) as f:
                    snippet = await f.read(500)
                    references.append(f"Snippet: {snippet[:200]}...")
            except:
                pass
                
        return ProcessedFile(
            metadata=metadata,
            references=references
        )
        
    async def _create_chunks(self, file_path: str, 
                           metadata: FileMetadata) -> List[FileChunk]:
        """Create intelligent file chunks"""
        chunks = []
        
        async with aiofiles.open(file_path, 'r', encoding=metadata.encoding) as f:
            content = await f.read()
            
        lines = content.split('\n')
        current_chunk = []
        current_tokens = 0
        chunk_sequence = 0
        
        for line_no, line in enumerate(lines):
            line_tokens = self._estimate_tokens(line)
            
            # Check if adding this line would exceed chunk size
            if current_tokens + line_tokens > self.max_chunk_size and current_chunk:
                # Create chunk from current content
                chunk_content = '\n'.join(current_chunk)
                chunk_id = f"{metadata.hash}_{chunk_sequence}"
                
                chunks.append(FileChunk(
                    chunk_id=chunk_id,
                    file_hash=metadata.hash,
                    sequence=chunk_sequence,
                    content=chunk_content,
                    token_count=current_tokens,
                    start_line=line_no - len(current_chunk),
                    end_line=line_no - 1
                ))
                
                chunk_sequence += 1
                current_chunk = []
                current_tokens = 0
                
            current_chunk.append(line)
            current_tokens += line_tokens
            
        # Handle remaining content
        if current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunk_id = f"{metadata.hash}_{chunk_sequence}"
            
            chunks.append(FileChunk(
                chunk_id=chunk_id,
                file_hash=metadata.hash,
                sequence=chunk_sequence,
                content=chunk_content,
                token_count=current_tokens,
                start_line=len(lines) - len(current_chunk),
                end_line=len(lines) - 1
            ))
            
        return chunks
        
    async def _create_file_summary(self, file_path: str, metadata: FileMetadata,
                                 sample_chunks: List[FileChunk]) -> str:
        """Create intelligent file summary"""
        path = Path(file_path)
        
        summary_parts = [
            f"File: {path.name}",
            f"Path: {metadata.path}",
            f"Size: {metadata.size:,} bytes ({len(sample_chunks)} chunks analyzed)",
            f"Type: {metadata.mime_type}"
        ]
        
        # Add content insights
        if sample_chunks:
            total_content = '\n'.join(chunk.content for chunk in sample_chunks)
            
            # Detect file type specific patterns
            if metadata.mime_type == 'text/x-python':
                summary_parts.extend(self._analyze_python_file(total_content))
            elif metadata.mime_type == 'application/json':
                summary_parts.extend(self._analyze_json_file(total_content))
            elif metadata.mime_type == 'text/markdown':
                summary_parts.extend(self._analyze_markdown_file(total_content))
            else:
                summary_parts.extend(self._analyze_generic_text(total_content))
                
        return '\n'.join(summary_parts)
        
    def _analyze_python_file(self, content: str) -> List[str]:
        """Analyze Python file content"""
        insights = []
        
        # Count functions and classes
        import_count = content.count('import ')
        function_count = content.count('def ')
        class_count = content.count('class ')
        
        insights.append(f"Python file with {class_count} classes, {function_count} functions, {import_count} imports")
        
        # Find main patterns
        if 'if __name__ == "__main__":' in content:
            insights.append("Executable script (has main block)")
            
        return insights
        
    def _analyze_json_file(self, content: str) -> List[str]:
        """Analyze JSON file content"""
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                return [f"JSON object with {len(data)} top-level keys: {', '.join(list(data.keys())[:5])}"]
            elif isinstance(data, list):
                return [f"JSON array with {len(data)} items"]
            else:
                return [f"JSON file containing {type(data).__name__}"]
        except:
            return ["JSON file (could not parse structure)"]
            
    def _analyze_markdown_file(self, content: str) -> List[str]:
        """Analyze Markdown file content"""
        insights = []
        
        header_count = content.count('#')
        code_block_count = content.count('```')
        
        insights.append(f"Markdown file with ~{header_count} headers, {code_block_count//2} code blocks")
        
        return insights
        
    def _analyze_generic_text(self, content: str) -> List[str]:
        """Analyze generic text content"""
        lines = len(content.split('\n'))
        words = len(content.split())
        
        return [f"Text file with {lines} lines, ~{words} words"]
        
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        # Rough estimation: 1 token ≈ 4 characters
        return len(text) // 4
        
    async def get_file_chunks(self, file_hash: str, 
                            start_chunk: int = 0, 
                            count: int = 5) -> List[FileChunk]:
        """Get specific chunks for a file"""
        if file_hash in self.chunk_cache:
            chunks = self.chunk_cache[file_hash]
            return chunks[start_chunk:start_chunk + count]
        return []
        
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get file storage cache statistics"""
        return {
            "cached_files": len(self.cache),
            "cached_chunks": sum(len(chunks) for chunks in self.chunk_cache.values()),
            "cache_size_estimate": sum(
                len(pf.content or '') + len(pf.summary or '') 
                for pf in self.cache.values()
            ),
            "processing_modes": {
                mode.value: sum(1 for pf in self.cache.values() 
                              if pf.metadata.processing_mode == mode)
                for mode in FileHandlingMode
            }
        }