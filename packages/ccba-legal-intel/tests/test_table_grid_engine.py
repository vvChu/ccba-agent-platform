# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests for Virtual 2D Grid Engine, ADR 0041 Table Knowledge Extraction, and Pipe Escaping."""

import re
from pathlib import Path
import pytest

from ccba_legal.converters.standard.handlers.table_handler import (
    escape_table_pipes,
    build_composite_headers,
    resolve_hierarchical_headers,
    detect_table_archetype,
)


def test_escape_table_pipes_in_prose_and_math():
    """Verify that unescaped pipe symbols in prose and math expressions are safely escaped."""
    # Prose pipe
    prose = "Cột A | Cột B"
    assert escape_table_pipes(prose) == r"Cột A \| Cột B"

    # Math absolute value
    math_abs = r"Điều kiện $|x| \le 1$ và $y > 0$"
    escaped_math = escape_table_pipes(math_abs)
    assert r"\vert " in escaped_math
    assert r"|" not in escaped_math.replace(r"\|", "").replace(r"\vert", "")

    # Conditional probability or set notation
    math_set = r"Tập hợp $\{x | x \ge 0\}$"
    escaped_set = escape_table_pipes(math_set)
    assert r"\vert " in escaped_set


def test_build_composite_headers_2tier():
    """Verify 2-tier composite header generation and deduplication."""
    header_rows = [
        ["Tường", "Tường", "Tường", "Mái"],
        ["Vùng K", "Vùng L", "Vùng M", "Mái"],
    ]
    composite = build_composite_headers(header_rows)
    assert composite == [
        "Tường — Vùng K",
        "Tường — Vùng L",
        "Tường — Vùng M",
        "Mái",
    ]


def test_build_composite_headers_3tier():
    """Verify 3-tier composite header generation."""
    header_rows = [
        ["Công suất", "Động cơ kiểu hở", "Động cơ kiểu hở", "Động cơ kiểu kín"],
        ["Công suất", "2 cực", "4 cực", "2 cực"],
        ["Công suất", "Tốc độ", "Tốc độ", "Tốc độ"],
    ]
    composite = build_composite_headers(header_rows)
    assert composite == [
        "Công suất",
        "Động cơ kiểu hở — 2 cực — Tốc độ",
        "Động cơ kiểu hở — 4 cực — Tốc độ",
        "Động cơ kiểu kín — 2 cực — Tốc độ",
    ]


def test_resolve_hierarchical_headers_backward_compatibility():
    """Ensure existing resolve_hierarchical_headers keeps backward compatibility."""
    grid = [
        ["Tường", "Tường", "Tường", "Các mặt đứng còn lại", "Mái"],
        ["Vùng K", "Vùng L", "Vùng M", "Các mặt đứng còn lại", "Mái"],
        ["0,8", "0,7", "0,6", "Theo Bảng F.4", "Theo Bảng F.5"],
    ]
    resolved = resolve_hierarchical_headers(grid)
    assert len(resolved) == 2
    assert resolved[0] == [
        "Tường — Vùng K",
        "Tường — Vùng L",
        "Tường — Vùng M",
        "Các mặt đứng còn lại",
        "Mái",
    ]
    assert resolved[1] == ["0,8", "0,7", "0,6", "Theo Bảng F.4", "Theo Bảng F.5"]


def test_detect_table_archetype():
    """Verify table archetype classification based on structure and keywords."""
    # Admin layout
    admin_text = "cộng hòa xã hội chủ nghĩa việt nam độc lập tự do hạnh phúc"
    assert detect_table_archetype(rows_count=2, cols_count=2, text=admin_text, is_captioned=False) == "BORDERLESS_LAYOUT"

    # Formula frame
    assert detect_table_archetype(rows_count=1, cols_count=2, text="(1)", is_formula_frame=True) == "BORDERLESS_LAYOUT"

    # Admin form
    form_text = "biên bản nghiệm thu công việc xây dựng [ ] đạt [ ] không đạt"
    assert detect_table_archetype(rows_count=10, cols_count=4, text=form_text, is_captioned=False) == "ADMIN_FORM"

    # In-cell multimodal
    assert detect_table_archetype(rows_count=5, cols_count=4, text="bảng f.12", has_images=True, is_captioned=True) == "IN_CELL_MULTIMODAL"

    # Hierarchical Grid
    assert detect_table_archetype(rows_count=10, cols_count=5, text="bảng 1", header_rows_count=2, is_captioned=True) == "HIERARCHICAL_GRID"

    # Flat matrix
    assert detect_table_archetype(rows_count=10, cols_count=4, text="bảng h.1", header_rows_count=1, is_captioned=True) == "FLAT_MATRIX"
