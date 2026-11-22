"""Unit and XML DOM round-trip tests for ``ccba_ooxml.xlsx`` seams."""

from __future__ import annotations

import hashlib
import os
import zipfile
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

import openpyxl
import pytest
from openpyxl.styles import Alignment, Font, PatternFill

from ccba_ooxml import (
    MergedCellWriteError,
    TemplateNotFoundError,
    TemplateProtectionError,
    XlsxFillConfig,
    XlsxHeaderStyle,
    XlsxMediaLimitError,
    XlsxReader,
    XlsxTemplateFiller,
    XlsxWorkbookWriter,
    recalc_xlsx,
    sanitize_xlsx_value,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]

_NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _build_template_xlsx(path: Path, *, with_merge: bool = False) -> Path:
    """Create a styled `.xlsx` template fixture in ``tmp_path``."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "HopDong"
    ws["B2"] = "Ten hop dong"
    ws["B4"] = "OLD_CODE"
    if with_merge:
        ws.merge_cells("B2:C2")

    # Styled sample row 5 with existing row 6 values to verify in-place overwrite (no insert_rows)
    for col_idx, val in enumerate(("STT", 0.0), start=1):
        cell = ws.cell(row=5, column=col_idx, value=val)
        cell.font = Font(name="Arial", size=11, bold=True)
        cell.fill = PatternFill(start_color="EEEEEE", end_color="EEEEEE", fill_type="solid")
        cell.alignment = Alignment(horizontal="right")
        if col_idx == 2:
            cell.number_format = "#,##0.00"
    ws.cell(row=8, column=1, value="FOOTER_ANCHOR")
    wb.save(path)
    wb.close()
    return path


def _append_zip_entry(src_xlsx: Path, dst_xlsx: Path, entry_name: str, payload: bytes) -> Path:
    """Copy an `.xlsx` archive while adding a synthetic ZIP entry compressed with DEFLATE."""
    with (
        zipfile.ZipFile(src_xlsx, "r") as zin,
        zipfile.ZipFile(dst_xlsx, "w", compression=zipfile.ZIP_DEFLATED) as zout,
    ):
        for item in zin.infolist():
            zout.writestr(item.filename, zin.read(item.filename))
        zout.writestr(entry_name, payload)
    return dst_xlsx


def _read_sheet_xml(xlsx_path: Path, sheet_xml: str = "xl/worksheets/sheet1.xml") -> ET.Element:
    with zipfile.ZipFile(xlsx_path, "r") as zf:
        return ET.fromstring(zf.read(sheet_xml))


def test_filler_round_trip_styles_in_place_and_bytes(tmp_path: Path) -> None:
    """Verify fill_cells, write_styled_row(s) in-place, style copy, export, and export_bytes."""
    tpl = _build_template_xlsx(tmp_path / "tpl.xlsx")
    tpl_sha_before = hashlib.sha256(tpl.read_bytes()).hexdigest()
    out_file = tmp_path / "out" / "filled.xlsx"

    with XlsxTemplateFiller(tpl) as filler:
        filler.fill_cells({"B4": "HD-842", (3, 2): Decimal("123.45")})
        filler.write_styled_row(6, [1, Decimal("999.5")], style_from_row=5)
        filler.write_styled_rows(
            7,
            [[2, "=CMD()"], [3, date(2026, 11, 22)]],
            style_from_row=5,
        )
        raw_bytes = filler.export_bytes()
        saved = filler.export(out_file)

    assert saved == out_file.resolve()
    assert raw_bytes[:2] == b"PK"
    # Template untouched by operations and __exit__
    assert hashlib.sha256(tpl.read_bytes()).hexdigest() == tpl_sha_before

    # XML DOM assertions: cell values & style preservation; row 8 FOOTER_ANCHOR did NOT shift down
    root = _read_sheet_xml(saved)
    b6 = root.find(".//main:c[@r='B6']", _NS)
    b5 = root.find(".//main:c[@r='B5']", _NS)
    assert b5 is not None and b6 is not None
    assert b6.attrib.get("s") == b5.attrib.get("s")

    with XlsxReader(saved) as reader:
        rows = list(reader.iter_rows(min_row=1, values_only=True))
    assert rows[2][1] == 123.45  # (3, 2) -> B3
    assert rows[3][1] == "HD-842"  # B4
    assert rows[5][:2] == (1, 999.5)  # row 6
    assert rows[6][:2] == (2, "'=CMD()")  # formula neutralized
    assert rows[7][1] == "2026-11-22"  # row 7 overwriting existing rows without shifting
    assert rows[7][0] == 3  # A8 overwritten cleanly (no insert_rows push to row 9)


def test_filler_template_protection_relative_and_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify TemplateProtectionError with relative paths and TemplateNotFoundError."""
    with pytest.raises(TemplateNotFoundError):
        XlsxTemplateFiller(tmp_path / "does_not_exist.xlsx")

    tpl = _build_template_xlsx(tmp_path / "immutable.xlsx")
    tpl_sha = hashlib.sha256(tpl.read_bytes()).hexdigest()
    monkeypatch.chdir(tmp_path)

    with XlsxTemplateFiller(Path("immutable.xlsx")) as filler:
        assert filler.template_path == tpl.resolve()
        with pytest.raises(TemplateProtectionError):
            filler.export(Path("./immutable.xlsx"))
        with pytest.raises(TemplateProtectionError):
            filler.export(tpl)

    assert hashlib.sha256(tpl.read_bytes()).hexdigest() == tpl_sha


