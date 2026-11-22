"""Configuration models, header styles, and typed exceptions for ``ccba_ooxml.xlsx``."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

MergedCellMode = Literal["error", "skip", "top_left"]


class XlsxMediaLimitError(Exception):
    """Raised when an XLSX archive exceeds configured ZIP safety ceilings."""


class MergedCellWriteError(Exception):
    """Raised when attempting to write to a non-anchor merged worksheet cell."""

    def __init__(
        self,
        sheet_name: str,
        coordinate: str,
        message: str | None = None,
    ) -> None:
        """Initialize the error with worksheet name and target cell coordinate."""
        self.sheet_name = sheet_name
        self.coordinate = coordinate
        super().__init__(
            message or f"Cannot write to non-anchor merged cell '{sheet_name}!{coordinate}'."
        )


@dataclass
class XlsxFillConfig:
    """Safety ceilings, sanitization flags, and merge-write policy for XLSX operations."""

    max_media_bytes: int = 2 * 1024 * 1024
    max_entry_bytes: int = 50 * 1024 * 1024
    max_total_bytes: int = 150 * 1024 * 1024
    max_entries: int = 400
    allow_formulas: bool = False
    date_as_iso: bool = True
    on_merged: MergedCellMode = "error"

    def __post_init__(self) -> None:
        """Validate positive integer ceilings and allowed merged-cell mode."""
        for attr in (
            "max_media_bytes",
            "max_entry_bytes",
            "max_total_bytes",
            "max_entries",
        ):
            if getattr(self, attr) <= 0:
                raise ValueError(f"XlsxFillConfig.{attr} must be > 0")
        if self.on_merged not in ("error", "skip", "top_left"):
            raise ValueError(f"Unsupported XlsxFillConfig.on_merged mode: {self.on_merged!r}")


@dataclass
class XlsxHeaderStyle:
    """Visual styling applied to row-1 worksheet headers created by ``XlsxWorkbookWriter``."""

    fill_color: str = "1F4E78"
    font_color: str = "FFFFFF"
    bold: bool = True
    horizontal: str = "center"
    vertical: str = "center"
    wrap_text: bool = True
