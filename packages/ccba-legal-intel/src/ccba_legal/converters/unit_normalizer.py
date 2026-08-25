"""Unit and Math Normalization Utilities (ADR 0030)."""

from __future__ import annotations

import re


def normalize_units_and_math(t_str: str) -> str:
    """Auto-converts raw unit strings with exponents into proper LaTeX notation."""
    if any(k in t_str for k in ["m2", "m3", "kg/m3", "daN/m2", "kN/m2"]):
        t_str = re.sub(r"\bdaN/m2\b", r"$\\text{daN/m}^2$", t_str)
        t_str = re.sub(r"\bdaN/m3\b", r"$\\text{daN/m}^3$", t_str)
        t_str = re.sub(r"\bkg/m3\b", r"$\\text{kg/m}^3$", t_str)
        t_str = re.sub(r"\bkN/m2\b", r"$\\text{kN/m}^2$", t_str)
        t_str = re.sub(r"\bkN/m3\b", r"$\\text{kN/m}^3$", t_str)
        t_str = re.sub(r"\b(\d+)\s*m2\b", r"$\1\\text{ m}^2$", t_str)
        t_str = re.sub(r"\b(\d+)\s*m3\b", r"$\1\\text{ m}^3$", t_str)
    return t_str


def normalize_clause_numbers(text: str) -> str:
    """Bold all clause numbers (**1.**, **2.**) to prevent CommonMark ordered list indentation."""
    clause_re = re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)")
    processed: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        m = clause_re.match(stripped)
        if m:
            num = m.group(1) or m.group(2)
            rest = m.group(3)
            processed.append(f"**{num}.** {rest}")
        else:
            processed.append(line)
    return "\n".join(processed)


def normalize_docx_markdown(md_text: str) -> str:
    """Normalize raw Mammoth output markdown."""
    md_text = re.sub(r'<a id="[^"]+"></a>', "", md_text)
    return (
        md_text.replace(r"\.", ".")
        .replace(r"\-", "-")
        .replace(r"\_", "_")
        .replace(r"\(", "(")
        .replace(r"\)", ")")
    )
