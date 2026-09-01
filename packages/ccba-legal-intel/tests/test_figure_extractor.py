"""Unit tests for Technical Figure Extractor and Markdown Figure Cards (ADR 0030 / ADR 0034)."""

from pathlib import Path
from ccba_legal.figure_extractor import (
    load_bundle_figures_overrides,
    render_markdown_figure_card,
)


def test_render_markdown_figure_card_basic() -> None:
    fig_entry = {
        "tag": "E.1",
        "title": "Kich thuoc tuong duong cho cac mat bang phuc tap",
        "anchor": "hinh-e_1",
        "image_relpath": "figures/images/hinh_e_1.png",
    }

    card_md = render_markdown_figure_card(fig_entry)
    assert "<a id=\"hinh-e_1\"></a>" in card_md
    assert "<p align=\"center\">" in card_md
    assert "![Hình E.1](figures/images/hinh_e_1.png)" in card_md
    assert "<strong>Hình E.1 — Kich thuoc tuong duong cho cac mat bang phuc tap</strong>" in card_md


def test_render_markdown_figure_card_with_geometry() -> None:
    sample_geometry = {
        "description": "Phân vùng khí động trên tường phẳng",
        "parameters": ["e = min(b, 2h)", "h (chiều cao)", "l (chiều dài)"],
        "zones": ["Vùng A (biên mép đón gió)", "Vùng B (dải tiếp theo)"],
        "related_tables": ["F.1"],
    }
    fig_entry = {
        "tag": "F.1",
        "title": "Phan vung khi dong tren tuong phang",
        "anchor": "hinh-f_1",
        "image_relpath": "figures/images/hinh_f_1.png",
        "geometry_rules": sample_geometry,
    }

    card_md = render_markdown_figure_card(fig_entry)
    assert "<p align=\"center\">" in card_md
    assert "> [!NOTE]" in card_md
    assert "> **Đặc tả Hình học & Tham chiếu Khí động:**" in card_md
    assert "Vùng A" in card_md
    assert "[F.1](#bang-bang-f-1)" in card_md


def test_load_bundle_figures_overrides(tmp_path: Path) -> None:
    bundle_dir = tmp_path / "test_bundle"
    bundle_dir.mkdir()
    override_file = bundle_dir / "figures_override.yaml"
    override_file.write_text("F.1:\n  title: 'Test Figure'\n", encoding="utf-8")

    res = load_bundle_figures_overrides(bundle_dir)
    assert "F.1" in res
    assert res["F.1"]["title"] == "Test Figure"

