"""Command-line interface for CCBA Diagramming Utilities."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ccba_diagram.matrix_table import generate_markdown_spec_table
from ccba_diagram.router import apply_smart_layout


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for ccba-diagram."""
    parser = argparse.ArgumentParser(
        prog="ccba-diagram",
        description="CCBA Diagramming Utilities — Deterministic Layout Engines & Visual Ergonomics",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: layout
    layout_parser = subparsers.add_parser("layout", help="Apply layout engine to Excalidraw JSON")
    layout_parser.add_argument("input", type=Path, help="Input Excalidraw JSON file")
    layout_parser.add_argument(
        "-o", "--output", type=Path, help="Output JSON file (default: stdout)"
    )
    layout_parser.add_argument(
        "--engine",
        choices=[
            "auto",
            "sugiyama",
            "wheel",
            "matrix",
            "tree",
            "radial",
            "concentric",
            "value_chain",
            "cycle",
        ],
        default="auto",
        help="Force specific layout engine or auto-detect (default: auto)",
    )

    # Command: spec-table
    table_parser = subparsers.add_parser(
        "spec-table", help="Generate Markdown Specification Table from Excalidraw JSON"
    )
    table_parser.add_argument("input", type=Path, help="Input Excalidraw JSON file")
    table_parser.add_argument(
        "-t",
        "--title",
        default="Bảng Đặc Tả Ma Trận Kiến Trúc",
        help="Table header title",
    )

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "layout":
        if not args.input.exists():
            sys.stderr.write(f"Error: Input file '{args.input}' does not exist.\n")
            return 1

        try:
            data = json.loads(args.input.read_text(encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"Error reading JSON from '{args.input}': {e}\n")
            return 1

        elements = data.get("elements", data) if isinstance(data, dict) else data
        if not isinstance(elements, list):
            sys.stderr.write("Error: Expected a list of elements or an Excalidraw JSON document.\n")
            return 1

        force_eng = None if args.engine == "auto" else args.engine
        chosen_eng = apply_smart_layout(elements, force_engine=force_eng)
        sys.stderr.write(f"Applied layout engine: {chosen_eng}\n")

        if isinstance(data, dict) and "elements" in data:
            data["elements"] = elements
            output_content = json.dumps(data, indent=2, ensure_ascii=False)
        else:
            output_content = json.dumps(elements, indent=2, ensure_ascii=False)

        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output_content, encoding="utf-8")
            sys.stderr.write(f"Saved layout to {args.output}\n")
        else:
            print(output_content)

        return 0

    elif args.command == "spec-table":
        if not args.input.exists():
            sys.stderr.write(f"Error: Input file '{args.input}' does not exist.\n")
            return 1

        try:
            data = json.loads(args.input.read_text(encoding="utf-8"))
        except Exception as e:
            sys.stderr.write(f"Error reading JSON from '{args.input}': {e}\n")
            return 1

        elements = data.get("elements", data) if isinstance(data, dict) else data
        if not isinstance(elements, list):
            sys.stderr.write("Error: Expected a list of elements or an Excalidraw JSON document.\n")
            return 1

        table_md = generate_markdown_spec_table(elements, table_title=args.title)
        print(table_md)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
