"""
PDF Analyzer — Refactored to use ccba_pdf_prep.
"""

from __future__ import annotations

import logging
from pathlib import Path

from ccba_pdf_prep import (
    PageDetail,
    PDFCategory,
)
from ccba_pdf_prep import (
    PDFAnalyzer as BaseAnalyzer,
)
from ccba_pdf_prep import (
    PDFReport as BaseReport,
)
from ccba_pdf_prep import (
    Segment as BaseSegment,
)

logger = logging.getLogger(__name__)

# Re-export Enums and simple dataclasses
__all__ = ["PDFCategory", "PageDetail", "Segment", "PDFReport", "PDFAnalyzer"]

class Segment(BaseSegment):
    """Segment with mdconverter specific defaults."""
    pass

class PDFReport(BaseReport):
    """Report with mdconverter specific logic."""

    def get_segments(self) -> list[Segment]:
        """Group contiguous pages of the same type into segments with mdconverter defaults."""
        hints = {
            "text": "qwen3.5-35b",
            "scan": "ocr-primary",
            "drawing": "qwen3.5-35b",
        }
        # In mdconverter, we use specific hints
        base_segments = super().get_segments(model_hints=hints)
        # Convert back to mdconverter Segment if needed, though they are compatible
        return [Segment(s.start_page, s.end_page, s.page_type, s.model_hint) for s in base_segments]

    @property
    def should_skip(self) -> bool:
        """Whether this PDF should be skipped by mdconverter."""
        return self.category == PDFCategory.DRAWING

    @property
    def skip_reason(self) -> str:
        """Human-readable reason for skipping."""
        if self.category == PDFCategory.DRAWING:
            return (
                f"Engineering drawing detected "
                f"({self.drawing_pages}/{self.pages} oversized pages). "
                f"Use specialised QC tools instead."
            )
        return ""

class PDFAnalyzer(BaseAnalyzer):
    """Analyzer subclass for mdconverter."""

    def analyze(self, pdf_path: Path) -> PDFReport:
        """Analyze and return mdconverter-specialized report."""
        base_report = super().analyze(pdf_path)
        # Cast/wrap the base report into our specialized report
        return PDFReport(
            file_path=base_report.file_path,
            category=base_report.category,
            recommended_model=base_report.recommended_model,
            confidence=base_report.confidence,
            pages=base_report.pages,
            text_pages=base_report.text_pages,
            image_pages=base_report.image_pages,
            drawing_pages=base_report.drawing_pages,
            total_text_chars=base_report.total_text_chars,
            avg_text_density=base_report.avg_text_density,
            size_mb=base_report.size_mb,
            is_oversized=base_report.is_oversized,
            page_details=base_report.page_details,
        )
