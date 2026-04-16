"""Tests for CompositeBuilder."""

from pathlib import Path

import pytest
from PIL import Image

from ccba_pdf_prep.composite import CompositeBuilder


def _make_solid_png(path: Path, width: int, height: int, color: tuple) -> Path:
    """Create a solid-color test PNG."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color)
    img.save(str(path))
    return path


@pytest.fixture
def four_images(tmp_path: Path) -> list[Path]:
    """Create 4 differently-colored 256x256 test images."""
    colors = [(200, 100, 100), (100, 200, 100), (100, 100, 200), (200, 200, 100)]
    return [_make_solid_png(tmp_path / f"img_{i}.png", 256, 256, c) for i, c in enumerate(colors)]


class TestCompositeBuilderQuadView:
    """Tests for quad_view (2x2 composite)."""

    def test_quad_view_creates_file(self, four_images: list[Path], tmp_path: Path) -> None:
        out = tmp_path / "quad.png"
        result = CompositeBuilder.quad_view(four_images, out)

        assert result == out
        assert out.exists()

    def test_quad_view_correct_size(self, four_images: list[Path], tmp_path: Path) -> None:
        """Output should be target_size × target_size pixels."""
        out = tmp_path / "quad_size.png"
        CompositeBuilder.quad_view(four_images, out, target_size=512)
        img = Image.open(out)
        assert img.size == (512, 512)

    def test_quad_view_with_labels(self, four_images: list[Path], tmp_path: Path) -> None:
        out = tmp_path / "quad_labeled.png"
        labels = ["Arch", "Structure", "MEP", "Fire"]
        result = CompositeBuilder.quad_view(four_images, out, labels=labels)
        assert result.exists()

    def test_quad_view_requires_four_images(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="4"):
            CompositeBuilder.quad_view([], tmp_path / "out.png")

    def test_quad_view_uses_first_four_of_more(
        self, four_images: list[Path], tmp_path: Path
    ) -> None:
        """Extra images beyond 4 should be silently ignored."""
        extra = four_images + [four_images[0]]  # 5 images
        out = tmp_path / "quad_extra.png"
        result = CompositeBuilder.quad_view(extra, out)
        assert result.exists()


class TestCompositeBuilderNWay:
    """Tests for n_way_composite."""

    def test_single_image(self, tmp_path: Path) -> None:
        img_path = _make_solid_png(tmp_path / "single.png", 200, 300, (255, 0, 0))
        out = tmp_path / "n_single.png"
        result = CompositeBuilder.n_way_composite([img_path], out, cols=1)
        assert result.exists()

    def test_three_images_two_cols(self, tmp_path: Path) -> None:
        """3 images with 2 cols → 2 rows (last row has 1 image + blank)."""
        imgs = [
            _make_solid_png(tmp_path / f"c{i}.png", 100, 100, (i * 80, 100, 100)) for i in range(3)
        ]
        out = tmp_path / "three.png"
        CompositeBuilder.n_way_composite(imgs, out, cols=2, cell_size=200)
        result = Image.open(out)
        assert result.width == 400  # 2 cols × 200
        assert result.height == 400  # 2 rows × 200

    def test_empty_images_raises(self, tmp_path: Path) -> None:
        with pytest.raises(ValueError, match="empty"):
            CompositeBuilder.n_way_composite([], tmp_path / "out.png")

    def test_custom_cell_size(self, tmp_path: Path) -> None:
        imgs = [
            _make_solid_png(tmp_path / f"cs{i}.png", 300, 200, (100, 100, i * 80)) for i in range(2)
        ]
        out = tmp_path / "cell_size.png"
        CompositeBuilder.n_way_composite(imgs, out, cols=2, cell_size=128)
        result = Image.open(out)
        assert result.width == 256  # 2 × 128
        assert result.height == 128  # 1 row

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        img_path = _make_solid_png(tmp_path / "p.png", 50, 50, (0, 0, 0))
        out = tmp_path / "deep" / "nested" / "out.png"
        CompositeBuilder.n_way_composite([img_path], out)
        assert out.exists()

    def test_labels_applied(self, tmp_path: Path) -> None:
        """Labels should not raise errors even if font not available."""
        imgs = [
            _make_solid_png(tmp_path / f"lbl{i}.png", 200, 200, (200, 200, 200)) for i in range(2)
        ]
        out = tmp_path / "labeled.png"
        result = CompositeBuilder.n_way_composite(imgs, out, cols=2, labels=["Arch", "KC"])
        assert result.exists()
