# packages/ccba-ooxml/tests/test_form_filler.py
"""Unit tests for Word Form Filler and Form Layout Guard (Issue #296)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import docx
import pytest
from docx.oxml.ns import qn

from ccba_ooxml.form_filler import (
    FormFillConfig,
    FormLayoutGuard,
    SofficeFallbackEngine,
    TableRule,
    TemplateNotFoundError,
    WinwordEngine,
    WordFormFiller,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_models_validation():
    """Validates FormFillConfig and TableRule schemas."""
    config = FormFillConfig(
        engine="auto",
        keep_font_formatting=True,
        prevent_row_split=True,
        prune_empty_rows=True,
        page_break_keywords=["PHẦN 2", "MỤC III"],
    )
    assert config.engine == "auto"
    assert config.keep_font_formatting is True
    assert len(config.page_break_keywords) == 2

    rule = TableRule(
        table_index=1,
        header_keyword="DANH SÁCH",
        data_rows=[{"Họ tên": "Nguyen Van A", "Năm sinh": "1990"}],
        delete_unused_template_rows=True,
        allow_break_across_pages=False,
    )
    assert rule.table_index == 1
    assert len(rule.data_rows) == 1
    assert rule.allow_break_across_pages is False


def test_template_not_found(tmp_path: Path):
    """Verifies that non-existent template raises TemplateNotFoundError."""
    missing_file = tmp_path / "missing_template.doc"
    with pytest.raises(TemplateNotFoundError):
        WordFormFiller(missing_file)


def test_layout_guard_docx_cant_split():
    """Verifies injection of <w:cantSplit/> XML element into table row properties."""
    doc = docx.Document()
    table = doc.add_table(rows=2, cols=2)
    row = table.rows[0]

    tr_pr = row._tr.get_or_add_trPr()
    assert tr_pr.find(qn("w:cantSplit")) is None

    FormLayoutGuard.apply_docx_cant_split(row)
    assert tr_pr.find(qn("w:cantSplit")) is not None

    # Calling twice should be idempotent
    FormLayoutGuard.apply_docx_cant_split(row)
    assert len(tr_pr.findall(qn("w:cantSplit"))) == 1


def test_layout_guard_empty_row_detection_and_removal():
    """Verifies detection and clean removal of empty table rows."""
    doc = docx.Document()
    table = doc.add_table(rows=3, cols=2)
    table.rows[0].cells[0].text = "Header 1"
    table.rows[0].cells[1].text = "Header 2"

    table.rows[1].cells[0].text = "Filled Data"
    table.rows[1].cells[1].text = "Some Value"

    # Row 2 remains empty
    assert not FormLayoutGuard.is_docx_row_empty(table.rows[0])
    assert not FormLayoutGuard.is_docx_row_empty(table.rows[1])
    assert FormLayoutGuard.is_docx_row_empty(table.rows[2])

    FormLayoutGuard.remove_docx_row(table, table.rows[2])
    assert len(table.rows) == 2


def test_fallback_engine_paragraph_and_table_filling(tmp_path: Path):
    """Verifies end-to-end template population using python-docx fallback engine."""
    # 1. Create a dummy DOCX template
    template_path = tmp_path / "test_template.docx"
    doc = docx.Document()
    doc.add_paragraph("HỒ SƠ THỊ THỰC / VISA APPLICATION")
    doc.add_paragraph("HỌ VÀ TÊN: {{HO_VA_TEN}}")
    doc.add_paragraph("NGÀY SINH: {{NGAY_SINH}}")

    # Add dynamic table: row 0 is header, row 1 is template row, row 2 is unused empty row
    table = doc.add_table(rows=3, cols=3)
    table.rows[0].cells[0].text = "STT"
    table.rows[0].cells[1].text = "Họ Tên"
    table.rows[0].cells[2].text = "Quan Hệ"

    table.rows[1].cells[0].text = "{{STT}}"
    table.rows[1].cells[1].text = "{{HO_TEN}}"
    table.rows[1].cells[2].text = "{{QUAN_HE}}"

    doc.add_paragraph("PHẦN KẾT LUẬN: Đã kiểm tra đầy đủ hồ sơ.")
    doc.save(str(template_path))

    # 2. Run WordFormFiller in soffice/fallback mode
    out_docx = tmp_path / "filled_output.docx"
    config = FormFillConfig(
        engine="soffice",
        prevent_row_split=True,
        prune_empty_rows=True,
        page_break_keywords=["PHẦN KẾT LUẬN"],
    )

    with WordFormFiller(template_path, config=config) as filler:
        filler.apply_paragraphs(
            {
                "{{HO_VA_TEN}}": "VŨ VĂN CHỦ",
                "{{NGAY_SINH}}": "15/08/1990",
            }
        )
        filler.apply_tables(
            [
                TableRule(
                    table_index=0,
                    data_rows=[
                        {"STT": "1", "Họ Tên": "Nguyễn Văn A", "Quan Hệ": "Bố"},
                        {"STT": "2", "Họ Tên": "Trần Thị B", "Quan Hệ": "Mẹ"},
                    ],
                    delete_unused_template_rows=True,
                    allow_break_across_pages=False,
                )
            ]
        )
        filler.export(doc_out=out_docx)

    assert out_docx.exists()

    # 3. Inspect generated document
    result_doc = docx.Document(str(out_docx))
    full_text = "\n".join(p.text for p in result_doc.paragraphs)
    assert "VŨ VĂN CHỦ" in full_text
    assert "15/08/1990" in full_text
    assert "{{HO_VA_TEN}}" not in full_text

    # Verify table rows
    res_table = result_doc.tables[0]
    # Header + 2 data rows = 3 rows total (empty row 2 pruned)
    assert len(res_table.rows) == 3
    assert res_table.rows[1].cells[1].text == "Nguyễn Văn A"
    assert res_table.rows[2].cells[1].text == "Trần Thị B"

    # Verify cantSplit guard applied across all rows
    for r in res_table.rows:
        tr_pr = r._tr.get_or_add_trPr()
        assert tr_pr.find(qn("w:cantSplit")) is not None


def test_winword_engine_mocked(tmp_path: Path):
    """Verifies WinwordEngine execution flow with a mocked Word COM application."""
    template_path = tmp_path / "mock_template.docx"
    template_path.write_text("Dummy binary content", encoding="utf-8")

    # Mock Word COM DOM hierarchy
    mock_word = MagicMock()
    mock_doc = MagicMock()
    mock_word.Documents.Open.return_value = mock_doc

    # Mock Paragraph
    mock_p = MagicMock()
    mock_p.Range.Text = "HỌ VÀ TÊN: {{HO_VA_TEN}}"
    mock_doc.Paragraphs = [mock_p]

    # Mock Table
    mock_table = MagicMock()
    mock_doc.Tables = MagicMock()
    mock_doc.Tables.Count = 1
    mock_doc.Tables.Item.return_value = mock_table
    mock_doc.Tables.__iter__.return_value = [mock_table]

    mock_row = MagicMock()
    mock_table.Rows = MagicMock()
    mock_table.Rows.Count = 1
    mock_table.Rows.__iter__.return_value = [mock_row]

    engine = WinwordEngine(
        template_path=template_path,
        config=FormFillConfig(prevent_row_split=True),
        word_app=mock_word,
    )

    engine.apply_paragraphs({"{{HO_VA_TEN}}": "TEST USER"})
    assert mock_p.Range.Text == "HỌ VÀ TÊN: TEST USER"

    engine.apply_layout_guard()
    assert mock_row.AllowBreakAcrossPages is False

    out_doc = tmp_path / "mock_out.doc"
    out_pdf = tmp_path / "mock_out.pdf"
    engine.export(doc_out=out_doc, pdf_out=out_pdf)

    assert mock_doc.SaveAs2.called
    assert mock_doc.ExportAsFixedFormat.called

    engine.close()
    mock_doc.Close.assert_called_with(SaveChanges=False)


def test_engine_auto_detection_on_linux(tmp_path: Path):
    """Verifies that engine='auto' resolves to SofficeFallbackEngine on non-Windows platforms."""
    template_path = tmp_path / "auto_test.docx"
    doc = docx.Document()
    doc.add_paragraph("Sample")
    doc.save(str(template_path))

    with WordFormFiller(template_path, engine="auto") as filler:
        assert isinstance(filler._engine, SofficeFallbackEngine)
