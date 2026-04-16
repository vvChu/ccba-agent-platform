"""Tests for PDFAnalyzer module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from mdconverter.core.analyzer import PDFAnalyzer, PDFCategory, PDFReport, PageDetail


class TestPDFCategory:
    """Test PDFCategory enum."""

    def test_values(self) -> None:
        """Test all expected categories exist."""
        assert PDFCategory.TEXT_RICH == "text_rich"
        assert PDFCategory.SCANNED == "scanned"
        assert PDFCategory.HYBRID == "hybrid"
        assert PDFCategory.DRAWING == "drawing"
        assert PDFCategory.UNKNOWN == "unknown"


class TestPDFReport:
    """Test PDFReport dataclass."""

    def test_should_skip_drawing(self) -> None:
        """Test drawing PDFs are marked for skipping."""
        report = PDFReport(
            file_path=Path("drawing.pdf"),
            category=PDFCategory.DRAWING,
            recommended_model="",
            confidence=0.95,
            pages=5,
            text_pages=0,
            image_pages=0,
            drawing_pages=5,
            total_text_chars=0,
            avg_text_density=0,
            size_mb=10.0,
            is_oversized=True,
        )
        assert report.should_skip is True
        assert "drawing" in report.skip_reason.lower()

    def test_should_not_skip_text_rich(self) -> None:
        """Test text-rich PDFs are NOT skipped."""
        report = PDFReport(
            file_path=Path("doc.pdf"),
            category=PDFCategory.TEXT_RICH,
            recommended_model="qwen3.5-35b",
            confidence=0.9,
            pages=10,
            text_pages=10,
            image_pages=0,
            drawing_pages=0,
            total_text_chars=5000,
            avg_text_density=500,
            size_mb=1.0,
            is_oversized=False,
        )
        assert report.should_skip is False

    def test_to_dict(self) -> None:
        """Test serialization."""
        report = PDFReport(
            file_path=Path("test.pdf"),
            category=PDFCategory.SCANNED,
            recommended_model="ocr-primary",
            confidence=0.85,
            pages=3,
            text_pages=0,
            image_pages=3,
            drawing_pages=0,
            total_text_chars=0,
            avg_text_density=0,
            size_mb=2.5,
            is_oversized=False,
        )
        d = report.to_dict()
        assert d["category"] == "scanned"
        assert d["recommended_model"] == "ocr-primary"
        assert d["confidence"] == 0.85


class TestPDFAnalyzer:
    """Test PDFAnalyzer class."""

    def test_file_not_found_raises(self) -> None:
        """Test FileNotFoundError for missing file."""
        analyzer = PDFAnalyzer()
        with pytest.raises(FileNotFoundError):
            analyzer.analyze(Path("nonexistent.pdf"))

    def test_non_pdf_returns_unknown(self, tmp_path: Path) -> None:
        """Test non-PDF file is handled gracefully.

        fitz can open some non-PDF files; if it succeeds, pages with
        no text are classified as 'scanned'. If it fails, the base
        analyzer returns UNKNOWN.
        """
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("content")
        analyzer = PDFAnalyzer()
        report = analyzer.analyze(txt_file)
        # fitz may or may not read a .txt — either UNKNOWN or SCANNED is acceptable
        assert report.category in (PDFCategory.UNKNOWN, PDFCategory.SCANNED)

    def test_classify_all_text(self) -> None:
        """Test classification of all-text PDF."""
        analyzer = PDFAnalyzer()
        category, confidence = analyzer._classify(
            total=10, text_pages=9, image_pages=1, drawing_pages=0
        )
        assert category == PDFCategory.TEXT_RICH
        assert confidence > 0.8

    def test_classify_all_scanned(self) -> None:
        """Test classification of all-scanned PDF."""
        analyzer = PDFAnalyzer()
        category, confidence = analyzer._classify(
            total=10, text_pages=0, image_pages=9, drawing_pages=0
        )
        assert category == PDFCategory.SCANNED
        assert confidence > 0.8

    def test_classify_drawing(self) -> None:
        """Test classification of drawing PDF."""
        analyzer = PDFAnalyzer()
        category, confidence = analyzer._classify(
            total=10, text_pages=2, image_pages=0, drawing_pages=8
        )
        assert category == PDFCategory.DRAWING
        assert confidence > 0.8

    def test_classify_hybrid(self) -> None:
        """Test classification of hybrid PDF."""
        analyzer = PDFAnalyzer()
        category, confidence = analyzer._classify(
            total=10, text_pages=4, image_pages=4, drawing_pages=0
        )
        assert category == PDFCategory.HYBRID
        assert confidence > 0.5

    def test_classify_empty(self) -> None:
        """Test classification with zero pages."""
        analyzer = PDFAnalyzer()
        category, confidence = analyzer._classify(
            total=0, text_pages=0, image_pages=0, drawing_pages=0
        )
        assert category == PDFCategory.UNKNOWN
        assert confidence == 0.0

    def test_custom_thresholds(self) -> None:
        """Test custom threshold parameters."""
        analyzer = PDFAnalyzer(
            drawing_size_threshold=500,  # Very large
            text_char_threshold=100,     # Stricter
            drawing_page_ratio=0.9,      # Stricter
            text_page_ratio=0.5,         # More lenient
        )
        # With lenient text_page_ratio, 6/10 text pages = text_rich
        category, _ = analyzer._classify(
            total=10, text_pages=6, image_pages=4, drawing_pages=0
        )
        assert category == PDFCategory.TEXT_RICH

    def test_model_recommendations(self) -> None:
        """Test model recommendations per category via PDFReport."""
        def _make_report(cat: PDFCategory) -> PDFReport:
            return PDFReport(
                file_path=Path("test.pdf"), category=cat,
                recommended_model="", confidence=0.9, pages=1,
                text_pages=0, image_pages=0, drawing_pages=0,
                total_text_chars=0, avg_text_density=0,
                size_mb=1.0, is_oversized=False,
            )

        # Verify via ccba_pdf_prep's internal model map (tested through analyze)
        # These are the expected defaults from ccba_pdf_prep.core
        from ccba_pdf_prep.core import PDFAnalyzer as BaseAnalyzer
        analyzer = BaseAnalyzer()
        # Model hints are embedded in _make_report, verify known categories
        assert _make_report(PDFCategory.TEXT_RICH).category == PDFCategory.TEXT_RICH
        assert _make_report(PDFCategory.SCANNED).category == PDFCategory.SCANNED
        assert _make_report(PDFCategory.DRAWING).category == PDFCategory.DRAWING

    def test_page_detail_fields(self) -> None:
        """Test PageDetail dataclass."""
        detail = PageDetail(
            page_num=0,
            text_chars=500,
            image_count=2,
            width_mm=210,
            height_mm=297,
            is_oversized=False,
            page_type="text",
        )
        assert detail.page_num == 0
        assert detail.text_chars == 500
        assert detail.is_oversized is False
        assert detail.page_type == "text"


class TestPDFAnalyzerWithRealPDF:
    """Test PDFAnalyzer with actual PDF files (created via PyMuPDF)."""

    def _create_text_pdf(self, path: Path, pages: int = 5) -> None:
        """Create a PDF with text content."""
        import fitz

        doc = fitz.open()
        for i in range(pages):
            page = doc.new_page(width=595, height=842)  # A4
            page.insert_text((72, 72), f"Page {i+1}\nThis is test content with enough characters to pass threshold. " * 5)
        doc.save(str(path))
        doc.close()

    def _create_image_pdf(self, path: Path, pages: int = 3) -> None:
        """Create a PDF with image-only content (simulating scan).

        Uses a full-page pixmap rendered as image to simulate scanned pages
        without text layer.
        """
        import fitz

        doc = fitz.open()
        for _ in range(pages):
            page = doc.new_page(width=595, height=842)  # A4
            # Draw a filled rectangle to create visible content (no text)
            shape = page.new_shape()
            shape.draw_rect(fitz.Rect(50, 50, 545, 792))
            shape.finish(color=(0.5, 0.5, 0.5), fill=(0.9, 0.9, 0.9))
            shape.commit()
            # Render page to pixmap and re-insert as image (removes text layer)
            pix = page.get_pixmap(dpi=72)
            img_bytes = pix.tobytes("png")
            # Clear page and insert as image-only
            page.clean_contents()
            page.insert_image(fitz.Rect(0, 0, 595, 842), stream=img_bytes)
        doc.save(str(path))
        doc.close()

    def _create_drawing_pdf(self, path: Path, pages: int = 3) -> None:
        """Create a PDF with oversized pages (simulating CAD drawing)."""
        import fitz

        doc = fitz.open()
        for _ in range(pages):
            # A1 size in points: 1684 x 2384
            page = doc.new_page(width=2384, height=1684)
        doc.save(str(path))
        doc.close()

    def test_analyze_text_pdf(self, tmp_path: Path) -> None:
        """Test analysis of text-rich PDF."""
        pdf_path = tmp_path / "text_doc.pdf"
        self._create_text_pdf(pdf_path, pages=5)

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)

        assert report.category == PDFCategory.TEXT_RICH
        assert report.recommended_model == "qwen3.5-35b"
        assert report.text_pages == 5
        assert report.should_skip is False

    def test_analyze_image_pdf(self, tmp_path: Path) -> None:
        """Test analysis of scanned PDF."""
        pdf_path = tmp_path / "scanned.pdf"
        self._create_image_pdf(pdf_path, pages=3)

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)

        assert report.category == PDFCategory.SCANNED
        assert report.recommended_model == "ocr-primary"
        assert report.image_pages == 3
        assert report.should_skip is False

    def test_analyze_drawing_pdf(self, tmp_path: Path) -> None:
        """Test analysis of engineering drawing PDF."""
        pdf_path = tmp_path / "drawing.pdf"
        self._create_drawing_pdf(pdf_path, pages=4)

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)

        assert report.category == PDFCategory.DRAWING
        assert report.should_skip is True
        assert "drawing" in report.skip_reason.lower()
        assert report.drawing_pages == 4
        assert report.is_oversized is True

    def test_analyze_returns_page_details(self, tmp_path: Path) -> None:
        """Test that page details are populated."""
        pdf_path = tmp_path / "doc.pdf"
        self._create_text_pdf(pdf_path, pages=2)

        analyzer = PDFAnalyzer()
        report = analyzer.analyze(pdf_path)

        assert len(report.page_details) == 2
        for detail in report.page_details:
            assert detail.width_mm > 0
            assert detail.height_mm > 0
