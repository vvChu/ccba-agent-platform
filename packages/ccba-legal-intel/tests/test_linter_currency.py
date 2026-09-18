"""test_linter_currency.py - Unit tests for context-aware legal currency linter (ADR 0050, ADR 0058)."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from ccba_legal.linter import (
    extract_file_lines,
    is_transitional_context,
    lint_file_currency,
    lint_target_path,
)


def test_assertive_obsolete_citations(tmp_path: Path) -> None:
    """Verify assertive citations of repealed statutes are flagged as ERROR."""
    doc = tmp_path / "proposal.md"
    doc.write_text(
        """# Đề xuất kỹ thuật
Căn cứ Nghị định 15/2021/NĐ-CP về quản lý dự án đầu tư xây dựng.
Áp dụng Thông tư 06/2021/TT-BXD để phân cấp công trình.
Theo quy định của Luật Xây dựng 2014.
""",
        encoding="utf-8",
    )

    findings = lint_file_currency(doc)
    errors = [f for f in findings if f["severity"] == "ERROR"]

    assert len(errors) == 3
    matched_docs = {f["obsolete_doc"] for f in errors}
    assert "Nghị định 15/2021/NĐ-CP" in matched_docs
    assert "Thông tư 06/2021/TT-BXD" in matched_docs
    assert "Luật Xây dựng 2014 (50/2014/QH13)" in matched_docs

    # Suggested replacements check
    rep_15 = next(f for f in errors if "15/2021" in f["matched_text"])
    assert "217/2026" in rep_15["replacement"]

    rep_06 = next(f for f in errors if "06/2021" in f["matched_text"])
    assert "34/2026" in rep_06["replacement"]


def test_transitional_context_exemption(tmp_path: Path) -> None:
    """Verify citations within transitional or comparative statements are exempted (PASS)."""
    doc = tmp_path / "transitional.md"
    doc.write_text(
        """# Báo cáo chuyển tiếp pháp lý
1. Dự án tuân thủ Nghị định 217/2026/NĐ-CP (thay thế cho Nghị định 15/2021/NĐ-CP trước đây).
2. Áp dụng Thông tư 34/2026/TT-BXD bãi bỏ Thông tư 06/2021/TT-BXD.
3. So sánh với quy định cũ tại Luật Xây dựng 2014, Luật 135/2025/QH15 có nhiều điểm mới.
4. Tuân thủ Nghị định 207/2026/NĐ-CP (trước đây là NĐ 06/2021/NĐ-CP).
""",
        encoding="utf-8",
    )

    findings = lint_file_currency(doc)
    errors = [f for f in findings if f["severity"] == "ERROR"]
    assert len(errors) == 0, f"Expected 0 errors due to transitional exemption, got: {errors}"


def test_valid_active_standards_preserved(tmp_path: Path) -> None:
    """Verify active standards with older years (e.g. TCVN 10333-1:2014) are not falsely flagged."""
    doc = tmp_path / "standards.md"
    doc.write_text(
        """# Tiêu chuẩn áp dụng
- Hố ga bê tông đúc sẵn: TCVN 10333-1:2014.
- An toàn cháy: QCVN 06:2022/BXD và Sửa đổi 1:2023 QCVN 06:2022/BXD.
- Tải trọng và tác động: TCVN 2737:2023.
- Kết cấu thép: TCVN 5575:2024.
- Luật hiện hành: Luật Xây dựng 2025 (135/2025/QH15).
""",
        encoding="utf-8",
    )

    findings = lint_file_currency(doc)
    errors = [f for f in findings if f["severity"] == "ERROR"]
    assert len(errors) == 0, f"Expected 0 errors for valid active standards, got: {errors}"


def test_two_tier_severity_unverified_statutes(tmp_path: Path) -> None:
    """Verify unverified statutes produce WARNING without failing total_errors (ADR 0058)."""
    doc = tmp_path / "unverified.md"
    doc.write_text(
        """# Văn bản tham khảo
Căn cứ Nghị định 999/2024/NĐ-CP của Chính phủ.
""",
        encoding="utf-8",
    )

    res = lint_target_path(doc, check_currency=True)
    assert res["currency_errors"] == 0
    assert res["currency_warnings"] == 1
    assert res["total_errors"] == 0  # Does not break build!


def test_pptx_currency_extraction(tmp_path: Path) -> None:
    """Verify PPTX slide XML extraction and obsolete citation detection without external deps."""
    pptx_path = tmp_path / "deck.pptx"

    # Construct a minimal valid PPTX zip structure
    slide1_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r><a:t>Căn cứ Nghị định 15/2021/NĐ-CP</a:t></a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""

    slide2_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
    <p:cSld>
        <p:spTree>
            <p:sp>
                <p:txBody>
                    <a:p>
                        <a:r><a:t>Áp dụng Nghị định 217/2026/NĐ-CP (thay thế NĐ 15/2021/NĐ-CP)</a:t></a:r>
                    </a:p>
                </p:txBody>
            </p:sp>
        </p:spTree>
    </p:cSld>
</p:sld>"""

    with zipfile.ZipFile(pptx_path, "w") as z:
        z.writestr("ppt/slides/slide1.xml", slide1_xml)
        z.writestr("ppt/slides/slide2.xml", slide2_xml)

    lines = extract_file_lines(pptx_path)
    assert len(lines) >= 2
    assert "Slide 1" in lines[0][1]

    findings = lint_file_currency(pptx_path)
    errors = [f for f in findings if f["severity"] == "ERROR"]

    # Only slide 1 should be flagged as ERROR; slide 2 has transitional "thay thế"
    assert len(errors) == 1
    assert "Slide 1" in errors[0]["location"]
    assert "15/2021" in errors[0]["matched_text"]


def test_directory_scan_ignores_legal_docs(tmp_path: Path) -> None:
    """Verify recursive directory scan skips legal_docs repository/archive directory."""
    work_dir = tmp_path / "project"
    work_dir.mkdir()

    # Deliverable file with obsolete citation
    deliv = work_dir / "deliverable.md"
    deliv.write_text("Căn cứ Nghị định 15/2021/NĐ-CP", encoding="utf-8")

    # Raw legal corpus archive inside project (should be skipped)
    legal_docs = work_dir / "legal_docs" / "01_vbpl" / "nd_15_2021"
    legal_docs.mkdir(parents=True)
    raw_file = legal_docs / "doc.md"
    raw_file.write_text("Nghị định 15/2021/NĐ-CP toàn văn...", encoding="utf-8")

    res = lint_target_path(work_dir, check_currency=True)
    assert res["files_scanned"] == 1  # Only deliverable.md, raw_file skipped!
    assert res["currency_errors"] == 1
    assert res["total_errors"] == 1
