"""
CLI interface using Typer.

Provides commands for converting, validating, and fixing Markdown documents.
"""

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mdconverter import __version__
from mdconverter.config import settings
from mdconverter.core.base import BaseConverter, ConversionResult, ConversionStatus

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


def get_files_to_convert(path: Path, recursive: bool) -> list[Path]:
    """Get list of convertible files from path."""
    extensions = {".pdf", ".docx", ".doc", ".html", ".htm", ".pptx", ".xlsx"}
    files: list[Path] = []

    if path.is_file():
        if path.suffix.lower() in extensions:
            files.append(path)
    elif path.is_dir():
        pattern = "**/*" if recursive else "*"
        for ext in extensions:
            files.extend(path.glob(f"{pattern}{ext}"))

    return sorted(files)


@app.command()
def convert(
    input_path: Path = typer.Argument(
        ...,
        help="Input file or directory to convert.",
        exists=True,
    ),
    output_dir: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory. Defaults to same as input.",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Recursively process directories.",
    ),
    tool: str = typer.Option(
        "auto",
        "--tool",
        "-t",
        help="Conversion tool: auto, gemini, pandoc, llamaparse.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be converted without actually converting.",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Watch for file changes and auto-convert.",
    ),
) -> None:
    """Convert documents to Markdown."""
    files = get_files_to_convert(input_path, recursive)

    if not files and not watch:
        console.print("[yellow]No convertible files found.[/yellow]")
        raise typer.Exit(1)

    if files:
        console.print(f"[bold]Found {len(files)} file(s) to convert[/bold]")

    if dry_run:
        for f in files:
            console.print(f"  [dim]Would convert:[/dim] {f}")
        raise typer.Exit(0)

    # Import converters
    from mdconverter.core.gemini import GeminiConverter
    from mdconverter.core.pandoc import PandocConverter

    # Limit concurrency
    sem = asyncio.Semaphore(10)

    async def convert_file_safe(file: Path) -> ConversionResult:
        """Convert a single file with concurrency limit."""
        async with sem:
            converter: BaseConverter
            if tool == "pandoc" or (
                tool == "auto" and file.suffix.lower() in {".docx", ".html", ".htm"}
            ):
                 # Pandoc is still sync, run in thread pool
                converter = PandocConverter(output_dir)
                return await asyncio.to_thread(converter.convert, file)
            else:
                # LLM based (async)
                converter = GeminiConverter(output_dir)
                return await converter.convert(file)

    async def process_files():
        results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Converting...", total=len(files))
            
            tasks = []
            for file in files:
                tasks.append(convert_file_safe(file))
                
            for future in asyncio.as_completed(tasks):
                result = await future
                results.append(result)
                
                if result.is_success:
                    console.print(
                        f"  [green]✓[/green] {result.source_path.name} → {result.output_path.name if result.output_path else 'done'}"
                    )
                else:
                    console.print(f"  [red]✗[/red] {result.source_path.name}: {result.error_message}")
                
                progress.advance(task)
        return results

    results = asyncio.run(process_files())

    # Summary
    success = sum(1 for r in results if r.status == ConversionStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == ConversionStatus.FAILED)

    console.print()
    console.print(f"[bold]Summary:[/bold] {success} success, {failed} failed")

    # Watch mode
    if watch:
        from mdconverter.core.watcher import FileWatcher

        watch_path = input_path if input_path.is_dir() else input_path.parent

        def on_file_change(file: Path) -> None:
            console.print(f"\n[cyan]File changed:[/cyan] {file.name}")
            result = convert_file(file)
            if result.is_success:
                console.print(
                    f"  [green]✓[/green] {file.name} → {result.output_path.name if result.output_path else 'done'}"
                )
            else:
                console.print(f"  [red]✗[/red] {file.name}: {result.error_message}")

        console.print()
        console.print(f"[bold cyan]👁 Watching for changes...[/bold cyan] {watch_path}")
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        watcher = FileWatcher(watch_path, on_file_change, recursive=recursive)
        watcher.start()
        try:
            watcher.wait()
        except KeyboardInterrupt:
            console.print("\n[yellow]Watch mode stopped.[/yellow]")
            watcher.stop()


@app.command()
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
    from mdconverter.plugins.manager import PluginManager
    from mdconverter.plugins.vn_legal.detector import is_legal_document
    from mdconverter.plugins.vn_legal.processor import VNLegalProcessor
    
    # Load plugins (demo)
    pm = PluginManager()
    pm.load_plugins()

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


@app.command()
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


app_config = typer.Typer(help="Manage configuration.", name="config")
app.add_typer(app_config, name="config")


@app_config.command(name="show")
def config_show() -> None:
    """Show current configuration."""
    table = Table(title="Current Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Proxy URL", settings.antigravity_proxy)
    table.add_row("Proxy Token", settings.antigravity_access_token or "[dim]None[/dim]")
    table.add_row("Models", ", ".join(settings.models))
    table.add_row("Max Tokens", str(settings.max_output_tokens))
    table.add_row("Timeout", f"{settings.timeout_seconds}s")
    table.add_row("Temperature", str(settings.temperature))

    console.print(table)


@app_config.command(name="set")
def config_set(
    key: str = typer.Option(..., "--key", "-k", help="Setting key to update."),
    value: str = typer.Option(..., "--value", "-v", help="New value for the setting."),
) -> None:
    """Update a configuration setting in .env file."""
    valid_keys = {
        "antigravity_proxy": "MDCONVERT_ANTIGRAVITY_PROXY",
        "antigravity_access_token": "MDCONVERT_ANTIGRAVITY_ACCESS_TOKEN",
        "gemini_api_key": "MDCONVERT_GEMINI_API_KEY",
        "llama_cloud_api_key": "MDCONVERT_LLAMA_CLOUD_API_KEY",
        "deepseek_api_key": "MDCONVERT_DEEPSEEK_API_KEY",
        "groq_api_key": "MDCONVERT_GROQ_API_KEY",
    }

    if key not in valid_keys:
        console.print(f"[red]Invalid key: {key}[/red]")
        console.print(f"Valid keys: {', '.join(valid_keys.keys())}")
        raise typer.Exit(1)

    env_var = valid_keys[key]
    env_path = Path(".env")
    
    # Read existing content
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    # Update or append
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{env_var}="):
            new_lines.append(f"{env_var}={value}")
            found = True
        else:
            new_lines.append(line)
    
    if not found:
        if new_lines and new_lines[-1] != "":
            new_lines.append("")
        new_lines.append(f"{env_var}={value}")

    # Write back
    env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    console.print(f"[green]Updated {key} ({env_var}) successfully![/green]")


if __name__ == "__main__":
    app()
