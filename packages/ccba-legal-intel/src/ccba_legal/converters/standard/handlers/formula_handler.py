# Copyright (c) 2026 CCBA. All rights reserved.
"""Specialized Formula & Math Handler for Technical Standards (OKF v2.4)."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.converters.omml import omml_to_latex
from ccba_legal.converters.standard.handlers.table_handler import clean_formula_latex
from ccba_legal.converters.standard.models import HierarchyState


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
    """Handle standalone formula headings, inline formula tags, expression-tag pairs, and embedded drawing blocks."""
    # 1. Blank paragraph with drawings/formulas
    if not text:
        p_xml = obj._element.xml
        has_drawings = "w:drawing" in p_xml or "v:imagedata" in p_xml or "v:shape" in p_xml
        if has_drawings and rendered_p:
            if rendered_p.startswith("$$"):
                has_math_op = any(
                    op in rendered_p
                    for op in [
                        "=",
                        "\\le",
                        "\\ge",
                        "<",
                        ">",
                        "\\approx",
                        "\\sum",
                        "\\int",
                        "\\frac",
                        "\\pm",
                        "\\times",
                        "\\cdot",
                        "\\partial",
                        "\\sqrt",
                    ]
                )
                if has_math_op:
                    m_f_tag = re.search(
                        r"(?:\\tag\{([0-9A-Za-zĐđ\.]+)\}|\\qquad\s*\(([0-9A-Za-zĐđ\.]+)\)|\(([0-9]{1,3}|[A-ZĐđ]\.[0-9]{1,2})\))",
                        rendered_p,
                    )
                    if m_f_tag and not rendered_p.startswith("<a id="):
                        tag_val = m_f_tag.group(1) or m_f_tag.group(2) or m_f_tag.group(3)
                        tag_slug = tag_val.lower().replace("đ", "dd").replace(".", "_")
                        ctx.emit(f'<a id="formula-{tag_slug}"></a>\n{rendered_p}\n\n')
                    else:
                        ctx.emit(f"{rendered_p}\n\n")
            elif rendered_p.startswith(("<a id=", "<p", "![", "**")):
                ctx.emit(f"{rendered_p}\n\n")
        return i + 1

    # 2. Inline Formula Tag (e.g. "RA x Ia <= 50 \t(1)", "R <= eq \f(50,Ia) \t(2)")
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

    # 3. Formula Expression at i followed by Tag (N) at i + 1
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

    # 4. Standalone Formula Tag (e.g. (1), (2.1), (A.1))
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
