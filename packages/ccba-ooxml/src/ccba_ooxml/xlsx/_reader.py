"""Read-only streaming Excel (.xlsx) workbook reader with preflight safety checks."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import Any

from openpyxl import load_workbook

from ._models import XlsxFillConfig
from ._safety import verify_xlsx_zip_safety


class XlsxReader:
    """Safe context-managed reader over ``.xlsx`` files defaulting to ``read_only=True``."""

    def __init__(
        self,
        path: Path | str,
        config: XlsxFillConfig | None = None,
        *,
        read_only: bool = True,
        data_only: bool = True,
    ) -> None:
        """Validate archive safety ceilings before opening workbook with ``openpyxl``."""
        self.path = Path(path).resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"XLSX file not found: {self.path}")
        self.config = config or XlsxFillConfig()
        verify_xlsx_zip_safety(self.path, self.config)
        self._wb: Any = load_workbook(
            self.path,
            read_only=read_only,
            data_only=data_only,
        )
        self._closed = False

    def __enter__(self) -> XlsxReader:
        """Enter context manager ensuring the reader is open."""
        self._require_open()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the underlying workbook and release file handles."""
        self.close()

    def close(self) -> None:
        """Close the reader workbook idempotently."""
        if not self._closed:
            self._wb.close()
            self._closed = True

    def _require_open(self) -> None:
        if self._closed:
            raise RuntimeError("XlsxReader workbook is already closed.")

    @property
    def sheet_names(self) -> list[str]:
        """Return worksheet names in workbook order."""
        self._require_open()
        return list(self._wb.sheetnames)

    def _iter_sheet_rows(
        self,
        ws: Any,
        *,
        min_row: int,
        max_row: int | None,
        values_only: bool,
    ) -> Iterator[tuple[Any, ...]]:
        for row in ws.iter_rows(
            min_row=min_row,
            max_row=max_row,
            values_only=values_only,
        ):
            self._require_open()
            yield row if isinstance(row, tuple) else tuple(row)

    def iter_rows(
        self,
        sheet_name: str | None = None,
        *,
        min_row: int = 1,
        max_row: int | None = None,
        values_only: bool = True,
    ) -> Iterator[tuple[Any, ...]]:
        """Stream worksheet rows within an active ``with XlsxReader(...)`` lifecycle."""
        self._require_open()
        if sheet_name is None:
            ws = self._wb.active
        elif sheet_name in self._wb.sheetnames:
            ws = self._wb[sheet_name]
        else:
            raise KeyError(f"Worksheet '{sheet_name}' not found.")
        return self._iter_sheet_rows(
            ws,
            min_row=min_row,
            max_row=max_row,
            values_only=values_only,
        )
