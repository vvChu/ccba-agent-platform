"""CCBA OOXML Utilities.

Shared library for packaging, unpackaging, validating, formatting, and DOM manipulating docx/pptx/xlsx documents.
"""

from __future__ import annotations

from .calc import recalc_xlsx, setup_libreoffice_macro
from .docx import (
    CommentEngine,
    Document,
    DocxDocument,
    DocxXMLEditor,
    XMLEditor,
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

__all__ = [
    # Document operations
    "pack_document",
    "unpack_document",
    "validate_document",
    "OOXMLWorkspace",
    # Spreadsheet calculation
    "recalc_xlsx",
    "setup_libreoffice_macro",
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
    "LayoutGuardError",
]
