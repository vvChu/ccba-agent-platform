# Copyright (c) 2026 CCBA. All rights reserved.
"""Paragraph and run AST renderer preserving subscripts, superscripts, and inline symbols."""

from __future__ import annotations

import re
from typing import Any

from ccba_legal.converters.standard.sanitizers.text_normalizer import (
    heal_orphaned_strains,
    normalize_degrees_and_angles,
    normalize_formula_equations,
)
from ccba_legal.converters.technical_formulas import GREEK_MAP, INLINE_SYMBOLS_MAP


def parse_word_eq_field(instr: str) -> str:
    """Convert Word EQ field instructions like 'eq \\f(50,Ia)' or 'eq \\f(S,2)' into KaTeX."""
    if not isinstance(instr, str):
        return ""
    clean = instr.strip()
    m_eq = re.match(r"^\s*(?:eq|EQ)\s+(.*)$", clean)
    if not m_eq:
        return ""
    rest = m_eq.group(1).strip()

    def _rep_frac(m: re.Match[str]) -> str:
        num = m.group(1).strip()
        den = m.group(2).strip()
        if re.match(r"^[A-Z][a-z0-9]$", num):
            num = f"{num[0]}_{num[1]}"
        if re.match(r"^[A-Z][a-z0-9]$", den):
            den = f"{den[0]}_{den[1]}"
        for g_char, g_latex in GREEK_MAP.items():
            def _rep_g_frac(_m: re.Match[str], gl: str = g_latex) -> str:
                return f"{gl} "
            num = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", _rep_g_frac, num)
            num = num.replace(g_char, g_latex)
            den = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", _rep_g_frac, den)
            den = den.replace(g_char, g_latex)
        return f"\\frac{{{num}}}{{{den}}}"

    def _rep_root(m: re.Match[str]) -> str:
        content = m.group(1).strip()
        if "," in content:
            parts = [p.strip() for p in content.split(",", 1)]
            if not parts[0]:
                return f"\\sqrt{{{parts[1]}}}"
            return f"\\sqrt[{parts[0]}]{{{parts[1]}}}"
        return f"\\sqrt{{{content}}}"

    # Iteratively resolve inner radicals and fractions (supporting nested EQ constructs)
    for _ in range(5):
        prev = rest
        rest = re.sub(r"\\r\(([^()]+)\)", _rep_root, rest, flags=re.IGNORECASE)
        rest = re.sub(r"\\f\(([^(),]+),([^(),]+)\)", _rep_frac, rest, flags=re.IGNORECASE)
        rest = re.sub(r"\\s(?:\\up\d*|\b)\(([^(),]+)\)", r"^{\1}", rest, flags=re.IGNORECASE)
        rest = re.sub(r"\\s\\do\d*\(([^(),]+)\)", r"_{\1}", rest, flags=re.IGNORECASE)
        if rest == prev:
            break

    for g_char, g_latex in GREEK_MAP.items():
        def _rep_g_rest(_m: re.Match[str], gl: str = g_latex) -> str:
            return f"{gl} "
        rest = re.sub(rf"{re.escape(g_char)}(?=[a-zA-Z0-9])", _rep_g_rest, rest)
        rest = rest.replace(g_char, g_latex)

    rest = re.sub(r"<=|≤", r" \\le ", rest)
    rest = re.sub(r">=|≥", r" \\ge ", rest)
    rest = re.sub(r"(?<=[0-9a-zA-Z\}\)])\s+x\s+(?=[0-9a-zA-Z\{\\])", r" \\times ", rest)
    return re.sub(r"\s+", " ", rest).strip()


