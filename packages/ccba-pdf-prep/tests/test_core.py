"""Tests for ccba_pdf_prep.core module."""

from pathlib import Path

import pytest

from ccba_pdf_prep import (
    PDFAnalyzer,
    PDFCategory,
    PDFReport,
    PageDetail,
    Segment,
    get_blind_chunks,
    split_pdf,
)


# ---------------------------------------------------------------------------
# get_blind_chunks
# ---------------------------------------------------------------------------
class TestGetBlindChunks:
    """Tests for blind chunking logic."""

    def test_basic_split(self) -> None:
        ranges = get_blind_chunks(50, chunk_size=20)
        assert ranges == [(0, 19), (20, 39), (40, 49)]

    def test_single_chunk(self) -> None:
        ranges = get_blind_chunks(5, chunk_size=10)
        assert ranges == [(0, 4)]

    def test_exact_multiple(self) -> None:
        ranges = get_blind_chunks(40, chunk_size=20)
        assert ranges == [(0, 19), (20, 39)]

    def test_zero_pages(self) -> None:
        ranges = get_blind_chunks(0, chunk_size=20)
        assert ranges == []

    def test_one_page(self) -> None:
        ranges = get_blind_chunks(1, chunk_size=20)
        assert ranges == [(0, 0)]


# ---------------------------------------------------------------------------
# split_pdf
# ---------------------------------------------------------------------------
class TestSplitPdf:
    """Tests for PDF splitting."""

    def test_split_into_two(self, tmp_pdf_large: Path, tmp_path: Path) -> None:
        ranges = [(0, 9), (10, 24)]
        chunks = split_pdf(tmp_pdf_large, ranges, tmp_path / "out")
        assert len(chunks) == 2
        assert all(c.exists() for c in chunks)

        from pypdf import PdfReader

        assert len(PdfReader(chunks[0]).pages) == 10
        assert len(PdfReader(chunks[1]).pages) == 15

    def test_split_file_not_found(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            split_pdf(tmp_path / "nonexistent.pdf", [(0, 4)], tmp_path / "out")

    def test_split_empty_ranges(self, tmp_pdf_large: Path, tmp_path: Path) -> None:
        chunks = split_pdf(tmp_pdf_large, [], tmp_path / "out")
        assert chunks == []


# ---------------------------------------------------------------------------
# PDFAnalyzer
# ---------------------------------------------------------------------------
class TestPDFAnalyzer:
    """Tests for PDF analysis and classification."""

    def test_analyze_text_rich(self, tmp_pdf_text: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_text)

        assert report.pages == 3
        assert report.category == PDFCategory.TEXT_RICH
        assert report.text_pages == 3
        assert report.drawing_pages == 0
        assert report.total_text_chars > 0
        assert report.confidence > 0.5

    def test_analyze_drawing(self, tmp_pdf_drawing: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_drawing)

        assert report.pages == 1
        assert report.category == PDFCategory.DRAWING
        assert report.drawing_pages == 1
        assert report.is_oversized is True

    def test_analyze_scan(self, tmp_pdf_scan: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_scan)

        assert report.pages == 2
        # Minimal text → classified as scanned
        assert report.category == PDFCategory.SCANNED
        assert report.image_pages == 2

    def test_analyze_file_not_found(self, tmp_path: Path) -> None:
        analyzer = PDFAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze(tmp_path / "nonexistent.pdf")

    def test_report_to_dict(self, tmp_pdf_text: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_text)
        d = report.to_dict()

        assert "file" in d
        assert "category" in d
        assert d["category"] == "text_rich"
        assert "pages" in d


# ---------------------------------------------------------------------------
# Segment grouping
# ---------------------------------------------------------------------------
class TestSegments:
    """Tests for segment grouping logic."""

    def test_segments_text_only(self, tmp_pdf_text: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_text)
        segments = report.get_segments()

        # All text pages → single segment
        assert len(segments) == 1
        assert segments[0].page_type == "text"
        assert segments[0].page_count == 3

    def test_segment_page_count(self) -> None:
        seg = Segment(start_page=5, end_page=10, page_type="text")
        assert seg.page_count == 6

    def test_segment_model_hints(self, tmp_pdf_text: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_text)
        custom_hints = {"text": "my-model", "scan": "ocr", "drawing": "vision"}
        segments = report.get_segments(model_hints=custom_hints)

        assert segments[0].model_hint == "my-model"


# ---------------------------------------------------------------------------
# PageDetail
# ---------------------------------------------------------------------------
class TestPageDetail:
    """Tests for page detail dataclass."""

    def test_page_detail_fields(self, tmp_pdf_text: Path) -> None:
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(tmp_pdf_text)

        assert len(report.page_details) == 3
        p0 = report.page_details[0]
        assert p0.page_num == 0
        assert p0.text_chars > 0
        assert p0.is_oversized is False
        assert p0.page_type == "text"
        # A4 is ~210 × 297 mm
        assert 200 < p0.width_mm < 220
        assert 290 < p0.height_mm < 300
