"""
PDF Analyzer — classify PDFs to auto-select optimal converter.

Uses PyMuPDF (fitz) to inspect text layers, image content, and page
dimensions without performing actual conversion.  The analysis takes
~50-200ms per file, which is acceptable given the accuracy gain.

Categories
----------
- **text_rich**: Digitally created PDFs with extractable text (export from
  Word, CAD annotation text).  Best handled by standard LLM models.
- **scanned**: Image-only pages from scanners / cameras.  Requires OCR.
- **hybrid**: Mix of text and scanned pages.  Route through OCR model
  which can handle both.
- **drawing**: Engineering/CAD drawings on oversized pages (A3+).
  Skipped by mdconverter — processed by specialised QC skills.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------
class PDFCategory(str, Enum):
    """Classification of a PDF document."""

    TEXT_RICH = "text_rich"
    SCANNED = "scanned"
    HYBRID = "hybrid"
    DRAWING = "drawing"
    UNKNOWN = "unknown"


@dataclass
class PageDetail:
    """Analysis result for a single page."""

    page_num: int
    text_chars: int
    image_count: int
    width_mm: float
    height_mm: float
    is_oversized: bool
    page_type: str  # "text", "scan", "drawing"


@dataclass
class PDFReport:
    """Complete analysis report for a PDF file."""

    file_path: Path
    category: PDFCategory
    recommended_model: str
    confidence: float
    pages: int
    text_pages: int
    image_pages: int
    drawing_pages: int
    total_text_chars: int
    avg_text_density: float
    size_mb: float
    is_oversized: bool
    page_details: list[PageDetail] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Serialize report to dictionary."""
        return {
            "file": str(self.file_path.name),
            "category": self.category.value,
            "recommended_model": self.recommended_model,
            "confidence": self.confidence,
            "pages": self.pages,
            "text_pages": self.text_pages,
            "image_pages": self.image_pages,
            "drawing_pages": self.drawing_pages,
            "avg_text_density": self.avg_text_density,
            "size_mb": self.size_mb,
        }

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


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------
# Default model recommendations per category
_MODEL_MAP: dict[PDFCategory, str] = {
    PDFCategory.TEXT_RICH: "qwen3.5-35b",
    PDFCategory.SCANNED: "ocr-primary",
    PDFCategory.HYBRID: "ocr-primary",
    PDFCategory.DRAWING: "",  # skipped
    PDFCategory.UNKNOWN: "gemini-3-flash",
}


