"""CCBA OOXML Utilities.

Shared library for packaging, unpackaging, validating, formatting, and DOM manipulating docx/pptx/xlsx documents.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .calc import audit_xlsx_formula_errors, recalc_xlsx, setup_libreoffice_macro
    from .converter import convert_to_pdf, docx_to_pdf, xlsx_to_pdf
    from .docx import (
        CCBADocxTheme,
        CommentEngine,
        Document,
        DocxDocument,
        DocxXMLEditor,
        TechnicalReportBuilder,
        XMLEditor,
        build_tech_report_from_yaml,
        clone_xml_text,
        get_authors_from_docx,
        get_tracked_change_authors,
        infer_author,
        merge_runs,
        revert_deletion,
        revert_insertion,
        simplify_redlines,
        suggest_deletion,
        suggest_paragraph,
    )
    from .form_filler import (
        BaseFormFillerEngine,
        EngineUnavailableError,
        FormFillConfig,
        FormFillerError,
        FormLayoutGuard,
        LayoutGuardError,
        SofficeFallbackEngine,
        TableRule,
        TemplateNotFoundError,
        TemplateProtectionError,
        WinwordEngine,
        WordFormFiller,
    )
    from .format import FormattingProfile, convert_md_to_docx, format_docx
    from .pack import pack_document, validate_document
    from .pptx import (
        CardItem,
        CCBAPresentationTheme,
        DeckBuilder,
        MarkdownDeckParser,
        ParagraphData,
        PresentationInventory,
        ShapeData,
        SlideSpec,
        SlideType,
        apply_replacements,
        build_presentation_from_markdown,
        extract_text_inventory,
        generate_thumbnails,
        get_inventory_as_dict,
        pptx_inventory,
        pptx_replace_text,
        rearrange_presentation,
        rearrange_slides,
        save_inventory,
    )
    from .soffice import find_soffice_bin, get_soffice_env, run_soffice
    from .tables import (
        StructuredTable,
        TableReconstructor,
        make_descriptive_table_slug,
        vietnamese_to_ascii,
    )
    from .unpack import unpack_document
    from .workspace import OOXMLWorkspace
    from .xlsx import (
        CalculationSheetBuilder,
        CCBAExcelTheme,
        MergedCellWriteError,
        XlsxFillConfig,
        XlsxHeaderStyle,
        XlsxMediaLimitError,
        XlsxReader,
        XlsxTemplateFiller,
        XlsxWorkbookWriter,
        build_calc_sheet_from_yaml,
        resolve_formula,
        sanitize_xlsx_value,
    )

__all__ = [
    # Document operations
    "pack_document",
    "unpack_document",
    "validate_document",
    "OOXMLWorkspace",
    "convert_to_pdf",
    "docx_to_pdf",
    "xlsx_to_pdf",
    # Spreadsheet calculation
    "recalc_xlsx",
    "setup_libreoffice_macro",
    "audit_xlsx_formula_errors",
    # Docx DOM manipulation & tracking
    "DocxDocument",
    "Document",
    "DocxXMLEditor",
    "CommentEngine",
    "XMLEditor",
    "revert_insertion",
    "revert_deletion",
    "suggest_paragraph",
    "suggest_deletion",
    "merge_runs",
    "simplify_redlines",
    "clone_xml_text",
    "get_tracked_change_authors",
    "get_authors_from_docx",
    "infer_author",
    # Docx formatting & markdown conversion
    "FormattingProfile",
    "format_docx",
    "convert_md_to_docx",
    # LibreOffice runner
    "run_soffice",
    "find_soffice_bin",
    "get_soffice_env",
    # Table extraction & reconstruction
    "StructuredTable",
    "TableReconstructor",
    "make_descriptive_table_slug",
    "vietnamese_to_ascii",
    # PowerPoint presentation builder & inspection (Deep Seams)
    "DeckBuilder",
    "MarkdownDeckParser",
    "SlideSpec",
    "SlideType",
    "CardItem",
    "build_presentation_from_markdown",
    "CCBAPresentationTheme",
    "ParagraphData",
    "ShapeData",
    "PresentationInventory",
    "extract_text_inventory",
    "get_inventory_as_dict",
    "pptx_inventory",
    "save_inventory",
    "apply_replacements",
    "pptx_replace_text",
    "rearrange_presentation",
    "rearrange_slides",
    "generate_thumbnails",
    # Form filler & layout guard (Issue #296)
    "WordFormFiller",
    "FormFillConfig",
    "TableRule",
    "FormLayoutGuard",
    "BaseFormFillerEngine",
    "WinwordEngine",
    "SofficeFallbackEngine",
    "FormFillerError",
    "EngineUnavailableError",
    "TemplateNotFoundError",
    "TemplateProtectionError",
    "LayoutGuardError",
    # Excel (.xlsx) safe reader, writer, and template filler (Issue #842)
    "XlsxTemplateFiller",
    "XlsxWorkbookWriter",
    "XlsxReader",
    "XlsxFillConfig",
    "XlsxHeaderStyle",
    "sanitize_xlsx_value",
    "XlsxMediaLimitError",
    "MergedCellWriteError",
    # Bilingual calculation sheet builder (Issue #851)
    "CCBAExcelTheme",
    "CalculationSheetBuilder",
    "build_calc_sheet_from_yaml",
    "resolve_formula",
    # Technical evaluation report builder (Issue #856)
    "CCBADocxTheme",
    "TechnicalReportBuilder",
    "build_tech_report_from_yaml",
]

# Unannotated ast.Assign so check_init_lazy_exports_parity inspects all keys.
_LAZY_EXPORTS = {
    "audit_xlsx_formula_errors": "ccba_ooxml.calc",
    "recalc_xlsx": "ccba_ooxml.calc",
    "setup_libreoffice_macro": "ccba_ooxml.calc",
    "convert_to_pdf": "ccba_ooxml.converter",
    "docx_to_pdf": "ccba_ooxml.converter",
    "xlsx_to_pdf": "ccba_ooxml.converter",
    "CommentEngine": "ccba_ooxml.docx",
    "Document": "ccba_ooxml.docx",
    "DocxDocument": "ccba_ooxml.docx",
    "DocxXMLEditor": "ccba_ooxml.docx",
    "XMLEditor": "ccba_ooxml.docx",
    "clone_xml_text": "ccba_ooxml.docx",
    "get_authors_from_docx": "ccba_ooxml.docx",
    "get_tracked_change_authors": "ccba_ooxml.docx",
    "infer_author": "ccba_ooxml.docx",
    "merge_runs": "ccba_ooxml.docx",
    "revert_deletion": "ccba_ooxml.docx",
    "revert_insertion": "ccba_ooxml.docx",
    "simplify_redlines": "ccba_ooxml.docx",
    "suggest_deletion": "ccba_ooxml.docx",
    "suggest_paragraph": "ccba_ooxml.docx",
    "BaseFormFillerEngine": "ccba_ooxml.form_filler",
    "EngineUnavailableError": "ccba_ooxml.form_filler",
    "FormFillConfig": "ccba_ooxml.form_filler",
    "FormFillerError": "ccba_ooxml.form_filler",
    "FormLayoutGuard": "ccba_ooxml.form_filler",
    "LayoutGuardError": "ccba_ooxml.form_filler",
    "SofficeFallbackEngine": "ccba_ooxml.form_filler",
    "TableRule": "ccba_ooxml.form_filler",
    "TemplateNotFoundError": "ccba_ooxml.form_filler",
    "TemplateProtectionError": "ccba_ooxml.form_filler",
    "WinwordEngine": "ccba_ooxml.form_filler",
    "WordFormFiller": "ccba_ooxml.form_filler",
    "FormattingProfile": "ccba_ooxml.format",
    "convert_md_to_docx": "ccba_ooxml.format",
    "format_docx": "ccba_ooxml.format",
    "pack_document": "ccba_ooxml.pack",
    "validate_document": "ccba_ooxml.pack",
    "CardItem": "ccba_ooxml.pptx",
    "CCBAPresentationTheme": "ccba_ooxml.pptx",
    "DeckBuilder": "ccba_ooxml.pptx",
    "MarkdownDeckParser": "ccba_ooxml.pptx",
    "ParagraphData": "ccba_ooxml.pptx",
    "PresentationInventory": "ccba_ooxml.pptx",
    "ShapeData": "ccba_ooxml.pptx",
    "SlideSpec": "ccba_ooxml.pptx",
    "SlideType": "ccba_ooxml.pptx",
    "apply_replacements": "ccba_ooxml.pptx",
    "build_presentation_from_markdown": "ccba_ooxml.pptx",
    "extract_text_inventory": "ccba_ooxml.pptx",
    "generate_thumbnails": "ccba_ooxml.pptx",
    "get_inventory_as_dict": "ccba_ooxml.pptx",
    "pptx_inventory": "ccba_ooxml.pptx",
    "pptx_replace_text": "ccba_ooxml.pptx",
    "rearrange_presentation": "ccba_ooxml.pptx",
    "rearrange_slides": "ccba_ooxml.pptx",
    "save_inventory": "ccba_ooxml.pptx",
    "find_soffice_bin": "ccba_ooxml.soffice",
    "get_soffice_env": "ccba_ooxml.soffice",
    "run_soffice": "ccba_ooxml.soffice",
    "StructuredTable": "ccba_ooxml.tables",
    "TableReconstructor": "ccba_ooxml.tables",
    "make_descriptive_table_slug": "ccba_ooxml.tables",
    "vietnamese_to_ascii": "ccba_ooxml.tables",
    "unpack_document": "ccba_ooxml.unpack",
    "OOXMLWorkspace": "ccba_ooxml.workspace",
    "MergedCellWriteError": "ccba_ooxml.xlsx",
    "XlsxFillConfig": "ccba_ooxml.xlsx",
    "XlsxHeaderStyle": "ccba_ooxml.xlsx",
    "XlsxMediaLimitError": "ccba_ooxml.xlsx",
    "XlsxReader": "ccba_ooxml.xlsx",
    "XlsxTemplateFiller": "ccba_ooxml.xlsx",
    "XlsxWorkbookWriter": "ccba_ooxml.xlsx",
    "sanitize_xlsx_value": "ccba_ooxml.xlsx",
    "CCBAExcelTheme": "ccba_ooxml.xlsx",
    "CalculationSheetBuilder": "ccba_ooxml.xlsx",
    "build_calc_sheet_from_yaml": "ccba_ooxml.xlsx",
    "resolve_formula": "ccba_ooxml.xlsx",
    "CCBADocxTheme": "ccba_ooxml.docx",
    "TechnicalReportBuilder": "ccba_ooxml.docx",
    "build_tech_report_from_yaml": "ccba_ooxml.docx",
}


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        mod = importlib.import_module(module_name)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(set(globals().keys()) | set(__all__))
