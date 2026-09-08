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


def test_parse_word_eq_field():
    """Verify Word EQ field parser handles fractions, dual subscripts, Greek symbols, radicals, and nesting."""
    from ccba_legal.converters.standard.sanitizers.run_renderer import parse_word_eq_field

    assert parse_word_eq_field(r"eq \f(50,Ia)") == r"\frac{50}{I_a}"
    assert parse_word_eq_field(r"EQ \f(S,2)") == r"\frac{S}{2}"
    assert parse_word_eq_field(r"eq \f(Ra,Ia)") == r"\frac{R_a}{I_a}"
    assert parse_word_eq_field(r"eq \f(50,Δn)") == r"\frac{50}{\Delta n}"
    # Nested fractions
    assert parse_word_eq_field(r"eq \f(\f(1,2), 3)") == r"\frac{\frac{1}{2}}{3}"
    # Radicals / square roots / n-th roots
    assert parse_word_eq_field(r"eq \r(50)") == r"\sqrt{50}"
    assert parse_word_eq_field(r"eq \r(3, 8)") == r"\sqrt[3]{8}"
    assert parse_word_eq_field(r"eq \f(1, \r(2))") == r"\frac{1}{\sqrt{2}}"
    # Inequalities and subscripts
    assert parse_word_eq_field(r"eq R\s\do(a) <= \f(50,Ia)") == r"R_{a} \le \frac{50}{I_a}"


def test_state_manager_trong_do_exit_on_lettered_and_vietnamese_d():
    """Verify that StateManager exits IN_TRONG_DO when encountering lettered clauses (b, c, đ)."""
    from ccba_legal.converters.standard.models import HierarchyState
    from ccba_legal.converters.standard.state_manager import (
        HierarchyStateManager,
        LineActionType,
    )

    sm = HierarchyStateManager()
    sm.process_paragraph("trong đó:", "trong đó:")
    assert sm.state == HierarchyState.IN_TRONG_DO

    act1 = sm.process_paragraph("- a là biến số", "- a là biến số")
    assert act1.action_type == LineActionType.EMIT_IN_TRONG_DO

    act2 = sm.process_paragraph("b) Trường hợp tiếp theo:", "b) Trường hợp tiếp theo:")
    assert sm.state == HierarchyState.IN_LETTERED_LIST
    assert act2.action_type == LineActionType.EMIT_LETTERED
    assert act2.letter == "b"

    act3 = sm.process_paragraph("đ) Phải dùng ống riêng:", "đ) Phải dùng ống riêng:")
    assert act3.action_type == LineActionType.EMIT_LETTERED
    assert act3.letter == "đ"


def test_render_paragraph_fld_simple_deduplication():
    """Verify that multiple runs within a single w:fldSimple do not cause duplicate text leakage."""
    mock_p = MagicMock()

    mock_fld = MagicMock()
    mock_fld.get.return_value = r"eq \f(50,Ia)"

    r1 = MagicMock()
    r1._r.xml = "<w:r><w:t>50</w:t></w:r>"
    r1._r.xpath.return_value = [mock_fld]
    r1.text = "50"
    r1.font.subscript = False
    r1.font.superscript = False

    r2 = MagicMock()
    r2._r.xml = "<w:r><w:t>/Ia</w:t></w:r>"
    r2._r.xpath.return_value = [mock_fld]
    r2.text = "/Ia"
    r2.font.subscript = False
    r2.font.superscript = False

    mock_p.runs = [r1, r2]
    res = render_paragraph_with_runs(mock_p)
    assert res == r"$\frac{50}{I_a}$"


def test_render_paragraph_symbol_font_mapping():
    """Verify that Symbol font w:sym elements correctly map to Unicode symbols."""
    mock_p = MagicMock()

    r1 = MagicMock()
    r1._r.xml = '<w:r><w:sym w:font="Symbol" w:char="F0B0"/><w:t>C</w:t></w:r>'
    r1.text = "C"
    r1.font.subscript = False
    r1.font.superscript = False

    r2 = MagicMock()
    r2._r.xml = '<w:r><w:sym w:font="Symbol" w:char="F0B4"/></w:r>'
    r2.text = ""
    r2.font.subscript = False
    r2.font.superscript = False

    mock_p.runs = [r1, r2]
    res = render_paragraph_with_runs(mock_p)
    assert "°" in res
    assert "×" in res


def test_clean_formula_latex_word_eq_and_operators():
    """Verify clean_formula_latex converts Word EQ fractions, radicals, Greek symbols, and <= / >= operators."""
    from ccba_legal.converters.standard.handlers.table_handler import clean_formula_latex

    raw1 = r"R <= eq \f(50,Ia)"
    res1 = clean_formula_latex(raw1)
    assert r"\le" in res1
    assert r"\frac{50}{I_a}" in res1

    raw2 = r"RA x Ia <= 50"
    res2 = clean_formula_latex(raw2)
    assert r"\le" in res2

    raw3 = r"eq \f(50,Δn)"
    res3 = clean_formula_latex(raw3)
    assert r"\frac{50}{\Delta n}" in res3

    raw4 = r"eq \f(1, \r(2))"
    res4 = clean_formula_latex(raw4)
    assert r"\frac{1}{\sqrt{2}}" in res4
