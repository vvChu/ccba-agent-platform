"""Tests for Phase 2 vision features: tile_page_smart and TitleBlockDetector."""

from pathlib import Path

import pytest

from ccba_pdf_prep.vision import TitleBlockDetector, TitleBlockRegion, VisionOptimizer


class TestTilePageSmart:
    """Tests for ink-ratio based smart tiling."""

    def test_smart_returns_fewer_tiles_than_plain(
        self, tmp_pdf_drawing: Path, tmp_path: Path
    ) -> None:
        """Smart tiling should filter out blank border tiles."""
        plain_tiles = VisionOptimizer.tile_page(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=tmp_path / "plain",
            dpi=150,
            tile_size_px=512,
        )

        smart_tiles, all_results = VisionOptimizer.tile_page_smart(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=tmp_path / "smart",
            dpi=150,
            tile_size_px=512,
            min_ink_ratio=0.01,
        )

        # Smart should keep <= plain (some blank tiles filtered)
        assert len(smart_tiles) <= len(plain_tiles)
        # Total result count equals plain count
        assert len(all_results) == len(plain_tiles)

    def test_smart_tile_results_have_ink_ratio(self, tmp_pdf_drawing: Path, tmp_path: Path) -> None:
        """Every TileResult should have a valid ink_ratio."""
        _, all_results = VisionOptimizer.tile_page_smart(
            pdf_path=tmp_pdf_drawing,
            page_num=0,
            output_dir=tmp_path / "ink",
            dpi=72,
            tile_size_px=512,
            min_ink_ratio=0.0,  # Keep all
        )

        assert all_results
        for r in all_results:
            assert 0.0 <= r.ink_ratio <= 1.0
            assert not r.skipped  # min_ink_ratio=0 keeps everything

    def test_smart_very_high_threshold_keeps_nothing(
        self, tmp_pdf_text: Path, tmp_path: Path
    ) -> None:
        """With min_ink_ratio=1.0, all tiles should be skipped."""
        kept, all_results = VisionOptimizer.tile_page_smart(
            pdf_path=tmp_pdf_text,
            page_num=0,
            output_dir=tmp_path / "none",
            dpi=72,
            tile_size_px=1024,
            min_ink_ratio=1.0,  # Impossible threshold
        )

        assert kept == []
        assert all(r.skipped for r in all_results)

    def test_smart_skipped_tiles_not_written(self, tmp_pdf_text: Path, tmp_path: Path) -> None:
        """Tiles marked as skipped must not be written to disk."""
        out = tmp_path / "skip_check"
        kept, all_results = VisionOptimizer.tile_page_smart(
            pdf_path=tmp_pdf_text,
            page_num=0,
            output_dir=out,
            dpi=72,
            tile_size_px=1024,
            min_ink_ratio=1.0,
        )

        skipped = [r for r in all_results if r.skipped]
        for r in skipped:
            assert not r.path.exists(), f"Skipped tile was written: {r.path}"

    def test_tile_result_fields(self, tmp_pdf_text: Path, tmp_path: Path) -> None:
        """TileResult should have correct row/col fields."""
        _, all_results = VisionOptimizer.tile_page_smart(
            pdf_path=tmp_pdf_text,
            page_num=0,
            output_dir=tmp_path / "fields",
            dpi=72,
            tile_size_px=1024,
            min_ink_ratio=0.0,
        )

        for r in all_results:
            assert r.row >= 0
            assert r.col >= 0
            assert "tile" in r.path.name


@pytest.fixture
def tmp_pdf_with_titleblock(tmp_path: Path) -> Path:
    """Create an A1 drawing PDF with a dense grid of lines in the bottom-right corner."""
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=2384, height=1684)  # A1

    # Draw title block area (bottom-right 30% x 25%) with dense lines
    tb_x0 = 2384 * 0.70
    tb_y0 = 1684 * 0.75
    shape = page.new_shape()

    # Draw outer border
    shape.draw_rect(fitz.Rect(tb_x0, tb_y0, 2384 - 10, 1684 - 10))
    # Draw internal grid lines (horizontal)
    for y in range(int(tb_y0) + 30, int(1684 - 10), 40):
        shape.draw_line(fitz.Point(tb_x0, y), fitz.Point(2384 - 10, y))
    # Draw internal grid lines (vertical)
    for x in range(int(tb_x0) + 60, int(2384 - 10), 80):
        shape.draw_line(fitz.Point(x, tb_y0), fitz.Point(x, 1684 - 10))

    shape.finish(color=(0, 0, 0), width=0.5)
    shape.commit()

    # Add some text in title block
    page.insert_text((tb_x0 + 10, tb_y0 + 20), "PROJECT: BV NTP", fontsize=10)
    page.insert_text((tb_x0 + 10, tb_y0 + 40), "DRAWING: ACMV-M-201", fontsize=8)

    path = tmp_path / "drawing_with_tb.pdf"
    doc.save(str(path))
    doc.close()
    return path


