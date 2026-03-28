"""Tests for VN Legal Processor."""

from mdconverter.plugins.vn_legal.processor import VNLegalProcessor


class TestVNLegalProcessor:
    """Test VNLegalProcessor class."""

    def test_process_empty_content(self) -> None:
        """Test processing empty content."""
        processor = VNLegalProcessor()
        result = processor.process("")
        assert result == "\n"  # Trailing newline added

    def test_normalize_list_markers_star(self) -> None:
        """Test normalizing * list markers to -."""
        processor = VNLegalProcessor()
        content = "* item 1\n* item 2"
        result = processor.process(content)
        assert "- item 1" in result
        assert "- item 2" in result

    def test_normalize_list_markers_plus(self) -> None:
        """Test normalizing + list markers to -."""
        processor = VNLegalProcessor()
        content = "+ item 1\n+ item 2"
        result = processor.process(content)
        assert "- item 1" in result
        assert "- item 2" in result

    def test_preserve_dash_markers(self) -> None:
        """Test that - markers stay unchanged."""
        processor = VNLegalProcessor()
        content = "- item 1\n- item 2"
        result = processor.process(content)
        assert "- item 1" in result
        assert "- item 2" in result

    def test_ensure_trailing_newline(self) -> None:
        """Test trailing newline is ensured."""
        processor = VNLegalProcessor()
        content = "Content without newline"
        result = processor.process(content)
        assert result.endswith("\n")

    def test_no_double_trailing_newline(self) -> None:
        """Test double newlines are normalized."""
        processor = VNLegalProcessor()
        content = "Content\n\n"
        result = processor.process(content)
        assert result == "Content\n"

    def test_get_fix_summary_empty(self) -> None:
        """Test fix summary is empty when no fixes."""
        processor = VNLegalProcessor()
        processor.process("- item")  # No fixes needed
        summary = processor.get_fix_summary()
        assert isinstance(summary, dict)

    def test_get_fix_summary_with_fixes(self) -> None:
        """Test fix summary with actual fixes."""
        processor = VNLegalProcessor()
        processor.process("* item 1\n+ item 2")
        summary = processor.get_fix_summary()
        assert "list_markers" in summary
        assert summary["list_markers"] == 2

    def test_multiple_processing_calls_reset(self) -> None:
        """Test processor resets fixes between calls."""
        processor = VNLegalProcessor()

        processor.process("* item 1")
        summary1 = processor.get_fix_summary()

        processor.process("+ item 2")
        summary2 = processor.get_fix_summary()

        # Each call should have independent counts
        assert summary1.get("list_markers") == 1
        assert summary2.get("list_markers") == 1
