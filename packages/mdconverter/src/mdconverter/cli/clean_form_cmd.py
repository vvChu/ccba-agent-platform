import sys
from pathlib import Path

import typer
from rich.console import Console

from mdconverter.core.form_cleaner import FormCleaner

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def clean_form(
    file: Path = typer.Option(
        ...,
        "--file",
        "-f",
        help="Path to the target markdown file (form/appendix).",
        exists=True,
    ),
) -> None:
    """Clean form template placeholders and recover actual form title using AI Gateway."""
    console.print(f"[bold blue]Cleaning form placeholders for:[/bold blue] {file.name}")

    cleaner = FormCleaner()
    try:
        recovered_title = cleaner.clean_form(file)

        if recovered_title:
            try:
                console.print(f"[green]Recovered Title:[/green] {recovered_title}")
            except Exception:
                try:
                    print(
                        f"Recovered Title: {recovered_title.encode('utf-8', errors='ignore').decode('utf-8')}"
                    )
                except Exception:
                    pass
            console.print(
                "[bold green]Success:[/bold green] Recovered and cleaned title successfully!"
            )
        else:
            console.print(
                "[yellow]No typical form placeholders or blank dotted lines detected in header. Skipping.[/yellow]"
            )

    except Exception as e:
        try:
            console.print(f"[bold red]Error:[/bold red] {e}")
        except Exception:
            print(f"Error: {str(e)}")
        raise typer.Exit(1) from e
