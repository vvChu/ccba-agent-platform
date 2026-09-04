# Copyright (c) 2026 CCBA. All rights reserved.
"""Mathematical constants, Greek maps, and standard formula catalogs (ADR 0030, ADR 0031, ADR 0036)."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

GREEK_MAP: dict[str, str] = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\epsilon",
    "η": r"\eta",
    "θ": r"\theta",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "π": r"\pi",
    "ρ": r"\rho",
    "σ": r"\sigma",
    "τ": r"\tau",
    "φ": r"\varphi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "Δ": r"\Delta",
    "Σ": r"\Sigma",
    "Ω": r"\Omega",
}

INLINE_SYMBOLS_MAP: dict[str, str] = {
    "rId18": r"\ell",
    "rId19": r"\bar{\epsilon}",
    "rId28": r"\bar{b}",
    "rId105": r"\frac{s_w}{h_0}",
    "rId106": r"\frac{s_w}{h_0}",
    "rId107": r"\frac{s_{w,\max}}{h_0}",
    "rId108": r"\frac{s_{w,\max}}{h_0}",
    "rId109": r"\frac{s_{w,\max}}{h_0}",
    "rId110": r"\frac{s_{w,\max}}{h_0}",
    "rId123": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
    "rId124": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
    "rId125": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
    "rId126": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
    "rId127": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
    "rId131": r"\frac{q_{sw,1} Z_1}{R_s A_{s,1}}",
}

MATH_OPERATORS_MAP: dict[str, str] = {
    "≤": r"\le",
    "≥": r"\ge",
    "≠": r"\ne",
    "≈": r"\approx",
    "±": r"\pm",
    "∓": r"\mp",
    "×": r"\times",
    "·": r"\cdot",
    "÷": r"\div",
    "∞": r"\infty",
    "→": r"\to",
    "ℓ": r"\ell",
}

# Retained for 100% backward-compatibility.
# Bundle-specific formula overrides now reside in individual <doc_slug>/formulas_override.yaml (ADR 0036).
FORMULAS_MAP: dict[str, tuple[str, str]] = {}


@lru_cache(maxsize=64)
def _load_bundle_formula_overrides_cached(bundle_dir_str: str) -> dict[str, tuple[str, str]]:
    """Cached internal loader reading bundle-level formulas_override.yaml."""
    override_file = Path(bundle_dir_str) / "formulas_override.yaml"
    if not override_file.is_file():
        return {}

    try:
        data = yaml.safe_load(override_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {}

        res: dict[str, tuple[str, str]] = {}
        for tag, val in data.items():
            str_tag = str(tag)
            if isinstance(val, dict):
                fid = val.get("formula_id", f"F_OVERRIDE_{str_tag.upper()}")
                latex = val.get("latex", "")
                res[str_tag] = (fid, latex)
            elif isinstance(val, tuple) and len(val) == 2:
                res[str_tag] = (str(val[0]), str(val[1]))
            elif isinstance(val, str):
                res[str_tag] = (f"F_OVERRIDE_{str_tag.upper()}", val)
        return res
    except yaml.YAMLError as exc:
        logger.warning("Cú pháp YAML không hợp lệ tại %s: %s", override_file, exc)
        return {}
    except OSError as exc:
        logger.warning("Không thể đọc tệp formula override tại %s: %s", override_file, exc)
        return {}


def load_bundle_formula_overrides(bundle_dir: Path | str) -> dict[str, tuple[str, str]]:
    """Load bundle-level formula overrides from `formulas_override.yaml` with LRU caching."""
    resolved_path = str(Path(bundle_dir).resolve())
    return _load_bundle_formula_overrides_cached(resolved_path)
