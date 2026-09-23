# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Formula & Math Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.converters.omml import omml_to_latex
from ccba_legal.converters.standard.handlers.table_handler import clean_formula_latex
from ccba_legal.converters.standard.models import HierarchyState
from ccba_legal.figure_extractor import render_markdown_figure_card

__all__ = [
    "_emit_figure_or_comment",
    "extract_math_expression",
    "handle_empty_paragraph_formula",
    "handle_formula_block",
]


def _emit_figure_or_comment(ctx: Any, comment_str: str) -> None:
    """Render figure card from HTML comment if matching FIGURE format, else emit raw comment."""
    m_fig = re.match(r"^<!--\s*FIGURE:\s*([^|]+)\|(.*)-->$", comment_str.strip())
    if m_fig:
        fig_slug = m_fig.group(1).strip()
        fig_title = m_fig.group(2).strip().rstrip("-").strip()
        fig_num = fig_slug.replace("hinh_", "").replace("_", ".").upper()
        fig_entry: dict[str, Any] = {
            "tag": fig_num,
            "title": fig_title,
            "anchor": fig_slug.replace("_", "-"),
            "image_relpath": f"figures/images/{fig_slug}.png",
            "geometry_rules": {},
        }
        ctx.emit(render_markdown_figure_card(fig_entry))
    else:
        ctx.emit(f"\n{comment_str}\n\n")


def handle_empty_paragraph_formula(ctx: Any, obj: Any, i: int) -> int:
    """Check if an empty paragraph contains standalone formula images/drawings (e.g. MathType equations) and emit KaTeX or figure card."""
    xml = obj._element.xml
    rids = re.findall(r'r:(?:id|embed)="([^"]+)"', xml)
    if rids:
        for rid in rids:
            if rid in ctx.formula_overrides:
                val = ctx.formula_overrides[rid]
                if isinstance(val, tuple):
                    fid, f_latex = val[0], val[1]
                elif isinstance(val, dict):
                    fid = val.get("formula_id", f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}")
                    f_latex = val.get("latex", "")
                else:
                    fid = f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}"
                    f_latex = str(val)
                f_latex = f_latex.strip()
                if not f_latex:
                    return i + 1
                if f_latex.startswith("<!--"):
                    _emit_figure_or_comment(ctx, f_latex)
                    ctx.state_mgr.reset()
                    return i + 1
                if f_latex.startswith("$$") and f_latex.endswith("$$"):
                    f_latex = f_latex[2:-2].strip()
                ctx.emit(f'\n$${f_latex}$$\n<!-- formula_id: "{fid}" -->\n\n')
                if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
                    ctx.state_mgr.reset()
                return i + 1
            elif ctx.rid_to_katex and rid in ctx.rid_to_katex:
                raw_k = ctx.rid_to_katex[rid].strip()
                if not raw_k:
                    return i + 1
                if raw_k.startswith("<!--"):
                    _emit_figure_or_comment(ctx, raw_k)
                    ctx.state_mgr.reset()
                    return i + 1
                fid = f"F_{ctx.bundle_dir.name.upper()}_{rid.upper()}"
                f_latex = (
                    raw_k[2:-2].strip()
                    if (raw_k.startswith("$$") and raw_k.endswith("$$"))
                    else raw_k
                )
                ctx.emit(f'\n$${f_latex}$$\n<!-- formula_id: "{fid}" -->\n\n')
                if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
                    ctx.state_mgr.reset()
                return i + 1
    return i + 1


def extract_math_expression(obj: Any, ctx: Any, fallback_tag: str) -> tuple[str, str]:
    """Extract clean mathematical expression in KaTeX format."""
    formula_id = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{fallback_tag.replace('.', '_')}"

    # 1. Bundle-level exact override
    if fallback_tag in ctx.formula_overrides:
        o = ctx.formula_overrides[fallback_tag]
        if isinstance(o, tuple):
            return o[0], o[1]
        elif isinstance(o, dict):
            return o.get("formula_id", formula_id), o.get("latex", "")
        return formula_id, str(o)

    # 2. Extract OMML from paragraph
    p_xml = obj._element.xml
    m_omml = re.search(r"<m:oMath[^>]*>(.*?)</m:oMath>", p_xml, re.DOTALL)
    if m_omml:
        try:
            latex = omml_to_latex(
                f'<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">{m_omml.group(1)}</m:oMath>'
            )
            if latex:
                return formula_id, latex
        except Exception:
            pass

    # 3. Harvested formula image via KaTeX vision
    for r in obj.runs:
        for rid in re.findall(r'r:(?:embed|id)="([^"]+)"', r._r.xml):
            if rid in ctx.rid_to_katex:
                return formula_id, ctx.rid_to_katex[rid]

    # Fallback to paragraph text
    clean_t = re.sub(r"^\(([0-9A-Za-z\.]+)\)$", "", obj.text.strip()).strip()
    return formula_id, clean_t or "\\dots"


