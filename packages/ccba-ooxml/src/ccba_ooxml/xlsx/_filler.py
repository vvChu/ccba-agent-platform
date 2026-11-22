"""In-place Excel (.xlsx) template filler with atomic merged-cell and template guards."""

from __future__ import annotations

import io
from collections.abc import Iterable, Mapping, Sequence
from copy import copy
from pathlib import Path
from types import TracebackType
from typing import Any

from openpyxl import load_workbook
from openpyxl.cell.cell import MergedCell
from openpyxl.utils.cell import coordinate_to_tuple

from ccba_ooxml.form_filler.exceptions import (
    TemplateNotFoundError,
    TemplateProtectionError,
)

from ._models import MergedCellWriteError, XlsxFillConfig
from ._safety import sanitize_xlsx_value, verify_xlsx_zip_safety


def _find_merge_anchor(ws: Any, row_idx: int, col_idx: int) -> tuple[int, int]:
    """Return top-left ``(min_row, min_col)`` anchor for a merged worksheet coordinate."""
    for merge_range in ws.merged_cells.ranges:
        if (
            merge_range.min_row <= row_idx <= merge_range.max_row
            and merge_range.min_col <= col_idx <= merge_range.max_col
        ):
            return int(merge_range.min_row), int(merge_range.min_col)
    return row_idx, col_idx


def _copy_cell_style(src: Any, dest: Any) -> None:
    """Copy font, border, fill, alignment, and number format from ``src`` to ``dest``."""
    if not getattr(src, "has_style", False):
        return
    dest.font = copy(src.font)
    dest.border = copy(src.border)
    dest.fill = copy(src.fill)
    dest.alignment = copy(src.alignment)
    dest.number_format = src.number_format


def _parse_coord(coord: str | tuple[int, int]) -> tuple[int, int]:
    """Normalize either ``'A1'`` coordinates or ``(row, col)`` tuples into 1-based ints."""
    if isinstance(coord, tuple):
        if len(coord) != 2:
            raise ValueError(f"Coordinate tuple must have 2 elements, got {coord!r}")
        row_idx, col_idx = int(coord[0]), int(coord[1])
    elif isinstance(coord, str):
        row_idx, col_idx = coordinate_to_tuple(coord)
    else:
        raise TypeError(f"Unsupported cell coordinate type: {type(coord).__name__}")
    if row_idx < 1 or col_idx < 1:
        raise ValueError(f"Cell coordinates must be >= 1, got {(row_idx, col_idx)}")
    return row_idx, col_idx


