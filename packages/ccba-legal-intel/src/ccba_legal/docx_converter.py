"""CCBA Universal Legal DOCX Converter Engine (OKF v2.2 Gateway) - Facade Dispatcher."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from ccba_legal.converters import (
    DocumentArchetype,
    FullDocStructuralScanner,
    classify_and_extract_tables,
    detect_document_pipeline,
    extract_legal_basis_graph,
    format_all_qcvn_md_tables,
    normalize_clause_numbers,
    normalize_docx_markdown,
    normalize_units_and_math,
    process_technical_standard_strategy,
    process_vbpl_bundle_okf_v22,
)

__all__ = [
    "DocumentArchetype",
    "FullDocStructuralScanner",
    "convert_docx_to_okf_bundle",
    "detect_document_pipeline",
    "classify_and_extract_tables",
    "process_technical_standard_strategy",
    "process_vbpl_bundle_okf_v22",
    "normalize_clause_numbers",
    "normalize_docx_markdown",
    "normalize_units_and_math",
    "format_all_qcvn_md_tables",
    "extract_legal_basis_graph",
]


def convert_docx_to_okf_bundle(
    docx_path: Path,
    target_bundle_dir: Path,
    output_filename: str | None = None,
    doc_type: str | None = None,
    registry_file: Path | None = None,
    archetype: str | None = None,
) -> dict[str, Any]:
    """Convert .docx file to Gold Standard OKF v2.2 Markdown bundle with Multi-Archetype Strategy Dispatcher."""
    if not docx_path.exists():
        raise FileNotFoundError(f"Input file not found: {docx_path}")

    target_bundle_dir.mkdir(parents=True, exist_ok=True)
    reg_file = registry_file or (Path.cwd() / "legal_registry.yaml")

    # Load registry metadata if available
    doc_meta: dict[str, Any] = {}
    if reg_file.exists():
        with open(reg_file, encoding="utf-8") as f:
            reg_data = yaml.safe_load(f)
            all_items = []
            for _k, v in reg_data.items():
                if isinstance(v, list):
                    all_items.extend(v)
            for item in all_items:
                if item.get("id") == target_bundle_dir.name or item.get("document_number") == target_bundle_dir.name:
                    doc_meta = item
                    break

    # Determine archetype
    detected_archetype = DocumentArchetype.VBPL_ADMIN
    if archetype and archetype.upper() in DocumentArchetype.__members__:
        detected_archetype = DocumentArchetype[archetype.upper()]
    else:
        scanner = FullDocStructuralScanner(
            docx_path=docx_path,
            doc_num_str=doc_meta.get("document_number", target_bundle_dir.name),
            doc_type_str=doc_meta.get("type", doc_type or ""),
        )
        detected_archetype = scanner.scan()

    if detected_archetype in (DocumentArchetype.TECHNICAL_TCVN, DocumentArchetype.TECHNICAL_QCVN):
        return process_technical_standard_strategy(
            docx_path=docx_path,
            bundle_dir=target_bundle_dir,
            registry_file=reg_file,
            doc_meta=doc_meta,
            output_filename=output_filename,
        )
    else:
        return process_vbpl_bundle_okf_v22(
            docx_path=docx_path,
            bundle_dir=target_bundle_dir,
            registry_file=reg_file,
            output_filename=output_filename,
        )
