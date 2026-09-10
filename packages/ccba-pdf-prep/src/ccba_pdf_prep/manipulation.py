"""manipulation.py - PDF manipulation tools: merge, split pages, and text extraction.

Provides reusable PDF manipulation operations (ADR-0035, ADR-0057):
1. parse_pages: Parses page string specifications ('1-3,5') to 0-indexed indices.
2. merge_pdfs: Concatenates multiple PDF files into one.
3. split_pdf_pages: Extracts a subset of pages into a new PDF.
4. extract_text_from_pdf: Extracts text content across all pages.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from pathlib import Path

from pypdf import PdfReader, PdfWriter

logger = logging.getLogger(__name__)


def parse_pages(pages_str: str) -> list[int]:
    """Parse pages specification string like '1-3,5' into 0-indexed page numbers.

    Args:
        pages_str: String with comma-separated page numbers or ranges (1-indexed).

    Returns:
        List of 0-indexed integer page numbers.

    Raises:
        ValueError: If pages_str contains invalid format.
    """
    if not pages_str or not pages_str.strip():
        return []

    pages: list[int] = []
    for part in pages_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start_str, end_str = part.split("-", 1)
            start = int(start_str.strip())
            end = int(end_str.strip())
            if start <= 0 or end <= 0 or start > end:
                raise ValueError(f"Invalid page range: '{part}'")
            pages.extend(range(start - 1, end))
        else:
            p = int(part)
            if p <= 0:
                raise ValueError(f"Page number must be positive: {p}")
            pages.append(p - 1)
    return pages


def merge_pdfs(inputs: Sequence[str | Path], output: str | Path) -> Path:
    """Merge multiple PDF files into a single output file.

    Args:
        inputs: Sequence of file paths to input PDFs.
        output: Destination file path for merged PDF.

    Returns:
        Path to the merged PDF.

    Raises:
        FileNotFoundError: If any input PDF file does not exist.
        ValueError: If inputs list is empty.
    """
    if not inputs:
        raise ValueError("At least one input PDF file is required to merge")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    writer = PdfWriter()
    for input_path in inputs:
        p = Path(input_path)
        if not p.exists():
            raise FileNotFoundError(f"Input PDF not found: {p}")
        writer.append(str(p))

    with open(out_path, "wb") as f:
        writer.write(f)

    logger.info("Successfully merged %d PDFs into %s", len(inputs), out_path)
    return out_path


def split_pdf_pages(
    input_pdf: str | Path,
    pages: str | Sequence[int],
    output: str | Path,
) -> Path:
    """Extract specified pages from a PDF file into a new output file.

    Args:
        input_pdf: Path to the input PDF file.
        pages: Either a string specification ('1-3,5') or a sequence of 0-indexed page indices.
        output: Destination file path for the split PDF.

    Returns:
        Path to the generated PDF.

    Raises:
        FileNotFoundError: If input_pdf does not exist.
        ValueError: If no valid pages are found.
    """
    src_path = Path(input_pdf)
    if not src_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {src_path}")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(pages, str):
        page_indices = parse_pages(pages)
    else:
        page_indices = list(pages)

    reader = PdfReader(str(src_path))
    writer = PdfWriter()

    total_pages = len(reader.pages)
    valid_count = 0
    for p in page_indices:
        if 0 <= p < total_pages:
            writer.add_page(reader.pages[p])
            valid_count += 1
        else:
            logger.warning("Page index %d out of bounds (0-%d), skipping", p, total_pages - 1)

    if valid_count == 0:
        raise ValueError(f"No valid pages found to extract from {src_path}")

    with open(out_path, "wb") as f:
        writer.write(f)

    logger.info("Successfully extracted %d pages into %s", valid_count, out_path)
    return out_path


def extract_text_from_pdf(input_pdf: str | Path, output: str | Path | None = None) -> str:
    """Extract text content from all pages of a PDF file.

    Args:
        input_pdf: Path to input PDF file.
        output: Optional path to save extracted text as a UTF-8 text file.

    Returns:
        Extracted text as a string.

    Raises:
        FileNotFoundError: If input_pdf does not exist.
    """
    src_path = Path(input_pdf)
    if not src_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {src_path}")

    reader = PdfReader(str(src_path))
    text_parts: list[str] = []

    for page in reader.pages:
        t = page.extract_text()
        if t:
            text_parts.append(t)

    full_text = "\n".join(text_parts)

    if output is not None:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(full_text, encoding="utf-8")
        logger.info("Extracted text saved to %s", out_path)

    return full_text


def split_pdf_chunks(
    source: str | Path,
    page_ranges: Sequence[tuple[int, int]],
    output_temp_dir: str | Path,
) -> list[Path]:
    """Split PDF into multiple chunk files based on page ranges.

    Args:
        source: Path to source PDF file.
        page_ranges: Sequence of (start_page, end_page) 0-indexed inclusive tuples.
        output_temp_dir: Directory where chunk files should be written.

    Returns:
        List of generated chunk PDF file paths.
    """
    src_path = Path(source)
    if not src_path.exists():
        raise FileNotFoundError(f"Source PDF not found: {src_path}")
    out_dir = Path(output_temp_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(src_path))
    chunk_paths: list[Path] = []

    for i, (start, end) in enumerate(page_ranges):
        start = max(0, start)
        end = min(len(reader.pages) - 1, end)
        if start > end:
            continue

        writer = PdfWriter()
        for page_num in range(start, end + 1):
            writer.add_page(reader.pages[page_num])

        chunk_path = out_dir / f"{src_path.stem}_part{i + 1}.pdf"
        with open(chunk_path, "wb") as f:
            writer.write(f)
        chunk_paths.append(chunk_path)
    return chunk_paths


def split_pdf(
    source: str | Path,
    pages_or_ranges: str | Sequence[int] | Sequence[tuple[int, int]],
    output: str | Path,
) -> Path | list[Path]:
    """Unified PDF splitter supporting both single page-list extraction and chunk ranges.

    If pages_or_ranges is a sequence of (start, end) tuples, delegates to split_pdf_chunks.
    Otherwise delegates to split_pdf_pages.
    """
    if (
        pages_or_ranges
        and isinstance(pages_or_ranges, (list, tuple))
        and isinstance(pages_or_ranges[0], tuple)
    ):
        return split_pdf_chunks(source, pages_or_ranges, output)  # type: ignore[arg-type]
    elif not pages_or_ranges and isinstance(pages_or_ranges, (list, tuple)):
        return split_pdf_chunks(source, [], output)
    return split_pdf_pages(source, pages_or_ranges, output)  # type: ignore[arg-type]


# Aliases for convenience & backward compatibility
extract_text = extract_text_from_pdf

