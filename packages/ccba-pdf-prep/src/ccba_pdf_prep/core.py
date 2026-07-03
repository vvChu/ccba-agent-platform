"""
CCBA PDF Preprocessor — Core logic for document analysis and manipulation.
Migrated and generalized from mdconverter.
"""

import logging
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF
from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)

# --- Data Models ---


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
class Segment:
    """A contiguous range of pages of the same type."""

    start_page: int  # 0-indexed
    end_page: int  # 0-indexed, inclusive
    page_type: str  # "text", "scan", "drawing"
    model_hint: str = ""

    @property
    def page_count(self) -> int:
        return self.end_page - self.start_page + 1


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

    def get_segments(self, model_hints: dict[str, str] | None = None) -> list[Segment]:
        """Group contiguous pages of the same type into segments."""
        if not self.page_details:
            return []

        hints = model_hints or {
            "text": "qwen3.5-35b",
            "scan": "ocr-primary",
            "drawing": "qwen3.5-35b",
        }

        segments: list[Segment] = []
        current_start = 0
        current_type = self.page_details[0].page_type

        for i in range(1, len(self.page_details)):
            ptype = self.page_details[i].page_type
            if ptype != current_type:
                segments.append(
                    Segment(
                        start_page=current_start,
                        end_page=i - 1,
                        page_type=current_type,
                        model_hint=hints.get(current_type, ""),
                    )
                )
                current_start = i
                current_type = ptype

        segments.append(
            Segment(
                start_page=current_start,
                end_page=len(self.page_details) - 1,
                page_type=current_type,
                model_hint=hints.get(current_type, ""),
            )
        )
        return segments


# --- Analyzer ---


class PDFAnalyzer:
    """Analyze PDF files to determine optimal processing strategy."""

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
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        size_mb = round(pdf_path.stat().st_size / (1024 * 1024), 2)
        try:
            doc = fitz.open(str(pdf_path))
        except Exception as e:
            logger.warning("Failed to open %s: %s", pdf_path.name, e)
            return self._make_report(pdf_path, size_mb, PDFCategory.UNKNOWN, 0.0, [], 0)

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
        category, confidence = self._classify(num_pages, text_pages, image_pages, drawing_pages)

        return self._make_report(
            pdf_path, size_mb, category, confidence, page_details, total_text_chars
        )

    def _analyze_page(self, page: fitz.Page, page_num: int) -> PageDetail:
        rect = page.rect
        w_mm = round(rect.width * 25.4 / 72, 1)
        h_mm = round(rect.height * 25.4 / 72, 1)
        is_oversized = w_mm > self.drawing_size_threshold or h_mm > self.drawing_size_threshold

        text = page.get_text("text").strip()
        char_count = len(text)
        num_images = len(page.get_images(full=True))

        if is_oversized:
            page_type = "drawing"
        elif char_count >= self.text_char_threshold:
            page_type = "text"
        else:
            page_type = "scan"

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
        self, total: int, text_pages: int, image_pages: int, drawing_pages: int
    ) -> tuple[PDFCategory, float]:
        if total == 0:
            return PDFCategory.UNKNOWN, 0.0
        drawing_ratio = drawing_pages / total
        text_ratio = text_pages / total
        image_ratio = image_pages / total

        if drawing_ratio >= self.drawing_page_ratio:
            return PDFCategory.DRAWING, round(min(drawing_ratio + 0.1, 1.0), 2)
        if text_ratio >= self.text_page_ratio:
            return PDFCategory.TEXT_RICH, round(min(text_ratio + 0.05, 1.0), 2)
        if image_ratio >= self.text_page_ratio:
            return PDFCategory.SCANNED, round(min(image_ratio + 0.05, 1.0), 2)
        if text_ratio > 0 and (image_ratio > 0 or drawing_ratio > 0):
            return PDFCategory.HYBRID, 0.7
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
        num_pages = len(page_details)
        text_pages = sum(1 for p in page_details if p.page_type == "text")
        image_pages = sum(1 for p in page_details if p.page_type == "scan")
        drawing_pages = sum(1 for p in page_details if p.page_type == "drawing")
        avg_density = round(total_text_chars / max(num_pages, 1), 1)
        is_oversized = any(p.is_oversized for p in page_details)

        model_map = {
            PDFCategory.TEXT_RICH: "qwen3.5-35b",
            PDFCategory.SCANNED: "ocr-primary",
            PDFCategory.HYBRID: "ocr-primary",
            PDFCategory.DRAWING: "",
            PDFCategory.UNKNOWN: "gemini-3-flash",
        }

        return PDFReport(
            file_path=pdf_path,
            category=category,
            recommended_model=model_map.get(category, "gemini-3-flash"),
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


# --- Utilities ---


def split_pdf(
    source: Path, page_ranges: Sequence[tuple[int, int]], output_temp_dir: Path
) -> list[Path]:
    """Split PDF into chunks."""
    if not source.exists():
        raise FileNotFoundError(f"Source PDF not found: {source}")
    output_temp_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(source)
    chunk_paths = []

    for i, (start, end) in enumerate(page_ranges):
        start = max(0, start)
        end = min(len(reader.pages) - 1, end)
        if start > end:
            continue

        writer = PdfWriter()
        for page_num in range(start, end + 1):
            writer.add_page(reader.pages[page_num])

        chunk_path = output_temp_dir / f"{source.stem}_part{i + 1}.pdf"
        with open(chunk_path, "wb") as f:
            writer.write(f)
        chunk_paths.append(chunk_path)
    return chunk_paths


def get_blind_chunks(total_pages: int, chunk_size: int = 20) -> list[tuple[int, int]]:
    """Generate equitable page ranges."""
    return [
        (s, min(s + chunk_size - 1, total_pages - 1)) for s in range(0, total_pages, chunk_size)
    ]


def render_page_to_image(
    pdf_path: Path,
    page_num: int,
    output_path: Path,
    dpi: int = 150,
) -> Path:
    """Render a single page of a PDF file to a PNG/JPEG image.

    Args:
        pdf_path: Path to the PDF file.
        page_num: 0-indexed page number to render.
        output_path: Target path for the output image.
        dpi: Target DPI for rendering.

    Returns:
        Path to the saved image file.
    """
    import fitz

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(pdf_path))
    try:
        if page_num < 0 or page_num >= len(doc):
            raise IndexError(f"Page number {page_num} out of range for PDF with {len(doc)} pages")
        page = doc[page_num]
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=matrix)
        pix.save(str(output_path))
    finally:
        doc.close()

    return output_path