class TestTitleBlockDetector:
    """Tests for TitleBlockDetector."""

    def test_detect_returns_region_for_drawing(self, tmp_pdf_with_titleblock: Path) -> None:
        """Should detect a non-None region from a drawing with a proper title block."""
        region = TitleBlockDetector.detect(tmp_pdf_with_titleblock, page_num=0)
        assert region is not None
        assert isinstance(region, TitleBlockRegion)

    def test_detect_region_within_page_bounds(self, tmp_pdf_with_titleblock: Path) -> None:
        """Detected region coordinates must be within the page."""
        import fitz

        doc = fitz.open(str(tmp_pdf_with_titleblock))
        page = doc[0]
        w, h = page.rect.width, page.rect.height
        doc.close()

        region = TitleBlockDetector.detect(tmp_pdf_with_titleblock, page_num=0)
        if region is not None:
            assert region.x0 >= 0
            assert region.y0 >= 0
            assert region.x1 <= w + 1  # +1 for float rounding
            assert region.y1 <= h + 1
            assert region.width > 0
            assert region.height > 0

    def test_detect_file_not_found(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing PDF."""
        with pytest.raises(FileNotFoundError):
            TitleBlockDetector.detect(tmp_path / "nonexistent.pdf")

    def test_detect_force_returns_region_for_blank_text_pdf(self, tmp_pdf_text: Path) -> None:
        """With force=True, detect() must always return a region even on blank pages."""
        # tmp_pdf_text has mostly white content — normally None without force
        region = TitleBlockDetector.detect(tmp_pdf_text, page_num=0, force=True)
        assert region is not None, "force=True should always return a region"
        assert region.width > 0
        assert region.height > 0

    def test_extract_force_always_saves_image(self, tmp_pdf_text: Path, tmp_path: Path) -> None:
        """With force=True, extract() must save a PNG even for sparse drawings."""
        out = tmp_path / "forced_titleblock.png"
        result = TitleBlockDetector.extract(
            pdf_path=tmp_pdf_text,
            page_num=0,
            output_path=out,
            dpi=72,
            force=True,
        )
        assert result is not None, "force=True should always produce an image"
        assert result.exists()
        assert result.stat().st_size > 0

    def test_extract_creates_image(self, tmp_pdf_with_titleblock: Path, tmp_path: Path) -> None:
        """extract() should save a PNG file when a title block is found."""
        out = tmp_path / "titleblock.png"
        result = TitleBlockDetector.extract(
            pdf_path=tmp_pdf_with_titleblock,
            page_num=0,
            output_path=out,
            dpi=72,
        )

        assert result is not None
        assert result.exists()
        assert result.suffix == ".png"

    def test_extract_default_path(self, tmp_pdf_with_titleblock: Path) -> None:
        """extract() with no output_path should save next to the PDF."""
        result = TitleBlockDetector.extract(
            pdf_path=tmp_pdf_with_titleblock,
            page_num=0,
            dpi=72,
        )

        if result is not None:
            assert result.parent == tmp_pdf_with_titleblock.parent
            assert "_titleblock" in result.name
            # cleanup
            result.unlink(missing_ok=True)

    def test_title_block_region_rect(self) -> None:
        """TitleBlockRegion.rect should return valid fitz.Rect."""
        import fitz

        region = TitleBlockRegion(x0=100, y0=200, x1=400, y1=500)
        rect = region.rect
        assert isinstance(rect, fitz.Rect)
        assert rect.x0 == 100
        assert rect.y1 == 500
        assert region.width == 300
        assert region.height == 300
