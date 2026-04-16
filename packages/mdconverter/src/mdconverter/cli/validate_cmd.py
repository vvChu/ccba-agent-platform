"""
Validate command for mdconverter CLI.
"""

from pathlib import Path

import typer
from rich.console import Console

from mdconverter.config import get_settings

console = Console()


def validate(
    target: Path = typer.Argument(
        ...,
        help="File or directory to validate.",
        exists=True,
    ),
    fix: bool = typer.Option(
        False,
        "--fix",
        "-f",
        help="Automatically fix issues where possible.",
    ),
) -> None:
    """Validate Markdown files for quality and structure."""
    from mdconverter.plugins.vn_legal.detector import is_legal_document
    from mdconverter.plugins.vn_legal.processor import VNLegalProcessor

    settings = get_settings()

    files: list[Path] = []
    if target.is_file():
        files = [target]
    else:
        files = list(target.rglob("*.md"))

    if not files:
        console.print("[yellow]No Markdown files found.[/yellow]")
        raise typer.Exit(1)

    console.print(f"[bold]Validating {len(files)} file(s)...[/bold]")

    issues_found = 0
    files_fixed = 0

    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
        except Exception as e:
            console.print(f"  [red]✗[/red] {file.name}: Cannot read file - {e}")
            issues_found += 1
            continue

        # Check quality metrics
        issues: list[str] = []

        if len(content) < settings.min_content_length:
            issues.append(f"Content too short ({len(content)} chars)")

        if not content.strip():
            issues.append("Empty file")

        if "# " not in content:
            issues.append("Missing main heading")

        # VN Legal specific checks
        if is_legal_document(content):
            processor = VNLegalProcessor()
            if fix:
                new_content = processor.process(content)
                if new_content != content:
                    file.write_text(new_content, encoding="utf-8")
                    files_fixed += 1
                    fixes = processor.get_fix_summary()
                    console.print(
                        f"  [green]✓[/green] {file.name}: Fixed {sum(fixes.values())} issues"
                    )
                else:
                    console.print(f"  [green]✓[/green] {file.name}: OK (VN Legal Doc)")
            else:
                console.print(f"  [dim]ℹ[/dim] {file.name}: VN Legal document detected")

        elif issues:
            issues_found += 1
            console.print(f"  [yellow]⚠[/yellow] {file.name}: {', '.join(issues)}")
        else:
            console.print(f"  [green]✓[/green] {file.name}: OK")

    console.print()
    if fix and files_fixed > 0:
        console.print(f"[bold]Fixed {files_fixed} file(s)[/bold]")
    if issues_found > 0:
        console.print(f"[yellow]Found {issues_found} file(s) with issues[/yellow]")
        raise typer.Exit(1)
    else:
        console.print("[green]All files OK![/green]")
