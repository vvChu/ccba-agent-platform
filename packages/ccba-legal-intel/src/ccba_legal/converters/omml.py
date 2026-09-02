"""omml.py - Zero-Dependency Deterministic Office Math (OMML) to KaTeX / LaTeX Converter.

Parses OpenXML <m:oMath> and <m:oMathPara> XML trees directly into standard LaTeX math expressions.
Standard: ISO/IEC 29500-1:2016 Mathematics (Office Open XML).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from ccba_legal.converters.technical_formulas import GREEK_MAP

OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

# Map of common OMML accent characters to LaTeX accents
ACCENT_MAP: dict[str, str] = {
    "\u0302": r"\hat",  # Comb hat
    "^": r"\hat",
    "\u0300": r"\grave",
    "\u0301": r"\acute",
    "\u0303": r"\tilde",
    "~": r"\tilde",
    "\u0304": r"\bar",  # Comb macron
    "\u00af": r"\bar",  # Macron
    "\u0305": r"\bar",  # Overline
    "\u0306": r"\breve",
    "\u0307": r"\dot",  # Comb dot
    "\u0308": r"\ddot",  # Comb diaeresis
    "\u20db": r"\dddot",
    "\u030a": r"\mathring",
    "\u20d7": r"\vec",  # Comb right arrow above
    "\u2192": r"\vec",
}

# Map of common standard mathematical operators and symbols
MATH_SYMBOLS_MAP: dict[str, str] = {
    "≤": r"\le",
    "≥": r"\ge",
    "≠": r"\ne",
    "≈": r"\approx",
    "≡": r"\equiv",
    "±": r"\pm",
    "∓": r"\mp",
    "×": r"\times",
    "·": r"\cdot",
    "÷": r"\div",
    "∞": r"\infty",
    "→": r"\to",
    "⇒": r"\Rightarrow",
    "⇔": r"\Leftrightarrow",
    "∈": r"\in",
    "∉": r"\notin",
    "⊂": r"\subset",
    "⊆": r"\subseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "∂": r"\partial",
    "∇": r"\nabla",
    "…": r"\dots",
    "⋯": r"\cdots",
    "ℓ": r"\ell",
}

# Standard math functions in LaTeX
STANDARD_FUNCTIONS = {
    "sin",
    "cos",
    "tan",
    "cot",
    "sec",
    "csc",
    "arcsin",
    "arccos",
    "arctan",
    "sinh",
    "cosh",
    "tanh",
    "exp",
    "ln",
    "log",
    "lg",
    "lim",
    "max",
    "min",
    "inf",
    "sup",
    "det",
    "dim",
    "gcd",
    "hom",
    "ker",
    "deg",
    "arg",
}


def _strip_ns(tag: str) -> str:
    """Strip XML namespace prefix from tag name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def omml_to_latex(element: ET.Element | str) -> str:
    """Convert an OMML XML Element or XML string (<m:oMath> or <m:oMathPara>) into KaTeX LaTeX.

    Args:
        element: An xml.etree.ElementTree.Element or raw XML string containing OMML math.

    Returns:
        A clean KaTeX/LaTeX math string (without $$ wrapping).
    """
    if isinstance(element, str):
        try:
            root = ET.fromstring(element)
        except Exception:
            return element.strip()
    else:
        root = element

    tag = _strip_ns(root.tag)
    if tag == "oMathPara":
        # oMathPara contains one or more oMath elements
        math_nodes = [n for n in root if _strip_ns(n.tag) == "oMath"]
        if math_nodes:
            return " ".join(omml_to_latex(m) for m in math_nodes)
        return _convert_children(root)
    elif tag == "oMath":
        return _convert_children(root).strip()
    else:
        # Search for any oMath children inside
        omaths = root.findall(f".//{{{OMML_NS}}}oMath")
        if omaths:
            return " ".join(omml_to_latex(m) for m in omaths).strip()
        return _convert_node(root).strip()


def _convert_children(node: ET.Element) -> str:
    """Convert all direct child elements of a node and concatenate results."""
    parts: list[str] = []
    for child in node:
        c_tag = _strip_ns(child.tag)
        if c_tag in ("oMathParaPr", "oMathPr", "rPr", "ctrlPr"):
            continue
        res = _convert_node(child)
        if res:
            parts.append(res)
    return "".join(parts)


