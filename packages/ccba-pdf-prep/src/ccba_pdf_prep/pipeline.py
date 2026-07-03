"""
CCBA PDF Preprocessor — Unified processing pipeline.

Single deep module that coordinates analysis, tiling, title-block extraction,
and composite building behind one ``process()`` seam.

Callers only need::

    pipeline = PDFProcessingPipeline()
    result = pipeline.process(pdf_path, output_dir)

All strategy decisions (which steps to run for each document category) are
encapsulated here. Sub-modules are injectable for testing.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple, Any

import fitz  # PyMuPDF

from .composite import CompositeBuilder
from .core import PDFAnalyzer, PDFCategory, PDFReport, Segment, get_blind_chunks, split_pdf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Vision Data types
# ---------------------------------------------------------------------------


class TileResult(NamedTuple):
    """Metadata for a single tile."""

    path: Path
    row: int
    col: int
    ink_ratio: float
    skipped: bool


class TitleBlockRegion(NamedTuple):
    """Bounding box of a detected title block (in page points)."""

    x0: float
    y0: float
    x1: float
    y1: float

    @property
    def rect(self) -> fitz.Rect:
        return fitz.Rect(self.x0, self.y0, self.x1, self.y1)

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


# ---------------------------------------------------------------------------
# Vision Helpers
# ---------------------------------------------------------------------------


def _compute_ink_ratio(pixmap: fitz.Pixmap) -> float:
    """Return fraction of non-white pixels (0.0-1.0) in a pixmap.

    Uses PyMuPDF's color-space samples directly to avoid a Pillow dependency
    for this specific check.
    """
    samples = pixmap.samples  # raw bytes, n channels per pixel
    n = pixmap.n  # channels (3=RGB, 4=RGBA)
    total = pixmap.width * pixmap.height
    if total == 0:
        return 0.0

    white = 0
    for i in range(0, len(samples), n):
        if samples[i] == 255 and samples[i + 1] == 255 and samples[i + 2] == 255:
            white += 1

    return 1.0 - (white / total)


def _normalize_vn(text: str) -> str:
    """Normalize Vietnamese diacritics for robust matching."""
    import unicodedata

    return "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )


# ---------------------------------------------------------------------------
# VisionOptimizer
# ---------------------------------------------------------------------------


class VisionOptimizer:
    """Utilities for optimizing PDF pages for AI Vision models."""

    @staticmethod
    def tile_page(
        pdf_path: Path,
        page_num: int,
        output_dir: Path,
        dpi: int = 300,
        tile_size_px: int = 1024,
        overlap_px: int = 0,
    ) -> list[Path]:
        """Render a PDF page at high DPI and slice it into tiles.

        Uses the 'clip' parameter for memory efficiency.

        Args:
            pdf_path: Path to the PDF file.
            page_num: Page index (0-indexed).
            output_dir: Directory to save tiles.
            dpi: Dots per inch for rendering.
            tile_size_px: Size of each square tile in pixels.
            overlap_px: Pixels of overlap between adjacent tiles.

        Returns:
            List of paths to generated image files.
        """
        results = VisionOptimizer._tile_internal(
            pdf_path=pdf_path,
            page_num=page_num,
            output_dir=output_dir,
            dpi=dpi,
            tile_size_px=tile_size_px,
            overlap_px=overlap_px,
            min_ink_ratio=None,
        )
        return [r.path for r in results if not r.skipped]

    @staticmethod
    def tile_page_smart(
        pdf_path: Path,
        page_num: int,
        output_dir: Path,
        dpi: int = 300,
        tile_size_px: int = 1024,
        overlap_px: int = 0,
        min_ink_ratio: float = 0.02,
    ) -> tuple[list[Path], list[TileResult]]:
        """Tile a page, skipping blank (white-space) tiles.

        Engineering drawings often have large white margins. Filtering tiles
        with < ``min_ink_ratio`` non-white pixels reduces API token usage
        by 30-50% on typical A1/A0 drawings.

        Args:
            pdf_path: Path to the PDF file.
            page_num: Page index (0-indexed).
            output_dir: Directory to save tiles.
            dpi: Rendering DPI.
            tile_size_px: Tile size in pixels.
            overlap_px: Overlap between tiles in pixels.
            min_ink_ratio: Minimum fraction of non-white pixels to keep a tile.

        Returns:
            Tuple of (kept_tile_paths, all_tile_results).
            all_tile_results includes skipped tiles with skipped=True.
        """
        results = VisionOptimizer._tile_internal(
            pdf_path=pdf_path,
            page_num=page_num,
            output_dir=output_dir,
            dpi=dpi,
            tile_size_px=tile_size_px,
            overlap_px=overlap_px,
            min_ink_ratio=min_ink_ratio,
        )
        kept = [r.path for r in results if not r.skipped]
        skipped = sum(1 for r in results if r.skipped)
        logger.info(
            "Smart tiling: kept %d / %d tiles (skipped %d blanks)",
            len(kept),
            len(results),
            skipped,
        )
        return kept, results

    @staticmethod
    def _tile_internal(
        pdf_path: Path,
        page_num: int,
        output_dir: Path,
        dpi: int,
        tile_size_px: int,
        overlap_px: int,
        min_ink_ratio: float | None,
    ) -> list[TileResult]:
        """Internal tiling engine shared by tile_page and tile_page_smart."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        doc = fitz.open(str(pdf_path))
        page = doc[page_num]

        width_pts = page.rect.width
        height_pts = page.rect.height
        width_px = int(width_pts * dpi / 72)
        height_px = int(height_pts * dpi / 72)

        logger.info(
            "Tiling page %d at %d DPI. Total size: %dx%d px",
            page_num + 1,
            dpi,
            width_px,
            height_px,
        )

        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        results: list[TileResult] = []
        stride = tile_size_px - overlap_px

        for row, y in enumerate(range(0, height_px, stride)):
            for col, x in enumerate(range(0, width_px, stride)):
                x0 = x * 72 / dpi
                y0 = y * 72 / dpi
                x1 = min((x + tile_size_px) * 72 / dpi, width_pts)
                y1 = min((y + tile_size_px) * 72 / dpi, height_pts)

                clip = fitz.Rect(x0, y0, x1, y1)
                tile_pix = page.get_pixmap(matrix=matrix, clip=clip)

                ink = _compute_ink_ratio(tile_pix)
                skipped = (min_ink_ratio is not None) and (ink < min_ink_ratio)

                tile_name = f"{pdf_path.stem}_p{page_num + 1}_tile_{row}_{col}.png"
                tile_path = output_dir / tile_name

                if not skipped:
                    tile_pix.save(str(tile_path))
                    logger.debug("Tile [%d,%d] ink=%.1f%% saved", row, col, ink * 100)
                else:
                    logger.debug("Tile [%d,%d] ink=%.1f%% SKIPPED", row, col, ink * 100)

                results.append(
                    TileResult(
                        path=tile_path,
                        row=row,
                        col=col,
                        ink_ratio=ink,
                        skipped=skipped,
                    )
                )

        doc.close()
        logger.info("Generated %d tiles in %s", len(results), output_dir)
        return results


