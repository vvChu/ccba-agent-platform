"""
Convert command for mdconverter CLI.
"""

import asyncio
import logging
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from mdconverter.cli.helpers import create_converter, get_files_to_convert
from mdconverter.core.base import ConversionResult, ConversionStatus
from mdconverter.core.logging import configure_logging, get_logger

console = Console()


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
    use_cache: bool = typer.Option(
        False,
        "--cache",
        help="Enable caching to skip unchanged files.",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable debug logging output.",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Only show warnings and errors.",
    ),
) -> None:
    """Convert documents to Markdown."""
    # Check mutually exclusive flags
    if verbose and quiet:
        console.print("[red]Error: --verbose and --quiet cannot be used together.[/red]")
        raise typer.Exit(1)

    # Configure logging based on flags
    log_level = logging.DEBUG if verbose else logging.INFO
    configure_logging(level=log_level, quiet=quiet)
    logger = get_logger(__name__)

    files = get_files_to_convert(input_path, recursive)
    logger.debug("Found %d files to process", len(files))

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
    from mdconverter.core.cache import ConversionCache

    # Initialize cache if enabled
    cache = ConversionCache() if use_cache else None

    # Limit concurrency
    sem = asyncio.Semaphore(10)

    async def convert_file_safe(file: Path) -> ConversionResult:
        """Convert a single file with concurrency limit."""
        loop = asyncio.get_running_loop()
        async with sem:
            # Check cache first (run sync I/O in thread pool to avoid blocking)
            if cache:
                cached_content = await loop.run_in_executor(None, cache.get, file)
                if cached_content:
                    # Compute expected output path
                    output_name = file.stem.lower().replace(" ", "_") + ".md"
                    expected_output = (output_dir or file.parent) / output_name

                    # Ensure parent directory exists before writing
                    def write_cached_output() -> None:
                        expected_output.parent.mkdir(parents=True, exist_ok=True)
                        expected_output.write_text(cached_content, encoding="utf-8")

                    await loop.run_in_executor(None, write_cached_output)
                    return ConversionResult(
                        source_path=file,
                        output_path=expected_output,
                        status=ConversionStatus.SUCCESS,
                        tool_used="cache",
                        content=cached_content,
                    )

            converter = create_converter(tool, file.suffix, output_dir)
            result = await converter.convert(file)

            # Apply VN Legal post-processing if applicable
            if result.is_success and result.content:
                from mdconverter.plugins.vn_legal.detector import is_legal_document
                from mdconverter.plugins.vn_legal.processor import VNLegalProcessor

                if is_legal_document(result.content):
                    processor = VNLegalProcessor()
                    processed_content = processor.process(result.content)
                    if processed_content != result.content:
                        result.content = processed_content
                        # Update the output file with processed content
                        if result.output_path and result.output_path.exists():
                            result.output_path.write_text(processed_content, encoding="utf-8")
                        logger.debug("Applied VN Legal rules: %s", processor.get_fix_summary())

            # Save to cache if successful (run sync I/O in thread pool)
            if cache and result.is_success and result.content:
                await loop.run_in_executor(None, cache.set, file, result.content, result.tool_used)

            return result

    async def process_files() -> list[ConversionResult]:
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
                    console.print(
                        f"  [red]✗[/red] {result.source_path.name}: {result.error_message}"
                    )

                progress.advance(task)
        return results

    results = asyncio.run(process_files())

    # Summary
    success = sum(1 for r in results if r.status == ConversionStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == ConversionStatus.FAILED)
    from_cache = sum(1 for r in results if r.tool_used == "cache")

    console.print()
    summary_parts = [f"{success} success", f"{failed} failed"]
    if from_cache > 0:
        summary_parts.append(f"{from_cache} from cache")
    console.print(f"[bold]Summary:[/bold] {', '.join(summary_parts)}")

    # Watch mode
    if watch:
        from mdconverter.core.watcher import FileWatcher

        watch_path = input_path if input_path.is_dir() else input_path.parent

        def on_file_change(file: Path) -> None:
            console.print(f"\n[cyan]File changed:[/cyan] {file.name}")

            async def convert_single() -> ConversionResult:
                converter = create_converter(tool, file.suffix, output_dir)
                return await converter.convert(file)

            result = asyncio.run(convert_single())
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
