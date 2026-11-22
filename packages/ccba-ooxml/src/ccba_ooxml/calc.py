"""Excel spreadsheet formula recalculation and error auditing utilities for OOXML files.

Supports Windows Excel COM recalculation/PDF export, headless LibreOffice Basic
Macro recalculation, RULE-5.13 archive preflight checks, and openpyxl save-back.
"""

from __future__ import annotations

import logging
import os
import platform
import subprocess
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

EXCEL_ERROR_TOKENS: tuple[str, ...] = (
    "#REF!",
    "#DIV/0!",
    "#VALUE!",
    "#NAME?",
    "#N/A",
    "#NUM!",
    "#NULL!",
)

__all__ = [
    "EXCEL_ERROR_TOKENS",
    "audit_xlsx_formula_errors",
    "recalc_xlsx",
    "setup_libreoffice_macro",
]

LIBREOFFICE_MACRO_SNIPPET = """    Sub RecalculateAndSave()
      ThisComponent.calculateAll()
      ThisComponent.store()
      ThisComponent.close(True)
    End Sub"""

LIBREOFFICE_MODULE_TEMPLATE = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/script" script:name="Module1" script:language="StarBasic">
{LIBREOFFICE_MACRO_SNIPPET}
</script:module>"""


def _resolve_libreoffice_macro_dir() -> str:
    """Resolve user Standard Basic macro directory across OS platforms."""
    system = platform.system()
    if system == "Darwin":
        return os.path.expanduser("~/Library/Application Support/LibreOffice/4/user/basic/Standard")
    if system == "Windows":
        app_data = os.getenv("APPDATA")
        if app_data:
            return os.path.join(app_data, "LibreOffice", "4", "user", "basic", "Standard")
        return str(
            Path.home()
            / "AppData"
            / "Roaming"
            / "LibreOffice"
            / "4"
            / "user"
            / "basic"
            / "Standard"
        )
    return os.path.expanduser("~/.config/libreoffice/4/user/basic/Standard")


def setup_libreoffice_macro() -> bool:
    """Setup LibreOffice macro for recalculation without destroying existing macros.

    Uses safe injection: if Module1.xba exists, injects RecalculateAndSave
    before the closing </script:module> tag rather than overwriting.

    Returns:
        bool: True if macro is ready, False otherwise.
    """
    macro_dir = _resolve_libreoffice_macro_dir()
    macro_file = os.path.join(macro_dir, "Module1.xba")

    if os.path.exists(macro_file):
        try:
            with open(macro_file, encoding="utf-8") as f:
                content = f.read()
            if "RecalculateAndSave" in content:
                return True
            if "</script:module>" in content:
                injected = content.replace(
                    "</script:module>",
                    f"\n{LIBREOFFICE_MACRO_SNIPPET}\n</script:module>",
                )
                with open(macro_file, "w", encoding="utf-8") as f:
                    f.write(injected)
                return True
        except Exception as e:
            logger.warning("Failed reading/injecting LibreOffice macro: %s", e)
            return False

    try:
        os.makedirs(macro_dir, exist_ok=True)
        with open(macro_file, "w", encoding="utf-8") as f:
            f.write(LIBREOFFICE_MODULE_TEMPLATE)
        return True
    except Exception as e:
        logger.warning("Failed creating LibreOffice macro directory/file: %s", e)
        return False


def audit_xlsx_formula_errors(filename: str | Path) -> list[dict[str, str]]:
    """Scan evaluated worksheet values for Excel error tokens (`#REF!`, `#DIV/0!`, etc.).

    Runs RULE-5.13 archive preflight before opening the workbook in read-only mode.

    Args:
        filename: Path to the ``.xlsx`` spreadsheet file.

    Returns:
        List of findings, each containing ``sheet``, ``cell``, and ``error`` keys.

    Raises:
        FileNotFoundError: If ``filename`` does not exist or is not a file.
    """
    file_path = Path(filename)
    if not file_path.is_file():
        raise FileNotFoundError(f"XLSX file not found: {file_path}")

    from openpyxl import load_workbook
    from openpyxl.utils import get_column_letter

    from ccba_ooxml.xlsx._safety import verify_xlsx_zip_safety

    verify_xlsx_zip_safety(file_path)
    findings: list[dict[str, str]] = []
    wb: Any = None
    try:
        wb = load_workbook(file_path, read_only=True, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                for c_idx, val in enumerate(row, start=1):
                    if isinstance(val, str):
                        token = val.strip().upper()
                        if token in EXCEL_ERROR_TOKENS:
                            findings.append(
                                {
                                    "sheet": str(sheet_name),
                                    "cell": f"{get_column_letter(c_idx)}{r_idx}",
                                    "error": val.strip(),
                                }
                            )
        return findings
    finally:
        if wb is not None:
            wb.close()


def _recalc_via_excel_com(abs_path: str, pdf_path: Path | None = None) -> dict[str, Any]:
    """Recalculate all formulas via Microsoft Excel COM on Windows and optionally export PDF."""
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    excel = None
    wb = None
    try:
        excel = win32com.client.DispatchEx("Excel.Application")
        excel.Visible = False
        excel.DisplayAlerts = False
        excel.ScreenUpdating = False

        wb = excel.Workbooks.Open(abs_path)
        excel.CalculateFullRebuild()
        wb.Save()
        if pdf_path is not None:
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            wb.ExportAsFixedFormat(0, str(pdf_path.resolve()))
        result: dict[str, Any] = {"success": True, "method": "ExcelCOM"}
        if pdf_path is not None:
            result["pdf_path"] = str(pdf_path.resolve())
        return result
    finally:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _recalc_via_libreoffice(abs_path: str, timeout: int) -> dict[str, Any] | None:
    """Attempt headless recalculation via LibreOffice StarBasic macro."""
    libreoffice_setup_ok = False
    try:
        libreoffice_setup_ok = setup_libreoffice_macro()
    except Exception as e:
        logger.warning("Failed to set up LibreOffice macro: %s", e)

    if not libreoffice_setup_ok:
        return None

    soffice_cmd = "soffice"
    if platform.system() == "Windows":
        win_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",  # ccba:allow-machine-path
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",  # ccba:allow-machine-path
        ]
        for p in win_paths:
            if os.path.exists(p):
                soffice_cmd = p
                break

    try:
        cmd = [
            soffice_cmd,
            "--headless",
            "--norestore",
            "vnd.sun.star.script:Standard.Module1.RecalculateAndSave?language=Basic&location=application",
            abs_path,
        ]
        res = subprocess.run(cmd, capture_output=True, timeout=timeout)
        if res.returncode == 0:
            return {"success": True, "method": "LibreOffice"}
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def _fallback_recalc_with_openpyxl(file_path: Path) -> dict[str, Any]:
    """Run RULE-5.13 ZIP safety preflight and save-back via lazy-imported openpyxl."""
    wb: Any = None
    try:
        from openpyxl import load_workbook

        from ccba_ooxml.xlsx._safety import verify_xlsx_zip_safety

        verify_xlsx_zip_safety(file_path)
        wb = load_workbook(file_path, data_only=False)
        wb.save(file_path)
        return {"success": True, "method": "openpyxl (Save-back only)"}
    except ImportError:
        return {"error": "Failed recalculation: Neither LibreOffice nor openpyxl is available."}
    except Exception as e:
        return {"error": f"Failed recalculation: {e}"}
    finally:
        if wb is not None:
            wb.close()


def _dispatch_recalc(
    file_path: Path,
    abs_path: str,
    timeout: int,
    prefer_engine: Literal["auto", "excel", "libreoffice"],
    pdf_out: Path | None,
) -> dict[str, Any]:
    """Execute formula recalculation using the requested or auto-selected engine."""
    if prefer_engine == "excel" and platform.system() != "Windows":
        return {"error": "Excel COM recalculation is only supported on Windows."}

    if prefer_engine in ("auto", "excel") and platform.system() == "Windows":
        try:
            com_res = _recalc_via_excel_com(abs_path, pdf_out)
            if isinstance(com_res, dict) and com_res.get("success"):
                return com_res
        except Exception as e:
            if prefer_engine == "excel":
                return {"error": f"Excel COM recalculation failed: {e}"}
            logger.warning("Excel COM recalculation skipped/failed (%s); trying LibreOffice.", e)

    if prefer_engine in ("auto", "libreoffice"):
        lo_res = _recalc_via_libreoffice(abs_path, timeout)
        if lo_res is not None:
            if pdf_out is not None:
                try:
                    from ccba_ooxml.converter import convert_to_pdf

                    exported = convert_to_pdf(
                        file_path, pdf_out, prefer_engine="soffice", timeout=timeout
                    )
                    lo_res["pdf_path"] = str(exported)
                except Exception as e:
                    return {
                        "error": f"LibreOffice recalculated workbook but PDF export failed: {e}"
                    }
            return lo_res
        if prefer_engine == "libreoffice":
            return {"error": "LibreOffice recalculation failed or is unavailable."}

    return _fallback_recalc_with_openpyxl(file_path)


def _attach_error_audit(file_path: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Attach formula error audit findings and fail closed when errors exist."""
    errors = audit_xlsx_formula_errors(file_path)
    result["formula_errors"] = errors
    if errors:
        result["success"] = False
        result["error"] = f"Found {len(errors)} Excel formula error(s)"
    return result


