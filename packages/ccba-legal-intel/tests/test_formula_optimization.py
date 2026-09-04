# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests verifying formula optimization, single-pass regex, caching, and zero diff."""

from __future__ import annotations

import logging
from pathlib import Path

from ccba_legal.converters.omml import _format_math_text
from ccba_legal.converters.technical_formulas import (
    FORMULAS_MAP,
    GREEK_MAP,
    INLINE_SYMBOLS_MAP,
    MATH_OPERATORS_MAP,
    load_bundle_formula_overrides,
)


def test_backward_compatibility_exports():
    """Verify that all public dictionary symbols remain importable."""
    assert isinstance(GREEK_MAP, dict)
    assert "α" in GREEK_MAP
    assert isinstance(INLINE_SYMBOLS_MAP, dict)
    assert "rId18" in INLINE_SYMBOLS_MAP
    assert isinstance(MATH_OPERATORS_MAP, dict)
    assert "≤" in MATH_OPERATORS_MAP
    assert isinstance(FORMULAS_MAP, dict)


def test_omml_single_pass_equivalence():
    """Verify that _format_math_text accurately replaces Greek letters and operators with single-pass regex."""
    # Test cases with combinations of Greek and math symbols
    test_inputs = [
        ("α + β ≤ γ", r"\alpha + \beta \le \gamma"),
        ("λ · μ ≥ ν", r"\lambda \cdot \mu \ge \nu"),
        ("Δ = b^2 - 4ac", r"\Delta = b^2 - 4ac"),
        ("x ∈ A ∪ B", r"x \in A \cup B"),
        ("f(x) → ∞", r"f(x) \to \infty"),
        ("∂y / ∂x ≠ 0", r"\partial y / \partial x \ne 0"),
        ("± 22,5", r"\pm 22,5"),
        ("", ""),
    ]

    for inp, expected in test_inputs:
        res = _format_math_text(inp)
        assert res.strip() == expected.strip(), (
            f"Mismatch for '{inp}': got '{res}', expected '{expected}'"
        )


def test_bundle_formula_overrides_caching(tmp_path: Path):
    """Verify that load_bundle_formula_overrides utilizes in-memory LRU caching."""
    yaml_content = """
1:
  formula_id: "F_TEST_1"
  latex: "a + b = c"
2:
  formula_id: "F_TEST_2"
  latex: "x^2 + y^2 = z^2"
"""
    override_file = tmp_path / "formulas_override.yaml"
    override_file.write_text(yaml_content, encoding="utf-8")

    # First call - loads from disk
    res1 = load_bundle_formula_overrides(tmp_path)
    assert len(res1) == 2
    assert res1["1"] == ("F_TEST_1", "a + b = c")

    # Second call - served from cache
    res2 = load_bundle_formula_overrides(tmp_path)
    assert res1 is res2  # Same cached dictionary object reference


def test_bundle_formula_overrides_yaml_error_handling(tmp_path: Path, caplog):
    """Verify that malformed YAML files log a warning and return an empty dict cleanly."""
    malformed_yaml = """
invalid: [this is unclosed yaml
"""
    override_file = tmp_path / "formulas_override.yaml"
    override_file.write_text(malformed_yaml, encoding="utf-8")

    with caplog.at_level(logging.WARNING):
        res = load_bundle_formula_overrides(tmp_path)
        assert res == {}
        assert any("Cú pháp YAML không hợp lệ" in record.message for record in caplog.records)
