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
    assert '<a id="hinh-e_1"></a>' in card_md
    assert '<p align="center">' in card_md
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
    assert '<p align="center">' in card_md
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


def test_vietnamese_d_figure_tag_and_slug() -> None:
    """Verify that Vietnamese letter Đ in figure tags produces non-colliding slug and figure_id."""
    f_tag = "Đ.1"
    f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_").replace("-", "_")
    assert f_slug == "dd_1"
    assert f"FIG_{f_slug.upper()}" == "FIG_DD_1"
    assert f"hinh-{f_slug}" == "hinh-dd_1"
    assert f"hinh_{f_slug}.png" == "hinh_dd_1.png"

    # Verify that D.1 and Đ.1 produce distinct slugs
    d_slug = "D.1".lower().replace("đ", "dd").replace(".", "_").replace("-", "_")
    assert d_slug == "d_1"
    assert d_slug != f_slug


def test_figure_caption_dot_and_dash_separators() -> None:
    """Verify figure caption matching works with dash, dot, and colon separators."""
    import re

    pattern = r"^(?:Hình|HÌNH)\s+([0-9A-Za-zĐđ]+(?:\.[0-9A-Za-zĐđ]+)*)\s*[\.\-–—:]\s*(.+)$"

    m1 = re.match(pattern, "Hình Đ.1 - Sơ đồ nguyên lý")
    assert m1 and m1.group(1) == "Đ.1" and m1.group(2) == "Sơ đồ nguyên lý"

    m2 = re.match(pattern, "Hình Đ.1. Sơ đồ nguyên lý")
    assert m2 and m2.group(1) == "Đ.1" and m2.group(2) == "Sơ đồ nguyên lý"

    m3 = re.match(pattern, "Hình 1: Mặt bằng bố trí")
    assert m3 and m3.group(1) == "1" and m3.group(2) == "Mặt bằng bố trí"

    m4 = re.match(pattern, "Hình 1. Mặt bằng bố trí")
    assert m4 and m4.group(1) == "1" and m4.group(2) == "Mặt bằng bố trí"


def test_subcaption_detection_guards() -> None:
    """Verify subcaption regex accepts lettered markers (including đ) and rejects numbered section headings."""
    import re

    pattern = r"^(?:[a-zđĐ]\s*[\)\.\-–—]|[0-9]+\))\s*"

    # Valid sub-captions
    assert bool(re.match(pattern, "a) Mặt bằng tầng 1", re.IGNORECASE))
    assert bool(re.match(pattern, "b. Mặt đứng chính", re.IGNORECASE))
    assert bool(re.match(pattern, "c - Chi tiết mối nối", re.IGNORECASE))
    assert bool(re.match(pattern, "c – Chi tiết mối nối", re.IGNORECASE))
    assert bool(re.match(pattern, "đ) Chi tiết neo cốt thép", re.IGNORECASE))
    assert bool(re.match(pattern, "Đ) Chi tiết bản đáy", re.IGNORECASE))
    assert bool(re.match(pattern, "1) Trường hợp tải trọng phân bố", re.IGNORECASE))

    # Section / clause headings MUST NOT match
    assert not bool(re.match(pattern, "1. Phạm vi áp dụng", re.IGNORECASE))
    assert not bool(re.match(pattern, "1.1 Quy định chung", re.IGNORECASE))
    assert not bool(re.match(pattern, "2. Tài liệu viện dẫn", re.IGNORECASE))