def test_filler_on_merged_three_modes_atomic(tmp_path: Path) -> None:
    """Verify on_merged modes: atomic error, skip, and top_left last-write-wins."""
    tpl = _build_template_xlsx(tmp_path / "merged.xlsx", with_merge=True)

    # error mode must pre-scan all targets before mutating A1
    with XlsxTemplateFiller(tpl, XlsxFillConfig(on_merged="error")) as f_err:
        with pytest.raises(MergedCellWriteError) as exc_info:
            f_err.fill_cells({"A1": "SHOULD_NOT_WRITE", "C2": "NON_ANCHOR"})
        assert exc_info.value.sheet_name == "HopDong"
        assert exc_info.value.coordinate == "C2"
        out_err = f_err.export(tmp_path / "err_check.xlsx")
    with XlsxReader(out_err) as r:
        assert list(r.iter_rows(min_row=1, max_row=2, values_only=True))[0][0] is None

    # skip mode leaves C2 untouched while writing normal cells
    with XlsxTemplateFiller(tpl, XlsxFillConfig(on_merged="skip")) as f_skip:
        f_skip.fill_cells({"A1": "OK", "C2": "SKIPPED"})
        out_skip = f_skip.export(tmp_path / "skip_check.xlsx")
    with XlsxReader(out_skip) as r:
        data = list(r.iter_rows(min_row=1, max_row=2, values_only=True))
        assert data[0][0] == "OK"
        assert data[1][1] == "Ten hop dong"

    # top_left redirects C2 -> B2, and later writes win in mapping order
    with XlsxTemplateFiller(tpl, XlsxFillConfig(on_merged="top_left")) as f_tl:
        f_tl.fill_cells({"C2": "FIRST", "B2": "LAST_WINS"})
        out_tl_1 = f_tl.export(tmp_path / "tl1.xlsx")
    with XlsxReader(out_tl_1) as r:
        assert list(r.iter_rows(min_row=2, max_row=2, values_only=True))[0][1] == "LAST_WINS"

    with XlsxTemplateFiller(tpl, XlsxFillConfig(on_merged="top_left")) as f_tl2:
        f_tl2.fill_cells({"B2": "FIRST", "C2": "REDIRECT_WINS"})
        out_tl_2 = f_tl2.export(tmp_path / "tl2.xlsx")
    with XlsxReader(out_tl_2) as r:
        assert list(r.iter_rows(min_row=2, max_row=2, values_only=True))[0][1] == "REDIRECT_WINS"


