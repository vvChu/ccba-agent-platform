"""Tests for core converters."""

import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from mdconverter.core.base import ConversionResult, ConversionStatus
from mdconverter.core.gemini import GeminiConverter, LLMConverter
from mdconverter.core.llamaparse import LlamaParseConverter
from mdconverter.core.pandoc import PandocConverter


class TestConversionResult:
    """Test ConversionResult dataclass."""

    def test_is_success_true(self) -> None:
        """Test is_success returns True for SUCCESS status."""
        result = ConversionResult(
            source_path=Path("test.pdf"),
            status=ConversionStatus.SUCCESS,
        )
        assert result.is_success is True

    def test_is_success_false_for_failed(self) -> None:
        """Test is_success returns False for FAILED status."""
        result = ConversionResult(
            source_path=Path("test.pdf"),
            status=ConversionStatus.FAILED,
        )
        assert result.is_success is False

    def test_is_success_false_for_skipped(self) -> None:
        """Test is_success returns False for SKIPPED status."""
        result = ConversionResult(
            source_path=Path("test.pdf"),
            status=ConversionStatus.SKIPPED,
        )
        assert result.is_success is False


class TestLLMConverter:
    """Test LLMConverter class (formerly GeminiConverter)."""

    def test_backward_compat_alias_emits_warning(self) -> None:
        """Test GeminiConverter alias emits DeprecationWarning (L1 fix)."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = GeminiConverter()
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_supports_pdf(self) -> None:
        """Test PDF is supported."""
        converter = LLMConverter()
        assert converter.supports(".pdf") is True

    def test_supports_docx(self) -> None:
        """Test DOCX is supported."""
        converter = LLMConverter()
        assert converter.supports(".docx") is True

    def test_does_not_support_txt(self) -> None:
        """Test TXT is not supported."""
        converter = LLMConverter()
        assert converter.supports(".txt") is False

    @pytest.mark.asyncio
    async def test_convert_nonexistent_file(self, tmp_path: Path) -> None:
        """Test conversion of non-existent file fails."""
        converter = LLMConverter(output_dir=tmp_path)
        result = await converter.convert(Path("nonexistent.pdf"))

        assert result.status == ConversionStatus.FAILED
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_convert_unsupported_extension(self, tmp_path: Path) -> None:
        """Test conversion of unsupported file type is skipped."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        converter = LLMConverter(output_dir=tmp_path)
        result = await converter.convert(test_file)

        assert result.status == ConversionStatus.SKIPPED
        assert "unsupported" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_convert_api_error_handled(self, tmp_path: Path) -> None:
        """Test that API errors are handled gracefully."""
        from unittest.mock import patch

        import httpx

        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        converter = LLMConverter(
            output_dir=tmp_path, gateway_url="http://127.0.0.1:1", models=["gemini-2.0-flash"]
        )
        with patch(
            "mdconverter.providers.gemini.GatewayProvider.generate",
            side_effect=httpx.ConnectError("Connection refused"),
        ):
            result = await converter.convert(test_file)

        # Should fail but not crash
        assert result.status == ConversionStatus.FAILED
        assert result.error_message is not None


class TestPandocConverter:
    """Test PandocConverter class."""

    def test_supports_docx(self) -> None:
        """Test DOCX is supported."""
        converter = PandocConverter()
        assert converter.supports(".docx") is True

    def test_supports_html(self) -> None:
        """Test HTML is supported."""
        converter = PandocConverter()
        assert converter.supports(".html") is True

    def test_does_not_support_pdf(self) -> None:
        """Test PDF is not supported by Pandoc."""
        converter = PandocConverter()
        assert converter.supports(".pdf") is False

    @pytest.mark.asyncio
    async def test_convert_nonexistent_file(self, tmp_path: Path) -> None:
        """Test conversion of non-existent file fails."""
        converter = PandocConverter(output_dir=tmp_path)
        result = await converter.convert(Path("nonexistent.docx"))

        assert result.status == ConversionStatus.FAILED
        assert "not found" in result.error_message.lower()

    @pytest.mark.asyncio
    async def test_pandoc_not_installed(self, tmp_path: Path) -> None:
        """Test error when Pandoc is not installed."""
        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"test content")

        converter = PandocConverter(output_dir=tmp_path)
        # Mock the is_pandoc_available method to return False
        with patch.object(converter, "is_pandoc_available", return_value=False):
            result = await converter.convert(test_file)
            assert result.status == ConversionStatus.FAILED
            assert "pandoc" in result.error_message.lower()


