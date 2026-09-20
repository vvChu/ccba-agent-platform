"""converter.py - Standalone Cross-Platform Document to Vector PDF Converter.

Supports Windows Word COM automation when available, with automatic headless
fallback to LibreOffice (soffice) on Linux/WSL or headless CI/CD environments.
Complies with ADR 0049.
"""

from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from typing import Literal

from ccba_ooxml.form_filler.exceptions import EngineUnavailableError, FormFillerError
from ccba_ooxml.soffice import find_soffice_bin, run_soffice

logger = logging.getLogger(__name__)

__all__ = ["convert_to_pdf", "docx_to_pdf"]


def _convert_via_winword(docx_path: Path, output_pdf_path: Path) -> Path:
    """Converts a DOCX/DOC file to PDF using Microsoft Word COM on Windows."""
    try:
        import pythoncom  # type: ignore[import-untyped]
        import win32com.client  # type: ignore[import-untyped]
    except ImportError as e:
        raise EngineUnavailableError(
            "win32com.client is not installed. Run on Windows with pywin32 installed."
        ) from e

    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0

        abs_input = str(docx_path.resolve())
        abs_output = str(output_pdf_path.resolve())

        doc = word.Documents.Open(abs_input, ReadOnly=True, ConfirmConversions=False)
        # wdExportFormatPDF = 17, wdExportOptimizeForPrint = 0
        doc.ExportAsFixedFormat(
            OutputFileName=abs_output,
            ExportFormat=17,
            OpenAfterExport=False,
            OptimizeFor=0,
        )
        return output_pdf_path
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=0)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        try:
            pythoncom.CoUninitialize()
        except Exception:
            pass


def _convert_via_soffice(input_path: Path, output_pdf_path: Path, timeout: int = 120) -> Path:
    """Converts a document to PDF using headless LibreOffice (soffice)."""
    soffice_bin = find_soffice_bin()
    if not soffice_bin:
        raise EngineUnavailableError(
            "LibreOffice (soffice) not found on PATH or default installation folders. "
            "Please install LibreOffice:\n"
            "  - Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y libreoffice-writer\n"
            "  - macOS: brew install --cask libreoffice\n"
            "  - Windows: https://www.libreoffice.org/download/download/"
        )

    out_dir = output_pdf_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        res = run_soffice(
            [
                "--headless",
                "--convert-to",
                "pdf",
                str(input_path.resolve()),
                "--outdir",
                str(out_dir.resolve()),
            ],
            timeout=timeout,
            capture_output=True,
            text=True,
        )
    except Exception as e:
        raise FormFillerError(f"LibreOffice conversion failed: {e}") from e

    if res.returncode != 0:
        raise FormFillerError(
            f"LibreOffice conversion exited with error code {res.returncode}: {res.stderr or res.stdout}"
        )

    # LibreOffice outputs with same stem as input_file in outdir
    expected_output = out_dir / f"{input_path.stem}.pdf"
    if expected_output.exists() and expected_output != output_pdf_path:
        shutil.move(str(expected_output), str(output_pdf_path))

    if not output_pdf_path.exists():
        raise FormFillerError(
            f"Conversion finished but output file was not found at '{output_pdf_path}'."
        )

    return output_pdf_path


def convert_to_pdf(
    input_file: Path | str,
    output_path: Path | str | None = None,
    prefer_engine: Literal["auto", "winword", "soffice"] = "auto",
    timeout: int = 120,
) -> Path:
    """Converts a document (.docx, .doc, .pptx, .xlsx) to high-precision Vector PDF.

    Args:
        input_file: Source document path.
        output_path: Target PDF output path. Defaults to input_file with .pdf extension.
        prefer_engine: 'auto', 'winword' (MS Word COM), or 'soffice' (headless LibreOffice).
        timeout: Subprocess timeout in seconds for LibreOffice.

    Returns:
        Path: Resolved path to the generated Vector PDF file.

    Raises:
        FileNotFoundError: If input_file does not exist.
        EngineUnavailableError: If requested engine or required software is missing.
        FormFillerError: If conversion fails.
    """
    in_path = Path(input_file).resolve()
    if not in_path.exists() or not in_path.is_file():
        raise FileNotFoundError(f"Source file not found: '{in_path}'")

    if output_path is None:
        out_pdf = in_path.with_suffix(".pdf")
    else:
        out_pdf = Path(output_path).resolve()

    out_pdf.parent.mkdir(parents=True, exist_ok=True)

    # Determine execution engine
    use_engine = prefer_engine
    if use_engine == "auto":
        if sys.platform == "win32":
            try:
                import win32com.client  # noqa: F401

                use_engine = "winword"
            except ImportError:
                use_engine = "soffice"
        else:
            use_engine = "soffice"

    if use_engine == "winword":
        try:
            return _convert_via_winword(in_path, out_pdf)
        except Exception as e:
            if prefer_engine == "auto":
                logger.warning(f"Word COM conversion failed ({e}), falling back to LibreOffice.")
                return _convert_via_soffice(in_path, out_pdf, timeout=timeout)
            raise

    return _convert_via_soffice(in_path, out_pdf, timeout=timeout)


# Convenient alias for legal and document pipelines
docx_to_pdf = convert_to_pdf
