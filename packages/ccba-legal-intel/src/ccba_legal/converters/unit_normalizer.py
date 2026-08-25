"""Unit and Math Normalization Utilities (ADR 0030)."""

from __future__ import annotations

import re


def normalize_units_and_math(t_str: str) -> str:
    """Auto-converts raw unit strings with exponents into proper LaTeX notation."""
    if "m2" in t_str or "m3" in t_str or "kg/m3" in t_str or "daN/m2" in t_str or "kN/m2" in t_str:
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
    lines = text.splitlines()
    processed: list[str] = []
    clause_re = re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)")
    for line in lines:
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
    md_text = (
        md_text.replace(r"\.", ".")
        .replace(r"\-", "-")
        .replace(r"\_", "_")
        .replace(r"\(", "(")
        .replace(r"\)", ")")
    )
    return md_text


def format_all_qcvn_md_tables(md_path: Path) -> int:
    """Scan and convert table blocks in md_path to 2D GFM Pipe Tables."""
    return 0
