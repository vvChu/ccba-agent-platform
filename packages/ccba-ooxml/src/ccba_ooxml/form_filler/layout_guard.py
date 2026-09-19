# packages/ccba-ooxml/src/ccba_ooxml/form_filler/layout_guard.py
"""Form Layout Guard rules and operations for both python-docx and Word COM."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("ccba.ooxml.form_filler.guard")


class FormLayoutGuard:
    """Enforces layout invariants: anti-row-split, pruning empty rows, page break rules."""

    # -------------------------------------------------------------------------
    # DOCX (python-docx / OpenXML) Engine Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def apply_docx_cant_split(row: Any) -> None:
        """Injects <w:cantSplit/> XML element into table row properties."""
        try:
            from docx.oxml import OxmlElement
            from docx.oxml.ns import qn

            tr_pr = row._tr.get_or_add_trPr()
            if tr_pr.find(qn("w:cantSplit")) is None:
                cant_split = OxmlElement("w:cantSplit")
                tr_pr.append(cant_split)
        except Exception as e:
            logger.debug(f"Failed to inject cantSplit into row: {e}")

    @staticmethod
    def apply_docx_page_break_before(paragraph: Any) -> None:
        """Enforces page break before paragraph in python-docx."""
        try:
            paragraph.paragraph_format.page_break_before = True
        except Exception as e:
            logger.debug(f"Failed to set page_break_before on paragraph: {e}")

    @staticmethod
    def is_docx_row_empty(row: Any) -> bool:
        """Checks if all cells in a python-docx row contain only whitespace."""
        try:
            return all(not cell.text.strip() for cell in row.cells)
        except Exception:
            return False

    @staticmethod
    def remove_docx_row(table: Any, row: Any) -> None:
        """Removes a row from python-docx table cleanly via XML parent."""
        try:
            tr = row._tr
            parent = tr.getparent()
            if parent is not None:
                parent.remove(tr)
        except Exception as e:
            logger.debug(f"Failed to remove docx table row: {e}")

    # -------------------------------------------------------------------------
    # COM (win32com / Word DOM) Engine Helpers
    # -------------------------------------------------------------------------

    @staticmethod
    def apply_com_cant_split(row: Any) -> None:
        """Sets AllowBreakAcrossPages = False on Word COM Row."""
        try:
            row.AllowBreakAcrossPages = False
        except Exception as e:
            logger.debug(f"Failed to set AllowBreakAcrossPages on COM row: {e}")

    @staticmethod
    def apply_com_page_break_before(paragraph: Any) -> None:
        """Sets PageBreakBefore = True on Word COM Paragraph."""
        try:
            paragraph.Format.PageBreakBefore = True
        except Exception as e:
            logger.debug(f"Failed to set PageBreakBefore on COM paragraph: {e}")

    @staticmethod
    def is_com_row_empty(row: Any) -> bool:
        """Checks if all cells in a Word COM row are empty (ignoring control chars)."""
        try:
            for cell in row.Cells:
                # Word COM cell text ends with \r\x07 (cell marker)
                cleaned = cell.Range.Text.replace("\r", "").replace("\x07", "").strip()
                if cleaned:
                    return False
            return True
        except Exception:
            return False

    @staticmethod
    def remove_com_row(row: Any) -> None:
        """Deletes a Word COM table row safely."""
        try:
            row.Delete()
        except Exception as e:
            logger.debug(f"Failed to delete COM row: {e}")