def _convert_node(node: ET.Element) -> str:
    """Convert a single OMML XML node into its LaTeX equivalent."""
    tag = _strip_ns(node.tag)

    # 1. Math Run (<m:r>)
    if tag == "r":
        t_nodes = [c for c in node if _strip_ns(c.tag) == "t"]
        text = "".join(t.text or "" for t in t_nodes)
        return _format_math_text(text)

    # 2. Plain Text node (<m:t>)
    if tag == "t":
        return _format_math_text(node.text or "")

    # 3. Fraction (<m:f>)
    if tag == "f":
        num_node = node.find(f"{{{OMML_NS}}}num")
        den_node = node.find(f"{{{OMML_NS}}}den")
        num_latex = _convert_children(num_node) if num_node is not None else ""
        den_latex = _convert_children(den_node) if den_node is not None else ""
        return f"\\frac{{{num_latex}}}{{{den_latex}}}"

    # 4. Radical / Square root (<m:rad>)
    if tag == "rad":
        deg_node = node.find(f"{{{OMML_NS}}}deg")
        e_node = node.find(f"{{{OMML_NS}}}e")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        deg_latex = _convert_children(deg_node).strip() if deg_node is not None else ""
        if deg_latex:
            return f"\\sqrt[{deg_latex}]{{{e_latex}}}"
        return f"\\sqrt{{{e_latex}}}"

    # 5. Subscript (<m:sSub>)
    if tag == "sSub":
        e_node = node.find(f"{{{OMML_NS}}}e")
        sub_node = node.find(f"{{{OMML_NS}}}sub")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        sub_latex = _convert_children(sub_node) if sub_node is not None else ""
        return f"{{{e_latex}}}_{{{sub_latex}}}"

    # 6. Superscript (<m:sSup>)
    if tag == "sSup":
        e_node = node.find(f"{{{OMML_NS}}}e")
        sup_node = node.find(f"{{{OMML_NS}}}sup")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        sup_latex = _convert_children(sup_node) if sup_node is not None else ""
        return f"{{{e_latex}}}^{{{sup_latex}}}"

    # 7. Subscript & Superscript (<m:sSubSup>)
    if tag == "sSubSup":
        e_node = node.find(f"{{{OMML_NS}}}e")
        sub_node = node.find(f"{{{OMML_NS}}}sub")
        sup_node = node.find(f"{{{OMML_NS}}}sup")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        sub_latex = _convert_children(sub_node) if sub_node is not None else ""
        sup_latex = _convert_children(sup_node) if sup_node is not None else ""
        return f"{{{e_latex}}}_{{{sub_latex}}}^{{{sup_latex}}}"

    # 8. Delimiter / Brackets (<m:d>)
    if tag == "d":
        d_pr = node.find(f"{{{OMML_NS}}}dPr")
        beg_chr = "("
        end_chr = ")"
        if d_pr is not None:
            beg_el = d_pr.find(f"{{{OMML_NS}}}begChr")
            end_el = d_pr.find(f"{{{OMML_NS}}}endChr")
            if beg_el is not None and "val" in beg_el.attrib:
                beg_chr = beg_el.attrib["val"]
            if end_el is not None and "val" in end_el.attrib:
                end_chr = end_el.attrib["val"]

        e_nodes = [c for c in node if _strip_ns(c.tag) == "e"]
        e_latex = " ".join(_convert_children(e) for e in e_nodes)

        l_del = _format_delimiter(beg_chr, is_left=True)
        r_del = _format_delimiter(end_chr, is_left=False)
        return f"{l_del}{e_latex}{r_del}"

    # 9. N-ary Operator: Sum, Integral, Product (<m:nary>)
    if tag == "nary":
        nary_pr = node.find(f"{{{OMML_NS}}}naryPr")
        op_chr = "∑"
        if nary_pr is not None:
            chr_el = nary_pr.find(f"{{{OMML_NS}}}chr")
            if chr_el is not None and "val" in chr_el.attrib:
                op_chr = chr_el.attrib["val"]

        op_latex = "\\sum"
        if op_chr in ("∫", "integral"):
            op_latex = "\\int"
        elif op_chr in ("∏", "product"):
            op_latex = "\\prod"
        elif op_chr in ("⋃", "union"):
            op_latex = "\\bigcup"
        elif op_chr in ("⋂", "intersection"):
            op_latex = "\\bigcap"

        sub_node = node.find(f"{{{OMML_NS}}}sub")
        sup_node = node.find(f"{{{OMML_NS}}}sup")
        e_node = node.find(f"{{{OMML_NS}}}e")

        sub_latex = _convert_children(sub_node) if sub_node is not None else ""
        sup_latex = _convert_children(sup_node) if sup_node is not None else ""
        e_latex = _convert_children(e_node) if e_node is not None else ""

        limits = ""
        if sub_latex:
            limits += f"_{{{sub_latex}}}"
        if sup_latex:
            limits += f"^{{{sup_latex}}}"

        return f"{op_latex}{limits} {e_latex}"

    # 10. Function (<m:func>)
    if tag == "func":
        fname_node = node.find(f"{{{OMML_NS}}}fName")
        e_node = node.find(f"{{{OMML_NS}}}e")
        fname_latex = _convert_children(fname_node).strip() if fname_node is not None else ""
        e_latex = _convert_children(e_node) if e_node is not None else ""

        if fname_latex in STANDARD_FUNCTIONS:
            return f"\\{fname_latex}{{{e_latex}}}"
        return f"\\operatorname{{{fname_latex}}}{{{e_latex}}}"

    # 11. Overbar / Underbar (<m:bar>)
    if tag == "bar":
        e_node = node.find(f"{{{OMML_NS}}}e")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        return f"\\bar{{{e_latex}}}"

    # 12. Accent (<m:acc>)
    if tag == "acc":
        acc_pr = node.find(f"{{{OMML_NS}}}accPr")
        acc_chr = "^"
        if acc_pr is not None:
            chr_el = acc_pr.find(f"{{{OMML_NS}}}chr")
            if chr_el is not None and "val" in chr_el.attrib:
                acc_chr = chr_el.attrib["val"]
        acc_cmd = ACCENT_MAP.get(acc_chr, r"\hat")
        e_node = node.find(f"{{{OMML_NS}}}e")
        e_latex = _convert_children(e_node) if e_node is not None else ""
        return f"{acc_cmd}{{{e_latex}}}"

    # 13. Matrix (<m:m>)
    if tag == "m":
        rows: list[str] = []
        for mr in node.findall(f"{{{OMML_NS}}}mr"):
            row_cells = [_convert_children(e) for e in mr.findall(f"{{{OMML_NS}}}e")]
            rows.append(" & ".join(row_cells))
        matrix_body = " \\\\ ".join(rows)
        return f"\\begin{{matrix}} {matrix_body} \\end{{matrix}}"

    # 14. Boxed / Group (<m:box>, <m:borderBox>, <m:groupChr>)
    if tag in ("box", "e"):
        return _convert_children(node)
    if tag == "borderBox":
        return f"\\boxed{{{_convert_children(node)}}}"

    # Default fallback: convert children
    return _convert_children(node)


def _format_math_text(text: str) -> str:
    """Format raw math text string into KaTeX-safe tokens."""
    if not text:
        return ""

    out = text
    # Replace Greek letters
    for g_char, g_latex in GREEK_MAP.items():
        out = out.replace(g_char, f"{g_latex} ")

    # Replace Math operators
    for op_char, op_latex in MATH_SYMBOLS_MAP.items():
        out = out.replace(op_char, f" {op_latex} ")

    # Normalize double spaces
    out = re.sub(r"\s+", " ", out)
    return out


def _format_delimiter(del_chr: str, is_left: bool) -> str:
    """Format matching delimiter characters with \\left or \\right."""
    if not del_chr:
        return r"\left." if is_left else r"\right."

    del_map = {
        "(": r"\left(" if is_left else r"\right(",
        ")": r"\left)" if is_left else r"\right)",
        "[": r"\left[" if is_left else r"\right[",
        "]": r"\left]" if is_left else r"\right]",
        "{": r"\left\{" if is_left else r"\right\{",
        "}": r"\left\}" if is_left else r"\right\}",
        "|": r"\left|" if is_left else r"\right|",
        "‖": r"\left\|" if is_left else r"\right\|",
    }
    return del_map.get(del_chr, del_chr)
