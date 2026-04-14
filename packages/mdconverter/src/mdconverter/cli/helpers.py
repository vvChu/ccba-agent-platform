"""
Shared utilities for CLI commands.
"""

from pathlib import Path

from mdconverter.core.base import BaseConverter


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


def create_converter(
    tool: str,
    file_extension: str,
    output_dir: Path | None = None,
) -> BaseConverter:
    """Create the appropriate converter based on tool choice and file extension.

    When tool is 'auto', delegates to ConverterRegistry.auto_select() for
    priority-based converter selection. For explicit tool names, uses the
    registry's create() method directly.

    Args:
        tool: Conversion tool name. Supported values:
            - 'auto': Use registry priority to select best converter.
            - 'pandoc': Use Pandoc converter.
            - 'llm': Use LLM-based converter.
            - 'gemini': Legacy alias for 'llm' (all models go via AI Gateway).
            - 'llamaparse': Use LlamaParse converter.
        file_extension: File extension including the dot (e.g., '.pdf').
        output_dir: Optional output directory.

    Returns:
        A BaseConverter instance.
    """
    from mdconverter.core.registry import ConverterRegistry

    if tool == "auto":
        return ConverterRegistry.auto_select(file_extension, output_dir=output_dir)

    # Map legacy CLI tool names to registry names
    tool_map = {
        "gemini": "llm",
        "pandoc": "pandoc",
        "llamaparse": "llamaparse",
        "llm": "llm",
    }
    registry_name = tool_map.get(tool, tool)
    return ConverterRegistry.create(registry_name, output_dir=output_dir)