def test_sanitize_xlsx_value_matrix() -> None:
    """Verify strict type order, control chars, formula defense, and date_as_iso."""
    assert sanitize_xlsx_value(None) == ""
    bool_true = sanitize_xlsx_value(True)
    bool_false = sanitize_xlsx_value(False)
    assert type(bool_true) is bool and bool_true is True
    assert type(bool_false) is bool and bool_false is False
    assert sanitize_xlsx_value(Decimal("42.5")) == 42.5
    assert sanitize_xlsx_value(10) == 10
    assert sanitize_xlsx_value(date(2026, 11, 22), date_as_iso=True) == "2026-11-22"
    raw_dt = datetime(2026, 11, 22, 10, 30)
    assert sanitize_xlsx_value(raw_dt, date_as_iso=False) == raw_dt

    class CustomObj:
        def __str__(self) -> str:
            return "obj\x0b=1"

    assert sanitize_xlsx_value(CustomObj()) == "obj=1"
    assert sanitize_xlsx_value("abc\x0bdef") == "abcdef"
    assert sanitize_xlsx_value("=CMD()") == "'=CMD()"
    assert sanitize_xlsx_value(" =CMD()") == "' =CMD()"
    assert sanitize_xlsx_value("+1+1") == "'+1+1"
    assert sanitize_xlsx_value("-1+1") == "'-1+1"
    assert sanitize_xlsx_value("@SUM(A1)") == "'@SUM(A1)"
    assert sanitize_xlsx_value("\t=CMD()") == "'\t=CMD()"
    assert sanitize_xlsx_value("\r+1") == "'\r+1"
    assert sanitize_xlsx_value("=SUM(A1:A2)\x0b", allow_formulas=True) == "=SUM(A1:A2)"


def test_preflight_rule_5_13_limits_and_corrupted_zip(tmp_path: Path) -> None:
    """Verify media/zip-bomb/path-traversal/corrupt checks abort BEFORE load_workbook()."""
    base_tpl = _build_template_xlsx(tmp_path / "base.xlsx")

    # 1. Media > 2 MiB (lowercase & mixed case) rejects BEFORE openpyxl.load_workbook
    oversized_payload = b"\x00" * (2 * 1024 * 1024 + 1)
    for idx, entry in enumerate(("xl/media/huge.bin", "XL/Media/HUGE.BIN")):
        bad_media = _append_zip_entry(
            base_tpl, tmp_path / f"bad_media_{idx}.xlsx", entry, oversized_payload
        )
        with (
            patch("ccba_ooxml.xlsx._reader.load_workbook") as mock_reader_lw,
            patch("ccba_ooxml.xlsx._filler.load_workbook") as mock_filler_lw,
        ):
            with pytest.raises(XlsxMediaLimitError):
                XlsxReader(bad_media)
            with pytest.raises(XlsxMediaLimitError):
                XlsxTemplateFiller(bad_media)
            mock_reader_lw.assert_not_called()
            mock_filler_lw.assert_not_called()

    # 2. Custom config ceilings for entry count, single entry size, and total size
    with pytest.raises(XlsxMediaLimitError):
        XlsxReader(base_tpl, XlsxFillConfig(max_entries=1))
    with pytest.raises(XlsxMediaLimitError):
        XlsxReader(base_tpl, XlsxFillConfig(max_entry_bytes=16))
    with pytest.raises(XlsxMediaLimitError):
        XlsxReader(base_tpl, XlsxFillConfig(max_total_bytes=64))

    # 3. Corrupted, empty, non-ZIP, OLE2 EncryptionInfo, ZIP EncryptionInfo, and path traversal
    empty_file = tmp_path / "empty.xlsx"
    empty_file.write_bytes(b"")
    non_zip = tmp_path / "not_zip.xlsx"
    non_zip.write_bytes(b"NOT_A_ZIP_ARCHIVE")
    ole2 = tmp_path / "encrypted_ole2.xlsx"
    ole2.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 32)
    zip_enc = _append_zip_entry(base_tpl, tmp_path / "zip_enc.xlsx", "EncryptionInfo", b"encrypted")
    traversal = _append_zip_entry(base_tpl, tmp_path / "trav.xlsx", "xl/media/../../evil.xml", b"x")

    for bad in (empty_file, non_zip, ole2, zip_enc, traversal):
        with pytest.raises(zipfile.BadZipFile):
            XlsxReader(bad)


