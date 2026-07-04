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

from .composite import CompositeBuilder
from .core import PDFAnalyzer, PDFCategory, PDFReport, Segment, get_blind_chunks, split_pdf
from .detector import TitleBlockDetector
from .vision import VisionOptimizer

logger = logging.getLogger(__name__)


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
