# Copyright (c) 2026 CCBA. All rights reserved.
"""Modular Technical Standard Strategy Converter (OKF v2.4 - ADR 0030, ADR 0034, ADR 0036)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, BinaryIO

from docx import Document

from ccba_legal.converters.standard.exporter import (
    build_frontmatter_yaml,
    export_standard_bundle,
)
from ccba_legal.converters.standard.handlers.figure_handler import handle_figure_card
from ccba_legal.converters.standard.handlers.formula_handler import (
    handle_empty_paragraph_formula,
    handle_formula_block,
)
from ccba_legal.converters.standard.handlers.heading_handler import handle_structural_heading
from ccba_legal.converters.standard.handlers.list_handler import handle_list_and_paragraph
from ccba_legal.converters.standard.handlers.table_handler import handle_table_block
from ccba_legal.converters.standard.preprocessor import (
    extract_document_blocks,
    find_normative_start_index,
    find_standard_header_start_index,
    process_preamble_blocks,
)
from ccba_legal.converters.standard.sanitizers import (
    GREEK_MAP,
    INLINE_SYMBOLS_MAP,
    render_paragraph_with_runs,
    sanitize_prose_greeks_and_variables,
)
from ccba_legal.converters.standard.state_manager import HierarchyStateManager
from ccba_legal.converters.technical_formulas import load_bundle_formula_overrides
from ccba_legal.figure_extractor import extract_docx_figures
from ccba_legal.formula_harvester import harvest_docx_formula_images

__all__ = [
    "GREEK_MAP",
    "INLINE_SYMBOLS_MAP",
    "StandardConversionContext",
    "process_technical_standard_strategy",
    "render_paragraph_with_runs",
    "sanitize_prose_greeks_and_variables",
]


@dataclass
class StandardConversionContext:
    """State machine container for technical standard conversions."""

    bundle_dir: Path
    output_filename: str | None
    rid_to_katex: dict[str, str] = field(default_factory=dict)
    body_md_parts: list[str] = field(default_factory=list)
    annex_buffers: dict[str, dict[str, Any]] = field(default_factory=dict)
    current_target: str = "main"
    current_part: str | None = None
    last_table_caption: str | None = None
    last_table_caption_num: str | None = None
    last_table_unit: str | None = None
    tables_extracted: list[dict[str, Any]] = field(default_factory=list)
    state_mgr: HierarchyStateManager = field(default_factory=HierarchyStateManager)
    formula_overrides: dict[str, Any] = field(default_factory=dict)
    doc_meta: dict[str, Any] = field(default_factory=dict)

    @property
    def active_parts(self) -> list[str]:
        """Return the active markdown parts buffer."""
        if self.current_target == "main":
            return self.body_md_parts
        parts: list[str] = self.annex_buffers[self.current_target]["parts"]
        return parts

    def emit(self, chunk: str) -> None:
        """Emit a markdown chunk to either the main body buffer or active modular annex buffer."""
        self.active_parts.append(chunk)


def _process_paragraph_block(
    ctx: StandardConversionContext, blocks: list[tuple[str, Any]], i: int
) -> int:
    """Dispatch a single paragraph block across specialized handlers in order."""
    obj = blocks[i][1]
    text = obj.text.strip()
    if not text:
        return handle_empty_paragraph_formula(ctx, obj, i)

    rendered_p = render_paragraph_with_runs(obj, rid_to_katex=ctx.rid_to_katex)

    # 1. Formula Handler
    res_f = handle_formula_block(ctx, blocks, i, text, obj, rendered_p)
    if res_f is not None:
        return res_f

    # 2. Structural Headings & Notes Handler
    res_h = handle_structural_heading(ctx, blocks, i, text, rendered_p, obj)
    if res_h is not None:
        return res_h

    # 3. Figure Card Handler
    res_fig = handle_figure_card(ctx, text, i)
    if res_fig is not None:
        return res_fig

    # 4. List Hierarchy & Paragraph Handler
    return handle_list_and_paragraph(ctx, blocks, i, text, rendered_p, obj)


def _process_table_block(
    ctx: StandardConversionContext, table_obj: Any, i: int, blocks: list[Any] | None = None
) -> None:
    """Extract and render tabular data into 2D Markdown, CSV, and JSON."""
    handle_table_block(ctx, table_obj, i, blocks=blocks)


def process_technical_standard_strategy(
    docx_path: Path | str,
    bundle_dir: Path | str,
    output_filename: str | None = None,
    rid_to_katex: dict[str, str] | None = None,
    registry_file: Path | str | None = None,
    doc_meta: dict[str, Any] | None = None,
    sanitized_stream: BinaryIO | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Process a Technical Standard (TCVN / QCVN) DOCX with 100% Visual Parity & Modular Annex Split."""
    docx_p = Path(docx_path)
    bundle_p = Path(bundle_dir)
    bundle_p.mkdir(parents=True, exist_ok=True)

    # 1. Harvest formulas and extract figures
    cache_dir = (
        bundle_p.parents[2] / ".md" / "cache" / "formula_vision"
        if len(bundle_p.parents) >= 3
        else bundle_p / ".cache"
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    skip_vis = os.environ.get("AI_SKIP_VISION") == "1"
    docx_rid_to_katex = rid_to_katex or harvest_docx_formula_images(
        docx_p, cache_dir=cache_dir, skip_vision=skip_vis
    )
    extract_docx_figures(docx_p, bundle_p / "figures")

    # 2. Extract and locate normative start
    doc = Document(sanitized_stream if sanitized_stream is not None else str(docx_p))
    blocks = extract_document_blocks(doc)
    std_start_idx = find_standard_header_start_index(blocks)
    start_idx = find_normative_start_index(blocks, start_from=std_start_idx)

    # 3. Initialize conversion context and process preamble
    ctx = StandardConversionContext(
        bundle_dir=bundle_p,
        output_filename=output_filename,
        rid_to_katex=docx_rid_to_katex,
        formula_overrides=load_bundle_formula_overrides(bundle_p),
        doc_meta=doc_meta or kwargs.get("doc_meta") or {},
    )
    process_preamble_blocks(ctx, blocks, std_start_idx, start_idx)

    # 4. Dual-Dispatch block iteration
    i = start_idx
    while i < len(blocks):
        b_type, obj = blocks[i]
        if b_type == "p":
            i = _process_paragraph_block(ctx, blocks, i)
        elif b_type == "tbl":
            _process_table_block(ctx, obj, i, blocks=blocks)
            i += 1

    # 5. Export modular bundle via exporter helper
    return export_standard_bundle(ctx)


# Backwards compatibility aliases
_extract_document_blocks = extract_document_blocks
_find_standard_header_start_index = find_standard_header_start_index
_find_normative_start_index = find_normative_start_index
_build_frontmatter_yaml = build_frontmatter_yaml
_export_modular_annexes_and_moc = export_standard_bundle
