# Copyright (c) 2026 CCBA. All rights reserved.
"""Pure text and formula sanitization functions for legal document converters."""

from __future__ import annotations

import re

from ccba_legal.converters.technical_formulas import GREEK_MAP


def sanitize_prose_greeks_and_variables(text: str) -> str:
    """Sanitize Vietnamese prose text by converting raw Greek letters and subscripts into KaTeX math mode."""
    if not text:
        return text

    for g_char, g_latex in GREEK_MAP.items():
        pattern = r"(?<!\$)\b" + g_char + r"([a-zA-Z0-9]+)\b(?!\$)"

        def _sub_greek_sub(m: re.Match[str], gl: str = g_latex) -> str:
            return f"${gl}_{{{m.group(1)}}}$"

        text = re.sub(pattern, _sub_greek_sub, text)
        pattern_alone = r"(?<![\$\w])" + g_char + r"(?![\$\w])"

        def _sub_greek_alone(m: re.Match[str], gl: str = g_latex) -> str:
            return f"${gl}$"

        text = re.sub(pattern_alone, _sub_greek_alone, text)

    for var in [
        "qk,t",
        "Qk,t",
        "qk,qper",
        "Wk",
        "W0",
        "Gk",
        "Qk",
        "QL",
        "Qt",
        "Ad",
        "ze",
        "zs",
        "Gf",
    ]:
        k_var = var.replace(",", "_{").replace("0", "_{0}")
        if "_{" in k_var and not k_var.endswith("}"):
            k_var += "}"
        elif len(var) > 1 and "_" not in k_var:
            k_var = f"{var[0]}_{{{var[1:]}}}"
        text = re.sub(rf"(?<!\$)\b{var}\b(?!\$)", f"${k_var}$", text)

    return text


def heal_orphaned_strains(text: str) -> str:
    """Heal orphaned strain subscripts like $_{b}$, $_{b1}$, $_{s}$ to \\varepsilon."""
    text = re.sub(r"\$(_\{b[0-9]*\})\$", r"$\\varepsilon\1$", text)
    text = re.sub(r"\$(_\{s[0-9]*\})\$", r"$\\varepsilon\1$", text)
    text = re.sub(r"([0-9])\s*≤\s*(_\{[^}]+\})", r"\1 ≤ $\\varepsilon\2$", text)
    text = re.sub(r"([0-9])\s*<=\s*(_\{[^}]+\})", r"\1 <= $\\varepsilon\2$", text)
    return text


def normalize_degrees_and_angles(text: str) -> str:
    """Normalize degrees Celsius and angles from Word superscript '0' or 'o' to Unicode."""
    # e.g. 40$^{0}$ C -> 40 °C, 49$^{0}$ C -> 49 °C
    text = re.sub(r"(\d+(?:[,\.]\d+)?)\s*(?:\$\^\{[0oO]\}\$|<sup>[0oO]</sup>)\s*C\b", r"\1 °C", text)
    # e.g. ± 22,5$^{0}$ -> ± 22,5°
    text = re.sub(r"(\d+(?:[,\.]\d+)?)\s*(?:\$\^\{[0oO]\}\$|<sup>[0oO]</sup>)", r"\1°", text)
    return text


def normalize_formula_equations(text: str) -> str:
    """Normalize specific equations in technical standards (e.g. Emin in QCVN 09 Bảng 2.7)."""
    return re.sub(
        r"\bEmin\s*=\s*([0-9\.,\s\+\-\*\/]+)\$V\^\{([^}]+)\}\$\s*(\([A-Za-z]+\))?",
        r"$E_{\\min} = \1V^{\2}$ \3",
        text,
    )
