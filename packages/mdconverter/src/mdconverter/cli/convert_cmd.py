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
from mdconverter.core.base import ConversionResult, ConversionStatus, ConversionTool
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
    tool: ConversionTool = typer.Option(
        ConversionTool.AUTO,
        "--tool",
        "-t",
        help="Conversion tool (auto, llm, pandoc, llamaparse).",
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

    # Import pipeline (deferred to avoid heavy imports for --help/--version)
    from mdconverter.core.cache import ConversionCache
    from mdconverter.core.pipeline import ConversionPipeline

    # Initialize pipeline
    cache = ConversionCache() if use_cache else None
    pipeline = ConversionPipeline(
        tool=tool,
        output_dir=output_dir,
        cache=cache,
    )

    async def process_files() -> list[ConversionResult]:
        results: list[ConversionResult] = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Converting...", total=len(files))

            tasks = [pipeline.process_file(f) for f in files]
            for future in asyncio.as_completed(tasks):
                result = await future
                results.append(result)
                _print_result(result)
                progress.advance(task)
        return results

    results = asyncio.run(process_files())

    # Summary
    success = sum(1 for r in results if r.status == ConversionStatus.SUCCESS)
    failed = sum(1 for r in results if r.status == ConversionStatus.FAILED)
    skipped = sum(1 for r in results if r.status == ConversionStatus.SKIPPED)
    from_cache = sum(1 for r in results if r.tool_used == "cache")

    console.print()
    summary_parts = [f"{success} success", f"{failed} failed"]
    if skipped > 0:
        summary_parts.append(f"{skipped} skipped")
    if from_cache > 0:
        summary_parts.append(f"{from_cache} from cache")
    console.print(f"[bold]Summary:[/bold] {', '.join(summary_parts)}")

    # Watch mode — H4 fix: use a dedicated event loop, not nested asyncio.run()
    if watch:
        _run_watch_mode(input_path, tool, output_dir, recursive)


def _print_result(result: ConversionResult) -> None:
    """Print a single conversion result to console."""
    if result.status == ConversionStatus.SKIPPED:
        # Show analysis-based skip reason (e.g. drawings)
        reason = result.error_message or "skipped"
        console.print(f"  [dim]⊘[/dim] {result.source_path.name}: {reason}")
    elif result.is_success:
        out_name = result.output_path.name if result.output_path else "done"
        # Show PDF category if available
        analysis = result.metadata.get("pdf_analysis", {})
        category = analysis.get("category", "")
        suffix = f" [dim]({category})[/dim]" if category else ""
        console.print(f"  [green]✓[/green] {result.source_path.name} → {out_name}{suffix}")
    else:
        console.print(f"  [red]✗[/red] {result.source_path.name}: {result.error_message}")


def _run_watch_mode(
    input_path: Path,
    tool: ConversionTool,
    output_dir: Path | None,
    recursive: bool,
) -> None:
    """Run watch mode with event-loop-safe callbacks.

    H4 fix: Uses a single persistent event loop running in a background
    thread.  The watchdog callback schedules coroutines onto that loop
    via ``loop.call_soon_threadsafe`` instead of calling ``asyncio.run()``
    which would create conflicting event loops.
    """
    import threading

    from mdconverter.core.watcher import FileWatcher

    watch_path = input_path if input_path.is_dir() else input_path.parent

    # Create a dedicated event loop for async conversions
    loop = asyncio.new_event_loop()

    def _run_loop() -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    loop_thread = threading.Thread(target=_run_loop, daemon=True)
    loop_thread.start()

    def on_file_change(file: Path) -> None:
        """Handle file change by scheduling conversion on the background loop."""
        console.print(f"\n[cyan]File changed:[/cyan] {file.name}")

        async def _convert_single() -> None:
            converter = create_converter(tool, file.suffix, output_dir)
            result = await converter.convert(file)
            _print_result(result)

        asyncio.run_coroutine_threadsafe(_convert_single(), loop)

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
        loop.call_soon_threadsafe(loop.stop)
        loop_thread.join(timeout=2)
