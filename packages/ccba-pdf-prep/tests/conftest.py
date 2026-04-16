"""Shared test fixtures for ccba-pdf-prep tests."""

from pathlib import Path

import fitz  # PyMuPDF
import pytest
from pypdf import PdfWriter


@pytest.fixture
def tmp_pdf_text(tmp_path: Path) -> Path:
    """Create a small text-rich PDF (3 pages, A4 size)."""
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=595, height=842)  # A4 in points
        text = f"Page {i + 1}\n" + ("Lorem ipsum dolor sit amet. " * 20)
        page.insert_text((72, 72), text, fontsize=11)
    path = tmp_path / "text_doc.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def tmp_pdf_drawing(tmp_path: Path) -> Path:
    """Create a single-page oversized PDF simulating an A1 drawing."""
    doc = fitz.open()
    # A1 in points: 841mm × 594mm → 2384 × 1684 pts
    page = doc.new_page(width=2384, height=1684)
    page.insert_text((100, 100), "DRAWING TITLE BLOCK", fontsize=14)
    # Draw some lines to simulate drawing content
    shape = page.new_shape()
    shape.draw_line(fitz.Point(200, 200), fitz.Point(2200, 200))
    shape.draw_line(fitz.Point(200, 200), fitz.Point(200, 1500))
    shape.draw_rect(fitz.Rect(1800, 1200, 2300, 1600))  # Title block area
    shape.finish(color=(0, 0, 0), width=1)
    shape.commit()
    path = tmp_path / "drawing.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def tmp_pdf_scan(tmp_path: Path) -> Path:
    """Create a PDF that looks like a scan (minimal text, has images)."""
    doc = fitz.open()
    for _ in range(2):
        page = doc.new_page(width=595, height=842)
        # Insert minimal text (below threshold of 50 chars)
        page.insert_text((72, 72), "Scan", fontsize=11)
    path = tmp_path / "scan_doc.pdf"
    doc.save(str(path))
    doc.close()
    return path


@pytest.fixture
def tmp_pdf_large(tmp_path: Path) -> Path:
    """Create a 25-page text PDF for chunking tests."""
    writer = PdfWriter()
    for _ in range(25):
        writer.add_blank_page(width=595, height=842)
    path = tmp_path / "large_doc.pdf"
    with open(path, "wb") as f:
        writer.write(f)
    return path