def render_paragraph_with_runs(p: Any, rid_to_katex: dict[str, str] | None = None) -> str:
    """Render a docx paragraph while preserving sub/superscripts, resolving Word EQ fields, and inline symbols."""
    runs = p.runs
    if not runs:
        return str(p.text).strip()

    grouped: list[tuple[str, str]] = []
    in_field = False
    in_field_result = False
    field_instr: list[str] = []
    field_result_runs: list[str] = []
    seen_fld_simples: set[Any] = set()

    for r in runs:
        xml = r._r.xml
        # Check w:fldSimple wrapper
        if hasattr(r, "_r") and hasattr(r._r, "xpath"):
            try:
                fld_simples = r._r.xpath("ancestor::*[local-name()='fldSimple']")
            except Exception:
                fld_simples = []
            if isinstance(fld_simples, list) and fld_simples:
                fld_simple = fld_simples[0]
                if fld_simple not in seen_fld_simples:
                    instr = fld_simple.get(
                        "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}instr", ""
                    ) or fld_simple.get("instr", "")
                    if isinstance(instr, str) and instr:
                        eq_latex = parse_word_eq_field(instr)
                        if eq_latex:
                            seen_fld_simples.add(fld_simple)
                            grouped.append(("norm", f"${eq_latex}$"))
                            continue
                else:
                    # Already rendered this fldSimple as eq_latex, skip its subsequent runs
                    continue

        if 'w:fldCharType="begin"' in xml:
            in_field = True
            in_field_result = False
            field_instr = []
            field_result_runs = []
            continue
        elif 'w:fldCharType="separate"' in xml:
            in_field_result = True
            continue
        elif 'w:fldCharType="end"' in xml:
            in_field = False
            in_field_result = False
            full_instr = "".join(field_instr).strip()
            eq_latex = parse_word_eq_field(full_instr)
            if eq_latex:
                grouped.append(("norm", f"${eq_latex}$"))
            else:
                for cached_txt in field_result_runs:
                    if cached_txt:
                        grouped.append(("norm", cached_txt))
            continue

        if in_field:
            if in_field_result:
                r_txt = r.text or ""
                if r_txt:
                    field_result_runs.append(r_txt)
            else:
                instr_elems = r._r.xpath('.//*[local-name()="instrText"]')
                if instr_elems:
                    is_sub = "subscript" in xml or (
                        hasattr(r, "font") and getattr(r.font, "subscript", None) is True
                    )
                    for el in instr_elems:
                        txt = el.text or ""
                        if is_sub:
                            txt = f"_{{{txt}}}" if len(txt) > 1 else f"_{txt}"
                        field_instr.append(txt)
            continue

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
        if "<w:tab" in xml:
            t = (t or "") + "\t"
        m_sym = re.search(r'<w:sym[^>]*w:char="([^"]+)"', xml)
        if m_sym:
            char_hex = m_sym.group(1).upper()
            if char_hex in ("F0B4", "00D7", "B4"):
                t = (t or "") + "×"
            elif char_hex in ("F0A3", "2264"):
                t = (t or "") + "≤"
            elif char_hex in ("F0B3", "2265"):
                t = (t or "") + "≥"
            elif char_hex in ("F0B1", "00B1"):
                t = (t or "") + "±"
            elif char_hex in ("F0B0", "00B0"):
                t = (t or "") + "°"
            elif char_hex in ("F0B7", "00B7"):
                t = (t or "") + "·"

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
                def _rep_g_run(_m: re.Match[str], gl: str = g_latex) -> str:
                    return f"{gl} "
                clean_t = re.sub(
                    rf"{re.escape(g_char)}(?=[a-zA-Z0-9])",
                    _rep_g_run,
                    clean_t,
                )
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

    def _rep_greek_in_math(m: re.Match[str]) -> str:
        content = m.group(1)
        for g_char, g_latex in GREEK_MAP.items():
            def _rep_g_inner(_m: re.Match[str], gl: str = g_latex) -> str:
                return f"{gl} "
            content = re.sub(
                rf"{re.escape(g_char)}(?=[a-zA-Z0-9])",
                _rep_g_inner,
                content,
            )
            content = content.replace(g_char, g_latex)
        return f"${content}$"

    def _rep_greek_cmd(m: re.Match[str]) -> str:
        return f"\\{m.group(1)} "

    res = re.sub(r"\$([^$]+)\$", _rep_greek_in_math, res)
    res = re.sub(
        r"\\(Delta|Sigma|Omega|alpha|beta|gamma|delta|epsilon|eta|theta|lambda|mu|nu|xi|pi|rho|sigma|tau|varphi|psi|omega)(?=[a-zA-Z0-9])",
        _rep_greek_cmd,
        res,
    )
    res = heal_orphaned_strains(res)
    res = res.replace("$$", "").replace("$_$", "").replace("$^$", "")
    res = normalize_degrees_and_angles(res)
    res = normalize_formula_equations(res)
    res = re.sub(r"\$([\\a-zA-Z0-9][^$]*?)\$([a-zA-Z\u00C0-\u024F\u1EA0-\u1EF9])", r"$\1$ \2", res)
    return res.strip()
