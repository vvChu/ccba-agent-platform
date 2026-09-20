"""Unit tests for Markdown Architectural Specification Matrix generator."""

from __future__ import annotations

from ccba_diagram.matrix_table import generate_markdown_spec_table
from helpers import make_arrow, make_shape


def test_generate_spec_table_basic():
    """Test generating standard Markdown specification table from diagram elements."""
    s1 = make_shape("HUB", text="Lõi Điều Phối [[coordinator|Điều Phối Viên]]", w=160, h=100)
    s1["backgroundColor"] = "#e3f2fd"  # Hub role
    s2 = make_shape("DAEMON", text="Tiến Trình Chạy Ngầm (Daemon #40;v8.15#41;)")
    arr = make_arrow("a1", "HUB", "DAEMON")

    elements = [s1, s2, arr]
    table_md = generate_markdown_spec_table(elements, table_title="Bảng Thử Nghiệm")

    # Table Title
    assert "### 📋 Bảng Thử Nghiệm" in table_md
    # Table Header
    assert (
        "| STT | Thành Phần / Nút Kiến Trúc | Phân Loại & Hình Khối | Kết Nối Đến / Luồng Dữ Liệu |"
        in table_md
    )
    # Wikilink pipe escaping
    assert "[[coordinator\\|Điều Phối Viên]]" in table_md
    # No HTML entity bracket leakage
    assert "#40;" not in table_md
    assert "#41;" not in table_md
    assert "(Daemon (v8.15))" in table_md or "(v8.15)" in table_md
    # Flow indicator
    assert "↳&nbsp;" in table_md
    # Hub designation
    assert "**Lõi Điều Phối (Hub/Core)**" in table_md


def test_generate_spec_table_empty():
    """Test empty diagram yields fallback message."""
    table_md = generate_markdown_spec_table([])
    assert "Không có nút hình học" in table_md
