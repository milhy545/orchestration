"""Exact chat transcript recall for archived conversations on HAS."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


DEFAULT_ARCHIVE_ROOT = "/home/chat-transcripts"
DEFAULT_CONTEXT_CHARS = 240


@dataclass(frozen=True)
class ArchiveDocument:
    archive_dir: Path
    text_path: Path
    manifest_path: Optional[Path]
    text: str
    manifest: Dict[str, Any]


class ChatRecall:
    """Search archived chat transcript text directly from the HAS archive mount."""

    def __init__(self, archive_root: Optional[str] = None) -> None:
        self.archive_root = Path(
            archive_root or os.getenv("CHAT_RECALL_ARCHIVE_ROOT", DEFAULT_ARCHIVE_ROOT)
        )

    def audit(self) -> Dict[str, Any]:
        root_exists = self.archive_root.exists()
        root_is_dir = self.archive_root.is_dir()
        transcript_files = list(self._iter_text_files()) if root_is_dir else []
        manifests = list(self.archive_root.glob("*/manifest.json")) if root_is_dir else []
        missing_manifests = [
            str(path.parent)
            for path in transcript_files
            if not (path.parent / "manifest.json").is_file()
        ]
        newest_mtime = max((path.stat().st_mtime for path in transcript_files), default=None)
        return {
            "archive_root": str(self.archive_root),
            "archive_root_exists": root_exists,
            "archive_root_is_dir": root_is_dir,
            "archive_dirs": len({path.parent for path in transcript_files}),
            "text_files": len(transcript_files),
            "manifest_files": len(manifests),
            "missing_manifest_dirs": missing_manifests[:50],
            "missing_manifest_count": len(missing_manifests),
            "newest_text_mtime": newest_mtime,
            "newest_text_age_seconds": time.time() - newest_mtime if newest_mtime else None,
        }

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        context_chars: int = DEFAULT_CONTEXT_CHARS,
        agent: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = query.strip()
        if not query:
            return {"error": "query is required"}

        hits: List[Dict[str, Any]] = []
        for document in self._iter_documents():
            if not self._matches_filters(
                document, agent=agent, date_from=date_from, date_to=date_to
            ):
                continue
            hit = self._find_hit(document, query, context_chars=context_chars)
            if hit:
                hits.append(hit)
                if len(hits) >= max(1, min(limit, 100)):
                    break

        return {
            "query": query,
            "mode": "exact",
            "archive_root": str(self.archive_root),
            "hit_count": len(hits),
            "hits": hits,
        }

    def _iter_text_files(self) -> Iterable[Path]:
        patterns = (
            "*/transcript.md",
            "*/transcript.part-*.md",
            "*/extracted_text.txt",
            "*/session.jsonl",
            "*/session.part-*.jsonl",
        )
        for pattern in patterns:
            yield from sorted(self.archive_root.glob(pattern))

    def _iter_documents(self) -> Iterable[ArchiveDocument]:
        for text_path in self._iter_text_files():
            try:
                text = text_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            manifest_path = text_path.parent / "manifest.json"
            manifest: Dict[str, Any] = {}
            if manifest_path.is_file():
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    manifest = {}
            yield ArchiveDocument(
                archive_dir=text_path.parent,
                text_path=text_path,
                manifest_path=manifest_path if manifest_path.is_file() else None,
                text=text,
                manifest=manifest,
            )

    def _find_hit(
        self, document: ArchiveDocument, query: str, *, context_chars: int
    ) -> Optional[Dict[str, Any]]:
        lower_text = document.text.lower()
        lower_query = query.lower()
        pos = lower_text.find(lower_query)
        if pos < 0:
            return None
        start = max(0, pos - context_chars)
        end = min(len(document.text), pos + len(query) + context_chars)
        excerpt = " ".join(document.text[start:end].split())
        return {
            "match_type": "exact",
            "source_path": str(document.text_path),
            "archive_dir": str(document.archive_dir),
            "manifest_path": str(document.manifest_path) if document.manifest_path else None,
            "title": document.manifest.get("title") or document.archive_dir.name,
            "kind": document.manifest.get("kind") or document.manifest.get("source_kind"),
            "agent": document.manifest.get("agent") or document.manifest.get("source_agent"),
            "position": pos,
            "excerpt": excerpt,
        }

    def _matches_filters(
        self,
        document: ArchiveDocument,
        *,
        agent: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> bool:
        haystack = " ".join(
            str(value)
            for value in (
                document.manifest.get("agent"),
                document.manifest.get("source_agent"),
                document.manifest.get("kind"),
                document.archive_dir.name,
            )
            if value
        ).lower()
        if agent and agent.lower() not in haystack:
            return False
        archive_name = document.archive_dir.name
        archive_date = archive_name[:10]
        if date_from and archive_date < date_from:
            return False
        if date_to and archive_date > date_to:
            return False
        return True
