"""Tests for ccba_pdf_prep.vision module."""

from pathlib import Path

import pytest

from ccba_pdf_prep.vision import VisionOptimizer


class TestVisionOptimizer:
    """Tests for VisionOptimizer tile_page."""

    def test_tile_page_basic(self, tmp_pdf_drawing: Path, tmp_path: Path) -> None:
        """Tile an oversized page and verify tiles are created."""
        output_dir = tmp_path / "tiles"
        tiles = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=output_dir,
            dpi=150,  # Lower DPI for faster tests
            tile_size_px=512,
        )

        assert len(tiles) > 0
        assert all(t.exists() for t in tiles)
        assert all(t.suffix == ".png" for t in tiles)
        assert output_dir.exists()

    def test_tile_page_with_overlap(self, tmp_pdf_drawing: Path, tmp_path: Path) -> None:
        """Tiles with overlap should produce more tiles than without."""
        output_no_overlap = tmp_path / "no_overlap"
        tiles_no_overlap = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=output_no_overlap,
            dpi=150,
            tile_size_px=512,
            overlap_px=0,
        )

        output_with_overlap = tmp_path / "with_overlap"
        tiles_with_overlap = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=output_with_overlap,
            dpi=150,
            tile_size_px=512,
            overlap_px=128,
        )

        # Overlap should produce equal or more tiles
        assert len(tiles_with_overlap) >= len(tiles_no_overlap)

    def test_tile_page_small_pdf(self, tmp_pdf_text: Path, tmp_path: Path) -> None:
        """Tiling an A4 page at low DPI should produce few tiles."""
        output_dir = tmp_path / "tiles_a4"
        tiles = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_text,
            page_num=0,
            output_dir=output_dir,
            dpi=72,  # Very low DPI
            tile_size_px=1024,
        )

        # A4 at 72 DPI = 595×842 px → fits in 1 tile
        assert len(tiles) == 1

    def test_tile_page_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError):
            VisionOptimizer.tile_page(
                pdf_path=tmp_path / "nonexistent.pdf",
                page_num=0,
                output_dir=tmp_path / "tiles",
            )

    def test_tile_naming_convention(self, tmp_pdf_drawing: Path, tmp_path: Path) -> None:
        """Verify tile file naming follows expected pattern."""
        output_dir = tmp_path / "named_tiles"
        tiles = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=output_dir,
            dpi=72,
            tile_size_px=512,
        )

        for t in tiles:
            assert tmp_pdf_drawing.stem in t.name
            assert "_p1_tile_" in t.name
            assert t.name.endswith(".png")
