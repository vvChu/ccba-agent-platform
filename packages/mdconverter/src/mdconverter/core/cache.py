"""Conversion cache for skipping unchanged files.

Provides a simple file-based cache to avoid re-converting
documents that haven't changed since the last conversion.
"""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConversionCache:
    """Cache for conversion results based on file content hash.

    Uses SHA256 hash of file content to detect changes.
    Cache is stored in a local directory with JSON index.
    Cache files are keyed by source path hash to avoid collision issues.
    """

    CHUNK_SIZE = 65536  # 64KB chunks for streaming hash

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache with optional custom directory.

        Args:
            cache_dir: Directory to store cache files. Defaults to .mdconvert_cache
        """
        self.cache_dir = cache_dir or Path(".mdconvert_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self.lock_path = self.cache_dir / ".index.lock"
        self._lock = threading.RLock()
        with self._acquire_lock():
            self._index: dict[str, dict[str, Any]] = self._load_index()
        self._hits: int = 0
        self._misses: int = 0

    @contextmanager
    def _acquire_lock(self) -> Iterator[None]:
        """Acquire thread-level RLock and cross-process FileMutexLock when available."""
        with self._lock:
            mutex: Any = None
            try:
                from ccba_harness import FileMutexLock

                candidate = FileMutexLock(self.lock_path, timeout=5.0, retry_interval=0.02)
                candidate.acquire()
                mutex = candidate
            except (ImportError, OSError, TimeoutError) as exc:
                logger.debug("Using thread-lock fallback for %s: %s", self.lock_path, exc)
            try:
                yield
            finally:
                if mutex is not None:
                    mutex.release()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load cache index from disk."""
        try:
            data: dict[str, dict[str, Any]] = json.loads(
                self.index_path.read_text(encoding="utf-8")
            )
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError, FileNotFoundError):
            return {}

    def _atomic_write_text(self, target_path: Path, text: str, suffix: str) -> bool:
        """Write text to target_path atomically via a temp file in cache_dir."""
        try:
            temp_fd, temp_path = tempfile.mkstemp(dir=self.cache_dir, suffix=suffix)
            try:
                with open(temp_fd, "w", encoding="utf-8") as f:
                    f.write(text)
                Path(temp_path).replace(target_path)
                return True
            except Exception:
                Path(temp_path).unlink(missing_ok=True)
                raise
        except OSError as exc:
            logger.warning("Failed to save cache artifact %s: %s", target_path, exc)
            return False

    def _save_index(self) -> None:
        """Save cache index to disk with atomic write for safety."""
        self._atomic_write_text(
            self.index_path,
            json.dumps(self._index, ensure_ascii=False),
            suffix=".tmp",
        )

    def _write_cache_markdown(self, cache_file: Path, content: str) -> bool:
        """Write converted markdown content atomically via temp file replace."""
        return self._atomic_write_text(cache_file, content, suffix=".md.tmp")

    def _get_cache_key(self, source_path: Path) -> str:
        """Get cache key based on source path (not content hash).

        This avoids collision issues where two files with same content
        share the same cache file.
        """
        key = str(source_path.resolve())
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def get_file_hash(self, file_path: Path) -> str:
        """Generate SHA256 hash of file content using streaming.

        Uses chunked reading to handle large files without
        loading entire content into memory.

        Args:
            file_path: Path to file to hash.

        Returns:
            First 32 characters of SHA256 hex digest.
        """
        sha256 = hashlib.sha256()
        with file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:32]

    def get(self, source_path: Path) -> str | None:
        """Get cached conversion result if valid.

        Args:
            source_path: Path to source file.

        Returns:
            Cached markdown content if exists and source unchanged, None otherwise.
        """
        # Use try-except to catch all I/O errors (not just FileNotFoundError)
        try:
            file_hash = self.get_file_hash(source_path)
        except OSError:
            with self._lock:
                self._misses += 1
            return None

        key = str(source_path.resolve())

        with self._acquire_lock():
            if key not in self._index or self._index[key].get("hash") != file_hash:
                self._index.update(self._load_index())

            if key in self._index:
                entry = self._index[key]
                if entry.get("hash") == file_hash:
                    # Use source-path-based cache key (not content hash)
                    cache_key = self._get_cache_key(source_path)
                    cache_file = self.cache_dir / f"{cache_key}.md"
                    try:
                        content = cache_file.read_text(encoding="utf-8")
                        self._hits += 1
                        return content
                    except OSError:
                        pass  # Cache file missing or unreadable (preserves stale index)

            self._misses += 1
            return None

    def set(self, source_path: Path, content: str, tool_used: str = "unknown") -> None:
        """Store conversion result in cache.

        Args:
            source_path: Path to source file.
            content: Converted markdown content.
            tool_used: Name of converter tool used.
        """
        try:
            file_hash = self.get_file_hash(source_path)
        except OSError:
            return  # Can't hash source, skip caching

        key = str(source_path.resolve())
        cache_key = self._get_cache_key(source_path)
        cache_file = self.cache_dir / f"{cache_key}.md"

        with self._acquire_lock():
            self._index.update(self._load_index())
            if not self._write_cache_markdown(cache_file, content):
                return  # Can't write cache file, skip

            self._index[key] = {
                "hash": file_hash,
                "cache_key": cache_key,
                "source_name": source_path.name,
                "tool_used": tool_used,
                "cached_at": datetime.now().isoformat(),
            }
            self._save_index()

    def invalidate(self, source_path: Path) -> bool:
        """Remove cached result for a file.

        Args:
            source_path: Path to source file.

        Returns:
            True if entry was removed, False if not found.
        """
        key = str(source_path.resolve())

        with self._acquire_lock():
            self._index.update(self._load_index())
            if key in self._index:
                entry = self._index.pop(key)
                # Use cache_key if available, fall back to hash for old entries
                cache_key = entry.get("cache_key", entry.get("hash", ""))
                cache_file = self.cache_dir / f"{cache_key}.md"
                try:
                    cache_file.unlink(missing_ok=True)
                except OSError:
                    pass
                self._save_index()
                return True

        return False

    def clear(self) -> int:
        """Clear all cached conversions.

        Returns:
            Number of entries cleared.
        """
        with self._acquire_lock():
            self._index.update(self._load_index())
            count = len(self._index)

            # Remove all cache files
            for entry in self._index.values():
                cache_key = entry.get("cache_key", entry.get("hash", ""))
                cache_file = self.cache_dir / f"{cache_key}.md"
                try:
                    cache_file.unlink(missing_ok=True)
                except OSError:
                    pass

            # Clear index
            self._index = {}
            self._save_index()

            return count

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats including hit/miss ratio.
        """
        with self._acquire_lock():
            self._index.update(self._load_index())
            total_size = 0
            for e in self._index.values():
                cache_key = e.get("cache_key", e.get("hash", ""))
                cache_file = self.cache_dir / f"{cache_key}.md"
                try:
                    total_size += cache_file.stat().st_size
                except OSError:
                    pass  # File may have been deleted

            total_lookups = self._hits + self._misses
            hit_ratio = self._hits / total_lookups if total_lookups > 0 else 0.0

            return {
                "entries": len(self._index),
                "total_size_bytes": total_size,
                "cache_dir": str(self.cache_dir),
                "hits": self._hits,
                "misses": self._misses,
                "hit_ratio": round(hit_ratio, 3),
            }
