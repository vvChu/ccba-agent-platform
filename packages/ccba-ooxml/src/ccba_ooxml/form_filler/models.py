# packages/ccba-ooxml/src/ccba_ooxml/form_filler/models.py
"""Pydantic data models and schemas for Form Filler module."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class TableRowData(BaseModel):
    """Data representation for a single row to be inserted into a table."""

    values: dict[str, str] = Field(
        default_factory=dict,
        description="Key-value mapping of column identifiers to cell values.",
    )


class TableRule(BaseModel):
    """Rule for filling and guarding a table in a Word document form."""

    table_index: int = Field(
        default=0,
        ge=0,
        description="Zero-based index of the target table in the document.",
    )
    header_keyword: str | None = Field(
        default=None,
        description="Optional keyword to identify target table if index is not fixed.",
    )
    data_rows: list[dict[str, str]] = Field(
        default_factory=list,
        description="List of row dictionaries where keys represent column headers or indices.",
    )
    delete_unused_template_rows: bool = Field(
        default=True,
        description="Whether to delete remaining placeholder/template rows that have no data.",
    )
    allow_break_across_pages: bool = Field(
        default=False,
        description="Whether to allow table rows to split across page boundaries.",
    )
    column_mapping: dict[str, str] | None = Field(
        default=None,
        description="Optional mapping from table header titles to dictionary keys.",
    )


class FormFillConfig(BaseModel):
    """Configuration options for Word Form Filler engine execution."""

    engine: Literal["auto", "winword", "soffice"] = Field(
        default="auto",
        description="Engine type: 'winword' (Windows Word COM), 'soffice' (LibreOffice fallback), or 'auto'.",
    )
    keep_font_formatting: bool = Field(
        default=True,
        description="Preserve original font size, name, weight, and color during placeholder substitution.",
    )
    prevent_row_split: bool = Field(
        default=True,
        description="Enforce row integrity preventing rows from splitting across page breaks.",
    )
    prune_empty_rows: bool = Field(
        default=True,
        description="Prune empty/unfilled template rows in dynamic list tables.",
    )
    page_break_keywords: list[str] = Field(
        default_factory=list,
        description="List of paragraph keywords that must start on a new page (PageBreakBefore).",
    )
    timeout_seconds: int = Field(
        default=120,
        gt=0,
        description="Maximum execution timeout in seconds.",
    )