def test_writer_multisheet_header_style_freeze_and_xml_dom(tmp_path: Path) -> None:
    """Verify XlsxWorkbookWriter multi-sheet output, header styles, freeze panes, and bytes."""
    style = XlsxHeaderStyle(fill_color="1F4E78", font_color="FFFFFF", bold=True)
    with XlsxWorkbookWriter() as writer:
        writer.add_sheet(
            "Sheet/With:Too*Long?SheetNameExceeding31Chars",
            ["Cot A", "=BAD_HDR"],
            [
                ["=CMD()", Decimal("100.25")],
                ["ok\x0btext", date(2026, 11, 22)],
            ],
            header_style=style,
            freeze_panes="A2",
        )
        writer.add_sheet("Second", ["H1"], [[True]], freeze_panes=None)
        payload = writer.export_bytes()
        out_path = writer.export(tmp_path / "report.xlsx")

    assert payload[:2] == b"PK"
    assert out_path.is_file()

    root1 = _read_sheet_xml(out_path, "xl/worksheets/sheet1.xml")
    pane = root1.find(".//main:pane", _NS)
    assert pane is not None
    assert pane.attrib.get("ySplit") == "1"
    assert pane.attrib.get("topLeftCell") == "A2"

    with XlsxReader(out_path) as reader:
        assert len(reader.sheet_names[0]) <= 31
        assert reader.sheet_names[1] == "Second"
        s1_rows = list(reader.iter_rows(reader.sheet_names[0], values_only=True))
        assert s1_rows[0] == ("Cot A", "'=BAD_HDR")
        assert s1_rows[1] == ("'=CMD()", 100.25)
        assert s1_rows[2] == ("oktext", "2026-11-22")


def test_reader_lifecycle_and_recalc_fallback_preflight(tmp_path: Path) -> None:
    """Verify XlsxReader closed errors and calc.recalc_xlsx openpyxl fallback preflight."""
    out_xlsx = tmp_path / "calc_test.xlsx"
    with XlsxWorkbookWriter() as writer:
        writer.add_sheet("Data", ["A"], [[123]])
        writer.export(out_xlsx)

    reader = XlsxReader(out_xlsx)
    with reader:
        assert list(reader.iter_rows("Data", min_row=2)) == [(123,)]
    with pytest.raises(RuntimeError, match="already closed"):
        list(reader.iter_rows("Data"))

    # Oversized media archive must be rejected by recalc_xlsx BEFORE load_workbook
    bad_media = _append_zip_entry(
        out_xlsx,
        tmp_path / "calc_bomb.xlsx",
        "xl/media/huge.png",
        b"\x00" * (2 * 1024 * 1024 + 1),
    )
    with (
        patch("ccba_ooxml.calc.setup_libreoffice_macro", return_value=False),
        patch("openpyxl.load_workbook") as mock_lw,
    ):
        err_res = recalc_xlsx(bad_media)
        assert "error" in err_res
        mock_lw.assert_not_called()

    # Valid workbook fallback succeeds
    with patch("ccba_ooxml.calc.setup_libreoffice_macro", return_value=False):
        ok_res = recalc_xlsx(out_xlsx)
    assert ok_res.get("success") is True
    assert "openpyxl" in str(ok_res.get("method", ""))
    assert os.path.exists(out_xlsx)
