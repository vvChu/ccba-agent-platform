"""Unit tests for ccba_ooxml spreadsheet recalculation, COM engine, and error audits."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
import pytest

from ccba_ooxml import (
    OOXMLWorkspace,
    audit_xlsx_formula_errors,
    recalc_xlsx,
    setup_libreoffice_macro,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_recalc_xlsx_nonexistent():
    res = recalc_xlsx("nonexistent_file_test.xlsx")
    assert "error" in res
    assert "not exist" in res["error"]


def test_safe_macro_injection_existing_file(tmp_path: Path):
    """Verify that existing macros in Module1.xba are not overwritten or deleted."""
    fake_appdata = tmp_path / "AppData" / "Roaming"
    macro_dir = fake_appdata / "LibreOffice" / "4" / "user" / "basic" / "Standard"
    macro_dir.mkdir(parents=True, exist_ok=True)
    macro_file = macro_dir / "Module1.xba"

    existing_macro_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
    Sub MyCustomUserMacro()
      ' Do some important engineer calculation
    End Sub
</script:module>"""
    macro_file.write_text(existing_macro_content, encoding="utf-8")

    with (
        patch("platform.system", return_value="Windows"),
        patch.dict(os.environ, {"APPDATA": str(fake_appdata)}),
    ):
        ok = setup_libreoffice_macro()
        assert ok is True

        content_after = macro_file.read_text(encoding="utf-8")
        # Ensure custom user macro is preserved
        assert "MyCustomUserMacro" in content_after
        # Ensure RecalculateAndSave was safely injected
        assert "RecalculateAndSave" in content_after
        assert "</script:module>" in content_after


def test_ooxml_workspace_recalculate_dispatch(tmp_path: Path):
    """Test OOXMLWorkspace.recalculate method validation and dispatch."""
    docx_file = tmp_path / "test.docx"
    docx_file.write_text("dummy", encoding="utf-8")

    ws = OOXMLWorkspace(docx_file, validate=False)
    res = ws.recalculate()
    assert "error" in res
    assert "only supported for .xlsx" in res["error"]


