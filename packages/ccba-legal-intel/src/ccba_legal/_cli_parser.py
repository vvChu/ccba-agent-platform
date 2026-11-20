"""Argument parser builders for the CCBA Legal Intelligence unified CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any


def _add_corpus_and_json_flags(
    parser: argparse.ArgumentParser,
    *,
    add_corpus: bool = True,
    short_corpus: bool = False,
) -> None:
    """Attach shared `--registry`, optional `--corpus`, and `--json` flags."""
    parser.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )
    if add_corpus:
        opts = ("-c", "--corpus") if short_corpus else ("--corpus",)
        parser.add_argument(
            *opts, type=Path, default=None, help="Path to legal_docs corpus directory"
        )
    parser.add_argument("--json", action="store_true", help="Output results in raw JSON format")


def _register_login_and_fetch_parsers(subparsers: Any) -> None:
    """Register `login`, `fetch`, and `batch-fetch` subcommands."""
    login_p = subparsers.add_parser(
        "login",
        help="Launch interactive Chromium browser with persistent TVPL VIP Profile on port 9222",
    )
    login_p.add_argument(
        "--port", "-p", type=int, default=9222, help="Debugging port (default: 9222)"
    )
    login_p.add_argument(
        "--url", "-u", type=str, default="https://thuvienphapluat.vn", help="Initial target URL"
    )

    fetch_p = subparsers.add_parser(
        "fetch", help="Crawl and download VIP Digital PDF and DOCX from TVPL"
    )
    fetch_p.add_argument(
        "target",
        help="URL or Document ID/Number (e.g. '02/2022/TT-BXD' or 'https://thuvienphapluat.vn/...')",
    )
    fetch_p.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=None,
        help="Target output directory for downloaded assets",
    )
    fetch_p.add_argument(
        "--format",
        "-f",
        choices=["docx", "pdf", "both"],
        default="both",
        help="Desired download format: 'docx' (Gold source input), 'pdf' (VIP Digital Vector PDF), 'both' (default)",
    )

    batch_p = subparsers.add_parser(
        "batch-fetch", help="Batch crawl document hierarchy (DAG) from TVPL VIP"
    )
    batch_p.add_argument("root_target", help="Root document URL or ID to start batch crawl")
    batch_p.add_argument(
        "-d", "--depth", type=int, default=1, help="Max hierarchy depth (default: 1)"
    )
    batch_p.add_argument(
        "-o", "--output-dir", type=Path, default=None, help="Directory to save extracted docs"
    )


def _register_convert_and_consolidate_parsers(subparsers: Any) -> None:
    """Register `convert` and `consolidate` subcommands."""
    conv_p = subparsers.add_parser(
        "convert",
        help="Convert official .docx to OKF v2.2 Knowledge Bundle (Markdown + Atomic Templates)",
    )
    conv_p.add_argument("docx_path", type=Path, help="Path to input .docx file")
    conv_p.add_argument("target_bundle_dir", type=Path, help="Path to target OKF bundle directory")
    conv_p.add_argument(
        "-o", "--output-filename", type=str, default=None, help="Custom output markdown filename"
    )
    conv_p.add_argument(
        "-t", "--doc-type", type=str, default=None, help="Document type profile (vbpl, qcvn, tcvn)"
    )
    conv_p.add_argument(
        "-r", "--registry", type=Path, default=None, help="Path to legal_registry.yaml"
    )
    conv_p.add_argument(
        "--archetype",
        type=str,
        default=None,
        help="Force specific document archetype (VBPL_ADMIN, TECHNICAL_TCVN, TECHNICAL_QCVN, CIRCULAR_COST_NORM)",
    )

    cons_p = subparsers.add_parser(
        "consolidate", help="Consolidate amending document into base document (VBHN Engine)"
    )
    cons_p.add_argument(
        "--manifest", "-m", type=Path, required=True, help="Path to patch_manifest.yaml"
    )
    cons_p.add_argument("--base", "-b", type=Path, required=True, help="Path to base document .md")
    cons_p.add_argument(
        "--output", "-o", type=Path, required=True, help="Target consolidated document .md"
    )
    cons_p.add_argument(
        "--amending",
        "-a",
        type=Path,
        default=None,
        help="Optional path to amending Markdown file (*.md)",
    )


def _register_lint_parser(subparsers: Any) -> None:
    """Register `lint` subcommand."""
    lint_p = subparsers.add_parser(
        "lint",
        help="Lint OKF Markdown bundles for visual parity & link integrity (ADR 0029 & ADR 0030)",
    )
    lint_p.add_argument(
        "target_path", type=Path, help="Path to markdown file or OKF bundle directory"
    )
    lint_p.add_argument(
        "--no-links", action="store_true", help="Disable relative link and anchor verification"
    )
    lint_p.add_argument(
        "-c",
        "--check-currency",
        action="store_true",
        help="Audit legal citations for obsolete/repealed statutes (ADR 0050 & ADR 0058)",
    )
    _add_corpus_and_json_flags(lint_p, add_corpus=False)


def _register_sync_parser(subparsers: Any) -> None:
    """Register the `sync` subcommand and its Spoke/NotebookLM options."""
    sync_p = subparsers.add_parser(
        "sync",
        help="Synchronize OKF v2.4 legal bundles to Spoke or Google Drive/NotebookLM (ADR 0050)",
    )
    for flag, help_txt in (
        ("--pull-latest", "Pull latest OKF bundles and merge registry into local Spoke"),
        (
            "--reference-only",
            "Only merge legal_registry.yaml without physically copying legal_docs/ bundles (Zero-Bloat Reference Architecture).",
        ),
        ("--to-notebooklm", "Sync local registry to Google NotebookLM"),
        ("--use-drive", "Use Google Drive intermediary for NotebookLM sync"),
        ("--download-pdf", "Download temporary PDFs before uploading to Drive"),
        ("--clean-drive", "Clean Google Drive folder before sync"),
    ):
        sync_p.add_argument(flag, action="store_true", default=False, help=help_txt)
    sync_p.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=None,
        help="Target legal_docs output directory (default: .md/legal_docs for consuming spokes, legal_docs for master spoke)",
    )
    sync_p.add_argument(
        "--doc", type=str, default=None, help="Specific document ID or number to sync"
    )
    sync_p.add_argument(
        "--source-corpus",
        type=Path,
        default=None,
        help="Explicit path to ccba-legal-knowledge repository",
    )
    sync_p.add_argument(
        "--notebook-id", type=str, default=None, help="Target NotebookLM Notebook ID"
    )
    sync_p.add_argument(
        "--drive-folder",
        type=str,
        default="1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2",
        help="Google Drive folder ID",
    )


def _register_ingest_parser(subparsers: Any) -> None:
    """Register `ingest` subcommand."""
    ing_p = subparsers.add_parser(
        "ingest",
        help="Universal 1-command autonomous ingestion from TVPL VIP to OKF Bundle and Drive Vault (ADR 0035)",
    )
    ing_p.add_argument(
        "target", help="URL or Document ID/Number (e.g. '01/2021/TT-BXD' or TVPL URL)"
    )
    ing_p.add_argument(
        "-c",
        "--category",
        choices=["01_vbpl", "02_qcvn", "03_tcvn"],
        default="01_vbpl",
        help="Document category",
    )
    ing_p.add_argument(
        "-o", "--output-dir", type=Path, default=None, help="Spoke legal_docs output root"
    )
    ing_p.add_argument(
        "--upload-drive",
        action="store_true",
        default=False,
        help="Upload binary assets to Google Drive Vault (ADR 0035)",
    )
    ing_p.add_argument(
        "-s",
        "--slug",
        default=None,
        help="Explicit OKF bundle directory slug (e.g. 'qcvn_09_2017_bxd')",
    )


def _register_hydrate_parser(subparsers: Any) -> None:
    """Register `hydrate` subcommand."""
    hyd_p = subparsers.add_parser(
        "hydrate",
        help="Hydrate binary assets (PDF/DOCX) from Cloud Vault with cryptographic SHA-256 verification (ADR 0035)",
    )
    hyd_p.add_argument(
        "--cohorts",
        type=str,
        default=None,
        help="Comma-separated list of document slugs (e.g. 'qcvn_04_2021_bxd,qcvn_06_2022_bxd')",
    )
    hyd_p.add_argument(
        "-c",
        "--category",
        choices=["01_vbpl", "02_qcvn", "03_tcvn"],
        default=None,
        help="Filter by legal document category",
    )
    for flag, help_txt in (
        ("--all", "Hydrate all documents across all categories"),
        ("--verify-only", "Only verify SHA-256 integrity of local assets without downloading"),
        ("--force", "Force re-download even if file already exists locally"),
        ("--dry-run", "Simulate hydration without writing any files"),
    ):
        hyd_p.add_argument(flag, action="store_true", default=False, help=help_txt)
    hyd_p.add_argument(
        "--spoke-dir",
        type=Path,
        default=None,
        help="Root path of the Spoke repository (defaults to current project root)",
    )


def _register_gdrive_and_clean_parsers(subparsers: Any) -> None:
    """Register `ingest-gdrive` and `clean-images` subcommands."""
    gd_p = subparsers.add_parser(
        "ingest-gdrive",
        help="Scan and ingest knowledge documents from Google Drive (3 zones: My Drive, Shared With Me, Shared Drives)",
    )
    gd_p.add_argument(
        "--scope",
        choices=["all", "my-drive", "shared", "drives"],
        default="all",
        help="Scanning scope: 'all', 'my-drive', 'shared' (Shared with me), 'drives' (Shared Drives)",
    )
    gd_p.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path(".md/extracted_docs/gdrive"),
        help="Target output directory for ingested assets (default: .md/extracted_docs/gdrive)",
    )
    gd_p.add_argument(
        "--folder-id",
        type=str,
        default=None,
        help="Optional specific Google Drive folder ID to scan",
    )
    gd_p.add_argument(
        "--dry-run", action="store_true", help="Simulate scanning without downloading files"
    )
    gd_p.add_argument(
        "--force", action="store_true", help="Force redownload even if file is present in registry"
    )

    clean_p = subparsers.add_parser(
        "clean-images",
        help="Scan and prune unreferenced orphan figure images from legal bundle (ADR 0036)",
    )
    clean_p.add_argument(
        "bundle_path",
        type=Path,
        nargs="?",
        default=None,
        help="Path to specific legal bundle directory",
    )
    clean_p.add_argument("--all", action="store_true", help="Scan all legal bundles in repository")
    clean_p.add_argument(
        "--prune",
        action="store_true",
        help="Permanently delete unreferenced orphan images (default: dry-run report)",
    )


def _register_query_parser(subparsers: Any) -> None:
    """Register `query` subcommand."""
    q_p = subparsers.add_parser(
        "query",
        help="Search legal registry and knowledge corpus with lifecycle status and replacement warnings",
    )
    q_p.add_argument(
        "search_query",
        help="Search keyword or document number (e.g. 'Luật Xây dựng', '135/2025/QH15')",
    )
    q_p.add_argument(
        "-k", "--top-k", type=int, default=5, help="Number of results to return (default: 5)"
    )
    _add_corpus_and_json_flags(q_p, short_corpus=True)
    q_p.add_argument(
        "--include-expired",
        action="store_true",
        default=False,
        help="Bao gồm cả các văn bản quy phạm đã hết hiệu lực thi hành hoặc bị thay thế.",
    )


def _register_extract_parsers(subparsers: Any) -> None:
    """Register `get-clause` and `get-table` subcommands."""
    cl_p = subparsers.add_parser(
        "get-clause",
        help="Extract specific clause/article Markdown from OKF bundle using tier-aware semantic slicing",
    )
    cl_p.add_argument(
        "-d",
        "--doc",
        required=True,
        help="Document ID or slug (e.g. 'Luat-Xay-dung-2025-135-2025-QH15')",
    )
    cl_p.add_argument(
        "-c", "--clause", required=True, help="Clause ID or alias (e.g. 'd1', 'dieu-1', 'd15k2')"
    )
    _add_corpus_and_json_flags(cl_p)

    tbl_p = subparsers.add_parser(
        "get-table", help="Extract table matrix from OKF bundle in Markdown or CSV format"
    )
    tbl_p.add_argument(
        "-d", "--doc", required=True, help="Document ID or slug (e.g. 'qcvn_06_2022_bxd')"
    )
    tbl_p.add_argument("-t", "--table", required=True, help="Table ID (e.g. 'bang_01')")
    tbl_p.add_argument(
        "-f",
        "--format",
        choices=["markdown", "csv"],
        default="markdown",
        help="Output format: markdown (default) or csv",
    )
    _add_corpus_and_json_flags(tbl_p)


def _register_compile_and_pptx_parsers(subparsers: Any) -> None:
    """Register `compile-registry` and `pptx` subcommands."""
    cr_p = subparsers.add_parser(
        "compile-registry",
        help="Compile sharded metadata.yaml bundles into consolidated legal_registry.yaml",
    )
    cr_p.add_argument(
        "--docs-dir",
        "-d",
        type=Path,
        default=None,
        help="Directory containing legal document bundles with metadata.yaml (default: legal_docs or .md/legal_docs)",
    )
    cr_p.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Path to output legal_registry.yaml (default: .md/data/legal_registry.yaml or legal_registry.yaml)",
    )
    cr_p.add_argument(
        "--base",
        "-b",
        type=Path,
        default=None,
        help="Base registry to preserve non-document sections (metadata, monitoring, seminars)",
    )
    cr_p.add_argument(
        "--check",
        action="store_true",
        help="Dry-run verification mode. Exit 0 if registry matches shards, exit 1 if out of sync",
    )

    pptx_p = subparsers.add_parser(
        "pptx",
        help="Convert legal markdown document to branded PowerPoint presentation (.pptx) via ccba-ooxml",
    )
    pptx_p.add_argument(
        "input_markdown",
        type=Path,
        help="Path to input Markdown file (e.g. concept.md, summary.md)",
    )
    pptx_p.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Target output .pptx file path (default: <input_markdown_stem>.pptx)",
    )


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
    _register_login_and_fetch_parsers(subparsers)
    _register_convert_and_consolidate_parsers(subparsers)
    _register_lint_parser(subparsers)
    _register_sync_parser(subparsers)
    _register_ingest_parser(subparsers)
    _register_hydrate_parser(subparsers)
    _register_gdrive_and_clean_parsers(subparsers)
    _register_query_parser(subparsers)
    _register_extract_parsers(subparsers)
    _register_compile_and_pptx_parsers(subparsers)
    return parser
