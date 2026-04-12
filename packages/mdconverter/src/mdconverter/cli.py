"""
CLI interface using Typer.

Provides commands for converting, validating, and fixing Markdown documents.

This module re-exports the app from the refactored cli/ package for
backward compatibility and as the entry-point target.
"""

from mdconverter.cli import app  # noqa: F401

if __name__ == "__main__":
    app()
