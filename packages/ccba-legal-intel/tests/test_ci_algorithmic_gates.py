# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests for Master CI 2.0 Algorithmic Gates (Gates 13, 14, 15)."""

from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from ccba_legal.constants import (
    CURRENT_CONVERTER_VERSION,
    CURRENT_OKF_SCHEMA_URI,
    CURRENT_OKF_SPEC,
    CURRENT_OKF_VERSION,
)


def test_constants_ssot():
    """Verify central SSoT constants are properly defined."""
    assert CURRENT_OKF_VERSION == "2.4"
    assert "v2.4" in CURRENT_OKF_SPEC
    assert CURRENT_CONVERTER_VERSION == "0.4.0"
    assert CURRENT_OKF_SCHEMA_URI.startswith("https://schemas.ccba.vn/okf/")


def test_table_matrix_regularity_logic(tmp_path: Path):
    """Test 2D CSV Matrix Regularity and Ragged Row detection (ADR 0041)."""
    # 1. Valid rectangular table
    valid_csv = tmp_path / "valid.csv"
    with open(valid_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Mã", "Tên", "Giá trị"])
        writer.writerow(["A1", "Cột 1", "100"])
        writer.writerow(["A2", "Cột 2", "200"])

    with open(valid_csv, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header_cols = len(rows[0])
    ragged_rows = [i for i, r in enumerate(rows[1:], start=2) if len(r) != header_cols]
    assert len(ragged_rows) == 0

    # 2. Ragged table (skewed rows)
    ragged_csv = tmp_path / "ragged.csv"
    with open(ragged_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Mã", "Tên", "Giá trị", "Ghi chú"])
        writer.writerow(["A1", "Cột 1", "100"])  # Missing 1 col
        writer.writerow(["A2", "Cột 2", "200", "OK", "Extra"])  # Extra col

    with open(ragged_csv, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    header_cols = len(rows[0])
    ragged_rows = [i for i, r in enumerate(rows[1:], start=2) if len(r) != header_cols]
    assert ragged_rows == [2, 3]

    # 3. Footnote contamination detection
    footnote_csv = tmp_path / "footnote.csv"
    with open(footnote_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Mã", "Tên"])
        writer.writerow(["A1", "Tên 1"])
        writer.writerow(["CHÚ THÍCH: Số liệu tính theo phụ lục", ""])

    with open(footnote_csv, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    leaks = [
        i
        for i, r in enumerate(rows[1:], start=2)
        if re.match(r"^(?:CHÚ\s+THÍCH|CHÚ\s+DẪN|Ghi\s+chú|\(\*\))\s*:", " ".join(r).strip(), re.I)
    ]
    assert leaks == [3]


def test_katex_syntax_integrity_lexer():
    """Test KaTeX regex lexer detecting critical rendering traps (ADR 0038)."""
    # 1. Valid KaTeX block
    valid_md = r"""
$$
w = w_0 \cdot k(z_e) \cdot c \qquad (1)
$$
"""
    # Even display math count
    assert len(re.findall(r"\$\$", valid_md)) % 2 == 0
    blocks = re.findall(r"\$\$([\s\S]*?)\$\$", valid_md)
    assert len(blocks) == 1
    assert "<!--" not in blocks[0]

    # 2. Unsupported \tag{...} inside aligned environment
    invalid_tag_md = r"""
$$
\begin{aligned}
a &= b + c \tag{1} \\
d &= e + f
\end{aligned}
$$
"""
    block = re.findall(r"\$\$([\s\S]*?)\$\$", invalid_tag_md)[0]
    has_tag_in_aligned = "\\begin{aligned}" in block and bool(re.search(r"\\tag\s*\{[^}]*\}", block))
    assert has_tag_in_aligned is True

    # 3. Embedded HTML comment inside $$
    invalid_comment_md = r"""
$$
E = mc^2 <!-- FIGURE: EINSTEIN -->
$$
"""
    block = re.findall(r"\$\$([\s\S]*?)\$\$", invalid_comment_md)[0]
    assert ("<!--" in block and "-->" in block) is True

    # 4. Unbalanced \left and \right
    unbalanced_left_md = r"""
$$
f(x) = \left[ \frac{a}{b} + c )
$$
"""
    block = re.findall(r"\$\$([\s\S]*?)\$\$", unbalanced_left_md)[0]
    left_count = len(re.findall(r"\\left[\(\[\{\.\vert]", block))
    right_count = len(re.findall(r"\\right[\)\]\}\.\vert]", block))
    assert left_count == 1
    assert right_count == 0


def test_provenance_attestation_logic():
    """Test Provenance stamp validation against SSoT constants."""
    metadata: dict[str, Any] = {
        "id": "test_bundle",
        "okf_spec": "v2.4 Universal",
        "converter_version": "0.4.0",
        "extracted_at": "2026-09-04T13:30:00Z",
        "schema_uri": "https://schemas.ccba.vn/okf/v2.4/schema.json",
    }
    assert metadata.get("okf_spec") == CURRENT_OKF_SPEC
    assert metadata.get("converter_version") == CURRENT_CONVERTER_VERSION
    # Validate ISO-8601 format
    parsed_date = datetime.fromisoformat(metadata["extracted_at"].replace("Z", "+00:00"))
    assert parsed_date.year == 2026