def handle_formula_block(
    ctx: Any,
    blocks: list[tuple[str, Any]],
    i: int,
    text: str,
    obj: Any,
    rendered_p: str,
) -> int | None:
    """Handle standalone formula headings, inline formula tags, and expression-tag pairs."""
    # 1. Inline Formula Tag (e.g. "RA x Ia <= 50 \t(1)", "R <= eq \f(50,Ia) \t(2)")
    m_inline = re.search(r"(?:\t|\s{2,})\(([0-9A-Za-zĐđ\.]+)\)\s*$", text)
    if not m_inline:
        m_inline = re.search(r"(?:\t|\s{2,})\(([0-9A-Za-zĐđ\.]+)\)\s*$", rendered_p)

    if m_inline:
        f_tag = m_inline.group(1)
        f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_")
        fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
        if f_tag in ctx.formula_overrides:
            o = ctx.formula_overrides[f_tag]
            if isinstance(o, tuple):
                fid, f_latex = o[0], o[1]
            elif isinstance(o, dict):
                fid = o.get("formula_id", fid)
                f_latex = o.get("latex", "")
            else:
                f_latex = str(o)
        else:
            p_xml = obj._element.xml
            has_embedded_math = (
                "<m:oMath" in p_xml
                or "<o:OLEObject" in p_xml
                or any(
                    rid in ctx.rid_to_katex
                    for rid in re.findall(r'r:(?:embed|id)="([^"]+)"', p_xml)
                )
            )
            if has_embedded_math:
                _, f_latex = extract_math_expression(obj, ctx, f_tag)
            else:
                clean_expr = re.sub(
                    r"(?:\t|\s{2,})\(([0-9A-Za-zĐđ\.]+)\)\s*$", "", rendered_p
                ).strip()
                f_latex = clean_formula_latex(clean_expr)
                f_latex = re.sub(
                    r"(?<=[0-9a-zA-Z\}\)])\s+x\s+(?=[0-9a-zA-Z\{\\])", r" \\times ", f_latex
                )
                if f_latex.startswith("và "):
                    f_latex = r"\text{và } " + f_latex[3:].strip()

        f_latex = f_latex.strip()
        if f_latex.startswith("$$") and f_latex.endswith("$$"):
            f_latex = f_latex[2:-2].strip()
        f_latex = re.sub(r"\\tag\{[^}]+\}", "", f_latex).strip()
        f_latex = re.sub(r"\\qquad\s*\([^)]+\)", "", f_latex).strip()
        f_latex = re.sub(r"(?:\t|\s{2,})\(([0-9A-Za-zĐđ\.]+)\)\s*$", "", f_latex).strip()

        ctx.emit(
            f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \\qquad ({f_tag})$$\n<!-- formula_id: "{fid}" -->\n\n'
        )
        if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
            ctx.state_mgr.reset()
        return i + 1

    # 2. Formula Expression at i followed by Tag (N) at i + 1
    # ONLY if block i actually contains math (OMML, OLE/imagedata, or Word EQ fields)
    p_xml = obj._element.xml
    has_math = (
        "<m:oMath" in p_xml
        or "<o:OLEObject" in p_xml
        or "w:fldSimple" in p_xml
        or "w:instrText" in p_xml
        or any(rid in ctx.rid_to_katex for rid in re.findall(r'r:(?:embed|id)="([^"]+)"', p_xml))
    )
    if has_math and i + 1 < len(blocks):
        next_b_type, next_obj = blocks[i + 1]
        if next_b_type == "p" and hasattr(next_obj, "text"):
            next_t = next_obj.text.strip()
            m_next_tag = re.match(r"^\(([0-9A-Za-zĐđ\.]+)\)$", next_t)
            if m_next_tag:
                f_tag = m_next_tag.group(1)
                f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_")
                fid = f"F_{ctx.bundle_dir.name.upper()}_FORMULA_{f_slug.upper()}"
                if f_tag in ctx.formula_overrides:
                    o = ctx.formula_overrides[f_tag]
                    if isinstance(o, tuple):
                        fid, f_latex = o[0], o[1]
                    elif isinstance(o, dict):
                        fid = o.get("formula_id", fid)
                        f_latex = o.get("latex", "")
                    else:
                        f_latex = str(o)
                else:
                    _, f_latex = extract_math_expression(obj, ctx, f_tag)
                    if f_latex == "\\dots":
                        f_latex = clean_formula_latex(rendered_p)

                f_latex = f_latex.strip()
                if f_latex.startswith("$$") and f_latex.endswith("$$"):
                    f_latex = f_latex[2:-2].strip()
                f_latex = re.sub(r"\\tag\{[^}]+\}", "", f_latex).strip()
                f_latex = re.sub(r"\\qquad\s*\([^)]+\)", "", f_latex).strip()
                ctx.emit(
                    f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \\qquad ({f_tag})$$\n<!-- formula_id: "{fid}" -->\n\n'
                )
                if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
                    ctx.state_mgr.reset()
                return i + 2

    # 3. Standalone Formula Tag (e.g. (1), (2.1), (A.1))
    m_f_head = re.match(r"^\(([0-9A-Za-zĐđ\.]+)\)$", text)
    if m_f_head:
        f_tag = m_f_head.group(1)
        f_slug = f_tag.lower().replace("đ", "dd").replace(".", "_")
        fid, f_latex = extract_math_expression(obj, ctx, f_tag)
        f_latex = f_latex.strip()
        if f_latex.startswith("$$") and f_latex.endswith("$$"):
            f_latex = f_latex[2:-2].strip()
        f_latex = re.sub(r"\\tag\{[^}]+\}", "", f_latex).strip()
        f_latex = re.sub(r"\\qquad\s*\([^)]+\)", "", f_latex).strip()
        ctx.emit(
            f'\n<a id="formula-{f_slug}"></a>\n$${f_latex} \\qquad ({f_tag})$$\n<!-- formula_id: "{fid}" -->\n\n'
        )
        if ctx.state_mgr.state != HierarchyState.IN_TRONG_DO:
            ctx.state_mgr.reset()
        return i + 1

    return None