def _make_sample_xlsx(path: Path, values: list[object]) -> Path:
    """Create a small valid `.xlsx` workbook in ``tmp_path``."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Calc"
    for idx, val in enumerate(values, start=1):
        ws.cell(row=idx, column=1, value=val)
    wb.save(path)
    wb.close()
    return path


def test_recalc_via_mocked_excel_com_and_pdf_export(tmp_path: Path) -> None:
    """Verify Windows Excel COM dispatch, CalculateFullRebuild, PDF export, and COM cleanup."""
    xlsx_path = _make_sample_xlsx(tmp_path / "sample.xlsx", [10, 20])
    pdf_path = tmp_path / "out" / "sample.pdf"

    mock_wb = MagicMock()
    mock_excel = MagicMock()
    mock_excel.Workbooks.Open.return_value = mock_wb

    def _fake_export(fmt: int, out_str: str) -> None:
        assert fmt == 0
        Path(out_str).write_bytes(b"%PDF-1.7\n")

    mock_wb.ExportAsFixedFormat.side_effect = _fake_export

    fake_client = MagicMock()
    fake_client.DispatchEx.return_value = mock_excel
    fake_win32com = types.ModuleType("win32com")
    fake_win32com.client = fake_client  # type: ignore[attr-defined]
    fake_pythoncom = MagicMock()

    with (
        patch("platform.system", return_value="Windows"),
        patch.dict(
            sys.modules,
            {
                "pythoncom": fake_pythoncom,
                "win32com": fake_win32com,
                "win32com.client": fake_client,
            },
        ),
    ):
        res = recalc_xlsx(xlsx_path, prefer_engine="excel", export_pdf=pdf_path, check_errors=True)

    assert res["success"] is True
    assert res["method"] == "ExcelCOM"
    assert res["formulas_evaluated"] is True
    assert Path(res["pdf_path"]) == pdf_path.resolve()
    assert pdf_path.is_file()
    assert res["formula_errors"] == []
    fake_pythoncom.CoInitialize.assert_called_once()
    assert mock_excel.AutomationSecurity == 3
    mock_excel.Workbooks.Open.assert_called_once_with(str(xlsx_path.resolve()), UpdateLinks=0)
    mock_excel.CalculateFullRebuild.assert_called_once()
    mock_wb.Save.assert_called_once()
    mock_wb.Close.assert_called_once_with(SaveChanges=False)
    mock_excel.Quit.assert_called_once()
    fake_pythoncom.CoUninitialize.assert_called_once()


def test_recalc_excel_com_fallback_to_openpyxl(tmp_path: Path) -> None:
    """Verify auto mode falls back cleanly from Excel COM failure to LibreOffice/openpyxl."""
    xlsx_path = _make_sample_xlsx(tmp_path / "fallback.xlsx", [42])
    with (
        patch("platform.system", return_value="Windows"),
        patch("ccba_ooxml.calc._recalc_via_excel_com", side_effect=RuntimeError("COM busy")),
        patch("ccba_ooxml.calc.setup_libreoffice_macro", return_value=False),
    ):
        res = recalc_xlsx(xlsx_path, prefer_engine="auto")
    assert res["success"] is True
    assert res["formulas_evaluated"] is False
    assert "openpyxl" in res["method"]


def test_recalc_xlsx_fails_loud_when_export_pdf_requested_without_engine(tmp_path: Path) -> None:
    """Verify recalc_xlsx fails loud if PDF export is requested but only openpyxl is available."""
    xlsx_path = _make_sample_xlsx(tmp_path / "no_pdf_engine.xlsx", [10])
    out_pdf = tmp_path / "out.pdf"
    with (
        patch("platform.system", return_value="Linux"),
        patch("ccba_ooxml.calc.setup_libreoffice_macro", return_value=False),
    ):
        res = recalc_xlsx(xlsx_path, prefer_engine="auto", export_pdf=out_pdf)
    assert res["success"] is False
    assert "PDF export requested" in res["error"]
    assert not out_pdf.exists()


def test_recalc_excel_engine_rejected_on_non_windows(tmp_path: Path) -> None:
    """Verify prefer_engine='excel' returns explicit error on non-Windows OS."""
    xlsx_path = _make_sample_xlsx(tmp_path / "linux.xlsx", [1])
    with patch("platform.system", return_value="Linux"):
        res = recalc_xlsx(xlsx_path, prefer_engine="excel")
    assert res.get("error") == "Excel COM recalculation is only supported on Windows."


def test_audit_xlsx_formula_errors_and_check_errors_gate(tmp_path: Path) -> None:
    """Verify audit_xlsx_formula_errors catches #REF!/#DIV/0! and check_errors fails closed."""
    clean_path = _make_sample_xlsx(tmp_path / "clean.xlsx", ["Header", 12.5])
    assert audit_xlsx_formula_errors(clean_path) == []

    broken_path = _make_sample_xlsx(tmp_path / "broken.xlsx", ["ok", "#REF!", " #DIV/0! "])
    findings = audit_xlsx_formula_errors(broken_path)
    assert len(findings) == 2
    assert findings[0] == {"sheet": "Calc", "cell": "A2", "error": "#REF!"}
    assert findings[1] == {"sheet": "Calc", "cell": "A3", "error": "#DIV/0!"}

    with (
        patch("platform.system", return_value="Linux"),
        patch("ccba_ooxml.calc.setup_libreoffice_macro", return_value=False),
    ):
        gate_res = recalc_xlsx(broken_path, check_errors=True)
    assert gate_res["success"] is False
    assert "Found 2 Excel formula error(s)" in gate_res["error"]
    assert len(gate_res["formula_errors"]) == 2
