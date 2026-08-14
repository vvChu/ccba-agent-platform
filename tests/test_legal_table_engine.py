"""Unit Tests for Legal DOCX Table Parsing Engine & Markdown Converter (ADR-021).

Tests Cleaners.convert_docx_table_to_markdown, extract_docx_with_tables, convert_markdown_to_docx,
and backward-compatible forwarding facades in scripts/legal/.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from scripts.legal.convert_rules_to_docx import convert_md_to_docx
from scripts.legal.tvpl_table_engine import (
    convert_docx_table_to_markdown as facade_convert_table,
)

from ccba_legal.cleaners import (
    Cleaners,
    convert_docx_table_to_markdown,
    convert_markdown_to_docx,
    extract_docx_with_tables,
)


class TestLegalTableEngine(unittest.TestCase):
    def test_convert_docx_table_to_markdown_mock(self) -> None:
        # Mock a docx Table object
        mock_row1 = MagicMock()
        cell1_1 = MagicMock()
        cell1_1.text = "Mã số\n(Code)"
        cell1_2 = MagicMock()
        cell1_2.text = "Tên Quy định"
        mock_row1.cells = [cell1_1, cell1_2]

        mock_row2 = MagicMock()
        cell2_1 = MagicMock()
        cell2_1.text = "QC-01"
        cell2_2 = MagicMock()
        cell2_2.text = "Quy chuẩn PCCC"
        mock_row2.cells = [cell2_1, cell2_2]

        mock_table = MagicMock()
        mock_table.rows = [mock_row1, mock_row2]

        md_output = convert_docx_table_to_markdown(mock_table)
        self.assertIn("| Mã số<br>(Code) | Tên Quy định |", md_output)
        self.assertIn("| --- | --- |", md_output)
        self.assertIn("| QC-01 | Quy chuẩn PCCC |", md_output)

    def test_extract_docx_with_tables_missing_file(self) -> None:
        result = extract_docx_with_tables("non_existent_file.docx")
        self.assertEqual(result, "")

    @pytest.mark.slow
    def test_convert_markdown_to_docx(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_md = Path(tmpdir) / "sample_rules.md"
            tmp_docx = Path(tmpdir) / "sample_rules.docx"

            sample_content = """---
title: Quy định Thẩm tra
---
# QUY ĐỊNH THẨM TRA THIẾT KẾ

**CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM**

## 1. Phạm Vi Điều Chỉnh

Văn bản này quy định về:
- Thẩm định thiết kế PCCC
- Thẩm tra giải pháp kiến trúc

1. Bước 1: Tiếp nhận hồ sơ
2. Bước 2: Thẩm tra đối soát

Đoạn văn với từ khóa **quan trọng** cần lưu ý.
"""
            tmp_md.write_text(sample_content, encoding="utf-8")

            # Run conversion
            convert_markdown_to_docx(tmp_md, tmp_docx)

            self.assertTrue(tmp_docx.exists())
            self.assertTrue(tmp_docx.stat().st_size > 1000)

    def test_facades_backward_compatibility(self) -> None:
        self.assertTrue(callable(facade_convert_table))
        self.assertTrue(callable(convert_md_to_docx))
        self.assertTrue(callable(Cleaners.convert_docx_table_to_markdown))


if __name__ == "__main__":
    unittest.main()
