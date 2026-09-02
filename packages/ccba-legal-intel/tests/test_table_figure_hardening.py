# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests for Table & Figure Hardening, In-Cell Schematics, and KaTeX Normalization (ADR 0039)."""

from pathlib import Path

from ccba_legal.converters.standard.handlers.figure_handler import (
    normalize_katex_in_title,
)
from ccba_legal.converters.standard.handlers.table_handler import (
    clean_formula_latex,
)
from ccba_legal.converters.standard.handlers.table_handler import (
    resolve_hierarchical_headers as resolve_table_headers,
)
from ccba_legal.converters.table_extractor import (
    resolve_hierarchical_headers as resolve_extractor_headers,
)
from ccba_legal.figure_extractor import scan_and_prune_orphan_figures


def test_resolve_hierarchical_headers_preserves_all_columns():
    """Verify that merged category headers across row 0 and row 1 are combined without collapsing columns."""
    grid = [
        ["Tường", "Tường", "Tường", "Các mặt đứng còn lại", "Mái"],
        ["Vùng K", "Vùng L", "Vùng M", "Các mặt đứng còn lại", "Mái"],
        ["0,8", "0,7", "0,6", "Theo Bảng F.4", "Theo Bảng F.5"],
    ]
    resolved = resolve_table_headers(grid)
    assert len(resolved) == 2
    assert resolved[0] == [
        "Tường — Vùng K",
        "Tường — Vùng L",
        "Tường — Vùng M",
        "Các mặt đứng còn lại",
        "Mái",
    ]
    assert resolved[1] == ["0,8", "0,7", "0,6", "Theo Bảng F.4", "Theo Bảng F.5"]


def test_resolve_extractor_headers():
    """Verify that table_extractor resolution correctly returns combined headers and normalized grid."""
    grid = [
        ["Nhóm chế độ", "Nhà và cạn trong nhà", "Nhà và cạn trong nhà", "Trụ ngoài trời"],
        ["Nhóm chế độ", "Cột nhà", "Dầm hãm", "Trụ ngoài trời"],
        ["A1", "h/500", "L/500", "h/1500"],
    ]
    norm_grid, headers = resolve_extractor_headers(grid)
    assert len(headers) == 4
    assert headers[0] == "Nhóm chế độ"
    assert headers[1] == "Nhà và cạn trong nhà — Cột nhà"
    assert headers[2] == "Nhà và cạn trong nhà — Dầm hãm"
    assert headers[3] == "Trụ ngoài trời"


def test_normalize_katex_in_title():
    """Verify that HTML subscripts and greek variables in figure and table titles are converted to KaTeX."""
    assert normalize_katex_in_title("Hệ số c<sub>e</sub> cho mái") == "Hệ số $c_e$ cho mái"
    assert (
        normalize_katex_in_title(r"Hệ số c<sub>x</sub> và c<sub>β</sub>")
        == r"Hệ số $c_x$ và $c_\beta$"
    )
    assert normalize_katex_in_title(r"Hệ số k<sub>λ</sub>") == r"Hệ số $k_\lambda$"
    assert normalize_katex_in_title(r"Mặt cao độ z<sub>0</sub>") == r"Mặt cao độ $z_{0}$"


def test_clean_formula_latex():
    """Verify formula sanitization, operator normalization, and KaTeX clean formatting."""
    raw = r"c_t = c_x(1 + \eta)k_1"
    cleaned = clean_formula_latex(raw)
    assert r"c_t = c_x(1 + \eta)k_1" in cleaned

    raw_ops = r"f \le fu \ge 0 \cdot 10^5"
    cleaned_ops = clean_formula_latex(raw_ops)
    assert r"\le" in cleaned_ops
    assert r"\ge" in cleaned_ops
    assert r"\cdot" in cleaned_ops


def test_orphan_figure_scanner_detects_html_img_tags(tmp_path: Path):
    """Verify that scan_and_prune_orphan_figures recognizes both Markdown and HTML <img> tags."""
    bundle_dir = tmp_path / "bundle"
    img_dir = bundle_dir / "figures" / "images"
    img_dir.mkdir(parents=True)

    # Create active image and orphan image
    (img_dir / "hinh_01.png").write_text("dummy")
    (img_dir / "in_cell_diagram.png").write_text("dummy")
    (img_dir / "orphan_img.png").write_text("dummy")

    # Markdown referencing hinh_01 via markdown syntax and in_cell_diagram via HTML <img>
    md_content = """
    # Tiêu chuẩn
    ![Hình 1](figures/images/hinh_01.png)
    
    | Sơ đồ | Giá trị |
    | <img src="figures/images/in_cell_diagram.png" width="90"> | 1,0 |
    """
    (bundle_dir / "doc.md").write_text(md_content, encoding="utf-8")

    result = scan_and_prune_orphan_figures(bundle_dir, prune=False)
    assert "hinh_01.png" in result["active"]
    assert "in_cell_diagram.png" in result["active"]
    assert "orphan_img.png" in result["orphaned"]
