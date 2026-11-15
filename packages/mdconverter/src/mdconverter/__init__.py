"""mdconverter - Modern Document to Markdown Converter.

A powerful Python library for converting documents (PDF, DOCX, HTML) to clean,
standardized Markdown with special support for Vietnamese legal documents,
academic writing verification, table reconstruction, and long-form document pipelines.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

__version__ = "2.3.0"
__author__ = "IBST BIM Team"

if TYPE_CHECKING:
    from mdconverter.academic import (
        AcademicAuditFinding,
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

    # Backward-compatible top-level alias while keeping __all__ collision-free
    AuditFinding = AcademicAuditFinding

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
    "AcademicAuditFinding",
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

# Unannotated ast.Assign so check_init_lazy_exports_parity inspects all keys.
# Keep core symbols mapped to "mdconverter.core" so _register_builtin_converters() runs on load.
_LAZY_EXPORTS = {
    "AcademicAuditFinding": "mdconverter.academic",
    "MicrostructureReport": "mdconverter.academic",
    "audit_microstructure": "mdconverter.academic",
    "export_paper_to_docx": "mdconverter.academic",
    "scaffold_manuscript": "mdconverter.academic",
    "Settings": "mdconverter.config",
    "get_settings": "mdconverter.config",
    "BaseConverter": "mdconverter.core",
    "ConversionCache": "mdconverter.core",
    "ConversionPipeline": "mdconverter.core",
    "ConversionResult": "mdconverter.core",
    "ConversionTimeoutError": "mdconverter.core",
    "ConverterNotAvailableError": "mdconverter.core",
    "ConverterRegistry": "mdconverter.core",
    "InvalidInputError": "mdconverter.core",
    "MDConvertError": "mdconverter.core",
    "PostProcessor": "mdconverter.core",
    "ProviderError": "mdconverter.core",
    "analyze_style_metrics": "mdconverter.style",
    "parse_template_placeholders": "mdconverter.style",
    "redact_sensitive_info": "mdconverter.style",
    "ExtractedTable": "mdconverter.tables",
    "convert_docx_to_okf_bundle": "mdconverter.tables",
    "extract_docx_tables": "mdconverter.tables",
    "format_all_qcvn_md_tables": "mdconverter.tables",
    "format_qcvn_md_table": "mdconverter.tables",
    "normalize_docx_markdown": "mdconverter.tables",
    "chunk_outline_sections": "mdconverter.writer",
    "save_markdown_to_docx": "mdconverter.writer",
    "stitch_markdown_sections": "mdconverter.writer",
}


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    if name == "AuditFinding":
        mod = importlib.import_module("mdconverter.academic")
        value = mod.AcademicAuditFinding
        globals()["AuditFinding"] = value
        return value
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        mod = importlib.import_module(module_name)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(set(globals().keys()) | set(__all__) | {"AuditFinding"})
