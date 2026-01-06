"""Conversion cache for skipping unchanged files.

Provides a simple file-based cache to avoid re-converting
documents that haven't changed since the last conversion.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ConversionCache:
    """Cache for conversion results based on file content hash.

    Uses SHA256 hash of file content to detect changes.
    Cache is stored in a local directory with JSON index.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache with optional custom directory.

        Args:
            cache_dir: Directory to store cache files. Defaults to .mdconvert_cache
        """
        self.cache_dir = cache_dir or Path(".mdconvert_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.cache_dir / "index.json"
        self._index: dict[str, dict[str, Any]] = self._load_index()

    def _load_index(self) -> dict[str, dict[str, Any]]:
        """Load cache index from disk."""
        if self.index_path.exists():
            try:
                data: dict[str, dict[str, Any]] = json.loads(
                    self.index_path.read_text(encoding="utf-8")
                )
                return data
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_index(self) -> None:
        """Save cache index to disk."""
        # No indent for smaller file size
        self.index_path.write_text(
            json.dumps(self._index, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_file_hash(self, file_path: Path) -> str:
        """Generate SHA256 hash of file content.

        Args:
            file_path: Path to file to hash.

        Returns:
            First 32 characters of SHA256 hex digest for better collision resistance.
        """
        content = file_path.read_bytes()
        return hashlib.sha256(content).hexdigest()[:32]

    def get(self, source_path: Path) -> str | None:
        """Get cached conversion result if valid.

        Args:
            source_path: Path to source file.

        Returns:
            Cached markdown content if exists and source unchanged, None otherwise.
        """
        # Use try-except instead of exists() to avoid TOCTOU race
        try:
            file_hash = self.get_file_hash(source_path)
        except FileNotFoundError:
            return None

        key = str(source_path.resolve())

        if key in self._index:
            entry = self._index[key]
            if entry.get("hash") == file_hash:
                cache_file = self.cache_dir / f"{file_hash}.md"
                try:
                    return cache_file.read_text(encoding="utf-8")
                except FileNotFoundError:
                    pass

        return None

    def set(self, source_path: Path, content: str, tool_used: str = "unknown") -> None:
        """Store conversion result in cache.

        Args:
            source_path: Path to source file.
            content: Converted markdown content.
            tool_used: Name of converter tool used.
        """
        file_hash = self.get_file_hash(source_path)
        key = str(source_path.resolve())

        # Save content
        cache_file = self.cache_dir / f"{file_hash}.md"
        cache_file.write_text(content, encoding="utf-8")

        # Update index
        self._index[key] = {
            "hash": file_hash,
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

        if key in self._index:
            entry = self._index.pop(key)
            cache_file = self.cache_dir / f"{entry['hash']}.md"
            if cache_file.exists():
                cache_file.unlink()
            self._save_index()
            return True

        return False

    def clear(self) -> int:
        """Clear all cached conversions.

        Returns:
            Number of entries cleared.
        """
        count = len(self._index)

        # Remove all cache files
        for entry in self._index.values():
            cache_file = self.cache_dir / f"{entry['hash']}.md"
            if cache_file.exists():
                cache_file.unlink()

        # Clear index
        self._index = {}
        self._save_index()

        return count

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats.
        """
        total_size = 0
        for e in self._index.values():
            cache_file = self.cache_dir / f"{e['hash']}.md"
            try:
                total_size += cache_file.stat().st_size
            except FileNotFoundError:
                pass  # File may have been deleted

        return {
            "entries": len(self._index),
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir),
        }
