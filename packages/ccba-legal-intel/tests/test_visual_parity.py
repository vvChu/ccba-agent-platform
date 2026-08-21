"""Unit tests for Visual Parity Auditor in ccba-legal-intel."""

from pathlib import Path

from ccba_legal.visual_parity import VisualParityAuditor


def test_visual_parity_clean(tmp_path: Path) -> None:
    legal_docs = tmp_path / "legal_docs"
    legal_docs.mkdir()

    clean_md = legal_docs / "clean.md"
    clean_md.write_text(
        "# Tiêu đề\n\n- Mục 1\n- Mục 2\n\n_CHÚ THÍCH:_\n- **CHÚ THÍCH 1:** Nội dung.\n",
        encoding="utf-8",
    )

    auditor = VisualParityAuditor(legal_docs_root=legal_docs)
    res = auditor.audit()
    assert res["passed"] is True
    assert res["critical_errors_count"] == 0


def test_visual_parity_detects_errors(tmp_path: Path) -> None:
    legal_docs = tmp_path / "legal_docs"
    legal_docs.mkdir()

    bad_md = legal_docs / "bad.md"
    bad_md.write_text(
        "# Tiêu đề lỗi\n\n"
        "- - Lỗi double bullet\n"
        "_CHÚ THÍCH:_\n"
        "_CHÚ THÍCH:_\n"
        "| Bảng | Cột |\n"
        "| --- | --- |\n"
        "| Dữ liệu | _1) Trapped footnote |\n",
        encoding="utf-8",
    )

    auditor = VisualParityAuditor(legal_docs_root=legal_docs)
    res = auditor.audit()
    assert res["passed"] is False
    assert res["critical_errors_count"] >= 3
