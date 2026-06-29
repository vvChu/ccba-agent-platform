import typer
from pathlib import Path
from rich.console import Console
from mdconverter.core.link_patcher import LinkPatcher

console = Console()

def patch_links(
    file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the target markdown file (decree) or directory.",
        exists=True,
    ),
) -> None:
    """Patch relative links to appendices inside the markdown files to ensure compatibility."""
    console.print(f"[bold blue]Patching links for:[/bold blue] {file.name}")
    
    patcher = LinkPatcher()
    modified_files = patcher.patch_links(file)
    
    if modified_files:
        for fpath in modified_files:
            console.print(f"[green]Patched links in:[/green] {fpath.name}")
    else:
        console.print("[yellow]No links needed patching in target file(s).[/yellow]")
        
    console.print("[bold green]Success:[/bold green] Link patching process completed!")
