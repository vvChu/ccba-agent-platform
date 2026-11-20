"""Crawler, login, sync, and Google Drive ingestion CLI subcommand handlers."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from ccba_legal.crawler import TVPLCrawler, get_tvpl_credentials


def resolve_cli_symbol(name: str, fallback: Any) -> Any:
    """Look up mock-patchable attributes on the `ccba_legal.cli` facade at call time."""
    cli_mod = sys.modules.get("ccba_legal.cli")
    return getattr(cli_mod, name, fallback) if cli_mod is not None else fallback


def handle_fetch(args: argparse.Namespace) -> int:
    """Handle fetch subcommand."""
    print("=================================================================")
    print("         CCBA LEGAL INTELLIGENCE (TVPL VIP CRAWLER)              ")
    print("=================================================================")
    print(f"🎯 Target: {args.target}")

    out_dir = args.output_dir or Path(".md/extracted_docs/tvpl_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)
    creds_fn = resolve_cli_symbol("get_tvpl_credentials", get_tvpl_credentials)
    try:
        creds_fn()
        print("🔐 Authenticating with TVPL VIP credentials from environment...")
    except OSError:
        print("ℹ️ No TVPL credentials found in environment. Proceeding with public/cache lookup...")

    crawler_cls = resolve_cli_symbol("TVPLCrawler", TVPLCrawler)
    crawler = crawler_cls(output_dir=out_dir)
    try:
        result = crawler.fetch_document(args.target)
        print(f"Result: {result}", flush=True)
        return 0
    except Exception as e:
        print(f"❌ Fetch Error: {e}", flush=True)
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


def _handle_sync_notebooklm(args: argparse.Namespace, engine: Any) -> int:
    """Handle `sync --to-notebooklm` or `--notebook-id` cloud sync path."""
    import asyncio

    notebook_id = args.notebook_id or os.environ.get("NOTEBOOKLM_NOTEBOOK_ID")
    if not notebook_id:
        print(
            "[Error] Thiếu Notebook ID. Cung cấp qua --notebook-id hoặc biến NOTEBOOKLM_NOTEBOOK_ID."
        )
        return 1
    reg_p = (
        Path(args.registry)
        if getattr(args, "registry", None)
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


def _report_sync_result(res: dict[str, Any], is_ref_only: bool) -> int:
    """Print Spoke pull sync summary and return 0 on success or 1 on incomplete sync."""
    print("-----------------------------------------------------------------")
    print(f"Status          : {res.get('status')}")
    print(f"Distribution Tier: {res.get('tier')}")
    if res.get("source"):
        print(f"Source Corpus   : {res.get('source')}")
    print(f"Target Directory: {res.get('target')}")
    print(f"Bundles Synced  : {len(res.get('bundles_synced', []))}")
    for b in res.get("bundles_synced", []):
        print(f"  - {b}")
    if reg_res := res.get("registry_merge", {}):
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
    if status == "fallback_cloud_vault" or (status == "success" and bundles_count == 0):
        print(
            f"⚠️ {res.get('message', 'Thư mục tri thức cục bộ ccba-legal-knowledge chưa được tìm thấy.')}"
        )
        print(
            "❌ Không có gói tri thức nào được tải về máy. Đồng bộ CHƯA hoàn tất (ADR-0058 Hard Completion Lock)."
        )
        return 1
    print(f"❌ Sync failed: {res.get('message', 'Unknown error')}")
    return 1


def handle_sync(args: argparse.Namespace) -> int:
    """Handle sync subcommand (ADR 0050)."""
    print("=================================================================")
    print("     CCBA LEGAL INTEL - AUTOMATED LEGAL KNOWLEDGE SYNC           ")
    print("=================================================================")
    from ccba_legal.sync import LegalSyncEngine

    engine = LegalSyncEngine()
    if args.to_notebooklm or args.notebook_id:
        return _handle_sync_notebooklm(args, engine)

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
    return _report_sync_result(res, is_ref_only)


def handle_ingest_gdrive(args: argparse.Namespace) -> int:
    """Handle Google Drive multi-scope knowledge ingestion."""
    from ccba_legal.sync.drive_client import GOOGLE_API_AVAILABLE
    from ccba_legal.sync.drive_ingestor import GoogleDriveIngestor

    if not GOOGLE_API_AVAILABLE:
        print(
            "❌ Thiếu thư viện googleapiclient hoặc google-auth. Cài đặt: pip install ccba-legal-intel[cloud]"
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
