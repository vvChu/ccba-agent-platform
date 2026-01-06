"""Tests for ConversionCache."""

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
        assert len(hash1) == 16  # First 16 chars of SHA256

    def test_get_returns_none_for_nonexistent_file(self, tmp_path: Path) -> None:
        """Test get returns None for file that doesn't exist."""
        cache = ConversionCache(cache_dir=tmp_path / ".cache")

        result = cache.get(tmp_path / "nonexistent.pdf")
        assert result is None
