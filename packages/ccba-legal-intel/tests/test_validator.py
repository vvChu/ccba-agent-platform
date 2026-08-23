"""Unit tests for OKF v2.2 Validator module and Spoke integrity checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ccba_legal.validator import validate_template_and_table_integrity


class TestValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.legal_docs = self.root / "legal_docs" / "01_vbpl"
        self.legal_docs.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_templates_detection(self) -> None:
        bundle_dir = self.legal_docs / "nghi_dinh_test_nd_cp"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        md_file = bundle_dir / "nghi_dinh_test_nd_cp.md"
        md_file.write_text(
            "Ban hành kèm theo Nghị định này các mẫu biểu Mẫu số 01/QTDA.",
            encoding="utf-8",
        )

        errors, warnings = validate_template_and_table_integrity(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("Template Integrity Error", errors[0])

    def test_lazy_list_continuation_detection(self) -> None:
        bundle_dir = self.legal_docs / "thong_tu_test_tt_bxd"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        md_file = bundle_dir / "thong_tu_test_tt_bxd.md"
        # Faulty: list item followed directly by subclause without blank line
        md_file.write_text(
            "- mục danh sách 1\n2.2.1. Tiểu mục bị dính dòng\n",
            encoding="utf-8",
        )

        errors, warnings = validate_template_and_table_integrity(self.root)
        self.assertEqual(len(errors), 1)
        self.assertIn("Markdown Formatting Error", errors[0])

    def test_valid_bundle_passes(self) -> None:
        bundle_dir = self.legal_docs / "thong_tu_valid_tt_bxd"
        bundle_dir.mkdir(parents=True, exist_ok=True)
        md_file = bundle_dir / "thong_tu_valid_tt_bxd.md"
        md_file.write_text(
            "- mục danh sách 1\n- mục danh sách 2\n\n**2.2.1.** Tiểu mục chuẩn có dòng trống\n",
            encoding="utf-8",
        )

        errors, warnings = validate_template_and_table_integrity(self.root)
        self.assertEqual(len(errors), 0)
        self.assertEqual(len(warnings), 0)


if __name__ == "__main__":
    unittest.main()
