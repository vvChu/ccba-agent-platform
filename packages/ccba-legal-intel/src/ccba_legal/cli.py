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
import os
import shutil
import sys
from pathlib import Path

from ccba_legal.consolidator import LegislativeConsolidator
from ccba_legal.crawler import TVPLCrawler, get_tvpl_credentials
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
        "login",
        help="Launch interactive Chromium browser with persistent TVPL VIP Profile on port 9222",
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
        "target",
        help="URL or Document ID/Number (e.g. '02/2022/TT-BXD' or 'https://thuvienphapluat.vn/...')",
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
        "convert",
        help="Convert official .docx to OKF v2.2 Knowledge Bundle (Markdown + Atomic Templates)",
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
        "lint",
        help="Lint OKF Markdown bundles for visual parity & link integrity (ADR 0029 & ADR 0030)",
    )
    lint_parser.add_argument(
        "target_path", type=Path, help="Path to markdown file or OKF bundle directory"
    )
    lint_parser.add_argument(
        "--no-links", action="store_true", help="Disable relative link and anchor verification"
    )
    lint_parser.add_argument(
        "-c",
        "--check-currency",
        action="store_true",
        help="Audit legal citations for obsolete/repealed statutes (ADR 0050 & ADR 0058)",
    )
    lint_parser.add_argument(
        "--json", action="store_true", help="Output results in raw JSON format"
    )
    lint_parser.add_argument(
        "-r",
        "--registry",
        type=Path,
        default=None,
        help="Optional path to legal_registry.yaml",
    )

    # 7. Sync Subcommand (Automated Spoke OKF Sync & Cloud Vault - ADR 0050)
    sync_parser = subparsers.add_parser(
        "sync",
        help="Synchronize OKF v2.4 legal bundles to Spoke or Google Drive/NotebookLM (ADR 0050)",
    )
    sync_parser.add_argument(
        "--pull-latest",
        action="store_true",
        default=False,
        help="Pull latest OKF bundles and merge registry into local Spoke",
    )
    sync_parser.add_argument(
        "--reference-only",
        action="store_true",
        default=False,
        help="Only merge legal_registry.yaml without physically copying legal_docs/ bundles (Zero-Bloat Reference Architecture).",
    )
    sync_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Target legal_docs output directory (default: .md/legal_docs for consuming spokes, legal_docs for master spoke)",
    )
    sync_parser.add_argument(
        "--doc", type=str, default=None, help="Specific document ID or number to sync"
    )
    sync_parser.add_argument(
        "--source-corpus",
        type=Path,
        default=None,
        help="Explicit path to ccba-legal-knowledge repository",
    )
    sync_parser.add_argument(
        "--to-notebooklm",
        action="store_true",
        default=False,
        help="Sync local registry to Google NotebookLM",
    )
    sync_parser.add_argument(
        "--notebook-id", type=str, default=None, help="Target NotebookLM Notebook ID"
    )
    sync_parser.add_argument(
        "--use-drive",
        action="store_true",
        default=False,
        help="Use Google Drive intermediary for NotebookLM sync",
    )
    sync_parser.add_argument(
        "--drive-folder",
        type=str,
        default="1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2",
        help="Google Drive folder ID",
    )
    sync_parser.add_argument(
        "--download-pdf",
        action="store_true",
        default=False,
        help="Download temporary PDFs before uploading to Drive",
    )
    sync_parser.add_argument(
        "--clean-drive",
        action="store_true",
        default=False,
        help="Clean Google Drive folder before sync",
    )

    # 8. Ingest Subcommand (Universal End-to-End OKF Ingestion Pipeline 2.0)
    ingest_parser = subparsers.add_parser(
        "ingest",
        help="Universal 1-command autonomous ingestion from TVPL VIP to OKF Bundle and Drive Vault (ADR 0035)",
    )
    ingest_parser.add_argument(
        "target", help="URL or Document ID/Number (e.g. '01/2021/TT-BXD' or TVPL URL)"
    )
    ingest_parser.add_argument(
        "-c",
        "--category",
        choices=["01_vbpl", "02_qcvn", "03_tcvn"],
        default="01_vbpl",
        help="Document category",
    )
    ingest_parser.add_argument(
        "-o", "--output-dir", type=Path, default=None, help="Spoke legal_docs output root"
    )
    ingest_parser.add_argument(
        "--upload-drive",
        action="store_true",
        default=False,
        help="Upload binary assets to Google Drive Vault (ADR 0035)",
    )
    ingest_parser.add_argument(
        "-s",
        "--slug",
        default=None,
        help="Explicit OKF bundle directory slug (e.g. 'qcvn_09_2017_bxd')",
    )

    # 8b. Hydrate Subcommand (Spoke Vault Hydration Engine - ADR 0035 & ADR 0059)
    hydrate_parser = subparsers.add_parser(
        "hydrate",
        help="Hydrate binary assets (PDF/DOCX) from Cloud Vault with cryptographic SHA-256 verification (ADR 0035)",
    )
    hydrate_parser.add_argument(
        "--cohorts",
        type=str,
        default=None,
        help="Comma-separated list of document slugs (e.g. 'qcvn_04_2021_bxd,qcvn_06_2022_bxd')",
    )
    hydrate_parser.add_argument(
        "-c",
        "--category",
        choices=["01_vbpl", "02_qcvn", "03_tcvn"],
        default=None,
        help="Filter by legal document category",
    )
    hydrate_parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Hydrate all documents across all categories",
    )
    hydrate_parser.add_argument(
        "--verify-only",
        action="store_true",
        default=False,
        help="Only verify SHA-256 integrity of local assets without downloading",
    )
    hydrate_parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Force re-download even if file already exists locally",
    )
    hydrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Simulate hydration without writing any files",
    )
    hydrate_parser.add_argument(
        "--spoke-dir",
        type=Path,
        default=None,
        help="Root path of the Spoke repository (defaults to current project root)",
    )

    # 9. Google Drive Ingestion Subcommand
    ingest_gdrive_parser = subparsers.add_parser(
        "ingest-gdrive",
        help="Scan and ingest knowledge documents from Google Drive (3 zones: My Drive, Shared With Me, Shared Drives)",
    )
    ingest_gdrive_parser.add_argument(
        "--scope",
        choices=["all", "my-drive", "shared", "drives"],
        default="all",
        help="Scanning scope: 'all', 'my-drive', 'shared' (Shared with me), 'drives' (Shared Drives)",
    )
    ingest_gdrive_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path(".md/extracted_docs/gdrive"),
        help="Target output directory for ingested assets (default: .md/extracted_docs/gdrive)",
    )
    ingest_gdrive_parser.add_argument(
        "--folder-id",
        type=str,
        default=None,
        help="Optional specific Google Drive folder ID to scan",
    )
    ingest_gdrive_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate scanning without downloading files",
    )
    ingest_gdrive_parser.add_argument(
        "--force",
        action="store_true",
        help="Force redownload even if file is present in registry",
    )

    # 10. Clean Images Subcommand (Zero-Orphan Figure Pruner - ADR 0036)
    clean_parser = subparsers.add_parser(
        "clean-images",
        help="Scan and prune unreferenced orphan figure images from legal bundle (ADR 0036)",
    )
    clean_parser.add_argument(
        "bundle_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to specific legal bundle directory",
    )
    clean_parser.add_argument(
        "--all",
        action="store_true",
        help="Scan all legal bundles in repository",
    )
    clean_parser.add_argument(
        "--prune",
        action="store_true",
        help="Permanently delete unreferenced orphan images (default: dry-run report)",
    )

    # 11. Query Subcommand (Master Registry & Lifecycle Search)
    query_parser = subparsers.add_parser(
        "query",
        help="Search legal registry and knowledge corpus with lifecycle status and replacement warnings",
    )
    query_parser.add_argument(
        "search_query",
        help="Search keyword or document number (e.g. 'Luật Xây dựng', '135/2025/QH15')",
    )
    query_parser.add_argument(
        "-k", "--top-k", type=int, default=5, help="Number of results to return (default: 5)"
    )
    query_parser.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )
    query_parser.add_argument(
        "-c", "--corpus", type=Path, default=None, help="Path to legal_docs corpus directory"
    )
    query_parser.add_argument(
        "--json", action="store_true", help="Output results in raw JSON format"
    )
    query_parser.add_argument(
        "--include-expired",
        action="store_true",
        default=False,
        help="Bao gồm cả các văn bản quy phạm đã hết hiệu lực thi hành hoặc bị thay thế.",
    )

    # 12. Get-Clause Subcommand (Tier-Aware Clause Slicing)
    clause_parser = subparsers.add_parser(
        "get-clause",
        help="Extract specific clause/article Markdown from OKF bundle using tier-aware semantic slicing",
    )
    clause_parser.add_argument(
        "-d",
        "--doc",
        required=True,
        help="Document ID or slug (e.g. 'Luat-Xay-dung-2025-135-2025-QH15')",
    )
    clause_parser.add_argument(
        "-c",
        "--clause",
        required=True,
        help="Clause ID or alias (e.g. 'd1', 'dieu-1', 'd15k2')",
    )
    clause_parser.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )
    clause_parser.add_argument(
        "--corpus", type=Path, default=None, help="Path to legal_docs corpus directory"
    )
    clause_parser.add_argument(
        "--json", action="store_true", help="Output clause in raw JSON format"
    )

    # 13. Get-Table Subcommand (Table Matrix Extractor)
    table_parser = subparsers.add_parser(
        "get-table",
        help="Extract table matrix from OKF bundle in Markdown or CSV format",
    )
    table_parser.add_argument(
        "-d",
        "--doc",
        required=True,
        help="Document ID or slug (e.g. 'qcvn_06_2022_bxd')",
    )
    table_parser.add_argument(
        "-t",
        "--table",
        required=True,
        help="Table ID (e.g. 'bang_01')",
    )
    table_parser.add_argument(
        "-f",
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format: markdown (default) or csv",
    )
    table_parser.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )
    table_parser.add_argument(
        "--corpus", type=Path, default=None, help="Path to legal_docs corpus directory"
    )
    table_parser.add_argument("--json", action="store_true", help="Output table in raw JSON format")

    # 13. Compile Registry Subcommand (Sharded Metadata Compiler)
    compile_reg_parser = subparsers.add_parser(
        "compile-registry",
        help="Compile sharded metadata.yaml bundles into consolidated legal_registry.yaml",
    )
    compile_reg_parser.add_argument(
        "--docs-dir",
        "-d",
        type=Path,
        default=None,
        help="Directory containing legal document bundles with metadata.yaml (default: legal_docs or .md/legal_docs)",
    )
    compile_reg_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to output legal_registry.yaml (default: .md/data/legal_registry.yaml or legal_registry.yaml)",
    )
    compile_reg_parser.add_argument(
        "--base",
        "-b",
        type=Path,
        default=None,
        help="Base registry to preserve non-document sections (metadata, monitoring, seminars)",
    )
    compile_reg_parser.add_argument(
        "--check",
        action="store_true",
        help="Dry-run verification mode. Exit 0 if registry matches shards, exit 1 if out of sync",
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
    patches_count = res.modified_clauses + res.added_clauses + res.repealed_clauses
    status_str = "success" if res.success else "failed"
    print(f"Status: {status_str}, Patches Applied: {patches_count}")
    if not res.success or res.errors:
        print(f"Errors: {res.errors}")
        return 1
    return 0


def handle_hydrate(args: argparse.Namespace) -> int:
    """Handle hydrate subcommand."""
    print("=================================================================")
    print("      CCBA SPOKE VAULT HYDRATION ENGINE (ADR 0035 / ADR 0059)     ")
    print("=================================================================")
    from ccba_legal.hydrator import SpokeHydrator
    from ccba_legal.registry import resolve_project_root

    if args.spoke_dir:
        spoke_root = args.spoke_dir.resolve()
    elif (Path.cwd() / "legal_docs").exists() or (Path.cwd() / "legal_registry.yaml").exists():
        spoke_root = Path.cwd().resolve()
    else:
        spoke_root = resolve_project_root()
    cohorts_list = [s.strip() for s in args.cohorts.split(",")] if args.cohorts else None

    print(f"🎯 Target Spoke: {spoke_root}")
    if cohorts_list:
        print(f"📦 Cohorts ({len(cohorts_list)}): {', '.join(cohorts_list)}")
    if args.category:
        print(f"📁 Category: {args.category}")
    print(f"⚙️ Mode: {'Verify-Only' if args.verify_only else 'Hydrate'}")
    if args.force:
        print("⚡ Force overwrite: True")
    if args.dry_run:
        print("🔍 Dry-run: True")
    print("-----------------------------------------------------------------")

    hydrator = SpokeHydrator(spoke_root=spoke_root)
    summary = hydrator.hydrate_all(
        category=args.category,
        cohorts=cohorts_list,
        force=args.force,
        verify_only=args.verify_only,
        dry_run=args.dry_run,
    )

    print(f"\n📊 HYDRATION SUMMARY ({summary.total_bundles} bundles inspected):")
    print(f"   🟢 Fully Hydrated   : {summary.fully_hydrated}")
    print(f"   🟡 Partially Hydrated: {summary.partially_hydrated}")
    print(f"   🔴 Unhydrated        : {summary.unhydrated}")
    print(f"   📄 Assets - Total   : {summary.total_assets}")
    print(f"   ✅ Up-to-Date       : {summary.up_to_date_assets}")
    print(f"   📥 Downloaded       : {summary.downloaded_assets}")
    print(f"   ⚠️ Missing          : {summary.missing_assets}")
    print(f"   ❌ Failed / Corrupt : {summary.failed_assets}")

    if summary.failed_assets > 0:
        print("\n❌ Errors encountered during hydration!")
        return 1
    if args.verify_only and summary.missing_assets > 0:
        print("\n⚠️ Note: Some assets are missing from local sources/.")
    return 0


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
    from ccba_legal.session import get_browser_executable_path

    port = args.port
    user_data = Path.home() / ".gemini" / "antigravity" / "chrome_vip"
    user_data.mkdir(parents=True, exist_ok=True)

    browser_path = get_browser_executable_path()
    if not browser_path:
        print("[Error] No Chromium browser (Chrome/Edge/Chromium/Brave) found on system.")
        print("        Please set CHROME_PATH environment variable or install Google Chrome.")
        return 1
    browser_exe = Path(browser_path)

    # Cảnh báo môi trường headless Linux
    import os
    if os.name != "nt" and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print("⚠️ Warning: Running on a headless Linux environment without DISPLAY.")
        print("   If browser fails to launch, please run via 'xvfb-run python -m ccba_legal login'")

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
        subprocess.Popen(
            [
                str(browser_exe),
                f"--remote-debugging-port={port}",
                "--remote-allow-origins=*",
                f"--user-data-dir={user_data}",
                "--no-first-run",
                "--no-default-browser-check",
                args.url,
            ]
        )
        return 0
    except Exception as e:
        print(f"❌ Failed to launch browser: {e}")
        return 1


def handle_lint(args: argparse.Namespace) -> int:
    """Handle lint subcommand with visual parity, link integrity, and legal currency gates."""
    from ccba_legal.linter import lint_target_path

    check_curr = getattr(args, "check_currency", False)
    reg_path = getattr(args, "registry", None)
    res = lint_target_path(
        args.target_path,
        check_links=not args.no_links,
        check_currency=check_curr,
        registry_path=reg_path,
    )

    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 1 if res["total_errors"] > 0 else 0

    banner_title = (
        "CCBA LEGAL INTEL - VISUAL PARITY & LEGAL CURRENCY LINTER"
        if check_curr
        else "CCBA LEGAL INTEL - VISUAL PARITY & HYPERLINK INTEGRITY LINTER"
    )
    print("=================================================================")
    print(f"     {banner_title}    ")
    print("=================================================================")
    print(f"🎯 Target Path: {args.target_path}")
    print("-----------------------------------------------------------------")
    print(f"Scanned files    : {res['files_scanned']}")
    print(f"Format errors    : {res['format_errors']}")
    print(f"Link errors      : {res['link_errors']}")
    if check_curr:
        print(f"Currency errors  : {res.get('currency_errors', 0)} (Khóa cứng ADR-0058)")
        print(f"Currency warnings: {res.get('currency_warnings', 0)}")
    print("-----------------------------------------------------------------")

    # Format & Link issues
    if res["format_errors"] > 0 or res["link_errors"] > 0:
        print("\n❌ [FORMAT & LINK ISSUES DETECTED]:")
        for item in res["details"]:
            for err in item.get("errors", []):
                print(f"  • {item.get('file', '')} -> {err}")
            for lerr in item.get("link_errors", []):
                print(f"  • {item.get('file', '')} -> {lerr}")

    # Legal Currency issues (only shown when currency checks are enabled)
    if check_curr:
        curr_findings = res.get("currency_findings", [])
        errors_list = [f for f in curr_findings if f.get("severity") == "ERROR"]
        warnings_list = [f for f in curr_findings if f.get("severity") == "WARNING"]

        if errors_list:
            print("\n🔴 [VĂN BẢN HẾT HIỆU LỰC / OBSOLETE CITATIONS] (Vi phạm ADR-0058):")
            for f in errors_list:
                f_name = Path(f["file"]).name
                print(f"  • [{f_name}] [{f['location']}]")
                print(f"    - Viện dẫn : {f['matched_text']} ({f['obsolete_doc']})")
                print(f"    - Thay thế : 👉 {f['replacement']}")
                if f.get("context"):
                    print(f'    - Ngữ cảnh : "{f["context"]}"')

        if warnings_list:
            print("\n⚠️ [VĂN BẢN CHƯA XÁC THỰC / UNVERIFIED CITATIONS] (Cần đối soát):")
            for f in warnings_list:
                f_name = Path(f["file"]).name
                print(
                    f"  • [{f_name}] [{f['location']}]: {f['matched_text']} -> {f['replacement']}"
                )

    print("\n=================================================================")
    if res["total_errors"] > 0:
        print(
            "❌ [FAIL] Khóa cứng ADR-0058: Phát hiện lỗi định dạng, liên kết hoặc văn bản bãi bỏ!"
        )
        return 1

    if check_curr and res.get("currency_warnings", 0) > 0:
        print(
            "⚠️ [PASSED WITH WARNINGS] Zero lỗi nghiêm trọng. Vui lòng rà soát cảnh báo văn bản chưa xác thực."
        )
        return 0

    if check_curr:
        print("✅ [PASSED] 100% Visual Parity, Zero Broken Links & Zero Obsolete Citations!")
    else:
        print("✅ [PASSED] 100% Visual Parity & Zero Broken Links!")
    return 0


def handle_ingest(args: argparse.Namespace) -> int:
    """Handle universal 1-command ingestion pipeline (ADR 0035)."""
    print("=================================================================")
    print("     CCBA LEGAL INTEL - UNIVERSAL INGESTION PIPELINE 2.0         ")
    print("=================================================================")
    print(f"🎯 Target: {args.target}")
    print(f"📂 Category: {args.category}")

    # 1. Fetch dual assets from TVPL
    out_dir = Path(".md/extracted_docs/tvpl_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)
    crawler = TVPLCrawler(output_dir=out_dir)
    print("\n>>> [1/5] Fetching official DOCX & PDF from TVPL VIP...")
    try:
        fetch_res = crawler.fetch_document(args.target)
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return 1

    if not fetch_res or not fetch_res.get("docx_path"):
        print("❌ Ingestion failed: Could not fetch DOCX source file.")
        return 1

    docx_path = Path(fetch_res["docx_path"])
    pdf_path = Path(fetch_res["pdf_path"]) if fetch_res.get("pdf_path") else None
    doc_slug = args.slug if args.slug else docx_path.stem.lower().replace("-", "_")

    # 2. Determine target bundle directory & create mandatory sources/ (OKF v2.4)
    base_out = args.output_dir or Path("legal_docs")
    target_bundle = base_out / args.category / doc_slug
    target_bundle.mkdir(parents=True, exist_ok=True)

    sources_dir = target_bundle / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    target_docx = sources_dir / (f"{doc_slug}.docx" if args.slug else docx_path.name)
    target_pdf = sources_dir / (
        f"{doc_slug}.pdf"
        if (args.slug and pdf_path)
        else (pdf_path.name if pdf_path else "doc.pdf")
    )
    raw_scan_target = sources_dir / f"{doc_slug}_raw_scan.pdf"
    if docx_path.exists():
        shutil.copy2(docx_path, target_docx)

    pdf_tier = fetch_res.get("pdf_tier") if isinstance(fetch_res, dict) else None
    is_vector_rendered = False

    # Nếu là bản Scan Tier 3 và có file DOCX: Kích hoạt ADR 0043 Dual-PDF
    if pdf_tier == 3 and target_docx.exists():
        print(f"[LegalIntel] [ADR 0043 Dual-PDF] Detected Tier 3 Gazette Scan.")
        if pdf_path and pdf_path.exists():
            shutil.copy2(pdf_path, raw_scan_target)
            print(f"  📦 Preserved official Gazette Scan: {raw_scan_target.name}")
        try:
            from ccba_ooxml.converter import convert_to_pdf

            print(f"  ⚙️ Rendering Born-Digital Vector PDF via LibreOffice...")
            convert_to_pdf(target_docx, target_pdf)
            print(f"  ✅ Successfully rendered Vector PDF: {target_pdf.name}")
            is_vector_rendered = True
        except Exception as e:
            print(f"  ⚠️ Vector PDF conversion failed ({e}), falling back to scan.")
            if pdf_path and pdf_path.exists():
                shutil.copy2(pdf_path, target_pdf)
            is_vector_rendered = False
    else:
        if pdf_path and pdf_path.exists():
            shutil.copy2(pdf_path, target_pdf)
        is_vector_rendered = False

    # 3. Google Drive Vault Upload (if requested or available)

    if args.upload_drive:
        print("\n>>> [2/5] Uploading binary assets to Google Drive Vault (ADR 0035)...")
        try:
            from ccba_legal.gdrive_vault import GoogleDriveVault

            vault = GoogleDriveVault()
            if vault.is_available():
                vault.upload_asset(target_docx, args.category, doc_slug)
                if target_pdf.exists():
                    vault.upload_asset(target_pdf, args.category, doc_slug)
                if raw_scan_target.exists():
                    vault.upload_asset(raw_scan_target, args.category, doc_slug)
                print("  ✅ Uploaded to Google Drive Vault successfully.")
            else:
                print("  ℹ️ Google Drive Vault offline. Proceeding in local mode.")
        except Exception as ve:
            print(f"  ⚠️ Drive upload warning: {ve}")

    # 4. Convert DOCX to OKF Bundle
    print(f"\n>>> [3/5] Converting to OKF Bundle with resilient parser at {target_bundle}...")
    try:
        convert_docx_to_okf_bundle(
            docx_path=target_docx,
            target_bundle_dir=target_bundle,
            doc_type=args.category,
        )
        if is_vector_rendered and (target_bundle / "metadata.yaml").exists():
            import hashlib
            import yaml

            meta_path = target_bundle / "metadata.yaml"
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}
            meta["pdf_origin"] = "docx_vector_rendered"
            if raw_scan_target.exists():
                meta["raw_scan_pdf"] = f"sources/{raw_scan_target.name}"
            if "source_assets" in meta and isinstance(meta["source_assets"], dict):
                if "pdf" in meta["source_assets"] and isinstance(meta["source_assets"]["pdf"], dict):
                    meta["source_assets"]["pdf"]["origin"] = "docx_vector_rendered"
                if raw_scan_target.exists() and "raw_scan" not in meta["source_assets"]:
                    raw_hash = hashlib.sha256(raw_scan_target.read_bytes()).hexdigest()
                    meta["source_assets"]["raw_scan"] = {
                        "sha256": raw_hash,
                        "vault_path": f"CCBA_Legal_Vault/{args.category}/{doc_slug}/{raw_scan_target.name}",
                        "status": "verified",
                        "acquisition_method": "official_gazette_scan",
                    }
            with open(meta_path, "w", encoding="utf-8") as f:
                yaml.dump(meta, f, allow_unicode=True, sort_keys=False)
    except Exception as ce:
        print(f"❌ Conversion Error: {ce}")
        return 1

    # 5. Process AST & Benchmark
    print("\n>>> [4/5] Processing AST clauses and QA benchmark dataset...")
    try:
        processor = GoldStandardProcessor()
        processor.process_bundle(target_bundle, doc_type=args.category)
    except Exception as pe:
        print(f"⚠️ AST processing warning: {pe}")

    # 6. Lint and Verify
    print("\n>>> [5/5] Running visual parity and link verification...")
    try:
        from ccba_legal.linter import lint_target_path

        lint_res = lint_target_path(target_bundle, check_links=True)
        if lint_res["total_errors"] > 0:
            print(f"⚠️ Lint warning: {lint_res['total_errors']} issues detected during ingestion.")
        else:
            print("✅ 100% Visual Parity & Zero Broken Links!")
    except Exception as le:
        print(f"⚠️ Lint verification warning: {le}")

    print("\n=================================================================")
    print("🎉 Ingestion Pipeline 2.0 Completed Successfully!")
    print(f"📁 Output Bundle: {target_bundle.resolve()}")
    print("=================================================================")
    return 0


def handle_sync(args: argparse.Namespace) -> int:
    """Handle sync subcommand (ADR 0050)."""
    print("=================================================================")
    print("     CCBA LEGAL INTEL - AUTOMATED LEGAL KNOWLEDGE SYNC           ")
    print("=================================================================")

    from ccba_legal.sync import LegalSyncEngine

    engine = LegalSyncEngine()

    if args.to_notebooklm or args.notebook_id:
        import asyncio

        notebook_id = args.notebook_id or os.environ.get("NOTEBOOKLM_NOTEBOOK_ID")
        if not notebook_id:
            print(
                "[Error] Thiếu Notebook ID. Cung cấp qua --notebook-id hoặc biến NOTEBOOKLM_NOTEBOOK_ID."
            )
            return 1

        reg_p = (
            Path(args.registry)
            if hasattr(args, "registry") and args.registry
            else Path(".md/data/legal_registry.yaml")
        )
        sources_p = Path(".md/data/sources_registry.yaml")

        print(f"🔄 Syncing registry {reg_p} to NotebookLM {notebook_id}...")
        try:
            asyncio.run(
                engine.sync_registry_to_notebooklm(
                    registry_path=reg_p,
                    sources_reg_path=sources_p,
                    notebook_id=notebook_id,
                    use_drive=args.use_drive,
                    drive_folder_id=args.drive_folder,
                    download_pdf=args.download_pdf,
                    clean_drive=args.clean_drive,
                )
            )
            print("✅ Cloud NotebookLM Sync Completed Successfully!")
            return 0
        except Exception as e:
            print(f"❌ Cloud Sync Error: {e}")
            return 1

    # Spoke Pull Mode (Tier 1 Local Corpus -> Tier 2 Cloud Vault)
    is_ref_only = getattr(args, "reference_only", False)
    if is_ref_only:
        print(
            "⚡ [Zero-Bloat Reference Architecture] Kéo tham chiếu legal_registry.yaml, không sao chép legal_docs/..."
        )
    else:
        print("📥 Pulling latest OKF v2.4 legal bundles into Spoke...")

    doc_ids = [args.doc] if args.doc else None
    res = engine.pull_latest_okf_bundles(
        target_dir=args.output_dir,
        doc_ids=doc_ids,
        source_corpus_dir=args.source_corpus,
        update_registry=True,
        pull_assets=not is_ref_only,
    )

    print("-----------------------------------------------------------------")
    print(f"Status          : {res.get('status')}")
    print(f"Distribution Tier: {res.get('tier')}")
    if res.get("source"):
        print(f"Source Corpus   : {res.get('source')}")
    print(f"Target Directory: {res.get('target')}")
    print(f"Bundles Synced  : {len(res.get('bundles_synced', []))}")
    for b in res.get("bundles_synced", []):
        print(f"  - {b}")
    reg_res = res.get("registry_merge", {})
    if reg_res:
        print(
            f"Registry Merge  : Updated={reg_res.get('updated', 0)}, Added={reg_res.get('added', 0)}"
        )
    print("-----------------------------------------------------------------")

    status = res.get("status")
    bundles_count = len(res.get("bundles_synced", []))
    is_preserved = res.get("mode") == "master_corpus_preserved"

    if status == "success" and (bundles_count > 0 or is_ref_only or is_preserved):
        print("✅ 1-Click Legal Sync Completed Successfully!")
        return 0
    elif status == "fallback_cloud_vault" or (status == "success" and bundles_count == 0):
        print(
            f"⚠️ {res.get('message', 'Thư mục tri thức cục bộ ccba-legal-knowledge chưa được tìm thấy.')}"
        )
        print(
            "❌ Không có gói tri thức nào được tải về máy. Đồng bộ CHƯA hoàn tất (ADR-0058 Hard Completion Lock)."
        )
        return 1
    else:
        print(f"❌ Sync failed: {res.get('message', 'Unknown error')}")
        return 1


def handle_ingest_gdrive(args: argparse.Namespace) -> int:
    """Handle Google Drive multi-scope knowledge ingestion."""
    from ccba_legal.sync.drive_client import GOOGLE_API_AVAILABLE
    from ccba_legal.sync.drive_ingestor import GoogleDriveIngestor

    if not GOOGLE_API_AVAILABLE:
        print(
            "❌ Thiếu thư viện googleapiclient hoặc google-auth. "
            "Cài đặt: pip install ccba-legal-intel[cloud]"
        )
        return 1

    print("=================================================================")
    print("      CCBA LEGAL INTEL - GOOGLE DRIVE MULTI-SCOPE INGESTOR       ")
    print("=================================================================")
    print(f"🌐 Scope: {args.scope}")
    print(f"📂 Output Directory: {args.output_dir}")
    if args.folder_id:
        print(f"📁 Folder ID: {args.folder_id}")
    if args.dry_run:
        print("🔎 Mode: DRY-RUN (không tải tệp thực tế)")

    try:
        ingestor = GoogleDriveIngestor(output_dir=args.output_dir)
        stats = ingestor.ingest(
            scope=args.scope,
            folder_id=args.folder_id,
            dest_dir=args.output_dir,
            dry_run=args.dry_run,
            force=args.force,
        )

        print("\n------------------ KẾT QUẢ THU THẬP ------------------")
        print(f"📊 Tổng số tệp đã quét: {stats['total_scanned']}")
        print(f"🎯 Số tệp phù hợp (.pdf, .docx, Google Docs): {stats['supported_found']}")
        if not args.dry_run:
            print(f"⬇️ Đã tải mới: {stats['downloaded']}")
            print(f"⏭️ Đã bỏ qua (trùng khớp registry): {stats['skipped']}")
            print(f"❌ Thất bại: {stats['failed']}")
        return 0
    except Exception as e:
        print(f"❌ Lỗi thực thi Ingestion: {e}")
        return 1


def handle_clean_images(args: argparse.Namespace) -> int:
    """Handle clean-images subcommand (ADR 0036)."""
    from ccba_legal.figure_extractor import scan_and_prune_orphan_figures

    print("=================================================================")
    print("     CCBA LEGAL INTEL - ORPHANED FIGURE IMAGES CLEANER           ")
    print("=================================================================")

    target_bundles: list[Path] = []
    if args.bundle_path:
        target_bundles.append(args.bundle_path)
    elif args.all:
        legal_docs = Path("legal_docs")
        if legal_docs.exists():
            for cat in ["01_vbpl", "02_qcvn", "03_tcvn"]:
                cat_dir = legal_docs / cat
                if cat_dir.exists():
                    for b in cat_dir.iterdir():
                        if b.is_dir() and not b.name.startswith("."):
                            target_bundles.append(b)
    else:
        print("⚠️ Vui lòng chỉ định đường dẫn bundle hoặc dùng cờ --all")
        return 1

    total_orphans = 0
    total_pruned_bytes = 0

    for b in target_bundles:
        res = scan_and_prune_orphan_figures(b, prune=args.prune)
        orphans = res.get("orphaned", [])
        if orphans:
            total_orphans += len(orphans)
            total_pruned_bytes += res.get("pruned_bytes", 0)
            action_str = (
                f"Đã xóa {res['pruned_count']} tệp ({res['pruned_bytes'] / 1024 / 1024:.2f} MB)"
                if args.prune
                else f"Phát hiện {len(orphans)} tệp rác (chạy với --prune để xóa)"
            )
            print(f"📁 [{b.name}]: {action_str}")
            for img_name in orphans[:5]:
                print(f"   • {img_name}")
            if len(orphans) > 5:
                print(f"   ... và {len(orphans) - 5} tệp khác")
        else:
            if args.bundle_path:
                print(f"✅ [{b.name}]: Thư mục figures/images hoàn toàn sạch sẽ (0 tệp rác).")

    print("=================================================================")
    if total_orphans == 0:
        print("🎉 Toàn bộ các gói tri thức đều đạt chuẩn 100% Zero-Orphan Figures!")
    else:
        if args.prune:
            print(
                f"✨ Đã dọn dẹp thành công {total_orphans} tệp ảnh mồ côi ({total_pruned_bytes / 1024 / 1024:.2f} MB)!"
            )
        else:
            print(
                f"⚠️ Tổng cộng phát hiện {total_orphans} tệp ảnh mồ côi. Chạy lại với cờ `--prune` để dọn dẹp."
            )
    return 0


def handle_query(args: argparse.Namespace) -> int:
    """Handle query subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    corpus = getattr(args, "corpus", None)
    engine = LegalKnowledgeEngine(registry_path=args.registry, corpus_dir=corpus)
    include_expired = getattr(args, "include_expired", False)
    results = engine.search(args.search_query, top_k=args.top_k, include_expired=include_expired)

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0

    print("=================================================================")
    print("          CCBA LEGAL INTEL - KNOWLEDGE REGISTRY QUERY            ")
    print("=================================================================")
    print(f"🔍 Query   : '{args.search_query}' (Top {args.top_k})")
    print(f"📁 Registry: {engine.registry_path}")
    print(f"⚙️ Include Expired: {'YES' if include_expired else 'NO (Default: Current Only)'}")
    print("-----------------------------------------------------------------")

    if not results:
        print("ℹ️ Không tìm thấy văn bản phù hợp với từ khóa.")
        return 0

    for idx, doc in enumerate(results, start=1):
        short_name = doc.get("short_name", "VBPL")
        doc_num = doc.get("document_number", doc.get("id", ""))
        title = doc.get("title", "")
        status = str(doc.get("status", "unknown")).upper()
        badge = "🟢 CURRENT" if status in {"ACTIVE", "CURRENT"} else f"🔴 {status}"

        print(f"\n{idx}. [{badge}] {short_name} - {doc_num}")
        if title:
            print(f"   Tiêu đề: {title}")
        if doc.get("lifecycle_warning"):
            print(f"   {doc['lifecycle_warning']}")
        if doc.get("suggested_replacement"):
            rep = doc["suggested_replacement"]
            rep_short = rep.get("short_name") or "VBPL"
            rep_num = rep.get("document_number", "")
            print(f"   👉 Thay thế bởi: [{rep_short} - {rep_num}]")

    print("\n=================================================================")
    return 0


def handle_get_clause(args: argparse.Namespace) -> int:
    """Handle get-clause subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    corpus = getattr(args, "corpus", None)
    engine = LegalKnowledgeEngine(registry_path=args.registry, corpus_dir=corpus)
    try:
        res = engine.get_clause(args.doc, args.clause)
    except ValueError as e:
        print(f"❌ Security Error: {e}", file=sys.stderr)
        return 1

    if not res:
        print(
            f"❌ Điều khoản '{args.clause}' không tìm thấy trong văn bản '{args.doc}'.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0

    print("=================================================================")
    print("         CCBA LEGAL INTEL - TIER-AWARE CLAUSE EXTRACTOR          ")
    print("=================================================================")
    print(f"📄 Văn bản   : {res['doc_id']}")
    print(f"🔖 Điều/Khoản: {res['clause_id']}")
    if res.get("title") and res["title"] != res["clause_id"]:
        print(f"📌 Tiêu đề   : {res['title']}")
    print("-----------------------------------------------------------------\n")
    print(res["content"])
    print("\n=================================================================")
    return 0


def handle_get_table(args: argparse.Namespace) -> int:
    """Handle get-table subcommand."""
    from ccba_legal.engine import LegalKnowledgeEngine

    corpus = getattr(args, "corpus", None)
    engine = LegalKnowledgeEngine(registry_path=args.registry, corpus_dir=corpus)
    try:
        res = engine.get_table(args.doc, args.table, format=args.format)
    except ValueError as e:
        print(f"❌ Security Error: {e}", file=sys.stderr)
        return 1

    if res is None:
        print(
            f"❌ Bảng số liệu '{args.table}' không tìm thấy trong văn bản '{args.doc}'.",
            file=sys.stderr,
        )
        return 1

    if args.json:
        out = {
            "doc_id": args.doc,
            "table_id": args.table,
            "format": args.format,
            "content": res,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0

    print(res)
    return 0


def handle_compile_registry(args: argparse.Namespace) -> int:
    """Handle compile-registry subcommand."""
    from ccba_legal.compiler import compile_sharded_registry

    docs_dir = args.docs_dir
    if not docs_dir:
        cand1 = Path("legal_docs")
        cand2 = Path(".md/legal_docs")
        if cand1.is_dir():
            docs_dir = cand1
        elif cand2.is_dir():
            docs_dir = cand2
        else:
            docs_dir = cand1

    output_path = args.output
    if not output_path:
        cand_out1 = Path(".md/data/legal_registry.yaml")
        cand_out2 = Path("legal_registry.yaml")
        if cand_out1.parent.is_dir():
            output_path = cand_out1
        else:
            output_path = cand_out2

    print("=================================================================")
    print("         CCBA LEGAL INTELLIGENCE (SHARDED REGISTRY COMPILER)      ")
    print("=================================================================")
    print(f"📂 Docs Directory: {docs_dir}")
    print(f"📄 Target Registry: {output_path}")
    print(f"🔍 Mode: {'Check Synchronization (--check)' if args.check else 'Compile & Write'}")

    compiled, is_in_sync, issues = compile_sharded_registry(
        docs_dir=docs_dir,
        output_file=output_path,
        base_registry_path=args.base,
        check_only=args.check,
    )

    doc_count = sum(
        len(v)
        for k, v in compiled.items()
        if k in {"laws", "decrees", "circulars", "decisions", "resolutions", "standards"}
    )
    print(f"\n✅ Total compiled legal documents: {doc_count}")
    for cat in ["laws", "decrees", "circulars", "decisions", "resolutions", "standards"]:
        count = len(compiled.get(cat, []))
        if count > 0:
            print(f"   - {cat}: {count}")

    if args.check:
        if is_in_sync:
            print(
                "\n🛡️ [CHECK PASS] legal_registry.yaml is 100% in sync with sharded metadata.yaml bundles."
            )
            return 0
        else:
            print(
                "\n❌ [CHECK FAILED] Discrepancies detected between registry and sharded bundles:"
            )
            for iss in issues:
                print(f"   - {iss}")
            return 1

    print(f"\n🎉 Successfully compiled registry to: {output_path}")
    return 0


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

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
    elif args.command == "hydrate":
        sys.exit(handle_hydrate(args))
    elif args.command == "lint":
        sys.exit(handle_lint(args))
    elif args.command == "sync":
        sys.exit(handle_sync(args))
    elif args.command == "ingest":
        sys.exit(handle_ingest(args))
    elif args.command == "ingest-gdrive":
        sys.exit(handle_ingest_gdrive(args))
    elif args.command == "clean-images":
        sys.exit(handle_clean_images(args))
    elif args.command == "query":
        sys.exit(handle_query(args))
    elif args.command == "get-clause":
        sys.exit(handle_get_clause(args))
    elif args.command == "get-table":
        sys.exit(handle_get_table(args))
    elif args.command == "compile-registry":
        sys.exit(handle_compile_registry(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
