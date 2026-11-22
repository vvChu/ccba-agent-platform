"""Multi-sheet Excel (.xlsx) workbook writer with header styling and formula guards."""

from __future__ import annotations

import io
import re
from collections.abc import Iterable, Sequence
from pathlib import Path
from types import TracebackType
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill

from ._models import XlsxFillConfig, XlsxHeaderStyle
from ._safety import sanitize_xlsx_value, verify_xlsx_zip_safety

_INVALID_SHEET_CHARS_RE = re.compile(r"[\\/*?:\[\]]")


def _sanitize_sheet_title(name: str) -> str:
    """Strip forbidden Excel sheet-title characters and clamp to 31 characters."""
    cleaned = _INVALID_SHEET_CHARS_RE.sub("_", str(name)).strip()[:31]
    return cleaned or "Sheet"


def _apply_header_row_style(ws: Any, style: XlsxHeaderStyle) -> None:
    """Apply fill, font, and alignment from ``XlsxHeaderStyle`` across row 1."""
    fill = PatternFill(
        start_color=style.fill_color,
        end_color=style.fill_color,
        fill_type="solid",
    )
    font = Font(color=style.font_color, bold=style.bold)
    alignment = Alignment(
        horizontal=style.horizontal,
        vertical=style.vertical,
        wrap_text=style.wrap_text,
    )
    for cell in ws[1]:
        cell.fill = fill
        cell.font = font
        cell.alignment = alignment


class XlsxWorkbookWriter:
    """Create new styled ``.xlsx`` workbooks using sanitized cell values."""

    def __init__(self, config: XlsxFillConfig | None = None) -> None:
        """Initialize a fresh empty workbook configured by ``config``."""
        self.config = config or XlsxFillConfig()
        self._wb: Any = Workbook()
        self._has_sheets = False
        self._closed = False

    def __enter__(self) -> XlsxWorkbookWriter:
        """Enter context manager ensuring the workbook is still open."""
        self._require_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the underlying workbook on scope exit."""
        self.close()

    def close(self) -> None:
        """Close the workbook idempotently."""
        if not self._closed:
            self._wb.close()
            self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("XlsxWorkbookWriter workbook is already closed.")

    def _sanitize(self, val: Any) -> Any:
        return sanitize_xlsx_value(
            val,
            allow_formulas=self.config.allow_formulas,
            date_as_iso=self.config.date_as_iso,
        )

    def add_sheet(
        self,
        name: str,
        headers: Sequence[Any],
        rows: Iterable[Sequence[Any]],
        *,
        header_style: XlsxHeaderStyle | None = None,
        freeze_panes: str | None = "A2",
    ) -> XlsxWorkbookWriter:
        """Append a styled sheet with header formatting, sanitized rows, and freeze panes."""
        self._require_open()
        if not self._has_sheets:
            ws = self._wb.active
            self._has_sheets = True
        else:
            ws = self._wb.create_sheet()
        ws.title = _sanitize_sheet_title(name)
        style = header_style or XlsxHeaderStyle()
        ws.append([self._sanitize(h) for h in headers])
        _apply_header_row_style(ws, style)
        for row in rows:
            ws.append([self._sanitize(val) for val in row])
        if freeze_panes:
            ws.freeze_panes = freeze_panes
        return self

    def export(self, xlsx_out: Path | str, *, recalc: bool = False) -> Path:
        """Write the generated workbook to ``xlsx_out`` and optionally recalculate."""
        self._require_open()
        out_path = Path(xlsx_out).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        self._wb.save(out_path)
        if recalc:
            verify_xlsx_zip_safety(out_path, self.config)
            from ccba_ooxml.calc import recalc_xlsx

            res = recalc_xlsx(out_path)
            if isinstance(res, dict) and "error" in res:
                raise RuntimeError(str(res["error"]))
        return out_path

    def export_bytes(self) -> bytes:
        """Serialize the generated workbook into an in-memory ``bytes`` buffer."""
        self._require_open()
        buf = io.BytesIO()
        self._wb.save(buf)
        return buf.getvalue()