def recalc_xlsx(
    filename: str | Path,
    timeout: int = 30,
    prefer_engine: Literal["auto", "excel", "libreoffice"] = "auto",
    export_pdf: str | Path | None = None,
    check_errors: bool = False,
) -> dict[str, Any]:
    """Recalculate formulas in an Excel file, optionally exporting PDF and checking errors.

    Runs RULE-5.13 archive preflight checks before invoking Excel COM, LibreOffice, or openpyxl.

    Args:
        filename: Path to the ``.xlsx`` spreadsheet file.
        timeout: Maximum seconds to wait for LibreOffice subprocess.
        prefer_engine: ``'auto'``, ``'excel'`` (Windows Excel COM), or ``'libreoffice'``.
        export_pdf: Optional target PDF path when recalculated via Excel COM or LibreOffice.
        check_errors: When True, audit cached formula values for Excel error tokens.

    Returns:
        Dictionary containing status, method used, optional ``pdf_path``, or error message.
    """
    file_path = Path(filename)
    if not file_path.exists():
        return {"error": f"File {filename} does not exist"}

    try:
        from ccba_ooxml.xlsx._safety import verify_xlsx_zip_safety

        verify_xlsx_zip_safety(file_path)
    except Exception as e:
        return {"error": f"XLSX safety preflight failed: {e}"}

    pdf_out = Path(export_pdf) if export_pdf is not None else None
    result = _dispatch_recalc(file_path, str(file_path.resolve()), timeout, prefer_engine, pdf_out)
    if result.get("success") and check_errors:
        return _attach_error_audit(file_path, result)
    return result
