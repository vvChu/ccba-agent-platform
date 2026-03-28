"""
Chunked PDF Conversion Script.

Splits large PDFs into chunks, converts each chunk separately using LLM,
then merges the results into a single Markdown file.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mdconverter.config import settings
from mdconverter.core.gemini import LLMConverter
from mdconverter.core.base import BaseConverter


def split_pdf(pdf_path: Path, pages_per_chunk: int = 15) -> list[Path]:
    """Split PDF into smaller chunks using PyMuPDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("Installing PyMuPDF...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pymupdf"], check=True)
        import fitz
    
    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    print(f"PDF has {total_pages} pages")
    
    if total_pages <= pages_per_chunk:
        doc.close()
        return [pdf_path]  # No need to split
    
    chunks: list[Path] = []
    temp_dir = Path(tempfile.mkdtemp(prefix="pdf_chunks_"))
    
    for start in range(0, total_pages, pages_per_chunk):
        end = min(start + pages_per_chunk, total_pages)
        chunk_doc = fitz.open()  # New empty PDF
        chunk_doc.insert_pdf(doc, from_page=start, to_page=end - 1)
        
        chunk_path = temp_dir / f"chunk_{start+1:03d}_to_{end:03d}.pdf"
        chunk_doc.save(chunk_path)
        chunk_doc.close()
        chunks.append(chunk_path)
        print(f"  Created chunk: pages {start+1}-{end} → {chunk_path.name}")
    
    doc.close()
    return chunks


async def convert_chunk(converter: LLMConverter, chunk_path: Path, chunk_num: int) -> str:
    """Convert a single PDF chunk to Markdown."""
    print(f"\n[Chunk {chunk_num}] Converting {chunk_path.name}...")
    
    result = await converter.convert(chunk_path)
    
    if result.is_success and result.content:
        # Remove frontmatter from chunk (will add once at the end)
        content = result.content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        
        print(f"[Chunk {chunk_num}] ✓ Converted ({len(content)} chars)")
        return content
    else:
        print(f"[Chunk {chunk_num}] ✗ Failed: {result.error_message}")
        return ""


def merge_chunks(contents: list[str]) -> str:
    """Merge chunk contents, removing potential overlaps at boundaries."""
    if not contents:
        return ""
    
    merged = contents[0]
    
    for i, content in enumerate(contents[1:], start=2):
        if not content:
            continue
        
        # Find potential overlap (last 100 chars of previous vs first 100 of next)
        # Simple approach: just add separator and merge
        merged += f"\n\n<!-- Chunk {i} -->\n\n"
        merged += content
    
    return merged


async def chunked_convert(pdf_path: Path, output_path: Path | None = None, pages_per_chunk: int = 15):
    """Main function to perform chunked PDF conversion."""
    print(f"\n{'='*60}")
    print(f"CHUNKED PDF CONVERSION")
    print(f"{'='*60}")
    print(f"Source: {pdf_path.name}")
    print(f"Pages per chunk: {pages_per_chunk}")
    
    # Split PDF
    print(f"\n[Step 1] Splitting PDF...")
    chunks = split_pdf(pdf_path, pages_per_chunk)
    print(f"Created {len(chunks)} chunk(s)")
    
    # Convert each chunk
    print(f"\n[Step 2] Converting chunks...")
    converter = LLMConverter()
    contents: list[str] = []
    
    for i, chunk_path in enumerate(chunks, start=1):
        content = await convert_chunk(converter, chunk_path, i)
        contents.append(content)
    
    # Merge results
    print(f"\n[Step 3] Merging results...")
    merged_content = merge_chunks(contents)
    
    # Add frontmatter
    from mdconverter.core.base import BaseConverter
    
    class TempConverter(BaseConverter):
        def supports(self, ext): return True
        async def convert(self, path): pass
    
    temp_conv = TempConverter()
    final_content = temp_conv.add_frontmatter(merged_content, pdf_path, "llm/chunked")
    
    # Write output
    if output_path is None:
        output_path = pdf_path.parent / (pdf_path.stem.lower().replace(" ", "_") + ".md")
    
    output_path.write_text(final_content, encoding="utf-8")
    
    print(f"\n{'='*60}")
    print(f"COMPLETED")
    print(f"{'='*60}")
    print(f"Output: {output_path}")
    print(f"Total length: {len(final_content):,} characters")
    print(f"Total lines: {final_content.count(chr(10)):,}")
    
    # Cleanup temp files
    if len(chunks) > 1:
        temp_dir = chunks[0].parent
        for chunk in chunks:
            chunk.unlink(missing_ok=True)
        temp_dir.rmdir()
        print(f"Cleaned up temp files")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python chunked_convert.py <pdf_path> [pages_per_chunk]")
        sys.exit(1)
    
    pdf_path = Path(sys.argv[1])
    pages_per_chunk = int(sys.argv[2]) if len(sys.argv) > 2 else 15
    
    if not pdf_path.exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    asyncio.run(chunked_convert(pdf_path, pages_per_chunk=pages_per_chunk))
