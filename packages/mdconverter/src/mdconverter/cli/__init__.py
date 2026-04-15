"""
CLI package for mdconverter.

Provides Typer-based commands for converting, validating, and linting documents.
"""

import typer
from rich.console import Console

from mdconverter import __version__
from mdconverter.cli.analyze_cmd import analyze
from mdconverter.cli.config_cmd import app_config
from mdconverter.cli.convert_cmd import convert
from mdconverter.cli.lint_cmd import lint
from mdconverter.cli.validate_cmd import validate

app = typer.Typer(
    name="mdconvert",
    help="Modern Document to Markdown Converter with Vietnamese legal document support.",
    add_completion=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"[bold blue]mdconverter[/bold blue] version [green]{__version__}[/green]")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """
    mdconvert - Modern Document to Markdown Converter.

    Convert PDF, DOCX, HTML, and other documents to clean, standardized Markdown.
    Includes special support for Vietnamese legal documents.
    """
    pass


# Register commands
app.command()(convert)
app.command()(validate)
app.command()(lint)
app.command()(analyze)
app.add_typer(app_config, name="config")
