"""Unit tests for Modernize Annex Engine (ccba_legal.modernize)."""

from pathlib import Path

from PIL import Image

from ccba_legal.modernize import (
    FigureAutoCompositor,
    MathEquationConverter,
    TableMatrixBuilder,
)


def test_figure_auto_compositor_vertical(tmp_path: Path) -> None:
    img1 = tmp_path / "panel_a.png"
    img2 = tmp_path / "panel_b.png"
    out_img = tmp_path / "composite.png"

    # Create dummy panel images
    Image.new("RGB", (100, 50), color=(200, 200, 200)).save(img1)
    Image.new("RGB", (120, 60), color=(150, 150, 150)).save(img2)

    res = FigureAutoCompositor.composite_panels(
        image_paths=[img1, img2],
        output_path=out_img,
        layout="vertical",
        panel_labels=["a) Mặt đứng", "b) Mặt bằng"],
    )
    assert res.exists()
    comp_img = Image.open(res)
    assert comp_img.width >= 120
    assert comp_img.height >= 110


def test_figure_auto_compositor_horizontal(tmp_path: Path) -> None:
    img1 = tmp_path / "panel_1.png"
    img2 = tmp_path / "panel_2.png"
    out_img = tmp_path / "composite_h.png"

    Image.new("RGB", (80, 40), color=(255, 255, 255)).save(img1)
    Image.new("RGB", (90, 50), color=(255, 255, 255)).save(img2)

    res = FigureAutoCompositor.composite_panels(
        image_paths=[img1, img2],
        output_path=out_img,
        layout="horizontal",
    )
    assert res.exists()
    comp_img = Image.open(res)
    assert comp_img.width >= 170


def test_table_matrix_builder_lossless() -> None:
    raw_rows = [
        ["Góc alpha", "Vùng F", "Vùng G", "Vùng H"],
        ["-45", "-0.6 / +0.0", "-0.6", "-0.8"],
        ["15", "-0.9 / +0.2", "-0.8 / +0.2", "-0.5"],
        ["CHÚ THÍCH 1: Dấu trừ là áp lực hút."],
    ]

    md_output = TableMatrixBuilder.format_lossless_matrix_table(
        raw_rows=raw_rows,
        caption="Hệ số khí động c_e",
        table_num="Bảng F.1",
    )

    assert "**Bảng F.1 — Hệ số khí động c_e**" in md_output
    assert "-0.6<br>+0.0" in md_output
    assert "-0.9<br>+0.2" in md_output
    assert "_CHÚ THÍCH:_" in md_output
    assert "Dấu trừ là áp lực hút." in md_output


def test_math_equation_converter() -> None:
    raw_md = """
Đây là công thức vận tốc gió:

V(z) = 0.68 * V0 * (z/10)^alpha (F.2)

Và phương trình độ võng:

f_u = L / 250 (G.1)
"""

    converted = MathEquationConverter.convert_numbered_equations(raw_md)
    assert "$$\nV(z) = 0.68 * V0 * (z/10)^alpha \\tag{F.2}\n$$" in converted
    assert "$$\nf_u = L / 250 \\tag{G.1}\n$$" in converted
