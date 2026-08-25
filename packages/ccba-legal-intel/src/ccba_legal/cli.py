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
    """Build unified argument parser for ccba-legal CLI with logical lifecycle ordering."""
    parser = argparse.ArgumentParser(
        prog="ccba-legal",
        description="🏛️ CCBA Legal Intelligence & Universal OKF v2.2 Knowledge Engine CLI",
        epilog="""Ví dụ vận hành:
  python -m ccba_legal login
  python -m ccba_legal fetch "02/2022/TT-BXD" -o ".md/extracted_docs"
  python -m ccba_legal convert ".md/extracted_docs/qcvn_02_2022_bxd.docx" "legal_docs/02_qcvn/qcvn_02_2022_bxd"
  python -m ccba_legal consolidate -m "legal_docs/01_vbpl/luat_xd/patch_manifest.yaml" -b "legal_docs/01_vbpl/luat_xd/luat_xd.md" -o "legal_docs/01_vbpl/luat_xd"
  python -m ccba_legal process "legal_docs/02_qcvn/qcvn_02_2022_bxd"
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available lifecycle subcommands")

    # 1. Login Subcommand (Session Initialization & Persistence)
    login_parser = subparsers.add_parser(
        "login", help="Launch interactive Chromium browser with persistent TVPL VIP Profile on port 9222"
    )
    login_parser.add_argument(
        "--port", "-p", type=int, default=9222, help="Debugging port (default: 9222)"
    )
    login_parser.add_argument(
        "--url", "-u", type=str, default="https://thuvienphapluat.vn", help="Initial target URL"
    )

    # 2. Fetch Subcommand (Single Document Harvest)
    fetch_parser = subparsers.add_parser(
        "fetch", help="Crawl and download VIP Digital PDF and DOCX from TVPL"
    )
    fetch_parser.add_argument(
        "target", help="URL or Document ID/Number (e.g. '02/2022/TT-BXD' or 'https://thuvienphapluat.vn/...')"
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
        help="Desired download format: 'docx' (Gold source input), 'pdf' (VIP Digital Vector PDF), 'both' (default)",
    )

    # 3. Batch Fetch Subcommand (DAG Hierarchy Crawl)
    batch_fetch_parser = subparsers.add_parser(
        "batch-fetch", help="Batch crawl document hierarchy (DAG) from TVPL VIP"
    )
    batch_fetch_parser.add_argument(
        "root_target", help="Root document URL or ID to start batch crawl"
    )
    batch_fetch_parser.add_argument(
        "-d", "--depth", type=int, default=1, help="Max hierarchy depth (default: 1)"
    )
    batch_fetch_parser.add_argument(
        "-o", "--output-dir", type=Path, default=None, help="Directory to save extracted docs"
    )

    # 4. Convert Subcommand (OKF v2.2 Bundle Generation)
    convert_parser = subparsers.add_parser(
        "convert", help="Convert official .docx to OKF v2.2 Knowledge Bundle (Markdown + Atomic Templates)"
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
    convert_parser.add_argument(
        "--archetype",
        type=str,
        default=None,
        help="Force specific document archetype (VBPL_ADMIN, TECHNICAL_TCVN, TECHNICAL_QCVN, CIRCULAR_COST_NORM)",
    )

    # 5. Consolidate Subcommand (VBHN Engine)
    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Consolidate amending document into base document (VBHN Engine)"
    )
    consolidate_parser.add_argument(
        "--manifest", "-m", type=Path, required=True, help="Path to patch_manifest.yaml"
    )
    consolidate_parser.add_argument(
        "--base", "-b", type=Path, required=True, help="Path to base document .md"
    )
    consolidate_parser.add_argument(
        "--output", "-o", type=Path, required=True, help="Target consolidated document .md"
    )
    consolidate_parser.add_argument(
        "--amending",
        "-a",
        type=Path,
        default=None,
        help="Optional path to amending Markdown file (*.md)",
    )

    # 6. Lint Subcommand (Visual Parity & Cross-Link Verification)
    lint_parser = subparsers.add_parser(
        "lint", help="Lint OKF Markdown bundles for visual parity & link integrity (ADR 0029 & ADR 0030)"
    )
    lint_parser.add_argument("target_path", type=Path, help="Path to markdown file or OKF bundle directory")
    lint_parser.add_argument(
        "--no-links", action="store_true", help="Disable relative link and anchor verification"
    )

    # 7. Process Subcommand (AST Clauses & QA Benchmark Indexing)
    process_parser = subparsers.add_parser(
        "process", help="Process and index OKF bundle (AST clauses.json & QA benchmark dataset)"
    )
    process_parser.add_argument("bundle_dir", type=Path, help="Path to OKF bundle directory")
    process_parser.add_argument(
        "-t", "--type", default=None, help="Document type profile (vbpl, qcvn, tcvn)"
    )

    return parser


def handle_fetch(args: argparse.Namespace) -> int:
    """Handle fetch subcommand."""
    print("=================================================================")
    print("         CCBA LEGAL INTELLIGENCE (TVPL VIP CRAWLER)              ")
    print("=================================================================")
    print(f"🎯 Target: {args.target}")

    out_dir = args.output_dir or Path(".md/extracted_docs/tvpl_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        username, password = get_tvpl_credentials()
        print("🔐 Authenticating with TVPL VIP credentials from environment...")
    except OSError:
        print("ℹ️ No TVPL credentials found in environment. Proceeding with public/cache lookup...")

    crawler = TVPLCrawler(output_dir=out_dir)
    try:
        result = crawler.fetch_document(args.target)
        print(f"Result: {result}", flush=True)
        return 0
    except Exception as e:
        print(f"❌ Fetch Error: {e}", flush=True)
        return 1


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
        archetype=args.archetype,
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
def handle_batch_fetch(args: argparse.Namespace) -> int:
    """Handle batch-fetch subcommand."""
    print("=================================================================")
    print("    CCBA LEGAL INTELLIGENCE (TVPL VIP BATCH TREE CRAWLER)       ")
    print("=================================================================")
    print(f"🎯 Root Target: {args.root_target}")
    print(f"🌲 Max Depth: {args.depth}")

    out_dir = args.output_dir or Path(".md/extracted_docs")
    out_dir.mkdir(parents=True, exist_ok=True)

    from ccba_legal.crawler import TVPLBatchCrawler

    batch_crawler = TVPLBatchCrawler(output_dir=out_dir)
    try:
        results = batch_crawler.crawl_hierarchy(args.root_target, max_depth=args.depth)
        print(f"✅ Batch Crawl Completed! Processed {len(results)} documents.")
        return 0
    except Exception as e:
        print(f"❌ Batch Fetch Error: {e}")
        return 1


def handle_login(args: argparse.Namespace) -> int:
    """Launch interactive Chromium browser for persistent VIP authentication."""
    import subprocess

    port = args.port
    user_data = Path.home() / ".gemini" / "antigravity" / "chrome_vip"
    user_data.mkdir(parents=True, exist_ok=True)

    browser_candidates = [
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    ]
    browser_exe = None
    for cand in browser_candidates:
        if cand.exists():
            browser_exe = cand
            break

    if not browser_exe:
        print("[Error] No Chromium browser (Chrome/Edge) found on system.")
        return 1

    print("=================================================================")
    print("          CCBA LEGAL INTEL - TVPL VIP LOGIN LAUNCHER             ")
    print("=================================================================")
    print(f"🌐 Launching: {browser_exe.name} on remote debugging port {port}")
    print(f"📁 Persistent Profile: {user_data}")
    print(f"🎯 Target: {args.url}")
    print("-----------------------------------------------------------------")
    print("💡 Please log in to your VIP account in the opened browser.")
    print("   The session cookies will be preserved for all CLI commands.")
    print("=================================================================")

    try:
        subprocess.Popen([
            str(browser_exe),
            f"--remote-debugging-port={port}",
            f"--user-data-dir={user_data}",
            "--no-first-run",
            "--no-default-browser-check",
            args.url,
        ])
        return 0
    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")
        return 1


def handle_lint(args: argparse.Namespace) -> int:
    """Handle lint subcommand."""
    print("=================================================================")
    print("     CCBA LEGAL INTEL - VISUAL PARITY & LINK LINTER GATE         ")
    print("=================================================================")
    print(f"🎯 Target Path: {args.target_path}")

    from ccba_legal.linter import lint_target_path

    res = lint_target_path(args.target_path, check_links=not args.no_links)

    print("-----------------------------------------------------------------")
    print(f"Scanned files  : {res['files_scanned']}")
    print(f"Format errors  : {res['format_errors']}")
    print(f"Link errors    : {res['link_errors']}")
    print("-----------------------------------------------------------------")

    if res["total_errors"] > 0:
        print("❌ [FAIL] Issues detected:")
        for item in res["details"]:
            for err in item.get("errors", []):
                print(f"  - {err}")
            for lerr in item.get("link_errors", []):
                print(f"  - {lerr}")
        return 1

    print("✅ PASSED: 100% Visual Parity & Zero Broken Links!")
    return 0


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)

    parser = build_parser()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "login":
        sys.exit(handle_login(args))
    elif args.command == "fetch":
        sys.exit(handle_fetch(args))
    elif args.command == "batch-fetch":
        sys.exit(handle_batch_fetch(args))
    elif args.command == "convert":
        sys.exit(handle_convert(args))
    elif args.command == "process":
        sys.exit(handle_process(args))
    elif args.command == "consolidate":
        sys.exit(handle_consolidate(args))
    elif args.command == "lint":
        sys.exit(handle_lint(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
