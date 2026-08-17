"""Tests for PDF and content utilities."""

from pathlib import Path

import pytest

from mdconverter.core.utils import (
    get_blind_chunks,
    int_to_roman,
    merge_markdown,
    roman_to_int,
    split_pdf,
)


def test_get_blind_chunks():
    """Test generating page ranges."""
    ranges = get_blind_chunks(50, chunk_size=20)
    assert ranges == [(0, 19), (20, 39), (40, 49)]

    ranges = get_blind_chunks(5, chunk_size=10)
    assert ranges == [(0, 4)]

    ranges = get_blind_chunks(0, chunk_size=20)
    assert ranges == []


def test_merge_markdown():
    """Test merging markdown parts."""
    parts = ["# Part 1", "  ", "## Part 2", ""]
    merged = merge_markdown(parts)
    assert merged == "# Part 1\n\n---\n\n## Part 2"

    merged = merge_markdown(parts, separator="***")
    assert merged == "# Part 1***## Part 2"


@pytest.mark.asyncio
async def test_split_pdf(tmp_path: Path):
    """Test splitting a real PDF using pypdf."""
    from pypdf import PdfWriter

    # Create a dummy 5-page PDF
    source_pdf = tmp_path / "source.pdf"
    writer = PdfWriter()
    for _ in range(5):
        writer.add_blank_page(width=72, height=72)
    with open(source_pdf, "wb") as f:
        writer.write(f)

    temp_dir = tmp_path / "chunks"
    ranges = [(0, 1), (2, 4)]  # 2 chunks: pages 1-2 and 3-5

    chunk_paths = split_pdf(source_pdf, ranges, temp_dir)

    assert len(chunk_paths) == 2
    assert chunk_paths[0].exists()
    assert chunk_paths[1].exists()

    # Verify page counts in chunks
    from pypdf import PdfReader

    assert len(PdfReader(chunk_paths[0]).pages) == 2
    assert len(PdfReader(chunk_paths[1]).pages) == 3


def test_roman_conversion():
    """Test roman numeral conversion functions."""
    # Basic values
    assert int_to_roman(1) == "I"
    assert int_to_roman(4) == "IV"
    assert int_to_roman(9) == "IX"
    assert int_to_roman(10) == "X"
    assert int_to_roman(45) == "XLV"
    assert int_to_roman(90) == "XC"
    assert int_to_roman(400) == "CD"
    assert int_to_roman(1994) == "MCMXCIV"
    assert int_to_roman(3000) == "MMM"

    # Case-insensitive parsing and whitespace stripping
    assert roman_to_int("i") == 1
    assert roman_to_int("  X  ") == 10
    assert roman_to_int("mcmxciv") == 1994
    assert roman_to_int("MMM") == 3000

    # Round trip
    for val in range(1, 3001):
        assert roman_to_int(int_to_roman(val)) == val

    # Invalid values
    with pytest.raises(ValueError, match="Invalid Roman numeral character"):
        roman_to_int("ABC")
