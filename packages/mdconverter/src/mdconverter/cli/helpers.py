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

    Args:
        tool: Conversion tool name ('auto', 'pandoc', 'gemini', 'llamaparse').
        file_extension: File extension including the dot (e.g., '.pdf').
        output_dir: Optional output directory.

    Returns:
        A BaseConverter instance.
    """
    from mdconverter.core.gemini import LLMConverter
    from mdconverter.core.pandoc import PandocConverter

    if tool == "pandoc" or (
        tool == "auto" and file_extension.lower() in {".docx", ".html", ".htm"}
    ):
        return PandocConverter(output_dir)
    else:
        return LLMConverter(output_dir)
