"""test_lint_construction_terminology.py - Unit and governance tests for CCILF Terminology Linter Gate (COND-18, ADR-0059)."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from scripts.governance.lint_construction_terminology import (
    run_terminology_linter,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_linter_detects_forbidden_synonyms() -> None:
    """Verifies that unexempted forbidden synonyms are detected with exit code 1."""
    with TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "test_doc.md"
        doc.write_text(
            "# Báo Cáo Dự Án\n"
            "Chủ tiền đã phê duyệt thiết kế chi tiết cho dự án và yêu cầu nộp bản vẽ như xây dựng.\n",
            encoding="utf-8",
        )

        exit_code, violations = run_terminology_linter(target_path=doc, check_mode=True)
        assert exit_code == 1
        assert len(violations) >= 2
        forbidden_found = {v.forbidden_term.lower() for v in violations}
        assert "chủ tiền" in forbidden_found
        assert "thiết kế chi tiết" in forbidden_found


def test_linter_respects_immutable_citations_and_quotes() -> None:
    """Verifies that citations and quotes are not falsely flagged (COND-11)."""
    with TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "safe_doc.md"
        doc.write_text(
            "# Trích Yếu Pháp Lý\n"
            "Căn cứ Điều 2 Khoản 17 Luật PCCC 2024 và QCVN 06:2022/BXD.\n"
            'Trích dẫn nguyên văn: "Thiết kế chi tiết theo hồ sơ lưu trữ năm 2010".\n'
            "`code: select * from terms where vi_forbidden = 1;`\n",
            encoding="utf-8",
        )

        exit_code, violations = run_terminology_linter(target_path=doc, check_mode=True)
        assert exit_code == 0
        assert len(violations) == 0


def test_linter_respects_exempt_tables_and_comments() -> None:
    """Verifies that comments and dictionary definition tables are exempted."""
    with TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "exempt_doc.md"
        doc.write_text(
            "# Bảng Thuật Ngữ Cấm\n"
            "| Tiếng Anh | Tiếng Việt | Thuật ngữ Cấm / Dịch sai (vi_forbidden) |\n"
            "| :--- | :--- | :--- |\n"
            "| Concept Design | Thiết kế ý tưởng | Thiết kế khái niệm, Khái niệm thiết kế |\n\n"
            "Dòng này có ghi chú miễn trừ: chủ tiền <!-- ccba:allow-term -->\n",
            encoding="utf-8",
        )

        exit_code, violations = run_terminology_linter(target_path=doc, check_mode=True)
        assert exit_code == 0
        assert len(violations) == 0


def test_linter_fix_mode_in_place() -> None:
    """Verifies that --fix cleanly replaces forbidden terms with canonical forms."""
    with TemporaryDirectory() as tmpdir:
        doc = Path(tmpdir) / "fix_doc.md"
        doc.write_text(
            "Đơn vị đã hoàn thành thiết kế khái niệm và chuẩn bị thiết kế chi tiết.\n",
            encoding="utf-8",
        )

        exit_code, _ = run_terminology_linter(target_path=doc, check_mode=True, fix_mode=True)
        assert exit_code == 0

        fixed_content = doc.read_text(encoding="utf-8")
        assert "Thiết kế ý tưởng" in fixed_content
        assert "Thiết kế bản vẽ thi công (TKBVTC)" in fixed_content
        assert "thiết kế khái niệm" not in fixed_content
