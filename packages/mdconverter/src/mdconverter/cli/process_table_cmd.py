from pathlib import Path

import typer
from rich.console import Console

from mdconverter.core.appendix_extractor import AppendixExtractor

console = Console()


def process_table(
    file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the target markdown file (appendix).",
        exists=True,
    ),
    docx: Path = typer.Option(
        ...,
        "--docx",
        "-d",
        help="Path to the original parent docx file.",
        exists=True,
    ),
) -> None:
    """Reconstruct broken markdown appendix from original Word document."""
    console.print(f"[bold blue]Extracting appendix for:[/bold blue] {file.name}")

    extractor = AppendixExtractor()
    success = extractor.extract_appendix(file, docx)

    if success:
        console.print("[bold green]Success:[/bold green] Extracted appendix successfully!")
    else:
        console.print("[bold red]Error:[/bold red] Appendix extraction failed.")
        raise typer.Exit(1)
