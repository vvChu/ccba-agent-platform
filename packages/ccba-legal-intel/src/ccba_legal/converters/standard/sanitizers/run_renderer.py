# Copyright (c) 2026 CCBA. All rights reserved.
"""Paragraph and run AST renderer preserving subscripts, superscripts, and inline symbols."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.converters.standard.sanitizers.text_normalizer import (
    GREEK_MAP,
    heal_orphaned_strains,
    normalize_degrees_and_angles,
    normalize_formula_equations,
)
from ccba_legal.converters.technical_formulas import INLINE_SYMBOLS_MAP


def render_paragraph_with_runs(p: Any, rid_to_katex: dict[str, str] | None = None) -> str:
    """Render a docx paragraph while preserving sub/superscripts and resolving inline image symbols as clean KaTeX tokens."""
    runs = p.runs
    if not runs:
        return str(p.text).strip()

    grouped: list[tuple[str, str]] = []
    for r in runs:
        xml = r._r.xml
        m_rid = re.search(r'r:(?:id|embed)="([^"]+)"', xml)
        if m_rid:
            rid = m_rid.group(1)
            if rid in INLINE_SYMBOLS_MAP:
                grouped.append(("norm", f"${INLINE_SYMBOLS_MAP[rid]}$"))
                continue
            if rid_to_katex and rid in rid_to_katex:
                k_sym = rid_to_katex[rid]
                if not k_sym.startswith("<!-- DIAGRAM"):
                    clean_k = k_sym.strip("$ ")
                    if "<!--" in clean_k:
                        clean_k = clean_k.split("<!--")[0].strip("$ \n\r")
                    grouped.append(("norm", f"${clean_k}$"))
                    continue
        t = r.text
        if not t:
            continue
        is_sub = "subscript" in xml or (r.font.subscript is True)
        is_sup = "superscript" in xml or (r.font.superscript is True)
        mode = "sub" if is_sub else ("sup" if is_sup else "norm")
        if grouped and grouped[-1][0] == mode:
            grouped[-1] = (mode, grouped[-1][1] + t)
        else:
            grouped.append((mode, t))

    out_tokens: list[str] = []
    for mode, text in grouped:
        if mode in ("sub", "sup"):
            clean_t = text.strip()
            if not clean_t:
                out_tokens.append(text)
                continue
            trailing_comma = ", " if clean_t.endswith(",") else ""
            clean_t = clean_t.rstrip(",").strip()
            for g_char, g_latex in GREEK_MAP.items():
                clean_t = clean_t.replace(g_char, g_latex)
            if mode == "sup" and re.match(r"^(\*+|\([0-9\*\+a-zA-Z]+\)|[0-9]+[)\.])$", clean_t):
                trailing_space = " " if text.endswith(" ") else ""
                out_tokens.append(f"<sup>{clean_t}</sup>{trailing_comma}{trailing_space}")
            else:
                wrap = f"_{{{clean_t}}}" if mode == "sub" else f"^{{{clean_t}}}"
                trailing_space = " " if text.endswith(" ") else ""
                out_tokens.append(f"${wrap}${trailing_comma}{trailing_space}")
        else:
            out_tokens.append(text)

    res = "".join(out_tokens)
    res = re.sub(
        r"([a-zA-ZÀ-ɏẠ-ỹͰ-Ͽ]+)\$(_\{[^}]+\}|_[a-zA-Z0-9,]+|\^\{[^}]+\}|\^[a-zA-Z0-9]+)\$",
        r"$\1\2$",
        res,
    )
    res = re.sub(
        r"\$([^$]+)\$", lambda m: f"${''.join(GREEK_MAP.get(c, c) for c in m.group(1))}$", res
    )
    res = heal_orphaned_strains(res)
    res = res.replace("$$", "").replace("$_$", "").replace("$^$", "")
    res = normalize_degrees_and_angles(res)
    res = normalize_formula_equations(res)
    res = re.sub(r"\$([\\a-zA-Z0-9][^$]*?)\$([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])", r"$\1$ \2", res)
    return res.strip()
