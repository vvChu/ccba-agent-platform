"""Unit tests verifying PDF manipulation operations (merge, split, extract text)."""

from __future__ import annotations

from pathlib import Path

import pytest
from pypdf import PdfReader

from ccba_pdf_prep.manipulation import (
    extract_pdf_pages_stream,
    extract_text_from_pdf,
    merge_pdfs,
    parse_pages,
    split_pdf_pages,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def _make_dummy_pdf(path: Path, num_pages: int, text_prefix: str = "Page") -> Path:
    """Helper to create a simple PDF with specified number of pages."""
    import fitz

    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)
        page.insert_text((72, 72), f"{text_prefix} {i + 1}", fontsize=12)
    doc.save(str(path))
    doc.close()
    return path


def test_parse_pages_valid():
    """Test parsing various valid page string formats."""
    assert parse_pages("1-3,5") == [0, 1, 2, 4]
    assert parse_pages(" 2 , 4 - 6 , 8 ") == [1, 3, 4, 5, 7]
    assert parse_pages("1") == [0]
    assert parse_pages("") == []
    assert parse_pages("   ") == []


def test_parse_pages_invalid():
    """Test parse_pages validation on erroneous inputs."""
    with pytest.raises(ValueError):
        parse_pages("5-2")
    with pytest.raises(ValueError):
        parse_pages("0")
    with pytest.raises(ValueError):
        parse_pages("abc")


def test_merge_pdfs(tmp_path: Path):
    """Test merging multiple PDF files into one."""
    pdf1 = _make_dummy_pdf(tmp_path / "doc1.pdf", num_pages=2, text_prefix="Doc1-P")
    pdf2 = _make_dummy_pdf(tmp_path / "doc2.pdf", num_pages=3, text_prefix="Doc2-P")
    out_pdf = tmp_path / "merged.pdf"

    res = merge_pdfs([pdf1, pdf2], out_pdf)
    assert res == out_pdf
    assert out_pdf.exists()

    reader = PdfReader(str(out_pdf))
    assert len(reader.pages) == 5


def test_merge_pdfs_empty_and_missing(tmp_path: Path):
    """Test merge_pdfs failure modes."""
    with pytest.raises(ValueError):
        merge_pdfs([], tmp_path / "out.pdf")

    with pytest.raises(FileNotFoundError):
        merge_pdfs([tmp_path / "missing1.pdf", tmp_path / "missing2.pdf"], tmp_path / "out.pdf")


def test_split_pdf_pages_str(tmp_path: Path):
    """Test splitting PDF pages using a range string."""
    src_pdf = _make_dummy_pdf(tmp_path / "src.pdf", num_pages=5)
    out_pdf = tmp_path / "split.pdf"

    res = split_pdf_pages(src_pdf, "1,3-4", out_pdf)
    assert res == out_pdf
    assert out_pdf.exists()

    reader = PdfReader(str(out_pdf))
    assert len(reader.pages) == 3


def test_split_pdf_pages_seq(tmp_path: Path):
    """Test splitting PDF pages using a sequence of ints."""
    src_pdf = _make_dummy_pdf(tmp_path / "src.pdf", num_pages=4)
    out_pdf = tmp_path / "split_seq.pdf"

    res = split_pdf_pages(src_pdf, [0, 2], out_pdf)
    assert res == out_pdf

    reader = PdfReader(str(out_pdf))
    assert len(reader.pages) == 2


def test_split_pdf_pages_invalid(tmp_path: Path):
    """Test split_pdf_pages when input is missing or page list has no valid pages."""
    with pytest.raises(FileNotFoundError):
        split_pdf_pages(tmp_path / "non_existent.pdf", "1-2", tmp_path / "out.pdf")

    src_pdf = _make_dummy_pdf(tmp_path / "src.pdf", num_pages=2)
    with pytest.raises(ValueError):
        split_pdf_pages(src_pdf, [10, 11], tmp_path / "out.pdf")


def test_extract_text_from_pdf(tmp_path: Path):
    """Test extracting text from PDF with and without output file."""
    src_pdf = _make_dummy_pdf(
        tmp_path / "text_sample.pdf", num_pages=2, text_prefix="Hello Section"
    )
    out_txt = tmp_path / "extracted.txt"

    text = extract_text_from_pdf(src_pdf, out_txt)
    assert "Hello Section 1" in text
    assert "Hello Section 2" in text

    assert out_txt.exists()
    saved_text = out_txt.read_text(encoding="utf-8")
    assert saved_text == text


def test_extract_text_missing_file(tmp_path: Path):
    """Test extract_text_from_pdf raises FileNotFoundError on missing file."""
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(tmp_path / "not_found.pdf")


def test_extract_pdf_pages_stream_from_path(tmp_path: Path):
    """Test extracting pages into stream from file path."""
    import io

    src_pdf = _make_dummy_pdf(tmp_path / "stream_src.pdf", num_pages=5)
    pdf_bytes = extract_pdf_pages_stream(src_pdf, "1,3,5")
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 3


def test_extract_pdf_pages_stream_from_bytes(tmp_path: Path):
    """Test extracting pages into stream from in-memory raw bytes."""
    import io

    src_pdf = _make_dummy_pdf(tmp_path / "bytes_src.pdf", num_pages=4)
    raw = src_pdf.read_bytes()
    pdf_bytes = extract_pdf_pages_stream(raw, [0, 2])
    assert isinstance(pdf_bytes, bytes)

    reader = PdfReader(io.BytesIO(pdf_bytes))
    assert len(reader.pages) == 2


def test_extract_pdf_pages_stream_invalid(tmp_path: Path):
    """Test extract_pdf_pages_stream failure on missing file or invalid pages."""
    with pytest.raises(FileNotFoundError):
        extract_pdf_pages_stream(tmp_path / "non_existent.pdf", "1-2")

    src_pdf = _make_dummy_pdf(tmp_path / "src.pdf", num_pages=2)
    with pytest.raises(ValueError):
        extract_pdf_pages_stream(src_pdf, [10, 11])