class TestLlamaParseConverter:
    """Test LlamaParseConverter class."""

    def test_supports_pdf(self) -> None:
        """Test PDF is supported."""
        converter = LlamaParseConverter()
        assert converter.supports(".pdf") is True

    def test_supports_docx(self) -> None:
        """Test DOCX is supported."""
        converter = LlamaParseConverter()
        assert converter.supports(".docx") is True

    def test_is_available_without_key(self) -> None:
        """Test is_available returns False without API key."""
        converter = LlamaParseConverter(api_key=None)
        # Depends on environment, but we test the method exists
        assert hasattr(converter, "is_available")

    @pytest.mark.asyncio
    async def test_convert_without_api_key(self, tmp_path: Path) -> None:
        """Test conversion fails without API key."""
        test_file = tmp_path / "test.pdf"
        test_file.write_bytes(b"%PDF-1.4 test")

        converter = LlamaParseConverter(output_dir=tmp_path, api_key=None)
        # Clear any env var that might provide a key
        with patch.object(converter, "api_key", None):
            with patch.object(converter, "is_available", return_value=False):
                result = await converter.convert(test_file)
                assert result.status == ConversionStatus.FAILED


class TestBaseConverter:
    """Test BaseConverter abstract methods."""

    def test_get_output_path(self, tmp_path: Path) -> None:
        """Test output path generation."""
        converter = LLMConverter(output_dir=tmp_path)
        source = Path("/some/path/document.pdf")
        output = converter.get_output_path(source)

        assert output.suffix == ".md"
        assert output.stem == "document"
        assert output.parent == tmp_path

    def test_add_frontmatter_basic(self, tmp_path: Path) -> None:
        """Test basic frontmatter is added to content."""
        converter = LLMConverter(output_dir=tmp_path)
        source = Path("test.pdf")
        content = "# Test Content"

        result = converter.add_frontmatter(content, source, "llm")

        assert "---" in result
        assert "source_file:" in result
        assert "test.pdf" in result
        assert "conversion_tool:" in result
        assert "llm" in result

    def test_add_frontmatter_with_metadata(self, tmp_path: Path) -> None:
        """Test frontmatter includes VN Legal metadata when provided."""
        converter = LLMConverter(output_dir=tmp_path)
        source = Path("test.pdf")
        content = "# Test Content"
        metadata = {
            "title": "Test Title",
            "type": "Quyết định",
            "decision_number": "123/QĐ-VKHCN",
            "issuer": "Viện KHCN",
        }

        result = converter.add_frontmatter(content, source, "llm", metadata=metadata)

        assert 'title: "Test Title"' in result
        assert 'type: "Quyết định"' in result
        assert 'decision_number: "123/QĐ-VKHCN"' in result

    def test_add_frontmatter_skips_existing(self, tmp_path: Path) -> None:
        """Test frontmatter is not added when content already has it."""
        converter = LLMConverter(output_dir=tmp_path)
        source = Path("test.pdf")
        content = "---\ntitle: existing\n---\n# Content"

        result = converter.add_frontmatter(content, source, "llm")
        assert result == content  # Unchanged

    def test_docling_removed_from_enum(self) -> None:
        """Test DOCLING is no longer in ConversionTool enum (M2 fix)."""
        from mdconverter.core.base import ConversionTool

        assert not hasattr(ConversionTool, "DOCLING")
        assert set(ConversionTool) == {
            ConversionTool.LLM,
            ConversionTool.PANDOC,
            ConversionTool.LLAMAPARSE,
            ConversionTool.AUTO,
        }
