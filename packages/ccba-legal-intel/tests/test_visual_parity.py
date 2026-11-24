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


def test_lint_document_detects_malformed_bold_glue_and_exempts_forms(tmp_path: Path) -> None:
    """Detect ____ glued to words/digits while ignoring administrative blank lines and code blocks."""
    normative_md = tmp_path / "nghi_dinh_35.md"
    normative_md.write_text(
        "____Điều 14. Sửa đổi, bổ sung\n"
        "__Sửa đổi ____khoản 4__\n"
        "**1.** ____1. Quy định chung\n"
        "Tên cơ quan: _____ [ghi tên cơ quan]\n"
        "____ [ghi tên đơn vị]\n"
        "____[ghi tên]\n"
        "Ngày ____ tháng ____ năm ____\n"
        "Số: ____/QĐ-BXD\n"
        "Họ tên:____Ngày sinh:\n"
        "____\n"
        "```text\n"
        "____Điều 99. Ví dụ trong code block\n"
        "```\n",
        encoding="utf-8",
    )

    errs = lint_document(normative_md)
    assert len(errs) == 3
    assert all("MALFORMED_BOLD_GLUE" in e for e in errs)
    assert any("Line 1:" in e and "____Điều 14" in e for e in errs)
    assert any("Line 2:" in e and "____khoản 4" in e for e in errs)
    assert any("Line 3:" in e and "____1. Quy định" in e for e in errs)


def test_lint_document_exempts_templates_and_sources_for_bold_glue(tmp_path: Path) -> None:
    """Exempt templates/ and sources/ from MALFORMED_BOLD_GLUE while linting annexes/."""
    legal_docs = tmp_path / "legal_docs"
    templates_dir = legal_docs / "01_vbpl" / "tt_03" / "templates"
    sources_dir = legal_docs / "01_vbpl" / "tt_03" / "sources"
    annexes_dir = legal_docs / "01_vbpl" / "tt_03" / "annexes"
    templates_dir.mkdir(parents=True)
    sources_dir.mkdir(parents=True)
    annexes_dir.mkdir(parents=True)

    tpl_md = templates_dir / "mau_01.md"
    tpl_md.write_text("____Điều 14\nTên cơ quan: _____ [ghi tên cơ quan]\n", encoding="utf-8")
    src_md = sources_dir / "raw.md"
    src_md.write_text("____khoản 4\n", encoding="utf-8")
    annex_ok = annexes_dir / "phu_luc.md"
    annex_ok.write_text("Tên cơ quan: _____ [ghi tên cơ quan]\n", encoding="utf-8")

    assert lint_document(tpl_md) == []
    assert lint_document(src_md) == []
    assert lint_document(annex_ok) == []

    annex_bad = annexes_dir / "phu_luc_bad.md"
    annex_bad.write_text("____Điều 14. Sửa đổi\n", encoding="utf-8")

    res = VisualParityAuditor(legal_docs_root=legal_docs).audit()
    assert res["passed"] is False
    assert res["critical_errors_count"] == 1
    assert "phu_luc_bad.md" in res["critical_errors"][0]
    assert "MALFORMED_BOLD_GLUE" in res["critical_errors"][0]
