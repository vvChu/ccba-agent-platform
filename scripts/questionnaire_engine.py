#!/usr/bin/env python3
"""CCBA Questionnaire Engine CLI Launcher.

Unified CLI script for rendering, exporting, and resolving CCBA Questionnaires:
- Export to Word (.docx), Web HTML Form, Micro Chat, and Email Table.
- Two-way execution loop with --reply to resolve decisions and update Markdown AST.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

# Add project root and packages to sys.path
_ROOT_DIR = Path(__file__).resolve().parent.parent
_OOXML_SRC = _ROOT_DIR / "packages" / "ccba-ooxml" / "src"

if str(_OOXML_SRC) not in sys.path:
    sys.path.insert(0, str(_OOXML_SRC))
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))


def configure_utf8_output() -> None:
    """Ensure UTF-8 encoding on standard output for Windows console."""
    if sys.platform == "win32":
        try:
            if isinstance(sys.stdout, io.TextIOWrapper):
                sys.stdout.reconfigure(encoding="utf-8")
            if isinstance(sys.stderr, io.TextIOWrapper):
                sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass


def main() -> None:
    """Main CLI entrypoint for questionnaire_engine.py."""
    configure_utf8_output()

    parser = argparse.ArgumentParser(
        prog="questionnaire_engine.py",
        description="CCBA Dual-Track Questionnaire Engine v2.0 — Multi-format export and two-way resolution.",
    )
    parser.add_argument(
        "input",
        type=str,
        help="Path to input questionnaire markdown (.md) file",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["all", "docx", "html", "chat", "email"],
        default="all",
        help="Output format to render (default: all)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=None,
        help="Target output directory (default: same as input file)",
    )
    parser.add_argument(
        "--reply",
        type=str,
        default=None,
        help="Reply string to apply (e.g. '1A, 2B, 3C')",
    )
    parser.add_argument(
        "--resolved-by",
        type=str,
        default="Chủ đầu tư / Ban QLDA",
        help="Name/entity for decision log sign-off",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="",
        help="Optional server base URL for web hosting and QR code",
    )

    args = parser.parse_args()

    input_p = Path(args.input)
    if not input_p.exists():
        print(f"Error: Input file '{args.input}' does not exist.", file=sys.stderr)
        sys.exit(1)

    from ccba_ooxml.questionnaire import (
        QuestionnaireEngine,
        parse_questionnaire_markdown,
        render_chat_snippet,
        render_email_table,
        render_questionnaire_docx,
        render_questionnaire_html,
    )

    # 1. Apply reply if specified
    if args.reply:
        try:
            mod_path = QuestionnaireEngine.reply(
                source_file=input_p,
                reply_str=args.reply,
                resolved_by=args.resolved_by,
            )
            print(
                f"SUCCESS: Applied reply '{args.reply}' and updated status to RESOLVED in '{mod_path}'"
            )
        except Exception as e:
            print(f"Error applying reply: {e}", file=sys.stderr)
            sys.exit(1)

    # 2. Render requested format(s)
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
