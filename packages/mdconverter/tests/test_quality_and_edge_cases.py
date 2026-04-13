"""Tests for quality scoring and converter edge cases."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mdconverter.core.base import ConversionResult, ConversionStatus
from mdconverter.core.gemini import LLMConverter
from mdconverter.core.pandoc import PandocConverter


class TestLLMConverterQualityScore:
    """Test _calculate_quality for LLMConverter."""

    def test_base_score_short_content(self) -> None:
        """Test base score for short content with no structure."""
        converter = LLMConverter()
        score = converter._calculate_quality("Hello")
        assert score == 50

    def test_length_bonus_medium(self) -> None:
        """Test length bonus for medium content."""
        converter = LLMConverter()
        content = "x" * 1500  # > 1000 chars
        score = converter._calculate_quality(content)
        assert score >= 60

    def test_length_bonus_long(self) -> None:
        """Test length bonus for long content."""
        converter = LLMConverter()
        content = "x" * 6000  # > 5000 chars
        score = converter._calculate_quality(content)
        assert score >= 70

    def test_structure_bonus_heading(self) -> None:
        """Test bonus for heading structure."""
        converter = LLMConverter()
        content = "x" * 6000 + "\n## Section\n### Subsection"
        score = converter._calculate_quality(content)
        assert score >= 75

    def test_table_bonus(self) -> None:
        """Test bonus for table content."""
        converter = LLMConverter()
        content = "x" * 6000 + "\n| Col1 | Col2 |\n-|-\n| A | B |"
        score = converter._calculate_quality(content)
        assert score >= 80

    def test_vietnamese_content_bonus(self) -> None:
        """Test bonus for Vietnamese content."""
        converter = LLMConverter()
        # Vietnamese chars have ord > 127
        content = "Điều 1. Quy chế quản lý chất lượng công trình xây dựng " * 100
        score = converter._calculate_quality(content)
        assert score >= 55

    def test_max_score_capped(self) -> None:
        """Test score is capped at 100."""
        converter = LLMConverter()
        # Content that would exceed 100 if not capped
        content = (
            "## Chương I\n### Điều 1\n" + "Nội dung " * 1000 + "\n| Col | Col |\n-|-\n| A | B |"
        )
        score = converter._calculate_quality(content)
        assert score <= 100


class TestPandocConverterQualityScore:
    """Test _calculate_quality for PandocConverter."""

    def test_base_score(self) -> None:
        """Test base score is 60 for Pandoc."""
        converter = PandocConverter()
        score = converter._calculate_quality("Short")
        assert score == 60

    def test_length_bonus(self) -> None:
        """Test length bonuses."""
        converter = PandocConverter()
        content = "x" * 3000
        score = converter._calculate_quality(content)
        assert score >= 80

    def test_structure_and_table_bonus(self) -> None:
        """Test structure and table bonuses."""
        converter = PandocConverter()
        content = "x" * 3000 + "\n## Heading\n| Col |"
        score = converter._calculate_quality(content)
        assert score >= 100


class TestLLMConverterFallbackChain:
    """Test model fallback chain behavior."""

    @pytest.mark.asyncio
    async def test_fallback_on_first_model_failure(self, tmp_path: Path) -> None:
        """Test that second model is tried when first fails."""
        converter = LLMConverter(
            output_dir=tmp_path,
            gateway_url="http://fake:1",
            models=["model-a", "model-b"],
        )

        call_count = 0

        async def mock_generate(prompt, file_content, mime_type, model, config):
            nonlocal call_count
            call_count += 1
            if model == "model-a":
                raise ConnectionError("Model A down")
            return "# Converted\n\n" + "Content " * 50  # > 100 chars

        with patch.object(converter.provider, "generate", side_effect=mock_generate):
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4 test content")

            result = await converter.convert(test_file)
            assert result.is_success
            assert "model-b" in result.tool_used
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_all_models_fail_reports_all_errors(self, tmp_path: Path) -> None:
        """Test that all errors are reported when all models fail."""
        converter = LLMConverter(
            output_dir=tmp_path,
            gateway_url="http://fake:1",
            models=["model-a", "model-b"],
        )

        async def mock_generate(prompt, file_content, mime_type, model, config):
            raise ConnectionError(f"{model} is down")

        with patch.object(converter.provider, "generate", side_effect=mock_generate):
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4 test content")

            result = await converter.convert(test_file)
            assert result.status == ConversionStatus.FAILED
            assert "model-a" in result.error_message
            assert "model-b" in result.error_message

    @pytest.mark.asyncio
    async def test_metadata_tracks_models_tried(self, tmp_path: Path) -> None:
        """Test that metadata includes models_tried and errors_per_model."""
        converter = LLMConverter(
            output_dir=tmp_path,
            gateway_url="http://fake:1",
            models=["model-a", "model-b"],
        )

        async def mock_generate(prompt, file_content, mime_type, model, config):
            if model == "model-a":
                raise ConnectionError("timeout")
            return "# Result\n\n" + "Content " * 50

        with patch.object(converter.provider, "generate", side_effect=mock_generate):
            test_file = tmp_path / "test.pdf"
            test_file.write_bytes(b"%PDF-1.4 test")

            result = await converter.convert(test_file)
            assert result.is_success
            assert result.metadata["models_tried"] == ["model-a", "model-b"]
            assert "model-a" in result.metadata["errors_per_model"]


class TestConverterEdgeCases:
    """Test edge cases for converters."""

    @pytest.mark.asyncio
    async def test_convert_zero_byte_file(self, tmp_path: Path) -> None:
        """Test conversion of zero-byte file."""
        test_file = tmp_path / "empty.pdf"
        test_file.write_bytes(b"")

        converter = LLMConverter(output_dir=tmp_path, gateway_url="http://fake:1")

        async def mock_generate(prompt, file_content, mime_type, model, config):
            return ""  # Empty response for empty file

        with patch.object(converter.provider, "generate", side_effect=mock_generate):
            result = await converter.convert(test_file)
            # Should fail because output is too short (< min_content_length)
            assert result.status == ConversionStatus.FAILED

    @pytest.mark.asyncio
    async def test_convert_with_spaces_in_filename(self, tmp_path: Path) -> None:
        """Test conversion handles filenames with spaces."""
        test_file = tmp_path / "my document.pdf"
        test_file.write_bytes(b"%PDF-1.4 test content")

        converter = LLMConverter(output_dir=tmp_path, gateway_url="http://fake:1")
        output_path = converter.get_output_path(test_file)

        assert " " not in output_path.stem  # Spaces should be replaced with _
        assert output_path.stem == "my_document"

    @pytest.mark.asyncio
    async def test_pandoc_convert_unsupported_extension(self, tmp_path: Path) -> None:
        """Test Pandoc skips unsupported extensions."""
        test_file = tmp_path / "test.xyz"
        test_file.write_text("content")

        converter = PandocConverter(output_dir=tmp_path)
        result = await converter.convert(test_file)
        assert result.status == ConversionStatus.SKIPPED

    def test_conversion_result_to_dict(self) -> None:
        """Test ConversionResult.to_dict includes all fields."""
        result = ConversionResult(
            source_path=Path("test.pdf"),
            output_path=Path("test.md"),
            status=ConversionStatus.SUCCESS,
            tool_used="llm/model-a",
            quality_score=85,
            duration_seconds=1.5,
        )
        d = result.to_dict()
        assert d["source"] == "test.pdf"
        assert d["output"] == "test.md"
        assert d["status"] == "success"
        assert d["tool"] == "llm/model-a"
        assert d["quality_score"] == 85
        assert d["duration"] == 1.5
