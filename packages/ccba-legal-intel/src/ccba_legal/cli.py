"""CCBA Legal Intelligence Unified CLI Dispatcher.

Provides standard command-line interfaces for:
- fetch: Crawl/Download official DOCX/PDF from TVPL VIP
- convert: Convert DOCX to Gold Standard OKF v2.2 Bundles
- process: Generate AST clauses.json and QA Benchmark for OKF Bundles
- consolidate: Patch amending documents into consolidated base document (VBHN)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ccba_legal.consolidator import LegislativeConsolidator
from ccba_legal.crawler import TVPLCrawler, download_three_tier, get_tvpl_credentials
from ccba_legal.docx_converter import convert_docx_to_okf_bundle
from ccba_legal.gold_standard import GoldStandardProcessor


def build_parser() -> argparse.ArgumentParser:
    """Build unified argument parser for ccba-legal CLI."""
    parser = argparse.ArgumentParser(
        prog="ccba-legal",
        description="CCBA Legal Intelligence & OKF Knowledge Engine CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # 1. Fetch Subcommand
    fetch_parser = subparsers.add_parser(
        "fetch", help="Crawl and download legal documents from TVPL VIP"
    )
    fetch_parser.add_argument(
        "target", help="URL or Document ID/Number (e.g. 'https://thuvienphapluat.vn/...')"
    )
    fetch_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Target output directory for downloaded assets",
    )
    fetch_parser.add_argument(
        "--format",
        "-f",
        choices=["docx", "pdf", "both"],
        default="both",
        help="Desired download format (default: both)",
    )

    # 2. Convert Subcommand
    convert_parser = subparsers.add_parser(
        "convert", help="Convert official .docx to OKF v2.2 Knowledge Bundle"
    )
    convert_parser.add_argument("docx_path", type=Path, help="Path to input .docx file")
    convert_parser.add_argument(
        "target_bundle_dir", type=Path, help="Path to target OKF bundle directory"
    )
    convert_parser.add_argument(
        "-o", "--output-filename", type=str, default=None, help="Custom output markdown filename"
    )
    convert_parser.add_argument(
        "-t",
        "--doc-type",
        type=str,
        default=None,
        help="Document type profile (vbpl, qcvn, tcvn)",
    )
    convert_parser.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )

    # 3. Process Subcommand
    process_parser = subparsers.add_parser(
        "process", help="Process and index OKF bundle (AST clauses & QA benchmark)"
    )
    process_parser.add_argument("bundle_dir", type=Path, help="Path to OKF bundle directory")
    process_parser.add_argument(
        "-t", "--type", default=None, help="Document type profile (vbpl, qcvn, tcvn)"
    )

    # 4. Consolidate Subcommand
    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Consolidate amending document into base document (VBHN)"
    )
    consolidate_parser.add_argument(
        "--manifest", "-m", type=Path, required=True, help="Path to patch_manifest.yaml"
    )
    consolidate_parser.add_argument(
        "--base", "-b", type=Path, required=True, help="Path to base Markdown file (*.md)"
    )
    consolidate_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Output directory for VBHN bundle"
    )
    consolidate_parser.add_argument(
        "--amending",
        "-a",
        type=Path,
        default=None,
        help="Optional path to amending Markdown file (*.md)",
    )

    return parser


def handle_fetch(args: argparse.Namespace) -> int:
    """Handle fetch subcommand."""
    print("=================================================================")
    print("         CCBA LEGAL INTELLIGENCE (TVPL VIP CRAWLER)              ")
    print("=================================================================")
    print(f"🎯 Target: {args.target}")

    try:
        username, password = get_tvpl_credentials()
        print("🔐 Authenticating with TVPL VIP credentials from environment...")
    except OSError as e:
        print(f"❌ Authentication Error: {e}")
        return 1

    out_dir = args.output_dir or Path(".md/extracted_docs/tvpl_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)

    crawler = TVPLCrawler(username=username, password=password)
    result = download_three_tier(crawler, args.target, out_dir)
    print(f"Result: {result}")
    return 0 if result.get("status") in ("success", "downloaded") else 1


def handle_convert(args: argparse.Namespace) -> int:
    """Handle convert subcommand."""
    print("=================================================================")
    print("      CCBA UNIVERSAL DOCX CONVERTER ENGINE (OKF v2.2)            ")
    print("=================================================================")
    print(f"📄 DOCX File: {args.docx_path}")
    print(f"📁 Target Bundle: {args.target_bundle_dir}")

    res = convert_docx_to_okf_bundle(
        docx_path=args.docx_path,
        target_bundle_dir=args.target_bundle_dir,
        output_filename=args.output_filename,
        doc_type=args.doc_type,
        registry_file=args.registry,
    )
    print("\n[COMPLETE OKF BUNDLE RESULT]:", json.dumps(res, indent=2, ensure_ascii=False))
    return 0 if res.get("status") == "success" else 1


def handle_process(args: argparse.Namespace) -> int:
    """Handle process subcommand."""
    print("=================================================================")
    print("        CCBA OKF BUNDLE GOLD STANDARD PROCESSOR                  ")
    print("=================================================================")
    print(f"📁 Bundle Dir: {args.bundle_dir}")

    res = GoldStandardProcessor.process_bundle(args.bundle_dir, doc_type=args.type)
    print(f"Result: {res}")
    return 0 if res.get("status") == "success" else 1


def handle_consolidate(args: argparse.Namespace) -> int:
    """Handle consolidate subcommand."""
    print("=================================================================")
    print("        CCBA LEGISLATIVE CONSOLIDATOR (VBHN Engine)              ")
    print("=================================================================")
    print(f"📄 Manifest: {args.manifest}")
    print(f"📄 Base: {args.base}")
    print(f"📁 Output: {args.output}")

    consolidator = LegislativeConsolidator.from_manifest_file(args.manifest)
    res = consolidator.consolidate(
        base_md_path=args.base,
        output_dir=args.output,
        amending_md_path=args.amending,
    )
    print(f"Status: {res.status}, Patches Applied: {len(res.patches_applied)}")
    if res.errors:
        print(f"Errors: {res.errors}")
        return 1
    return 0


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "fetch":
        sys.exit(handle_fetch(args))
    elif args.command == "convert":
        sys.exit(handle_convert(args))
    elif args.command == "process":
        sys.exit(handle_process(args))
    elif args.command == "consolidate":
        sys.exit(handle_consolidate(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
