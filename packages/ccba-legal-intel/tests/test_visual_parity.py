"""Unit tests for Visual Parity Auditor & Linter in ccba-legal-intel."""

from pathlib import Path

from ccba_legal.visual_parity import VisualParityAuditor, lint_document


def test_visual_parity_clean(tmp_path: Path) -> None:
    legal_docs = tmp_path / "legal_docs"
    legal_docs.mkdir()

    clean_md = legal_docs / "clean.md"
    clean_md.write_text(
        "# Tiêu đề\n\n- Mục 1\n- Mục 2\n\n_CHÚ THÍCH:_\n1) Nội dung chú thích.\n",
        encoding="utf-8",
    )

    auditor = VisualParityAuditor(legal_docs_root=legal_docs)
    res = auditor.audit()
    assert res["passed"] is True
    assert res["critical_errors_count"] == 0


def test_lint_document_detects_all_anomalies(tmp_path: Path) -> None:
    bad_md = tmp_path / "bad.md"
    bad_md.write_text(
        "# Tiêu đề lỗi\n\n"
        "- - Lỗi double bullet\n"
        "_CHÚ THÍCH:_\n"
        "_CHÚ THÍCH:_\n"
        "| Bảng | Cột |\n"
        "| --- | --- |\n"
        "| Dữ liệu | _1) Trapped footnote |\n"
        "- **CHÚ THÍCH 1:** Bị thừa bullet\n"
        "<table><tr><td>HTML table</td></tr></table>\n",
        encoding="utf-8",
    )

    errs = lint_document(bad_md)
    assert len(errs) >= 5
    assert any("DOUBLE_BULLET" in e for e in errs)
    assert any("DUPLICATE_NOTE_HEADER" in e for e in errs)
    assert any("TRAPPED_TABLE_FOOTNOTE" in e for e in errs)
    assert any("REDUNDANT_NOTE_BULLET" in e for e in errs)
    assert any("UNCLEAN_HTML_TABLE" in e for e in errs)


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