class PDFAnalyzer:
    """Analyze PDF files to determine optimal conversion strategy.

    Uses heuristics based on:
    - **Page dimensions** — oversized pages (>A3) indicate drawings
    - **Text layer presence** — extractable text vs image-only
    - **Image density** — high image count with zero text = scanned

    Args:
        drawing_size_threshold: Minimum dimension (mm) to flag as drawing.
            Default 350mm ≈ A3 long edge.
        text_char_threshold: Minimum characters per page to count as
            "has text".  Default 50.
        drawing_page_ratio: Fraction of oversized pages required to
            classify as drawing.  Default 0.5.
        text_page_ratio: Fraction of text pages required to classify
            as text_rich.  Default 0.8.
    """

    def __init__(
        self,
        drawing_size_threshold: float = 350.0,
        text_char_threshold: int = 50,
        drawing_page_ratio: float = 0.5,
        text_page_ratio: float = 0.8,
    ) -> None:
        self.drawing_size_threshold = drawing_size_threshold
        self.text_char_threshold = text_char_threshold
        self.drawing_page_ratio = drawing_page_ratio
        self.text_page_ratio = text_page_ratio

    def analyze(self, pdf_path: Path) -> PDFReport:
        """Analyze a PDF file and return classification report.

        Args:
            pdf_path: Path to the PDF file.

        Returns:
            PDFReport with category, recommended model, and page details.

        Raises:
            FileNotFoundError: If pdf_path does not exist.
            ValueError: If file is not a PDF.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        if pdf_path.suffix.lower() != ".pdf":
            raise ValueError(f"Not a PDF file: {pdf_path}")

        size_mb = round(pdf_path.stat().st_size / (1024 * 1024), 2)

        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            logger.warning("Failed to open %s: %s", pdf_path.name, e)
            return self._make_report(
                pdf_path, size_mb, PDFCategory.UNKNOWN, 0.0, [], 0
            )

        page_details: list[PageDetail] = []
        text_pages = 0
        image_pages = 0
        drawing_pages = 0
        total_text_chars = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            detail = self._analyze_page(page, page_num)
            page_details.append(detail)

            total_text_chars += detail.text_chars

            if detail.page_type == "drawing":
                drawing_pages += 1
            elif detail.page_type == "text":
                text_pages += 1
            elif detail.page_type == "scan":
                image_pages += 1

        doc.close()

        num_pages = len(page_details)
        category, confidence = self._classify(
            num_pages, text_pages, image_pages, drawing_pages
        )

        return self._make_report(
            pdf_path, size_mb, category, confidence,
            page_details, total_text_chars,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _analyze_page(self, page: fitz.Page, page_num: int) -> PageDetail:
        """Analyze a single PDF page."""
        rect = page.rect
        w_mm = round(rect.width * 25.4 / 72, 1)
        h_mm = round(rect.height * 25.4 / 72, 1)
        is_oversized = w_mm > self.drawing_size_threshold or h_mm > self.drawing_size_threshold

        text = page.get_text("text")
        char_count = len(text.strip())

        image_list = page.get_images(full=True)
        num_images = len(image_list)

        # Classify page
        if is_oversized:
            page_type = "drawing"
        elif char_count >= self.text_char_threshold:
            page_type = "text"
        elif num_images > 0:
            page_type = "scan"
        else:
            page_type = "scan"  # empty page → treat as scan

        return PageDetail(
            page_num=page_num,
            text_chars=char_count,
            image_count=num_images,
            width_mm=w_mm,
            height_mm=h_mm,
            is_oversized=is_oversized,
            page_type=page_type,
        )

    def _classify(
        self,
        total: int,
        text_pages: int,
        image_pages: int,
        drawing_pages: int,
    ) -> tuple[PDFCategory, float]:
        """Classify PDF based on page type distribution.

        Returns:
            Tuple of (category, confidence 0.0-1.0).
        """
        if total == 0:
            return PDFCategory.UNKNOWN, 0.0

        drawing_ratio = drawing_pages / total
        text_ratio = text_pages / total
        image_ratio = image_pages / total

        # Priority 1: Drawing (oversized pages dominate)
        if drawing_ratio >= self.drawing_page_ratio:
            confidence = min(drawing_ratio + 0.1, 1.0)
            return PDFCategory.DRAWING, round(confidence, 2)

        # Priority 2: Text-rich (mostly text pages)
        if text_ratio >= self.text_page_ratio:
            confidence = min(text_ratio + 0.05, 1.0)
            return PDFCategory.TEXT_RICH, round(confidence, 2)

        # Priority 3: Scanned (mostly image pages, no text)
        if image_ratio >= self.text_page_ratio:
            confidence = min(image_ratio + 0.05, 1.0)
            return PDFCategory.SCANNED, round(confidence, 2)

        # Priority 4: Hybrid (significant mix)
        if text_ratio > 0 and (image_ratio > 0 or drawing_ratio > 0):
            confidence = 0.7  # inherently less certain
            return PDFCategory.HYBRID, confidence

        return PDFCategory.UNKNOWN, 0.3

    def _make_report(
        self,
        pdf_path: Path,
        size_mb: float,
        category: PDFCategory,
        confidence: float,
        page_details: list[PageDetail],
        total_text_chars: int,
    ) -> PDFReport:
        """Construct a PDFReport from analysis data."""
        num_pages = len(page_details)
        text_pages = sum(1 for p in page_details if p.page_type == "text")
        image_pages = sum(1 for p in page_details if p.page_type == "scan")
        drawing_pages = sum(1 for p in page_details if p.page_type == "drawing")
        avg_density = round(total_text_chars / max(num_pages, 1), 1)
        is_oversized = any(p.is_oversized for p in page_details)

        return PDFReport(
            file_path=pdf_path,
            category=category,
            recommended_model=_MODEL_MAP.get(category, "gemini-3-flash"),
            confidence=confidence,
            pages=num_pages,
            text_pages=text_pages,
            image_pages=image_pages,
            drawing_pages=drawing_pages,
            total_text_chars=total_text_chars,
            avg_text_density=avg_density,
            size_mb=size_mb,
            is_oversized=is_oversized,
            page_details=page_details,
        )
