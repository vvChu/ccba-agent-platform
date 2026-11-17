"""Tests for ConversionCache."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from mdconverter.core.cache import ConversionCache


class TestConversionCache:
    """Test ConversionCache class."""

    def test_cache_miss_for_new_file(self, tmp_path: Path) -> None:
        """Test cache returns None for files not yet cached."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        result = cache.get(test_file)
        assert result is None

    def test_cache_hit_after_set(self, tmp_path: Path) -> None:
        """Test cache returns content after set."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        content = "# Converted Markdown\n\nTest content."
        cache.set(test_file, content, "test-tool")

        result = cache.get(test_file)
        assert result == content

    def test_cache_miss_after_file_change(self, tmp_path: Path) -> None:
        """Test cache misses when source file changes."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 original content")

        content = "# Original Conversion"
        cache.set(test_file, content, "test-tool")

        # Modify the source file
        test_file.write_bytes(b"%PDF-1.4 modified content")

        result = cache.get(test_file)
        assert result is None  # Cache miss due to content change

    def test_invalidate_removes_entry(self, tmp_path: Path) -> None:
        """Test invalidate removes cached entry."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        cache.set(test_file, "# Content", "test-tool")
        assert cache.get(test_file) is not None

        removed = cache.invalidate(test_file)
        assert removed is True
        assert cache.get(test_file) is None

    def test_invalidate_returns_false_for_missing(self, tmp_path: Path) -> None:
        """Test invalidate returns False for uncached file."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        removed = cache.invalidate(test_file)
        assert removed is False

    def test_clear_removes_all_entries(self, tmp_path: Path) -> None:
        """Test clear removes all cached conversions."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")

        # Add multiple entries
        for i in range(3):
            test_file = tmp_path / f"test{i}.pdf"
            test_file.write_bytes(f"PDF content {i}".encode())
            cache.set(test_file, f"# Content {i}", "test-tool")

        count = cache.clear()
        assert count == 3

        # Verify all cleared
        for i in range(3):
            test_file = tmp_path / f"test{i}.pdf"
            assert cache.get(test_file) is None

    def test_stats_returns_info(self, tmp_path: Path) -> None:
        """Test stats returns cache information."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        cache.set(test_file, "# Content", "test-tool")

        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["total_size_bytes"] > 0
        assert ".cache" in stats["cache_dir"]

    def test_get_file_hash_is_consistent(self, tmp_path: Path) -> None:
        """Test file hash is consistent for same content."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        hash1 = cache.get_file_hash(test_file)
        hash2 = cache.get_file_hash(test_file)

        assert hash1 == hash2
        assert len(hash1) == 32  # 32 chars (128 bits) is sufficient for this use case

    def test_get_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test get returns None for file that doesn't exist."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")

        result = cache.get(tmp_path / "nonexistent.pdf")
        assert result is None

    def test_hit_miss_counters(self, tmp_path: Path) -> None:
        """Test cache hit/miss counters are tracked correctly."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        # First get: miss (not cached yet)
        cache.get(test_file)
        assert cache._misses == 1
        assert cache._hits == 0

        # Set content
        cache.set(test_file, "# Cached Content", "test-tool")

        # Second get: hit
        cache.get(test_file)
        assert cache._hits == 1
        assert cache._misses == 1

        # Third get with different file: miss
        other_file = tmp_path / "other.pdf"
        other_file.write_bytes(b"%PDF-1.4 other")
        cache.get(other_file)
        assert cache._misses == 2

        # Check stats include hit/miss info
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 2
        assert stats["hit_ratio"] == round(1 / 3, 3)

    def test_concurrent_set_and_get_thread_safety(self, tmp_path: Path) -> None:
        """Test concurrent set/get across threads preserves all entries in index.json."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")
        sources = []
        for idx in range(16):
            src = tmp_path / f"doc_{idx}.pdf"
            src.write_bytes(f"%PDF-1.4 payload {idx}".encode())
            sources.append((idx, src))

        def _write_and_read(item: tuple[int, Path]) -> tuple[int, str | None]:
            idx, path = item
            expected = f"# Document {idx}\n\nBody {idx}"
            cache.set(path, expected, "concurrent-tool")
            return idx, cache.get(path)

        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(_write_and_read, sources))

        for idx, got in results:
            assert got == f"# Document {idx}\n\nBody {idx}"

        reloaded = ConversionCache(cache_dir=tmp_path / ".cache")
        assert reloaded.stats()["entries"] == 16
        for idx, path in sources:
            assert reloaded.get(path) == f"# Document {idx}\n\nBody {idx}"

    def test_multi_instance_shared_cache_dir_merges_index(self, tmp_path: Path) -> None:
        """Test two independent ConversionCache instances merge index entries without lost updates."""
        cache_dir = tmp_path / ".shared_cache"
        cache_a = ConversionCache(cache_dir=cache_dir)
        cache_b = ConversionCache(cache_dir=cache_dir)

        file_a = tmp_path / "a.pdf"
        file_b = tmp_path / "b.pdf"
        file_a.write_bytes(b"content-a")
        file_b.write_bytes(b"content-b")

        cache_a.set(file_a, "# Alpha", "tool-a")
        cache_b.set(file_b, "# Beta", "tool-b")

        assert cache_a.get(file_b) == "# Beta"
        assert cache_b.get(file_a) == "# Alpha"
        assert cache_b.stats()["entries"] == 2
