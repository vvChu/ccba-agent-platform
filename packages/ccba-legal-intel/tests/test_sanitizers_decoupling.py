# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests verifying sanitizers decoupling and zero circular dependency."""

from __future__ import annotations

from unittest.mock import MagicMock

from ccba_legal.converters.standard.sanitizers import (
    normalize_degrees_and_angles,
    normalize_formula_equations,
    render_paragraph_with_runs,
    sanitize_prose_greeks_and_variables,
)


def test_zero_circular_imports():
    """Verify that strategy and table_handler import cleanly without circular dependency."""
    import ccba_legal.converters.standard.handlers.table_handler as th
    import ccba_legal.converters.standard.strategy as st

    assert hasattr(st, "render_paragraph_with_runs")
    assert hasattr(th, "render_table_markdown")
    assert hasattr(th, "handle_table_block")


def test_render_paragraph_with_runs_footnote_callout():
    """Verify that footnote callouts in superscript runs render as HTML <sup>(*)</sup>."""
    mock_p = MagicMock()

    r1 = MagicMock()
    r1._r.xml = "<w:r><w:t>3,10</w:t></w:r>"
    r1.text = "3,10"
    r1.font.subscript = False
    r1.font.superscript = False

    r2 = MagicMock()
    r2._r.xml = '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:t>(*)</w:t></w:r>'
    r2.text = "(*)"
    r2.font.subscript = False
    r2.font.superscript = True

    mock_p.runs = [r1, r2]
    res = render_paragraph_with_runs(mock_p)
    assert res == "3,10<sup>(*)</sup>"


def test_normalize_degrees_and_angles():
    """Verify that Word superscript '0' or 'o' for degrees is normalized to Unicode ° and °C."""
    raw_c1 = "nhiệt độ không vượt quá 49$^{0}$ C;"
    raw_c2 = "nhiệt độ không vượt quá 43$^{0}$ C;"
    raw_deg = "biên độ dao động trong khoảng ± 22,5$^{0}$ so với"

    assert normalize_degrees_and_angles(raw_c1) == "nhiệt độ không vượt quá 49 °C;"
    assert normalize_degrees_and_angles(raw_c2) == "nhiệt độ không vượt quá 43 °C;"
    assert normalize_degrees_and_angles(raw_deg) == "biên độ dao động trong khoảng ± 22,5° so với"


def test_normalize_formula_equations():
    """Verify that technical formulas like Emin are properly wrapped in KaTeX."""
    raw_eq = "Emin = 5,9 + 5,3$V^{0,5}$ (W)"
    norm = normalize_formula_equations(raw_eq)
    assert norm == "$E_{\\min} = 5,9 + 5,3V^{0,5}$ (W)"


def test_sanitize_prose_greeks_and_variables():
    """Verify that Greek characters and subscripted standard variables convert to KaTeX."""
    prose = "Hệ số dẫn nhiệt λ của vật liệu và áp lực gió W0 được tính theo công thức."
    res = sanitize_prose_greeks_and_variables(prose)
    assert "$\\lambda$" in res
    assert "$W_{0}$" in res