class XlsxTemplateFiller:
    """Fill existing ``.xlsx`` templates safely without mutating the source template file."""

    def __init__(
        self,
        template_path: Path | str,
        config: XlsxFillConfig | None = None,
    ) -> None:
        """Validate ``template_path`` via preflight checks and open workbook in memory."""
        self.template_path = Path(template_path).resolve()
        if not self.template_path.is_file():
            raise TemplateNotFoundError(f"XLSX template '{self.template_path}' not found.")
        self.config = config or XlsxFillConfig()
        verify_xlsx_zip_safety(self.template_path, self.config)
        self._wb: Any = load_workbook(
            self.template_path,
            read_only=False,
            data_only=False,
        )
        self._closed = False

    def __enter__(self) -> XlsxTemplateFiller:
        """Enter context manager ensuring the workbook is still open."""
        self._require_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the in-memory workbook without ever writing back to the template."""
        self.close()

    def close(self) -> None:
        """Close the loaded workbook idempotently."""
        if not self._closed:
            self._wb.close()
            self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("XlsxTemplateFiller workbook is already closed.")

    def _resolve_worksheet(self, sheet_name: str | None) -> Any:
        self._require_open()
        if sheet_name is None:
            return self._wb.active
        if sheet_name not in self._wb.sheetnames:
            raise KeyError(f"Worksheet '{sheet_name}' not found.")
        return self._wb[sheet_name]

    def _sanitize(self, val: Any) -> Any:
        return sanitize_xlsx_value(
            val,
            allow_formulas=self.config.allow_formulas,
            date_as_iso=self.config.date_as_iso,
        )

    def _plan_writes(
        self,
        ws: Any,
        writes: Sequence[tuple[int, int, Any]],
    ) -> list[tuple[int, int, int, Any]]:
        """Pre-scan all target cells against merged ranges before mutating any cell."""
        planned: list[tuple[int, int, int, Any]] = []
        mode = self.config.on_merged
        for row_idx, col_idx, raw_val in writes:
            cell = ws.cell(row=row_idx, column=col_idx)
            if isinstance(cell, MergedCell):
                if mode == "error":
                    raise MergedCellWriteError(ws.title, cell.coordinate)
                if mode == "skip":
                    continue
                anchor_r, anchor_c = _find_merge_anchor(ws, row_idx, col_idx)
                planned.append((anchor_r, anchor_c, col_idx, raw_val))
            else:
                planned.append((row_idx, col_idx, col_idx, raw_val))
        return planned

    def _commit_writes(
        self,
        ws: Any,
        planned: Sequence[tuple[int, int, int, Any]],
        style_from_row: int | None = None,
    ) -> None:
        """Write sanitized values and optionally copy row styles atomically after pre-scan."""
        for dest_r, dest_c, style_col, raw_val in planned:
            dest = ws.cell(row=dest_r, column=dest_c, value=self._sanitize(raw_val))
            if style_from_row is not None and dest_r != style_from_row:
                src = ws.cell(row=style_from_row, column=style_col)
                _copy_cell_style(src, dest)

    def fill_cells(
        self,
        mapping: Mapping[str | tuple[int, int], Any],
        *,
        sheet_name: str | None = None,
    ) -> XlsxTemplateFiller:
        """Assign sanitized values to explicit coordinates (e.g. ``'B4'`` or ``(4, 2)``)."""
        ws = self._resolve_worksheet(sheet_name)
        raw_writes = [(*_parse_coord(coord), val) for coord, val in mapping.items()]
        planned = self._plan_writes(ws, raw_writes)
        self._commit_writes(ws, planned)
        return self

    def write_styled_row(
        self,
        row_idx: int,
        values: Sequence[Any],
        *,
        style_from_row: int | None = None,
        sheet_name: str | None = None,
        start_col: int = 1,
    ) -> XlsxTemplateFiller:
        """Write one row in-place and copy style from ``style_from_row`` when specified."""
        ws = self._resolve_worksheet(sheet_name)
        raw_writes = [(row_idx, start_col + offset, val) for offset, val in enumerate(values)]
        planned = self._plan_writes(ws, raw_writes)
        self._commit_writes(ws, planned, style_from_row=style_from_row)
        return self

    def write_styled_rows(
        self,
        start_row: int,
        rows: Iterable[Sequence[Any]],
        *,
        style_from_row: int | None = None,
        sheet_name: str | None = None,
        start_col: int = 1,
    ) -> XlsxTemplateFiller:
        """Write multiple rows sequentially in-place without calling ``insert_rows``."""
        ws = self._resolve_worksheet(sheet_name)
        raw_writes = [
            (start_row + r_offset, start_col + c_offset, val)
            for r_offset, row in enumerate(rows)
            for c_offset, val in enumerate(row)
        ]
        planned = self._plan_writes(ws, raw_writes)
        self._commit_writes(ws, planned, style_from_row=style_from_row)
        return self

    def export(self, xlsx_out: Path | str, *, recalc: bool = False) -> Path:
        """Save filled workbook to ``xlsx_out``, refusing to overwrite ``template_path``."""
        self._require_open()
        out_path = Path(xlsx_out).resolve()
        if out_path == self.template_path:
            raise TemplateProtectionError(
                f"Refusing to overwrite source template '{self.template_path}'."
            )
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
        """Serialize filled workbook directly to an in-memory ``bytes`` payload."""
        self._require_open()
        buf = io.BytesIO()
        self._wb.save(buf)
        return buf.getvalue()
