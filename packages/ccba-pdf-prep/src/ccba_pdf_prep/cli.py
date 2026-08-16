"""
CCBA PDF Preprocessor — CLI interface.

Commands:
    analyze  - Classify PDFs (text_rich, scanned, hybrid, drawing)
    tile     - Slice drawing pages into high-res tiles
    split    - Split a large PDF into smaller chunks
"""

import json
import os
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="ccba-pdf",
    help="CCBA PDF Preprocessor — Analyze, tile, and split PDF documents.",
    no_args_is_help=True,
)
# Force ASCII-safe rendering on Windows legacy consoles
console = Console(force_terminal=bool(os.name == "nt"))

# --------------------------------------------------------------------------
# Category display helpers
# --------------------------------------------------------------------------
_CATEGORY_STYLE = {
    "text_rich": "[green]text_rich[/green]",
    "scanned": "[yellow]scanned[/yellow]",
    "hybrid": "[cyan]hybrid[/cyan]",
    "drawing": "[dim]drawing[/dim]",
    "unknown": "[red]unknown[/red]",
}

_CATEGORY_ICON = {
    "text_rich": "T",
    "scanned": "S",
    "hybrid": "H",
    "drawing": "D",
    "unknown": "?",
}


# --------------------------------------------------------------------------
# analyze
# --------------------------------------------------------------------------
@app.command()
def analyze(
    path: Path = typer.Argument(..., help="PDF file or directory to analyze."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan subdirectories."),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
    detail: bool = typer.Option(False, "--detail", "-d", help="Show per-page details."),
) -> None:
    """Analyze PDF files and recommend optimal processing strategy."""
    from .core import PDFAnalyzer

    analyzer = PDFAnalyzer()
    pdf_files = _collect_pdfs(path, recursive)

    console.print(f"\n[bold]Analyzing {len(pdf_files)} PDF file(s)...[/bold]\n")

    reports = []
    for pdf in pdf_files:
        try:
            report = analyzer.analyze(pdf)
            reports.append(report)
        except Exception as e:
            console.print(f"  [red]x[/red] {pdf.name}: {e}")

    if json_output:
        data = [r.to_dict() for r in reports]
        console.print_json(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_analysis_table(reports, show_detail=detail)
        _print_summary(reports)


# --------------------------------------------------------------------------
# tile
# --------------------------------------------------------------------------
@app.command()
def tile(
    pdf_path: Path = typer.Argument(..., help="PDF file to tile.", exists=True),
    page: int = typer.Option(0, "--page", "-p", help="Page number (0-indexed)."),
    output_dir: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for tiles."
    ),
    dpi: int = typer.Option(300, "--dpi", help="Rendering DPI."),
    tile_size: int = typer.Option(1024, "--tile-size", help="Tile size in pixels."),
    overlap: int = typer.Option(0, "--overlap", help="Overlap between tiles in pixels."),
) -> None:
    """Slice a PDF page into high-resolution tiles for AI Vision."""
    from .vision import VisionOptimizer

    out = output_dir or (pdf_path.parent / "tiles")
    console.print(f"[bold]Tiling[/bold] {pdf_path.name} page {page + 1} at {dpi} DPI...")

    tiles = VisionOptimizer.tile_page(
        pdf_path=pdf_path,
        page_num=page,
        output_dir=out,
        dpi=dpi,
        tile_size_px=tile_size,
        overlap_px=overlap,
    )

    console.print(f"  [green]OK[/green] Generated {len(tiles)} tiles in {out}")
    for t in tiles:
        console.print(f"    - {t.name}")


# --------------------------------------------------------------------------
# split
# --------------------------------------------------------------------------
@app.command()
def split(
    pdf_path: Path = typer.Argument(..., help="PDF file to split.", exists=True),
    chunk_size: int = typer.Option(20, "--chunk-size", "-c", help="Pages per chunk."),
    output_dir: Path | None = typer.Option(
        None, "--output", "-o", help="Output directory for chunks."
    ),
) -> None:
    """Split a large PDF into smaller chunks."""
    import fitz

    from .core import get_blind_chunks, split_pdf

    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    doc.close()

    out = output_dir or (pdf_path.parent / "chunks")
    ranges = get_blind_chunks(total_pages, chunk_size=chunk_size)

    console.print(
        f"[bold]Splitting[/bold] {pdf_path.name} ({total_pages} pages) "
        f"into {len(ranges)} chunks of ~{chunk_size} pages..."
    )

    chunk_paths = split_pdf(pdf_path, ranges, out)

    console.print(f"  [green]OK[/green] Created {len(chunk_paths)} chunks in {out}")
    for cp in chunk_paths:
        console.print(f"    - {cp.name}")


# --------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------
def _collect_pdfs(path: Path, recursive: bool) -> list[Path]:
    """Collect PDF files from a path (file or directory)."""
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            console.print(f"[red]Error:[/red] {path} is not a PDF file.")
            raise typer.Exit(code=1)
        return [path]
    if path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        files = sorted(path.glob(pattern))
        if not files:
            console.print(f"[yellow]No PDF files found in {path}[/yellow]")
            raise typer.Exit(code=1)
        return files
    console.print(f"[red]Error:[/red] {path} not found.")
    raise typer.Exit(code=1)


def _print_analysis_table(reports: list[Any], show_detail: bool = False) -> None:
    """Print analysis results as a rich table."""
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("", width=2)
    table.add_column("File", min_width=30)
    table.add_column("Size", justify="right")
    table.add_column("Pages", justify="right")
    table.add_column("Txt/Img/Drw", justify="center")
    table.add_column("Category")
    table.add_column("Confidence", justify="right")
    table.add_column("Model")

    for r in reports:
        icon = _CATEGORY_ICON.get(r.category.value, "")
        cat_styled = _CATEGORY_STYLE.get(r.category.value, r.category.value)
        dist = f"{r.text_pages}/{r.image_pages}/{r.drawing_pages}"
        conf = f"{r.confidence:.0%}"
        model = r.recommended_model or "-"

        table.add_row(
            icon,
            r.file_path.name[:40],
            f"{r.size_mb:.1f}M",
            str(r.pages),
            dist,
            cat_styled,
            conf,
            model,
        )

    console.print(table)

    if show_detail:
        for r in reports:
            if r.page_details:
                console.print(f"\n[bold]{r.file_path.name}[/bold] -- per-page breakdown:")
                for p in r.page_details[:20]:
                    size = f"{p.width_mm:.0f}x{p.height_mm:.0f}mm"
                    oversized = " [red]OVERSIZED[/red]" if p.is_oversized else ""
                    console.print(
                        f"  p{p.page_num + 1:>3}: {p.page_type:<8} "
                        f"chars={p.text_chars:>5}  imgs={p.image_count}  "
                        f"{size}{oversized}"
                    )
                if len(r.page_details) > 20:
                    console.print(f"  ... and {len(r.page_details) - 20} more pages")


def _print_summary(reports: list[Any]) -> None:
    """Print category summary."""
    from collections import Counter

    cats = Counter(r.category.value for r in reports)
    total = len(reports)

    console.print(f"\n[bold]Summary:[/bold] {total} files analyzed")
    for cat, count in cats.most_common():
        icon = _CATEGORY_ICON.get(cat, "")
        pct = count / total * 100
        bar_len = int(pct / 5)
        bar = "#" * bar_len + "." * (20 - bar_len)
        console.print(f"  {icon} {cat:<12} {bar} {count:>3} ({pct:.0f}%)")


if __name__ == "__main__":
    app()
