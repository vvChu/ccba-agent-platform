import typer
from pathlib import Path
from rich.console import Console
from mdconverter.core.table_reconstructor import TableReconstructor

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
    """Reconstruct broken markdown tables from original Word document."""
    console.print(f"[bold blue]Processing table for:[/bold blue] {file.name}")
    
    reconstructor = TableReconstructor()
    success = reconstructor.reconstruct_table(file, docx)
    
    if success:
        console.print("[bold green]Success:[/bold green] Reconstructed table successfully!")
    else:
        console.print("[bold red]Error:[/bold red] Table reconstruction failed.")
        raise typer.Exit(1)
