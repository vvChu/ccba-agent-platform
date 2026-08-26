"""Unit tests for Technical Figure Extractor and Markdown Figure Cards (ADR 0030 / ADR 0034)."""

from ccba_legal.figure_extractor import (
    AERODYNAMIC_FIGURES_GEOMETRY,
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
    fig_entry = {
        "tag": "F.1",
        "title": "Phan vung khi dong tren tuong phang",
        "anchor": "hinh-f_1",
        "image_relpath": "figures/images/hinh_f_1.png",
        "geometry_rules": AERODYNAMIC_FIGURES_GEOMETRY["F.1"],
    }

    card_md = render_markdown_figure_card(fig_entry)
    assert "<p align=\"center\">" in card_md
    assert "> [!NOTE]" in card_md
    assert "> **Đặc tả Hình học & Tham chiếu Khí động:**" in card_md
    assert "Vùng A" in card_md
    assert "[F.1](#bang-bang-f-1)" in card_md


def test_aerodynamic_geometry_rules() -> None:
    assert "F.1" in AERODYNAMIC_FIGURES_GEOMETRY
    assert "F.3" in AERODYNAMIC_FIGURES_GEOMETRY
    assert "F.5a" in AERODYNAMIC_FIGURES_GEOMETRY
    f1 = AERODYNAMIC_FIGURES_GEOMETRY["F.1"]
    assert "parameters" in f1
    assert "zones" in f1
