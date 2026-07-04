"""
CCBA PDF Preprocessor — Title Block Detector.
Provides tools to automatically locate and extract the title block from PDF sheets.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import NamedTuple

import fitz  # PyMuPDF

from .vision import _compute_ink_ratio

logger = logging.getLogger(__name__)


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
