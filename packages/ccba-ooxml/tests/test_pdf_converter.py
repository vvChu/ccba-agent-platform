"""Unit tests for standalone Vector PDF conversion (Issue #299 / #306)."""

from __future__ import annotations

import subprocess
import sys
import types
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
import pytest

from ccba_ooxml import convert_to_pdf, docx_to_pdf, xlsx_to_pdf
from ccba_ooxml.form_filler.exceptions import EngineUnavailableError, FormFillerError

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_convert_to_pdf_missing_source_file():
    """Verify FileNotFoundError when input document does not exist."""
    with pytest.raises(FileNotFoundError):
        convert_to_pdf("non_existent_doc_12345.docx")


def test_convert_to_pdf_via_soffice(tmp_path: Path):
    """Verify headless conversion to PDF via LibreOffice (soffice)."""
    in_docx = tmp_path / "sample.docx"
    in_docx.write_text("dummy docx content", encoding="utf-8")
    out_pdf = tmp_path / "custom_output.pdf"

    def fake_run_soffice(args, **kwargs):
        # Create expected output in outdir
        stem = in_docx.stem
        (tmp_path / f"{stem}.pdf").write_bytes(b"%PDF-1.5 sample")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="OK", stderr="")

    with (
        patch("ccba_ooxml.converter.sys.platform", "linux"),
        patch("ccba_ooxml.converter.find_soffice_bin", return_value="/usr/bin/soffice"),
        patch("ccba_ooxml.converter.run_soffice", side_effect=fake_run_soffice),
    ):
        res = convert_to_pdf(in_docx, out_pdf, prefer_engine="soffice")
        assert res == out_pdf.resolve()
        assert out_pdf.exists()
        assert out_pdf.read_bytes().startswith(b"%PDF-")


def test_docx_to_pdf_alias_and_default_output(tmp_path: Path):
    """Verify docx_to_pdf alias and default .pdf naming."""
    in_docx = tmp_path / "contract.docx"
    in_docx.write_text("contract text", encoding="utf-8")
    expected_pdf = tmp_path / "contract.pdf"

    def fake_run_soffice(args, **kwargs):
        expected_pdf.write_bytes(b"%PDF-1.4 contract")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    with (
        patch("ccba_ooxml.converter.sys.platform", "linux"),
        patch("ccba_ooxml.converter.find_soffice_bin", return_value="/usr/bin/soffice"),
        patch("ccba_ooxml.converter.run_soffice", side_effect=fake_run_soffice),
    ):
        res = docx_to_pdf(in_docx)
        assert res == expected_pdf.resolve()
        assert expected_pdf.exists()


def test_convert_to_pdf_missing_soffice_raises_engine_error(tmp_path: Path):
    """Verify EngineUnavailableError with installation instructions when soffice is missing."""
    in_docx = tmp_path / "test.docx"
    in_docx.write_text("text", encoding="utf-8")

    with patch("ccba_ooxml.converter.find_soffice_bin", return_value=None):
        with pytest.raises(EngineUnavailableError) as exc_info:
            convert_to_pdf(in_docx, prefer_engine="soffice")
        assert "sudo apt-get install -y libreoffice-writer" in str(exc_info.value)


def test_convert_to_pdf_soffice_failure_raises_form_filler_error(tmp_path: Path):
    """Verify FormFillerError when soffice returns non-zero exit code."""
    in_docx = tmp_path / "corrupted.docx"
    in_docx.write_text("corrupted", encoding="utf-8")

    bad_proc = subprocess.CompletedProcess(
        args=["soffice"], returncode=1, stdout="", stderr="Corrupted file format"
    )

    with (
        patch("ccba_ooxml.converter.find_soffice_bin", return_value="/usr/bin/soffice"),
        patch("ccba_ooxml.converter.run_soffice", return_value=bad_proc),
    ):
        with pytest.raises(FormFillerError) as exc_info:
            convert_to_pdf(in_docx, prefer_engine="soffice")
        assert "exited with error code 1" in str(exc_info.value)


