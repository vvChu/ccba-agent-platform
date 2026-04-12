"""
Lint command for mdconverter CLI.
"""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def lint(
    target: Path = typer.Argument(
        Path("."),
        help="File or directory to lint.",
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix lint issues.",
    ),
    vn_only: bool = typer.Option(
        False,
        "--vn-only",
        help="Only run Vietnamese legal document checks.",
    ),
) -> None:
    """Lint Markdown files using PyMarkdown and VN Legal rules."""
    from mdconverter.plugins.vn_legal.linter import VNLegalLinter

    console.print(f"[bold]Linting:[/bold] {target}")

    # VN Legal Lint
    linter = VNLegalLinter()
    if target.is_file():
        issues = linter.lint_file(target)
    else:
        issues = linter.lint_directory(target)

    if issues:
        # Group by file
        table = Table(title="Vietnamese Legal Document Issues")
        table.add_column("File", style="cyan")
        table.add_column("Line", style="yellow")
        table.add_column("Rule", style="magenta")
        table.add_column("Message", style="white")

        for issue in issues:
            table.add_row(
                issue.file.name,
                str(issue.line),
                issue.rule_id,
                issue.message,
            )

        console.print(table)
        console.print(f"\n[yellow]Found {len(issues)} issue(s)[/yellow]")
        raise typer.Exit(1)
    else:
        console.print("[green]✓[/green] No issues found!")