# ---------------------------------------------------------------------------
# TitleBlockDetector
# ---------------------------------------------------------------------------


class TitleBlockDetector:
    """Auto-detect and extract the title block from engineering drawings.

    In Vietnamese construction drawings (TCVN-style), the title block
    (khung ten) is typically located in the bottom-right corner of the
    sheet, occupying approximately:
      - Width: 15-25% of total page width
      - Height: 10-20% of total page height

    Detection uses two strategies:
    1. Vector path density in the bottom-right search region.
    2. Heuristic bounding box fallback (bottom-right fraction).
    """

    _SEARCH_RIGHT_FRAC = 0.30  # Rightmost 30% of page width
    _SEARCH_BOTTOM_FRAC = 0.25  # Bottom 25% of page height
    _MIN_CONTENT_RATIO = 0.02  # Minimum ink ratio to accept heuristic region

    @classmethod
    def detect(
        cls,
        pdf_path: Path,
        page_num: int = 0,
        force: bool = False,
    ) -> TitleBlockRegion | None:
        """Detect the title block region on a drawing page.

        Args:
            pdf_path: Path to the PDF file.
            page_num: Page index (0-indexed).
            force: If True, always return the heuristic bottom-right region
                   even when ink content is below the threshold. Use this for
                   sparse single-page A1/A0 drawings where the title block is
                   present but rendered lightly.

        Returns:
            TitleBlockRegion with coordinates in page points, or None if
            no title block is detected (and force=False).
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        page = doc[page_num]
        w = page.rect.width
        h = page.rect.height

        region = cls._detect_via_paths(page, w, h)
        if region:
            doc.close()
            return region

        region = cls._detect_heuristic(page, w, h, force=force)
        doc.close()
        return region

    @classmethod
    def extract(
        cls,
        pdf_path: Path,
        page_num: int = 0,
        output_path: Path | None = None,
        dpi: int = 200,
        force: bool = False,
    ) -> Path | None:
        """Extract the title block as a PNG image.

        Args:
            pdf_path: Path to the PDF file.
            page_num: Page index (0-indexed).
            output_path: Where to save the PNG. Defaults to
                         <pdf_stem>_p<N>_titleblock.png beside the PDF.
            dpi: Rendering DPI for the extracted image.
            force: If True, always extract the bottom-right corner even if no
                   strong title block signal found. Useful for sparse drawings.

        Returns:
            Path to the saved PNG, or None if no title block detected
            (and force=False).
        """
        region = cls.detect(pdf_path, page_num, force=force)
        if region is None:
            logger.warning("No title block detected in %s page %d", pdf_path.name, page_num)
            return None

        if output_path is None:
            output_path = pdf_path.parent / (f"{pdf_path.stem}_p{page_num + 1}_titleblock.png")

        doc = fitz.open(str(pdf_path))
        page = doc[page_num]
        matrix = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=matrix, clip=region.rect)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_path))
        doc.close()

        logger.info("Title block extracted to %s", output_path)
        return output_path

    @classmethod
    def _detect_via_paths(
        cls,
        page: fitz.Page,
        w: float,
        h: float,
    ) -> TitleBlockRegion | None:
        """Use vector path density to locate the title block."""
        search_rect = fitz.Rect(
            w * (1 - cls._SEARCH_RIGHT_FRAC),
            h * (1 - cls._SEARCH_BOTTOM_FRAC),
            w,
            h,
        )

        paths = page.get_drawings()
        if not paths:
            return None

        xs: list[float] = []
        ys: list[float] = []
        for path in paths:
            rect = fitz.Rect(path.get("rect", [0, 0, 0, 0]))
            if search_rect.intersects(rect):
                xs.extend([rect.x0, rect.x1])
                ys.extend([rect.y0, rect.y1])

        if len(xs) < 4:  # Relaxed: 4 points = 2 bounding boxes minimum
            return None

        x0 = max(min(xs), search_rect.x0)
        y0 = max(min(ys), search_rect.y0)
        x1 = min(max(xs), w)
        y1 = min(max(ys), h)

        if (x1 - x0) < 20 or (y1 - y0) < 20:
            return None

        logger.debug("Path-based title block: (%.0f, %.0f)-(%.0f, %.0f)", x0, y0, x1, y1)
        return TitleBlockRegion(x0=x0, y0=y0, x1=x1, y1=y1)

    @classmethod
    def _detect_heuristic(
        cls,
        page: fitz.Page,
        w: float,
        h: float,
        force: bool = False,
    ) -> TitleBlockRegion | None:
        """Fall back to bottom-right heuristic bounding box.

        Args:
            force: If True, skip ink-ratio check and always return the region.
                   Useful for very sparse title blocks on A1/A0 single-page drawings.
        """
        x0 = w * (1 - cls._SEARCH_RIGHT_FRAC)
        y0 = h * (1 - cls._SEARCH_BOTTOM_FRAC)
        region = TitleBlockRegion(x0=x0, y0=y0, x1=w, y1=h)

        if force:
            logger.debug(
                "Heuristic title block (forced): (%.0f, %.0f)-(%.0f, %.0f)",
                x0,
                y0,
                w,
                h,
            )
            return region

        # Verify region has actual content
        matrix = fitz.Matrix(1.0, 1.0)  # 72 DPI thumbnail
        pix = page.get_pixmap(matrix=matrix, clip=region.rect)
        ink = _compute_ink_ratio(pix)

        if ink < cls._MIN_CONTENT_RATIO:
            logger.debug("Heuristic title block too blank (ink=%.1f%%)", ink * 100)
            return None

        logger.debug(
            "Heuristic title block: (%.0f, %.0f)-(%.0f, %.0f), ink=%.1f%%",
            x0,
            y0,
            w,
            h,
            ink * 100,
        )
        return region


# ---------------------------------------------------------------------------
# Result
# ---------------------------------------------------------------------------


@dataclass
class ProcessingResult:
    """Complete output from a single ``PDFProcessingPipeline.process()`` call.

    Attributes:
        report: Full analysis report (category, confidence, page details, etc.)
        segments: Contiguous page-type segments inferred from the report.
        chunk_paths: PDF chunks written to disk (populated for text/scan docs).
        tile_paths: High-res tile images (populated for drawing pages).
        titleblock_path: Extracted title-block PNG, if detected.
        composite_path: Composite overview image, if built.
    """

    report: PDFReport
    segments: list[Segment] = field(default_factory=list)
    chunk_paths: list[Path] = field(default_factory=list)
    tile_paths: list[Path] = field(default_factory=list)
    titleblock_path: Path | None = None
    composite_path: Path | None = None


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PDFProcessingError(RuntimeError):
    """Raised when the pipeline cannot process a PDF."""

    pass


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class PDFProcessingPipeline:
    """Deep module for end-to-end PDF preprocessing.

    Coordinates ``PDFAnalyzer``, ``VisionOptimizer``, ``TitleBlockDetector``,
    and ``CompositeBuilder`` behind a single ``process()`` seam. The pipeline
    decides which steps to run based on the document category — callers are
    not exposed to that branching logic.

    Sub-modules are accepted as constructor arguments so tests can inject
    controlled fakes without touching the filesystem or GPU.

    Args:
        analyzer: Optional ``PDFAnalyzer`` instance. Defaults to a fresh one.
        optimizer: Optional ``VisionOptimizer`` class/instance. Reserved for
            future per-instance config; currently uses class-level statics.
        detector: Optional ``TitleBlockDetector`` class/instance.
        composer: Optional ``CompositeBuilder`` class/instance.
        tile_dpi: DPI used when rasterising drawing tiles.
        tile_size_px: Pixel edge-length for each tile.
        chunk_size: Pages per PDF chunk for text/scan documents.
        composite_target_size: Pixel edge-length for the composite overview.
    """

    def __init__(
        self,
        analyzer: PDFAnalyzer | None = None,
        optimizer: type[VisionOptimizer] | None = None,
        detector: type[TitleBlockDetector] | None = None,
        composer: type[CompositeBuilder] | None = None,
        tile_dpi: int = 300,
        tile_size_px: int = 1024,
        chunk_size: int = 20,
        composite_target_size: int = 2048,
        min_ink_ratio: float = 0.02,
    ) -> None:
        self._analyzer = analyzer or PDFAnalyzer()
        self._optimizer = optimizer or VisionOptimizer
        self._detector = detector or TitleBlockDetector
        self._composer = composer or CompositeBuilder
        self._tile_dpi = tile_dpi
        self._tile_size_px = tile_size_px
        self._chunk_size = chunk_size
        self._composite_target_size = composite_target_size
        self._min_ink_ratio = min_ink_ratio

    # ------------------------------------------------------------------
    # Public seam
    # ------------------------------------------------------------------

    def process(self, pdf_path: Path, output_dir: Path) -> ProcessingResult:
        """Analyse and preprocess a PDF, returning all generated artifacts.

        The pipeline selects the processing strategy automatically based on
        the document category determined by ``PDFAnalyzer``:

        - ``DRAWING``  → tile oversized pages + extract title block + composite
        - ``TEXT_RICH``→ split into page-range chunks for LLM ingestion
        - ``SCANNED``  → split into chunks (no tiling; OCR model handles it)
        - ``HYBRID``   → split into chunks
        - ``UNKNOWN``  → minimal: only segments, no splitting or tiling

        Args:
            pdf_path: Path to the source PDF file. Must exist.
            output_dir: Directory where all output artifacts are written.
                        Created automatically if it does not exist.

        Returns:
            ``ProcessingResult`` with all populated artifacts.

        Raises:
            PDFProcessingError: If the file is missing, unreadable, or any
                processing step fails unrecoverably.
        """
        if not pdf_path.exists():
            raise PDFProcessingError(f"PDF not found: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            report = self._analyzer.analyze(pdf_path)
        except Exception as exc:
            raise PDFProcessingError(f"Analysis failed for {pdf_path.name}: {exc}") from exc

        segments = report.get_segments()

        match report.category:
            case PDFCategory.DRAWING:
                return self._process_drawing(pdf_path, output_dir, report, segments)
            case PDFCategory.TEXT_RICH:
                return self._process_text(pdf_path, output_dir, report, segments)
            case PDFCategory.SCANNED | PDFCategory.HYBRID:
                return self._process_scanned(pdf_path, output_dir, report, segments)
            case _:
                logger.info(
                    "Category '%s' for %s — returning minimal result (segments only).",
                    report.category.value,
                    pdf_path.name,
                )
                return ProcessingResult(report=report, segments=segments)

    # ------------------------------------------------------------------
    # Internal strategies
    # ------------------------------------------------------------------

    def _process_drawing(
        self,
        pdf_path: Path,
        output_dir: Path,
        report: PDFReport,
        segments: list[Segment],
    ) -> ProcessingResult:
        """Strategy for oversized engineering drawing PDFs."""
        tile_dir = output_dir / "tiles"
        tile_paths: list[Path] = []

        try:
            for detail in report.page_details:
                if detail.is_oversized:
                    page_tiles, _ = self._optimizer.tile_page_smart(
                        pdf_path=pdf_path,
                        page_num=detail.page_num,
                        output_dir=tile_dir,
                        dpi=self._tile_dpi,
                        tile_size_px=self._tile_size_px,
                        min_ink_ratio=self._min_ink_ratio,
                    )
                    tile_paths.extend(page_tiles)
        except Exception as exc:
            raise PDFProcessingError(f"Tiling failed for {pdf_path.name}: {exc}") from exc

        # Title block — attempt detection on first page
        titleblock_path: Path | None = None
        try:
            titleblock_path = self._detector.extract(
                pdf_path=pdf_path,
                page_num=0,
                output_path=output_dir / f"{pdf_path.stem}_titleblock.png",
            )
        except Exception as exc:
            logger.warning("Title block extraction failed for %s: %s", pdf_path.name, exc)

        # Composite — first 4 tiles if available
        composite_path: Path | None = None
        if len(tile_paths) >= 4:
            try:
                composite_path = self._composer.quad_view(
                    images=tile_paths[:4],
                    output_path=output_dir / f"{pdf_path.stem}_composite.png",
                    labels=[f"Tile {i + 1}" for i in range(4)],
                    target_size=self._composite_target_size,
                )
            except Exception as exc:
                logger.warning("Composite build failed for %s: %s", pdf_path.name, exc)

        return ProcessingResult(
            report=report,
            segments=segments,
            tile_paths=tile_paths,
            titleblock_path=titleblock_path,
            composite_path=composite_path,
        )

    def _process_text(
        self,
        pdf_path: Path,
        output_dir: Path,
        report: PDFReport,
        segments: list[Segment],
    ) -> ProcessingResult:
        """Strategy for text-rich PDFs: split into LLM-sized chunks."""
        chunk_dir = output_dir / "chunks"
        ranges = get_blind_chunks(report.pages, self._chunk_size)
        try:
            chunk_paths = split_pdf(pdf_path, ranges, chunk_dir)
        except Exception as exc:
            raise PDFProcessingError(f"Chunking failed for {pdf_path.name}: {exc}") from exc

        return ProcessingResult(
            report=report,
            segments=segments,
            chunk_paths=chunk_paths,
        )

    def _process_scanned(
        self,
        pdf_path: Path,
        output_dir: Path,
        report: PDFReport,
        segments: list[Segment],
    ) -> ProcessingResult:
        """Strategy for scanned/hybrid PDFs: split for OCR pipeline."""
        chunk_dir = output_dir / "chunks"
        ranges = get_blind_chunks(report.pages, self._chunk_size)
        try:
            chunk_paths = split_pdf(pdf_path, ranges, chunk_dir)
        except Exception as exc:
            raise PDFProcessingError(f"Chunking failed for {pdf_path.name}: {exc}") from exc

        return ProcessingResult(
            report=report,
            segments=segments,
            chunk_paths=chunk_paths,
        )