def test_convert_to_pdf_auto_winword_fallback_to_soffice(tmp_path: Path):
    """Verify that if Word COM fails on Windows with auto engine, it falls back to LibreOffice."""
    in_docx = tmp_path / "fallback_doc.docx"
    in_docx.write_text("fallback doc content", encoding="utf-8")
    expected_pdf = tmp_path / "fallback_doc.pdf"

    def fake_run_soffice(args, **kwargs):
        expected_pdf.write_bytes(b"%PDF-1.5 fallback")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    with (
        patch("sys.platform", "win32"),
        patch(
            "ccba_ooxml.converter._convert_via_winword", side_effect=Exception("Word COM crashed")
        ),
        patch("ccba_ooxml.converter.find_soffice_bin", return_value="/usr/bin/soffice"),
        patch("ccba_ooxml.converter.run_soffice", side_effect=fake_run_soffice),
    ):
        res = convert_to_pdf(in_docx, prefer_engine="auto")
        assert res == expected_pdf.resolve()
        assert expected_pdf.exists()


def test_convert_to_pdf_auto_routes_xlsx_to_excel_com_not_word(tmp_path: Path) -> None:
    """Verify Windows auto engine routes .xlsx to Excel COM rather than Word COM."""
    in_xlsx = tmp_path / "calc.xlsx"
    wb = openpyxl.Workbook()
    wb.save(in_xlsx)
    wb.close()
    out_pdf = tmp_path / "calc.pdf"

    mock_wb = MagicMock()
    mock_excel = MagicMock()
    mock_excel.Workbooks.Open.return_value = mock_wb

    def _fake_export(fmt: int, target_str: str) -> None:
        assert fmt == 0
        Path(target_str).write_bytes(b"%PDF-1.6\n")

    mock_wb.ExportAsFixedFormat.side_effect = _fake_export
    fake_client = MagicMock()
    fake_client.DispatchEx.return_value = mock_excel
    fake_win32com = types.ModuleType("win32com")
    fake_win32com.client = fake_client  # type: ignore[attr-defined]
    fake_pythoncom = MagicMock()

    with (
        patch("sys.platform", "win32"),
        patch("ccba_ooxml.converter._convert_via_winword") as mock_word,
        patch.dict(
            sys.modules,
            {
                "pythoncom": fake_pythoncom,
                "win32com": fake_win32com,
                "win32com.client": fake_client,
            },
        ),
    ):
        res = convert_to_pdf(in_xlsx, out_pdf, prefer_engine="auto")

    mock_word.assert_not_called()
    assert mock_excel.AutomationSecurity == 3
    mock_excel.Workbooks.Open.assert_called_once_with(
        str(in_xlsx.resolve()), UpdateLinks=0, ReadOnly=True
    )
    assert res == out_pdf.resolve()
    assert out_pdf.is_file()
    mock_excel.Quit.assert_called_once()


def test_convert_via_excel_rejects_corrupted_xlsx_before_com(tmp_path: Path) -> None:
    """Verify _convert_via_excel runs RULE-5.13 ZIP safety preflight before invoking COM."""
    bad_xlsx = tmp_path / "corrupt.xlsx"
    bad_xlsx.write_bytes(b"NOT_A_ZIP")

    fake_client = MagicMock()
    fake_win32com = types.ModuleType("win32com")
    fake_win32com.client = fake_client  # type: ignore[attr-defined]
    fake_pythoncom = MagicMock()

    with (
        patch.dict(
            sys.modules,
            {
                "pythoncom": fake_pythoncom,
                "win32com": fake_win32com,
                "win32com.client": fake_client,
            },
        ),
        pytest.raises(zipfile.BadZipFile),
    ):
        convert_to_pdf(bad_xlsx, prefer_engine="winexcel")

    fake_client.DispatchEx.assert_not_called()


def test_xlsx_to_pdf_win32_auto_falls_back_to_soffice(tmp_path: Path) -> None:
    """Verify xlsx_to_pdf alias falls back to LibreOffice when Excel COM raises on Windows."""
    in_xlsx = tmp_path / "calc_fallback.xlsx"
    in_xlsx.write_bytes(b"PK")
    expected_pdf = tmp_path / "calc_fallback.pdf"

    def fake_run_soffice(args, **kwargs):
        expected_pdf.write_bytes(b"%PDF-1.5 xlsx fallback")
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    with (
        patch("sys.platform", "win32"),
        patch.dict(
            sys.modules, {"win32com": types.ModuleType("win32com"), "win32com.client": MagicMock()}
        ),
        patch("ccba_ooxml.converter._convert_via_excel", side_effect=RuntimeError("Excel error")),
        patch("ccba_ooxml.converter.find_soffice_bin", return_value="/usr/bin/soffice"),
        patch("ccba_ooxml.converter.run_soffice", side_effect=fake_run_soffice),
    ):
        res = xlsx_to_pdf(in_xlsx)
    assert res == expected_pdf.resolve()
    assert expected_pdf.exists()
