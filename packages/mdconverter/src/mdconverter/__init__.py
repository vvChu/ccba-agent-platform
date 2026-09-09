"""mdconverter - Modern Document to Markdown Converter.

A powerful Python library for converting documents (PDF, DOCX, HTML) to clean,
standardized Markdown with special support for Vietnamese legal documents,
academic writing verification, table reconstruction, and long-form document pipelines.
"""

from __future__ import annotations

__version__ = "2.3.0"
__author__ = "IBST BIM Team"

from mdconverter.academic import (
    AuditFinding,
    MicrostructureReport,
    audit_microstructure,
    export_paper_to_docx,
    scaffold_manuscript,
)
from mdconverter.config import Settings, get_settings
from mdconverter.core import (
    BaseConverter,
    ConversionCache,
    ConversionPipeline,
    ConversionResult,
    ConversionTimeoutError,
    ConverterNotAvailableError,
    ConverterRegistry,
    InvalidInputError,
    MDConvertError,
    PostProcessor,
    ProviderError,
)
from mdconverter.style import (
    analyze_style_metrics,
    parse_template_placeholders,
    redact_sensitive_info,
)
from mdconverter.tables import (
    ExtractedTable,
    convert_docx_to_okf_bundle,
    extract_docx_tables,
    format_all_qcvn_md_tables,
    format_qcvn_md_table,
    normalize_docx_markdown,
)
from mdconverter.writer import (
    chunk_outline_sections,
    save_markdown_to_docx,
    stitch_markdown_sections,
)

__all__ = [
    # Configuration & Core Pipeline
    "Settings",
    "get_settings",
    "BaseConverter",
    "ConversionCache",
    "ConversionPipeline",
    "ConversionResult",
    "ConverterRegistry",
    "PostProcessor",
    "MDConvertError",
    "ConverterNotAvailableError",
    "ConversionTimeoutError",
    "InvalidInputError",
    "ProviderError",
    "__version__",
    # Academic Writing Seams
    "AuditFinding",
    "MicrostructureReport",
    "audit_microstructure",
    "scaffold_manuscript",
    "export_paper_to_docx",
    # Tables & QCVN Markdown Normalization
    "ExtractedTable",
    "extract_docx_tables",
    "format_qcvn_md_table",
    "format_all_qcvn_md_tables",
    "normalize_docx_markdown",
    "convert_docx_to_okf_bundle",
    # Style Analysis & Sanitization
    "redact_sensitive_info",
    "analyze_style_metrics",
    "parse_template_placeholders",
    # Long-form Document Generation
    "chunk_outline_sections",
    "stitch_markdown_sections",
    "save_markdown_to_docx",
]
