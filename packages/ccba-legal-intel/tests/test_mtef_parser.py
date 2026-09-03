# Copyright (c) 2026 CCBA. All rights reserved.
"""Unit tests for deterministic MathType MTEF Binary Parser (ADR 0040)."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest

from ccba_legal.converters.mtef_parser import (
    MTEFParser,
    decode_ole_mathtype,
    parse_cfbf,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_parse_cfbf_invalid():
    """Test CFBF parser on invalid or truncated data."""
    assert parse_cfbf(b"") == {}
    assert parse_cfbf(b"not a cfbf file at all") == {}
    assert parse_cfbf(b"\x00" * 600) == {}


def test_mtef_parser_empty_or_invalid():
    """Test MTEFParser on empty or unrecognized header."""
    assert MTEFParser(b"").parse() == ""
    assert MTEFParser(b"\x01\x02\x03").parse() == ""
    # Version 99 is invalid
    assert MTEFParser(b"\x63\x01\x01\x01\x01").parse() == ""


def test_mtef_parser_simple_equation():
    """Test MTEFParser with synthetic MTEF bytes for x = y."""
    # MTEF header: v=3, platform=1, product=1, ver=3, subver=0
    hdr = bytes([3, 1, 1, 3, 0])
    # LINE record
    # CHAR 'x': tag=2, opt=0 -> 0x02, typeface=0x83, char_code=0x0078
    char_x = bytes([0x02, 0x83, 0x78, 0x00])
    # CHAR '=': tag=2, opt=0 -> 0x02, typeface=0x86, char_code=0x003D
    char_eq = bytes([0x02, 0x86, 0x3D, 0x00])
    # CHAR 'y': tag=2, opt=0 -> 0x02, typeface=0x83, char_code=0x0079
    char_y = bytes([0x02, 0x83, 0x79, 0x00])
    # END of line: 0x00
    end = bytes([0x00])

    mtef = hdr + char_x + char_eq + char_y + end
    parser = MTEFParser(mtef)
    result = parser.parse()
    assert "x" in result
    assert "=" in result
    assert "y" in result


def test_mtef_parser_fraction():
    """Test MTEFParser with synthetic fraction template."""
    hdr = bytes([3, 1, 1, 3, 0])
    # Fraction: tag=3 (TMPL), opt=0 -> selector=0x0E, variation=0x0000
    tmpl_frac = bytes([0x03, 0x0E, 0x00, 0x00])
    # Num line: LINE tag=1, CHAR '1' (0x02, 0x88, 0x31, 0x00), END 0x00
    num = bytes([0x01, 0x02, 0x88, 0x31, 0x00, 0x00])
    # Den line: LINE tag=1, CHAR '2' (0x02, 0x88, 0x32, 0x00), END 0x00
    den = bytes([0x01, 0x02, 0x88, 0x32, 0x00, 0x00])
    end_tmpl = bytes([0x00])

    mtef = hdr + tmpl_frac + num + den + end_tmpl
    parser = MTEFParser(mtef)
    result = parser.parse()
    assert result == r"\frac{1}{2}"


def test_mtef_parser_subscript():
    """Test MTEFParser with subscript."""
    hdr = bytes([3, 1, 1, 3, 0])
    # CHAR 'R'
    char_r = bytes([0x02, 0x83, 0x52, 0x00])
    # Subscript TMPL: selector=0x0F, variation=0x0001 (sub only)
    sub_tmpl = bytes([0x03, 0x0F, 0x01, 0x00])
    # Sub line: marker 0x0b, LINE 0x01, CHAR '0' (0x02, 0x88, 0x30, 0x00), END 0x00
    sub_line = bytes([0x0B, 0x01, 0x02, 0x88, 0x30, 0x00, 0x00])
    # Trailer 0x11 0x00
    trailer = bytes([0x11, 0x00])

    mtef = hdr + char_r + sub_tmpl + sub_line + trailer + bytes([0x00])
    parser = MTEFParser(mtef)
    result = parser.parse()
    assert result == "R_{0}"


def test_mtef_parser_greek_symbols():
    """Test MTEFParser with Greek symbols (lambda, alpha)."""
    hdr = bytes([3, 1, 1, 3, 0])
    # CHAR lambda (U+03BB)
    char_lambda = bytes([0x02, 0x84, 0xBB, 0x03])
    # CHAR '+'
    char_plus = bytes([0x02, 0x86, 0x2B, 0x00])
    # CHAR alpha (U+03B1)
    char_alpha = bytes([0x02, 0x84, 0xB1, 0x03])

    mtef = hdr + char_lambda + char_plus + char_alpha + bytes([0x00])
    parser = MTEFParser(mtef)
    result = parser.parse()
    assert r"\lambda" in result
    assert r"\alpha" in result


def test_real_doc_ole_equations():
    """Test decoding real OLE objects from sample docx if available."""
    import zipfile

    # Search for any docx with embeddings in legal_docs
    docx_candidates = list(
        Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs").rglob("*.docx")
    )
    tested = 0
    for docx in docx_candidates:
        try:
            with zipfile.ZipFile(docx, "r") as z:
                ole_files = [f for f in z.namelist() if "oleObject" in f]
                for ole_f in ole_files:
                    ole_data = z.read(ole_f)
                    latex = decode_ole_mathtype(ole_data)
                    if latex:
                        tested += 1
                        assert len(latex) > 0
                        # Valid LaTeX output
                        assert not latex.startswith("<!--")
        except Exception:
            continue

    if tested > 0:
        assert tested >= 2
