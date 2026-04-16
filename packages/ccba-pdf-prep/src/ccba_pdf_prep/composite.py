"""
CCBA PDF Preprocessor — Composite image builder.

Provides utilities for assembling multiple PDF pages or tile images into
a single composite (e.g. quad-view for multi-disciplinary clash detection).
"""

import logging
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Default label style
_LABEL_BG = (30, 30, 30)  # Dark background
_LABEL_FG = (255, 255, 255)  # White text
_LABEL_HEIGHT_PX = 32


class CompositeBuilder:
    """Build composite images from multiple input images.

    Typical uses:
    - ``quad_view`` — 2×2 collage for 4-discipline clash detection
    - ``n_way_composite`` — flexible N×M grid for any set of images
    """

    @staticmethod
    def quad_view(
        images: list[Path],
        output_path: Path,
        labels: list[str] | None = None,
        target_size: int = 2048,
    ) -> Path:
        """Create a 2×2 composite from exactly 4 images.

        Images are resized to a common cell size (target_size // 2),
        then arranged in a 2-column grid. Optional labels are drawn
        at the top of each cell.

        Args:
            images: Exactly 4 image paths (any common raster format).
            output_path: Where to save the composite PNG.
            labels: Optional list of 4 label strings.
            target_size: Edge length of the final square composite in pixels.

        Returns:
            Path to the saved composite PNG.

        Raises:
            ValueError: If fewer than 4 images are provided.
        """
        if len(images) < 4:
            raise ValueError(f"quad_view requires exactly 4 images, got {len(images)}")
        return CompositeBuilder.n_way_composite(
            images=images[:4],
            output_path=output_path,
            cols=2,
            labels=labels,
            cell_size=target_size // 2,
        )

    @staticmethod
    def n_way_composite(
        images: list[Path],
        output_path: Path,
        cols: int = 2,
        labels: list[str] | None = None,
        cell_size: int | None = None,
    ) -> Path:
        """Create an N×M composite grid from a list of images.

        Images are padded/resized to ``cell_size`` pixels (square).
        If ``cell_size`` is None, the max dimension of the first image
        is used as the cell size.

        Args:
            images: List of image paths.
            output_path: Output PNG path.
            cols: Number of columns.
            labels: Optional label for each image cell.
            cell_size: Square cell size in pixels.

        Returns:
            Path to the saved composite PNG.

        Raises:
            ValueError: If images list is empty.
        """
        if not images:
            raise ValueError("images list must not be empty")

        loaded = [Image.open(p).convert("RGB") for p in images]

        if cell_size is None:
            cell_size = max(max(img.width, img.height) for img in loaded)

        rows = (len(images) + cols - 1) // cols
        canvas_w = cols * cell_size
        canvas_h = rows * cell_size
        canvas = Image.new("RGB", (canvas_w, canvas_h), (255, 255, 255))

        for idx, img in enumerate(loaded):
            # Fit image into cell_size × cell_size while preserving aspect ratio
            img.thumbnail((cell_size, cell_size), Image.LANCZOS)
            cell_img = Image.new("RGB", (cell_size, cell_size), (255, 255, 255))
            # Center the thumbnail in the cell
            x_off = (cell_size - img.width) // 2
            y_off = (cell_size - img.height) // 2
            cell_img.paste(img, (x_off, y_off))

            # Draw label if provided
            label = labels[idx] if labels and idx < len(labels) else None
            if label:
                cell_img = CompositeBuilder._draw_label(cell_img, label)

            # Paste cell into canvas
            row, col = divmod(idx, cols)
            canvas.paste(cell_img, (col * cell_size, row * cell_size))

        output_path.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(str(output_path), format="PNG")
        logger.info("Composite %dx%d saved to %s", canvas_w, canvas_h, output_path)
        return output_path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _draw_label(img: Image.Image, text: str) -> Image.Image:
        """Draw a dark label strip at the top of an image cell."""
        label_h = _LABEL_HEIGHT_PX
        draw = ImageDraw.Draw(img)

        # Background rectangle
        draw.rectangle([(0, 0), (img.width, label_h)], fill=_LABEL_BG)

        # Try to use a basic font, fall back to default
        try:
            font = ImageFont.truetype("arial.ttf", size=18)
        except OSError:
            font = ImageFont.load_default()

        draw.text((8, 6), text, fill=_LABEL_FG, font=font)
        return img
