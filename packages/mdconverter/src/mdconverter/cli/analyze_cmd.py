"""
CLI command: analyze — inspect PDF files and classify them.

Shows PDF category (text_rich, scanned, hybrid, drawing), recommended
converter model, page details, and confidence score without performing
actual conversion.
"""

from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from mdconverter.core.analyzer import PDFReport

console = Console()


def analyze(
    path: Path = typer.Argument(..., help="PDF file or directory to analyze."),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Scan subdirectories."),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON."),
    detail: bool = typer.Option(False, "--detail", "-d", help="Show per-page details."),
) -> None:
    """Analyze PDF files and recommend optimal conversion strategy.

    Inspects text layers, page dimensions, and image content to classify
    PDFs as text_rich, scanned, hybrid, or drawing.
    """
    from mdconverter.core.analyzer import PDFAnalyzer

    analyzer = PDFAnalyzer()

    # Collect PDF files
    pdf_files: list[Path] = []
    if path.is_file():
        if path.suffix.lower() != ".pdf":
            console.print(f"[red]Error:[/red] {path} is not a PDF file.")
            raise typer.Exit(code=1)
        pdf_files.append(path)
    elif path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        pdf_files = sorted(path.glob(pattern))
    else:
        console.print(f"[red]Error:[/red] {path} not found.")
        raise typer.Exit(code=1)

    if not pdf_files:
        console.print(f"[yellow]No PDF files found in {path}[/yellow]")
        raise typer.Exit(code=1)

    console.print(f"\n[bold]Analyzing {len(pdf_files)} PDF files...[/bold]\n")

    # Analyze
    reports = []
    for pdf in pdf_files:
        try:
            report = analyzer.analyze(pdf)
            reports.append(report)
        except Exception as e:
            console.print(f"  [red]✗[/red] {pdf.name}: {e}")

    if json_output:
        _print_json(reports)
    else:
        _print_table(reports, show_detail=detail)
        _print_summary(reports)


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------
_CATEGORY_STYLE = {
    "text_rich": "[green]text_rich[/green]",
    "scanned": "[yellow]scanned[/yellow]",
    "hybrid": "[cyan]hybrid[/cyan]",
    "drawing": "[dim]drawing[/dim]",
    "unknown": "[red]unknown[/red]",
}

_CATEGORY_ICON = {
    "text_rich": "📄",
    "scanned": "📷",
    "hybrid": "🔀",
    "drawing": "📐",
    "unknown": "❓",
}


def _print_table(reports: list["PDFReport"], show_detail: bool = False) -> None:
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
        model = r.recommended_model or "—"

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

    # Page details if requested
    if show_detail:
        for r in reports:
            if r.page_details:
                console.print(f"\n[bold]{r.file_path.name}[/bold] — per-page breakdown:")
                for p in r.page_details[:20]:  # Cap at 20 pages
                    size = f"{p.width_mm:.0f}×{p.height_mm:.0f}mm"
                    oversized = " [red]OVERSIZED[/red]" if p.is_oversized else ""
                    console.print(
                        f"  p{p.page_num + 1:>3}: {p.page_type:<8} "
                        f"chars={p.text_chars:>5}  imgs={p.image_count}  "
                        f"{size}{oversized}"
                    )
                if len(r.page_details) > 20:
                    console.print(f"  ... and {len(r.page_details) - 20} more pages")


def _print_summary(reports: list["PDFReport"]) -> None:
    """Print category summary."""
    from collections import Counter

    cats = Counter(r.category.value for r in reports)
    total = len(reports)

    console.print(f"\n[bold]Summary:[/bold] {total} files analyzed")

    for cat, count in cats.most_common():
        icon = _CATEGORY_ICON.get(cat, "")
        pct = count / total * 100
        bar_len = int(pct / 5)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        console.print(f"  {icon} {cat:<12} {bar} {count:>3} ({pct:.0f}%)")

    skip_count = sum(1 for r in reports if r.should_skip)
    convert_count = total - skip_count
    console.print(
        f"\n  → [green]{convert_count}[/green] convertible, "
        f"[dim]{skip_count} skipped (drawings)[/dim]"
    )


def _print_json(reports: list["PDFReport"]) -> None:
    """Print reports as JSON."""
    import json

    data = [r.to_dict() for r in reports]
    console.print_json(json.dumps(data, ensure_ascii=False, indent=2))
