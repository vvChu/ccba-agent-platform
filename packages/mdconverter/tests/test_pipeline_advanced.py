"""Tests for advanced ConversionPipeline features (v2.3.0)."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mdconverter import ConversionPipeline, ConversionResult
from mdconverter.core.analyzer import PageDetail, PDFReport, Segment
from mdconverter.core.base import ConversionStatus


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def mock_analyzer_report():
    """Create a mock hybrid PDF report."""
    report = MagicMock(spec=PDFReport)
    report.file_path = Path("hybrid.pdf")
    report.category = "hybrid"
    report.pages = 10
    report.should_skip = False
    report.recommended_model = "ocr-primary"

    # Text pages 1-5, Scan pages 6-10
    pages = []
    for i in range(5):
        pages.append(PageDetail(i, 500, 1, 210, 297, False, "text"))
    for i in range(5, 10):
        pages.append(PageDetail(i, 0, 1, 210, 297, False, "scan"))

    report.page_details = pages

    # Mock get_segments
    report.get_segments.return_value = [
        Segment(0, 4, "text", "qwen-local-primary"),
        Segment(5, 9, "scan", "ocr-primary"),
    ]
    report.to_dict.return_value = {"category": "hybrid", "pages": 10}
    return report


@pytest.mark.anyio
async def test_process_segmented_hybrid(tmp_path: Path, mock_analyzer_report):
    """Test that a hybrid PDF is split and converted per segment."""
    pipeline = ConversionPipeline(output_dir=tmp_path)

    # Mock split_pdf to return dummy paths
    chunk1 = tmp_path / "part1.pdf"
    chunk2 = tmp_path / "part2.pdf"
    chunk1.touch()
    chunk2.touch()

    # Mock converter results
    res1 = ConversionResult(
        chunk1, status=ConversionStatus.SUCCESS, content="Text part content", tool_used="llm"
    )
    res2 = ConversionResult(
        chunk2, status=ConversionStatus.SUCCESS, content="Scan part content", tool_used="llm"
    )

    mock_conv1 = AsyncMock()
    mock_conv1.convert.return_value = res1
    mock_conv2 = AsyncMock()
    mock_conv2.convert.return_value = res2

    with (
        patch("mdconverter.core.pipeline.split_pdf", return_value=[chunk1, chunk2]),
        patch.object(pipeline, "_create_converter_for_segment") as mock_create_conv,
        patch("shutil.rmtree"),
    ):
        mock_create_conv.side_effect = [mock_conv1, mock_conv2]

        result = await pipeline._process_segmented(Path("hybrid.pdf"), mock_analyzer_report)

        assert result.status == ConversionStatus.SUCCESS
        assert "Text part content" in result.content
        assert "Scan part content" in result.content
        assert result.metadata["segments"] == 2
        assert result.tool_used == "segmented"


@pytest.mark.anyio
async def test_drawing_extraction_enabled(tmp_path: Path):
    """Test that drawings are NOT skipped when extract_drawing is True."""
    pipeline = ConversionPipeline(output_dir=tmp_path, extract_drawing=True)

    report = MagicMock(spec=PDFReport)
    report.category = "drawing"
    report.should_skip = True  # Standard check still returns True
    report.skip_reason = "Oversized"
    report.pages = 1
    report.recommended_model = "qwen-local-primary"  # Fixed: Add missing attribute
    report.to_dict.return_value = {"category": "drawing"}

    # Mock analyzer and converter
    with (
        patch.object(pipeline, "_analyze_pdf", return_value=report),
        patch.object(pipeline, "_create_drawing_converter") as mock_create_conv,
    ):
        mock_conv = AsyncMock()
        mock_conv.convert.return_value = ConversionResult(
            Path("dwg.pdf"), status=ConversionStatus.SUCCESS, content="Extracted from drawing"
        )
        mock_create_conv.return_value = mock_conv

        result = await pipeline.process_file(Path("dwg.pdf"))

        assert result.status == ConversionStatus.SUCCESS
        assert "Extracted" in result.content
        mock_create_conv.assert_called_once()


@pytest.mark.anyio
async def test_large_pdf_chunking(tmp_path: Path):
    """Test that a large non-hybrid PDF is chunked."""
    pipeline = ConversionPipeline(output_dir=tmp_path)

    report = MagicMock(spec=PDFReport)
    report.category = "text_rich"
    report.pages = 50
    report.should_skip = False
    report.recommended_model = "qwen-local-primary"
    report.to_dict.return_value = {"category": "text_rich"}

    # Mock split_pdf and converters
    with (
        patch.object(pipeline, "_analyze_pdf", return_value=report),
        patch("mdconverter.core.pipeline.split_pdf") as mock_split,
        patch.object(pipeline, "_create_converter_for_segment") as mock_create_conv,
        patch("shutil.rmtree"),
    ):
        # Should have 3 chunks (20, 20, 10)
        mock_split.return_value = [Path("c1.pdf"), Path("c2.pdf"), Path("c3.pdf")]

        mock_conv = AsyncMock()
        mock_conv.convert.return_value = ConversionResult(
            Path("c.pdf"), status=ConversionStatus.SUCCESS, content="Chunk"
        )
        mock_create_conv.return_value = mock_conv

        result = await pipeline.process_file(Path("large.pdf"))

        assert result.tool_used == "segmented"
        assert result.metadata["segments"] == 3
        assert mock_split.call_count == 1
