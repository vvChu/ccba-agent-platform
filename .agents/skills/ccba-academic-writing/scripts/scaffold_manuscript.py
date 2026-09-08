#!/usr/bin/env python3
"""scaffold_manuscript.py - Generates a blank academic research paper template.

Thin CLI Adapter delegating to mdconverter.academic.scaffold_manuscript.
"""

from __future__ import annotations

import sys
from pathlib import Path

from mdconverter.academic import scaffold_manuscript


def main() -> None:
    """Entry point for scaffolding academic paper templates."""
    if len(sys.argv) < 2:
        print("Usage: python scaffold_manuscript.py <output_file.md>")
        sys.exit(1)

    output_path = Path(sys.argv[1])
    if output_path.exists():
        print(f"Error: Target file '{output_path}' already exists. Operation aborted.")
        sys.exit(1)

    scaffold_manuscript(output_path)
    print(f"Successfully generated manuscript skeleton at: {output_path.absolute()}")


if __name__ == "__main__":
    main()
