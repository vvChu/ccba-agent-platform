"""Tests for PDFProcessingPipeline — the unified processing seam."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_pdf_prep import PDFProcessingError, PDFProcessingPipeline, ProcessingResult
from ccba_pdf_prep.core import (
    PageDetail,
    PDFCategory,
    PDFReport,
)

# ---------------------------------------------------------------------------
# Helpers / Fakes
# ---------------------------------------------------------------------------


def _make_report(
    tmp_path: Path,
    category: PDFCategory = PDFCategory.TEXT_RICH,
    pages: int = 3,
) -> PDFReport:
    """Build a minimal PDFReport without touching the filesystem."""
    page_details = [
        PageDetail(
            page_num=i,
            text_chars=200,
            image_count=0,
            width_mm=210.0,
            height_mm=297.0,
            is_oversized=False,
            page_type="text",
        )
        for i in range(pages)
    ]
    return PDFReport(
        file_path=tmp_path / "fake.pdf",
        category=category,
        recommended_model="qwen-local-primary",
        confidence=0.95,
        pages=pages,
        text_pages=pages,
        image_pages=0,
        drawing_pages=0,
        total_text_chars=pages * 200,
        avg_text_density=200.0,
        size_mb=0.5,
        is_oversized=False,
        page_details=page_details,
    )


def _make_drawing_report(tmp_path: Path) -> PDFReport:
    """Build a PDFReport that looks like an oversized drawing."""
    page_details = [
        PageDetail(
            page_num=0,
            text_chars=10,
            image_count=0,
            width_mm=841.0,  # A1 width
            height_mm=594.0,
            is_oversized=True,
            page_type="drawing",
        )
    ]
    return PDFReport(
        file_path=tmp_path / "drawing.pdf",
        category=PDFCategory.DRAWING,
        recommended_model="",
        confidence=0.9,
        pages=1,
        text_pages=0,
        image_pages=0,
        drawing_pages=1,
        total_text_chars=10,
        avg_text_density=10.0,
        size_mb=2.0,
        is_oversized=True,
        page_details=page_details,
    )


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------


class TestPipelineErrors:
    def test_raises_when_pdf_missing(self, tmp_path: Path) -> None:
        pipeline = PDFProcessingPipeline()
        with pytest.raises(PDFProcessingError, match="PDF not found"):
            pipeline.process(tmp_path / "nonexistent.pdf", tmp_path / "out")

    def test_raises_when_analyzer_fails(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_bytes(b"not a pdf")

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.side_effect = RuntimeError("corrupt file")

        pipeline = PDFProcessingPipeline(analyzer=mock_analyzer)
        with pytest.raises(PDFProcessingError, match="Analysis failed"):
            pipeline.process(fake_pdf, tmp_path / "out")


# ---------------------------------------------------------------------------
# Text-rich strategy
# ---------------------------------------------------------------------------


class TestTextRichStrategy:
    def test_returns_chunk_paths(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "doc.pdf"
        fake_pdf.write_bytes(b"placeholder")
        report = _make_report(tmp_path, PDFCategory.TEXT_RICH, pages=3)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = report

        # Patch split_pdf at the pipeline module level
        with patch("ccba_pdf_prep.pipeline.split_pdf") as mock_split:
            mock_split.return_value = [tmp_path / "chunk1.pdf", tmp_path / "chunk2.pdf"]
            pipeline = PDFProcessingPipeline(analyzer=mock_analyzer, chunk_size=2)
            result = pipeline.process(fake_pdf, tmp_path / "out")

        assert isinstance(result, ProcessingResult)
        assert result.report.category == PDFCategory.TEXT_RICH
        assert len(result.chunk_paths) == 2
        assert result.tile_paths == []
        assert result.titleblock_path is None

    def test_raises_when_split_fails(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "doc.pdf"
        fake_pdf.write_bytes(b"placeholder")
        report = _make_report(tmp_path, PDFCategory.TEXT_RICH)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = report

        with patch("ccba_pdf_prep.pipeline.split_pdf") as mock_split:
            mock_split.side_effect = OSError("disk full")
            pipeline = PDFProcessingPipeline(analyzer=mock_analyzer)
            with pytest.raises(PDFProcessingError, match="Chunking failed"):
                pipeline.process(fake_pdf, tmp_path / "out")


# ---------------------------------------------------------------------------
# Drawing strategy
# ---------------------------------------------------------------------------


class TestDrawingStrategy:
    def test_tiles_drawing_pages(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "drawing.pdf"
        fake_pdf.write_bytes(b"placeholder")
        report = _make_drawing_report(tmp_path)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = report

        mock_optimizer = MagicMock()
        tile1 = tmp_path / "tile_0_0.png"
        tile1.touch()
        mock_optimizer.tile_page_smart.return_value = ([tile1], [])

        mock_detector = MagicMock()
        mock_detector.extract.return_value = None  # No title block found

        mock_composer = MagicMock()

        pipeline = PDFProcessingPipeline(
            analyzer=mock_analyzer,
            optimizer=mock_optimizer,
            detector=mock_detector,
            composer=mock_composer,
        )
        result = pipeline.process(fake_pdf, tmp_path / "out")

        assert result.report.category == PDFCategory.DRAWING
        assert len(result.tile_paths) == 1
        mock_optimizer.tile_page_smart.assert_called_once_with(
            pdf_path=fake_pdf,
            page_num=0,
            output_dir=tmp_path / "out" / "tiles",
            dpi=300,
            tile_size_px=1024,
            min_ink_ratio=0.02,
        )

    def test_composite_built_when_four_tiles_available(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "drawing.pdf"
        fake_pdf.write_bytes(b"placeholder")
        report = _make_drawing_report(tmp_path)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = report

        tiles = [tmp_path / f"tile_{i}.png" for i in range(4)]
        for t in tiles:
            t.touch()

        mock_optimizer = MagicMock()
        mock_optimizer.tile_page_smart.return_value = (tiles, [])

        mock_detector = MagicMock()
        mock_detector.extract.return_value = tmp_path / "titleblock.png"

        composite_path = tmp_path / "composite.png"
        composite_path.touch()
        mock_composer = MagicMock()
        mock_composer.quad_view.return_value = composite_path

        pipeline = PDFProcessingPipeline(
            analyzer=mock_analyzer,
            optimizer=mock_optimizer,
            detector=mock_detector,
            composer=mock_composer,
        )
        result = pipeline.process(fake_pdf, tmp_path / "out")

        assert result.composite_path == composite_path
        assert result.titleblock_path == tmp_path / "titleblock.png"
        mock_composer.quad_view.assert_called_once()


# ---------------------------------------------------------------------------
# Unknown category — minimal result
# ---------------------------------------------------------------------------


class TestUnknownStrategy:
    def test_returns_segments_only(self, tmp_path: Path) -> None:
        fake_pdf = tmp_path / "weird.pdf"
        fake_pdf.write_bytes(b"placeholder")
        report = _make_report(tmp_path, PDFCategory.UNKNOWN, pages=2)

        mock_analyzer = MagicMock()
        mock_analyzer.analyze.return_value = report

        pipeline = PDFProcessingPipeline(analyzer=mock_analyzer)
        result = pipeline.process(fake_pdf, tmp_path / "out")

        assert result.report.category == PDFCategory.UNKNOWN
        assert result.chunk_paths == []
        assert result.tile_paths == []
        assert result.composite_path is None


# ---------------------------------------------------------------------------
# Integration: full text PDF
# ---------------------------------------------------------------------------


class TestIntegration:
    def test_text_pdf_end_to_end(self, tmp_path: Path, tmp_pdf_text: Path) -> None:
        """Integration test using a real text PDF fixture (no mocks)."""
        pipeline = PDFProcessingPipeline(chunk_size=2)
        result = pipeline.process(tmp_pdf_text, tmp_path / "out")

        assert result.report.category == PDFCategory.TEXT_RICH
        assert len(result.chunk_paths) >= 1
        assert all(p.exists() for p in result.chunk_paths)

    def test_drawing_pdf_end_to_end(self, tmp_path: Path, tmp_pdf_drawing: Path) -> None:
        """Integration test using a real drawing PDF fixture (no mocks).

        min_ink_ratio=0.0 disables blank-tile filtering — the synthetic fixture
        is very sparse so tiles would all be filtered at the default threshold.
        """
        pipeline = PDFProcessingPipeline(tile_dpi=72, tile_size_px=512, min_ink_ratio=0.0)
        result = pipeline.process(tmp_pdf_drawing, tmp_path / "out")

        assert result.report.category == PDFCategory.DRAWING
        assert len(result.tile_paths) >= 1
        assert all(p.exists() for p in result.tile_paths)
