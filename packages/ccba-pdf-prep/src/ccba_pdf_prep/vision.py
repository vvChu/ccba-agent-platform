"""
CCBA PDF Preprocessor — Vision Utilities.
Provides page tiling and ink ratio calculations for AI Vision models.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import NamedTuple

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class TileResult(NamedTuple):
    """Metadata for a single tile."""

    path: Path
    row: int
    col: int
    ink_ratio: float
    skipped: bool


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

    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


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
