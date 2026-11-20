"""Document conversion, consolidation, hydration, linting, ingestion, and cleanup handlers."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from ccba_legal._cli_crawl_handlers import resolve_cli_symbol
from ccba_legal.consolidator import LegislativeConsolidator
from ccba_legal.crawler import TVPLCrawler
from ccba_legal.docx_converter import convert_docx_to_okf_bundle
from ccba_legal.gold_standard import GoldStandardProcessor


def handle_convert(args: argparse.Namespace) -> int:
    """Handle convert subcommand."""
    print("=================================================================")
    print("      CCBA UNIVERSAL DOCX CONVERTER ENGINE (OKF v2.2)            ")
    print("=================================================================")
    print(f"📄 DOCX File: {args.docx_path}")
    print(f"📁 Target Bundle: {args.target_bundle_dir}")
    conv_fn = resolve_cli_symbol("convert_docx_to_okf_bundle", convert_docx_to_okf_bundle)
    res = conv_fn(
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
    proc_cls = resolve_cli_symbol("GoldStandardProcessor", GoldStandardProcessor)
    res = proc_cls.process_bundle(args.bundle_dir, doc_type=args.type)
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
    cons_cls = resolve_cli_symbol("LegislativeConsolidator", LegislativeConsolidator)
    consolidator = cons_cls.from_manifest_file(args.manifest)
    res = consolidator.consolidate(
        base_md_path=args.base, output_dir=args.output, amending_md_path=args.amending
    )
    patches_count = res.modified_clauses + res.added_clauses + res.repealed_clauses
    status_str = "success" if res.success else "failed"
    print(f"Status: {status_str}, Patches Applied: {patches_count}")
    if not res.success or res.errors:
        print(f"Errors: {res.errors}")
        return 1
    return 0


def _resolve_hydrate_spoke_root(args: argparse.Namespace) -> Path:
    """Determine target Spoke root directory for asset hydration."""
    from ccba_legal.registry import resolve_project_root

    if args.spoke_dir:
        return Path(args.spoke_dir).resolve()
    if (Path.cwd() / "legal_docs").exists() or (Path.cwd() / "legal_registry.yaml").exists():
        return Path.cwd().resolve()
    return resolve_project_root()


def _print_hydration_summary(summary: Any, verify_only: bool) -> int:
    """Print hydration statistics table and return exit status code."""
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
    if verify_only and summary.missing_assets > 0:
        print("\n⚠️ Note: Some assets are missing from local sources/.")
    return 0


def handle_hydrate(args: argparse.Namespace) -> int:
    """Handle hydrate subcommand."""
    print("=================================================================")
    print("      CCBA SPOKE VAULT HYDRATION ENGINE (ADR 0035 / ADR 0059)     ")
    print("=================================================================")
    from ccba_legal.hydrator import SpokeHydrator

    spoke_root = _resolve_hydrate_spoke_root(args)
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
    summary = SpokeHydrator(spoke_root=spoke_root).hydrate_all(
        category=args.category,
        cohorts=cohorts_list,
        force=args.force,
        verify_only=args.verify_only,
        dry_run=args.dry_run,
    )
    return _print_hydration_summary(summary, args.verify_only)


def _print_lint_currency_findings(res: dict[str, Any]) -> None:
    """Print obsolete and unverified citation findings from legal currency audit."""
    curr_findings = res.get("currency_findings", [])
    errors_list = [f for f in curr_findings if f.get("severity") == "ERROR"]
    warnings_list = [f for f in curr_findings if f.get("severity") == "WARNING"]
    if errors_list:
        print("\n🔴 [VĂN BẢN HẾT HIỆU LỰC / OBSOLETE CITATIONS] (Vi phạm ADR-0058):")
        for f in errors_list:
            print(f"  • [{Path(f['file']).name}] [{f['location']}]")
            print(f"    - Viện dẫn : {f['matched_text']} ({f['obsolete_doc']})")
            print(f"    - Thay thế : 👉 {f['replacement']}")
            if f.get("context"):
                print(f'    - Ngữ cảnh : "{f["context"]}"')
    if warnings_list:
        print("\n⚠️ [VĂN BẢN CHƯA XÁC THỰC / UNVERIFIED CITATIONS] (Cần đối soát):")
        for f in warnings_list:
            print(
                f"  • [{Path(f['file']).name}] [{f['location']}]: {f['matched_text']} -> {f['replacement']}"
            )


def _print_lint_report(res: dict[str, Any], target_path: Path, check_curr: bool) -> int:
    """Format and display human-readable lint summary banner and findings."""
    banner = (
        "CCBA LEGAL INTEL - VISUAL PARITY & LEGAL CURRENCY LINTER"
        if check_curr
        else "CCBA LEGAL INTEL - VISUAL PARITY & HYPERLINK INTEGRITY LINTER"
    )
    print("=================================================================")
    print(f"     {banner}    ")
    print("=================================================================")
    print(f"🎯 Target Path: {target_path}")
    print("-----------------------------------------------------------------")
    print(f"Scanned files    : {res['files_scanned']}")
    print(f"Format errors    : {res['format_errors']}")
    print(f"Link errors      : {res['link_errors']}")
    if check_curr:
        print(f"Currency errors  : {res.get('currency_errors', 0)} (Khóa cứng ADR-0058)")
        print(f"Currency warnings: {res.get('currency_warnings', 0)}")
    print("-----------------------------------------------------------------")
    if res["format_errors"] > 0 or res["link_errors"] > 0:
        print("\n❌ [FORMAT & LINK ISSUES DETECTED]:")
        for item in res["details"]:
            for err in item.get("errors", []):
                print(f"  • {item.get('file', '')} -> {err}")
            for lerr in item.get("link_errors", []):
                print(f"  • {item.get('file', '')} -> {lerr}")
    if check_curr:
        _print_lint_currency_findings(res)
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
    msg = (
        "✅ [PASSED] 100% Visual Parity, Zero Broken Links & Zero Obsolete Citations!"
        if check_curr
        else "✅ [PASSED] 100% Visual Parity & Zero Broken Links!"
    )
    print(msg)
    return 0


def handle_lint(args: argparse.Namespace) -> int:
    """Handle lint subcommand with visual parity, link integrity, and legal currency gates."""
    from ccba_legal.linter import lint_target_path

    check_curr = getattr(args, "check_currency", False)
    res = lint_target_path(
        args.target_path,
        check_links=not args.no_links,
        check_currency=check_curr,
        registry_path=getattr(args, "registry", None),
    )
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 1 if res["total_errors"] > 0 else 0
    return _print_lint_report(res, args.target_path, check_curr)


def _prepare_ingest_dual_pdf(
    fetch_res: dict[str, Any],
    pdf_path: Path | None,
    target_docx: Path,
    target_pdf: Path,
    raw_scan_target: Path,
) -> bool:
    """Handle ADR 0043 Dual-PDF rendering when source PDF is a Tier 3 Gazette scan."""
    pdf_tier = fetch_res.get("pdf_tier") if isinstance(fetch_res, dict) else None
    if not (pdf_tier == 3 and target_docx.exists()):
        if pdf_path and pdf_path.exists() and pdf_path.resolve() != target_pdf.resolve():
            shutil.copy2(pdf_path, target_pdf)
        return False

    print("[LegalIntel] [ADR 0043 Dual-PDF] Detected Tier 3 Gazette Scan.")
    if pdf_path and pdf_path.exists() and pdf_path.resolve() != raw_scan_target.resolve():
        shutil.copy2(pdf_path, raw_scan_target)
        print(f"  📦 Preserved official Gazette Scan: {raw_scan_target.name}")
    try:
        from ccba_ooxml.converter import convert_to_pdf

        print("  ⚙️ Rendering Born-Digital Vector PDF via LibreOffice...")
        convert_to_pdf(target_docx, target_pdf)
        print(f"  ✅ Successfully rendered Vector PDF: {target_pdf.name}")
        return True
    except Exception as e:
        print(f"  ⚠️ Vector PDF conversion failed ({e}), falling back to scan.")
        if raw_scan_target.exists():
            try:
                raw_scan_target.unlink()
            except OSError:
                pass
        if pdf_path and pdf_path.exists() and pdf_path.resolve() != target_pdf.resolve():
            shutil.copy2(pdf_path, target_pdf)
        return False


def _upload_ingest_vault(
    category: str, doc_slug: str, target_docx: Path, target_pdf: Path, raw_scan_target: Path
) -> None:
    """Upload ingested DOCX/PDF/raw-scan assets to Google Drive Vault when available."""
    print("\n>>> [2/5] Uploading binary assets to Google Drive Vault (ADR 0035)...")
    try:
        from ccba_legal.gdrive_vault import GoogleDriveVault

        vault = GoogleDriveVault()
        if not vault.is_available():
            print("  ℹ️ Google Drive Vault offline. Proceeding in local mode.")
            return
        vault.upload_asset(target_docx, category, doc_slug)
        if target_pdf.exists():
            vault.upload_asset(target_pdf, category, doc_slug)
        if raw_scan_target.exists():
            vault.upload_asset(raw_scan_target, category, doc_slug)
        print("  ✅ Uploaded to Google Drive Vault successfully.")
    except Exception as ve:
        print(f"  ⚠️ Drive upload warning: {ve}")


def _stamp_dual_pdf_metadata(
    target_bundle: Path, target_pdf: Path, raw_scan_target: Path, category: str, doc_slug: str
) -> None:
    """Stamp SHA-256 and Dual-PDF provenance hashes into bundle `metadata.yaml`."""
    meta_path = target_bundle / "metadata.yaml"
    if not meta_path.exists():
        return
    import yaml

    with open(meta_path, encoding="utf-8") as f:
        meta = yaml.safe_load(f) or {}
    meta["pdf_origin"] = "docx_vector_rendered"
    if raw_scan_target.exists():
        meta["raw_scan_pdf"] = f"sources/{raw_scan_target.name}"
    if not isinstance(meta.get("source_assets"), dict):
        meta["source_assets"] = {}
    if target_pdf.exists():
        pdf_hash = hashlib.sha256(target_pdf.read_bytes()).hexdigest()
        meta["pdf_sha256"] = pdf_hash
        meta["source_assets"]["pdf"] = {
            "sha256": pdf_hash,
            "vault_path": f"CCBA_Legal_Vault/{category}/{doc_slug}/{target_pdf.name}",
            "status": "verified",
            "origin": "docx_vector_rendered",
        }
    if raw_scan_target.exists():
        raw_hash = hashlib.sha256(raw_scan_target.read_bytes()).hexdigest()
        meta["source_assets"]["raw_scan"] = {
            "sha256": raw_hash,
            "vault_path": f"CCBA_Legal_Vault/{category}/{doc_slug}/{raw_scan_target.name}",
            "status": "verified",
            "acquisition_method": "official_gazette_scan",
        }
    with open(meta_path, "w", encoding="utf-8") as f:
        yaml.dump(meta, f, allow_unicode=True, sort_keys=False)


def _run_ingest_post_steps(
    args: argparse.Namespace,
    target_bundle: Path,
    target_docx: Path,
    target_pdf: Path,
    raw_scan_target: Path,
    is_vector_rendered: bool,
    doc_slug: str,
) -> int:
    """Run Steps 3-5 of ingestion (DOCX->OKF conversion, AST processing, visual lint)."""
    print(f"\n>>> [3/5] Converting to OKF Bundle with resilient parser at {target_bundle}...")
    try:
        conv_fn = resolve_cli_symbol("convert_docx_to_okf_bundle", convert_docx_to_okf_bundle)
        conv_fn(docx_path=target_docx, target_bundle_dir=target_bundle, doc_type=args.category)
        if is_vector_rendered:
            _stamp_dual_pdf_metadata(
                target_bundle, target_pdf, raw_scan_target, args.category, doc_slug
            )
    except Exception as ce:
        print(f"❌ Conversion Error: {ce}")
        return 1

    print("\n>>> [4/5] Processing AST clauses and QA benchmark dataset...")
    try:
        proc_cls = resolve_cli_symbol("GoldStandardProcessor", GoldStandardProcessor)
        proc_cls().process_bundle(target_bundle, doc_type=args.category)
    except Exception as pe:
        print(f"⚠️ AST processing warning: {pe}")

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
    return 0


def handle_ingest(args: argparse.Namespace) -> int:
    """Handle universal 1-command ingestion pipeline (ADR 0035)."""
    print("=================================================================")
    print("     CCBA LEGAL INTEL - UNIVERSAL INGESTION PIPELINE 2.0         ")
    print("=================================================================")
    print(f"🎯 Target: {args.target}")
    print(f"📂 Category: {args.category}")

    out_dir = Path(".md/extracted_docs/tvpl_downloads")
    out_dir.mkdir(parents=True, exist_ok=True)
    crawler_cls = resolve_cli_symbol("TVPLCrawler", TVPLCrawler)
    print("\n>>> [1/5] Fetching official DOCX & PDF from TVPL VIP...")
    try:
        fetch_res = crawler_cls(output_dir=out_dir).fetch_document(args.target)
    except Exception as e:
        print(f"❌ Fetch Error: {e}")
        return 1
    if not fetch_res or not fetch_res.get("docx_path"):
        print("❌ Ingestion failed: Could not fetch DOCX source file.")
        return 1

    docx_path = Path(fetch_res["docx_path"])
    pdf_path = Path(fetch_res["pdf_path"]) if fetch_res.get("pdf_path") else None
    doc_slug = args.slug if args.slug else docx_path.stem.lower().replace("-", "_")
    target_bundle = (args.output_dir or Path("legal_docs")) / args.category / doc_slug
    sources_dir = target_bundle / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    target_docx = sources_dir / f"{doc_slug}.docx"
    target_pdf = sources_dir / f"{doc_slug}.pdf"
    raw_scan_target = sources_dir / f"{doc_slug}_raw_scan.pdf"
    if docx_path.exists() and docx_path.resolve() != target_docx.resolve():
        shutil.copy2(docx_path, target_docx)

    is_vector_rendered = _prepare_ingest_dual_pdf(
        fetch_res, pdf_path, target_docx, target_pdf, raw_scan_target
    )
    if args.upload_drive:
        _upload_ingest_vault(args.category, doc_slug, target_docx, target_pdf, raw_scan_target)

    rc = _run_ingest_post_steps(
        args, target_bundle, target_docx, target_pdf, raw_scan_target, is_vector_rendered, doc_slug
    )
    if rc != 0:
        return rc
    print("\n=================================================================")
    print("🎉 Ingestion Pipeline 2.0 Completed Successfully!")
    print(f"📁 Output Bundle: {target_bundle.resolve()}")
    print("=================================================================")
    return 0


def _collect_clean_images_targets(args: argparse.Namespace) -> list[Path] | None:
    """Resolve target OKF bundle directories for `clean-images`."""
    if args.bundle_path:
        return [Path(args.bundle_path)]
    if not args.all:
        print("⚠️ Vui lòng chỉ định đường dẫn bundle hoặc dùng cờ --all")
        return None
    bundles: list[Path] = []
    legal_docs = Path("legal_docs")
    if legal_docs.exists():
        for cat in ("01_vbpl", "02_qcvn", "03_tcvn"):
            cat_dir = legal_docs / cat
            if cat_dir.exists():
                bundles.extend(
                    sorted(
                        b for b in cat_dir.iterdir() if b.is_dir() and not b.name.startswith(".")
                    )
                )
    return bundles


def handle_clean_images(args: argparse.Namespace) -> int:
    """Handle clean-images subcommand (ADR 0036)."""
    from ccba_legal.figure_extractor import scan_and_prune_orphan_figures

    print("=================================================================")
    print("     CCBA LEGAL INTEL - ORPHANED FIGURE IMAGES CLEANER           ")
    print("=================================================================")
    target_bundles = _collect_clean_images_targets(args)
    if target_bundles is None:
        return 1

    total_orphans = 0
    total_pruned_bytes = 0
    for b in target_bundles:
        res = scan_and_prune_orphan_figures(b, prune=args.prune)
        orphans = res.get("orphaned", [])
        if orphans:
            total_orphans += len(orphans)
            total_pruned_bytes += res.get("pruned_bytes", 0)
            msg = (
                f"Đã xóa {res['pruned_count']} tệp ({res['pruned_bytes'] / 1024 / 1024:.2f} MB)"
                if args.prune
                else f"Phát hiện {len(orphans)} tệp rác (chạy với --prune để xóa)"
            )
            print(f"📁 [{b.name}]: {msg}")
            for img_name in orphans[:5]:
                print(f"   • {img_name}")
            if len(orphans) > 5:
                print(f"   ... và {len(orphans) - 5} tệp khác")
        elif args.bundle_path:
            print(f"✅ [{b.name}]: Thư mục figures/images hoàn toàn sạch sẽ (0 tệp rác).")

    print("=================================================================")
    if total_orphans == 0:
        print("🎉 Toàn bộ các gói tri thức đều đạt chuẩn 100% Zero-Orphan Figures!")
    elif args.prune:
        print(
            f"✨ Đã dọn dẹp thành công {total_orphans} tệp ảnh mồ côi ({total_pruned_bytes / 1024 / 1024:.2f} MB)!"
        )
    else:
        print(
            f"⚠️ Tổng cộng phát hiện {total_orphans} tệp ảnh mồ côi. Chạy lại với cờ `--prune` để dọn dẹp."
        )
    return 0
