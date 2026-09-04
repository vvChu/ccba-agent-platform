"""CCBA OOXML Command Line Interface (CLI).

Supports automated slide deck building from Markdown, OOXML packaging,
unpacking, and schema validation.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng (IBST).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pack import pack_document, validate_document
from .pptx import CCBAPresentationTheme, DeckBuilder
from .unpack import unpack_document
from .validation import OOXMLValidator


def main() -> None:
    """Main CLI entrypoint for ccba-ooxml."""
    parser = argparse.ArgumentParser(
        prog="ccba-ooxml",
        description="CCBA OOXML Tools — Presentation Builder, DOCX DOM Manipulation, and XML Validation.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: build-deck
    deck_parser = subparsers.add_parser(
        "build-deck",
        help="Build a professional PowerPoint (.pptx) presentation from a Markdown file",
    )
    deck_parser.add_argument(
        "input",
        type=str,
        help="Path to input markdown (.md) file",
    )
    deck_parser.add_argument(
        "-o",
        "--output",
        type=str,
        default="",
        help="Path to output .pptx file (default: same name as input with .pptx extension)",
    )
    deck_parser.add_argument(
        "--aspect-ratio",
        choices=["16:9", "4:3"],
        default="16:9",
        help="Slide aspect ratio (default: 16:9)",
    )
    deck_parser.add_argument(
        "--font",
        type=str,
        default="Segoe UI",
        help="Primary font family (default: Segoe UI for universal Windows compatibility)",
    )

    # Subcommand: pack
    pack_parser = subparsers.add_parser(
        "pack",
        help="Pack an unpacked directory back into a .docx/.pptx/.xlsx file",
    )
    pack_parser.add_argument("input_dir", type=str, help="Directory containing unpacked XML files")
    pack_parser.add_argument("output_file", type=str, help="Target Office file (.docx/.pptx/.xlsx)")

    # Subcommand: unpack
    unpack_parser = subparsers.add_parser(
        "unpack",
        help="Unpack a .docx/.pptx/.xlsx file into an XML directory",
    )
    unpack_parser.add_argument(
        "input_file", type=str, help="Source Office file (.docx/.pptx/.xlsx)"
    )
    unpack_parser.add_argument("output_dir", type=str, help="Target extraction directory")

    # Subcommand: validate
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate an Office file or unpacked XML directory",
    )
    val_parser.add_argument(
        "target", type=str, help="Path to Office file (.docx/.pptx/.xlsx) or unpacked XML directory"
    )
    val_parser.add_argument(
        "--original",
        type=str,
        default=None,
        help="Path to original file for schema comparison (required when target is a directory)",
    )

    # Subcommand: questionnaire
    q_parser = subparsers.add_parser(
        "questionnaire",
        help="Manage, render, and resolve CCBA Questionnaires (.docx, .html, .chat, .email)",
    )
    q_parser.add_argument("input", type=str, help="Path to input questionnaire markdown (.md) file")
    q_parser.add_argument(
        "-f",
        "--format",
        choices=["all", "docx", "html", "chat", "email"],
        default="all",
        help="Output format to render (default: all)",
    )
    q_parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save rendered outputs (default: same directory as input file)",
    )
    q_parser.add_argument(
        "--reply",
        type=str,
        default=None,
        help="Apply reply string to resolve questionnaire (e.g. '1A, 2B, 3C')",
    )
    q_parser.add_argument(
        "--resolved-by",
        type=str,
        default="Chủ đầu tư / Ban QLDA",
        help="Name or title of approver for decision log",
    )
    q_parser.add_argument(
        "--base-url",
        type=str,
        default="",
        help="Optional server base URL for web hosting and QR code",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "build-deck":
        input_p = Path(args.input)
        if not input_p.exists():
            print(f"Error: Input markdown file '{args.input}' does not exist.", file=sys.stderr)
            sys.exit(1)

        output_str = args.output
        if not output_str:
            output_str = str(input_p.with_suffix(".pptx"))

        md_content = input_p.read_text(encoding="utf-8")
        theme = CCBAPresentationTheme(
            aspect_ratio=args.aspect_ratio,
            font_family=args.font,
        )
        builder = DeckBuilder(theme=theme)
        out_path = builder.build_from_markdown(md_content, output_str)
        print(f"SUCCESS: Generated CCBA PowerPoint presentation at '{out_path}'")

    elif args.command == "pack":
        success = pack_document(args.input_dir, args.output_file)
        sys.exit(0 if success else 1)

    elif args.command == "unpack":
        unpack_document(args.input_file, args.output_dir)
        sys.exit(0)

    elif args.command == "validate":
        target = Path(args.target)
        if target.is_file():
            success = validate_document(target)
        elif target.is_dir():
            if not args.original:
                print(
                    "Error: --original <original_file> is required when validating an unpacked directory.",
                    file=sys.stderr,
                )
                sys.exit(1)
            validator = OOXMLValidator(str(target), args.original)
            success = validator.validate()
        else:
            print(f"Error: Target path '{args.target}' does not exist.", file=sys.stderr)
            sys.exit(1)
        sys.exit(0 if success else 1)

    elif args.command == "questionnaire":
        from .questionnaire import (
            QuestionnaireEngine,
            parse_questionnaire_markdown,
            render_chat_snippet,
            render_email_table,
            render_questionnaire_docx,
            render_questionnaire_html,
        )

        input_p = Path(args.input)
        if not input_p.exists():
            print(f"Error: Input questionnaire file '{args.input}' does not exist.", file=sys.stderr)
            sys.exit(1)

        # Handle --reply if provided
        if args.reply:
            try:
                mod_path = QuestionnaireEngine.reply(
                    source_file=input_p,
                    reply_str=args.reply,
                    resolved_by=args.resolved_by,
                )
                print(f"SUCCESS: Applied reply '{args.reply}' and updated status to RESOLVED in '{mod_path}'")
            except Exception as e:
                print(f"Error applying reply: {e}", file=sys.stderr)
                sys.exit(1)

        # Handle export / rendering
        if args.format == "all":
            results = QuestionnaireEngine.export_all(
                source=input_p,
                output_dir=args.output_dir,
                base_url=args.base_url,
            )
            print(f"SUCCESS: Exported all formats for '{input_p.name}':")
            for fmt, p in results.items():
                print(f"  - [{fmt.upper()}]: {p}")
        else:
            data = parse_questionnaire_markdown(input_p)
            out_dir = Path(args.output_dir) if args.output_dir else input_p.parent
            out_dir.mkdir(parents=True, exist_ok=True)
            stem = input_p.stem

            if args.format == "docx":
                target = out_dir / f"{stem}.docx"
                render_questionnaire_docx(data, target)
                print(f"SUCCESS: Generated DOCX at '{target}'")
            elif args.format == "html":
                target = out_dir / f"{stem}.html"
                render_questionnaire_html(data, target, base_url=args.base_url)
                print(f"SUCCESS: Generated HTML Form at '{target}'")
            elif args.format == "chat":
                target = out_dir / f"{stem}.chat.txt"
                target.write_text(render_chat_snippet(data), encoding="utf-8")
                print(f"SUCCESS: Generated Chat snippet at '{target}'")
            elif args.format == "email":
                target = out_dir / f"{stem}.email.html"
                target.write_text(render_email_table(data), encoding="utf-8")
                print(f"SUCCESS: Generated Email table at '{target}'")


if __name__ == "__main__":
    main()
