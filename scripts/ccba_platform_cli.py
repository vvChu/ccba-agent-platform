#!/usr/bin/env python3
"""CCBA Platform Unified CLI Launcher.

Provides a unified command-line entry point for CCBA Platform operations:
- init-spoke: Initialize deterministic CCBA Spoke workspace.
- adopt-spoke: Adopt brownfield spoke codebase.
- sync-spoke: Synchronize platform skills and workflows to spoke.
- bootstrap-spoke: Bootstrap editable links to Hub packages for Spoke venv (ADR 0044).
- spoke-status: Display CCBA Spoke Health & Synchronization Dashboard.
- ingest-legal: Autonomous Crawler-to-Spoke Legal Ingestion (ADR 0039).
- doc-audit: Run 5-axis governance documentation auditor.
- validate-cross-ref: Verify cross-reference traceability matrix.
- protect-repo: Automated GitHub repository protection (rulesets, Dependabot, secret scanning).
- find-seam: Search Public Deep Seams, Capability Contracts, and Skills (ADR-0061).

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

_ROOT_DIR = Path(__file__).resolve().parents[1]
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

for _pkg_name in ("ccba-legal-intel", "ccba-ooxml"):
    _pkg_src = _ROOT_DIR / "packages" / _pkg_name / "src"
    if _pkg_src.exists() and str(_pkg_src) not in sys.path:
        sys.path.insert(0, str(_pkg_src))

_MINIMAL_PDF_BYTES = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj "
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj "
    b"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n"
    b"0000000056 00000 n \n0000000111 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
)


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


def resolve_default_legal_spoke(spoke_name_or_path: str | None = None) -> Path:
    """Resolve the path to the legal spoke by name, explicit path, or registry discovery."""
    if spoke_name_or_path:
        p = Path(spoke_name_or_path)
        if p.exists():
            return p

    try:
        from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

        spokes = get_registered_spokes(hub_root=_ROOT_DIR)
        if spoke_name_or_path:
            for s in spokes:
                if s.get("name") == spoke_name_or_path or s.get("spoke_id") == spoke_name_or_path:
                    return Path(s["path"])
        else:
            for s in spokes:
                if (
                    "legal" in s.get("name", "").lower()
                    or "pháp điển" in s.get("project_type", "").lower()
                ):
                    return Path(s["path"])
    except Exception:
        pass

    env_spoke = os.getenv("CCBA_LEGAL_SPOKE_PATH") or os.getenv("CCBA_LEGAL_KNOWLEDGE_PATH")
    if env_spoke and Path(env_spoke).exists():
        return Path(env_spoke)

    candidates = [
        _ROOT_DIR.parent / "ccba-legal-knowledge",
        Path.cwd() / "ccba-legal-knowledge",
        Path.home() / "ccba" / "ccba-legal-knowledge",
        Path.home() / "GitHubProjects" / "ccba-legal-knowledge",
    ]
    for c in candidates:
        if c.exists() and (c / "legal_registry.yaml").exists():
            return c
    return candidates[0]


def sanitize_doc_slug(url_or_id: str) -> str:
    """Derive clean snake_case document slug from URL or ID."""
    raw = url_or_id.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        path_part = raw.split("?")[0].split("#")[0].rstrip("/")
        raw = path_part.split("/")[-1]
        for ext in [".aspx", ".html", ".htm", ".docx", ".pdf"]:
            if raw.lower().endswith(ext):
                raw = raw[: -len(ext)]
                break

    clean = raw.lower().replace("đ", "d").replace("-", "_")
    clean = re.sub(r"[^\w\d]+", "_", clean)
    clean = re.sub(r"_+", "_", clean).strip("_")

    if re.search(r"_\d{5,}$", clean):
        m = re.match(
            r"^((?:nghi_dinh|thong_tu|luat|nghi_quyet|quyet_dinh|qcvn|tcvn)_[0-9]+_[0-9]{4}_(?:nd_cp|tt_[a-z]+|qd_[a-z]+|qh[0-9]+|[a-z0-9]+))",
            clean,
        )
        if m:
            return m.group(1)

    return clean or "legal_document"


def _infer_mock_doc_number(slug: str) -> str:
    """Infer synthetic document number from slug pattern for mock testing."""
    m_nd = re.search(r"(?:nghi_dinh|nd)[_-](\d+)[_-](\d+)[_-](?:nd_cp|ndcp)", slug)
    m_tt = re.search(r"(?:thong_tu|tt)[_-](\d+)[_-](\d+)[_-]([a-z]+)", slug)
    m_law = re.search(r"luat[_-].*?(\d+)[_-](\d+)[_-]([a-z0-9]+)", slug)
    if m_nd:
        return f"{m_nd.group(1)}/{m_nd.group(2)}/NĐ-CP"
    if m_tt:
        return f"{m_tt.group(1)}/{m_tt.group(2)}/TT-{m_tt.group(3).upper()}"
    if m_law:
        return f"{m_law.group(1)}/{m_law.group(2)}/{m_law.group(3).upper()}"
    return slug.replace("_", " ").upper()


def _stage_offline_assets(
    docx: str | Path,
    pdf: str | Path | None,
    url: str,
    slug: str,
    category: str,
    doc_type: str,
    sandbox_path: Path,
) -> bool:
    """Copy local offline DOCX/PDF assets and write metadata handoff into sandbox."""
    p_docx = Path(docx)
    if not p_docx.exists():
        print(f"  [Error] Provided docx file not found: {docx}")
        return False
    shutil.copy2(p_docx, sandbox_path / f"{slug}.docx")
    if pdf:
        p_pdf = Path(pdf)
        if not p_pdf.exists():
            print(f"  [Error] Provided pdf file not found: {pdf}")
            return False
        shutil.copy2(p_pdf, sandbox_path / f"{slug}.pdf")

    meta_data = {
        "source_url": url,
        "id": slug,
        "doc_id": slug,
        "document_number": "",
        "title": "",
        "category": category,
        "doc_type": doc_type,
        "status": "active",
    }
    (sandbox_path / "metadata_handoff.json").write_text(
        json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  [Offline Mode] Copied assets into sandbox from {docx}")
    return True


def _write_mock_docx(temp_docx_path: Path, slug: str, category: str, doc_type: str) -> None:
    """Write synthetic DOCX file into sandbox using ccba_ooxml seam for mock testing."""
    if category == "03_tcvn" or doc_type == "tcvn":
        md_body = (
            f"# TIÊU CHUẨN QUỐC GIA: {slug.upper()}\n\n"
            "1. Phạm vi áp dụng\nTiêu chuẩn này quy định các yêu cầu kỹ thuật cơ bản..."
        )
    elif category == "02_qcvn" or doc_type == "qcvn":
        md_body = (
            f"# QUY CHUẨN KỸ THUẬT QUỐC GIA: {slug.upper()}\n\n"
            "1. QUY ĐỊNH CHUNG\nQuy chuẩn này quy định các giới hạn kỹ thuật bắt buộc..."
        )
    else:
        md_body = f"# Văn bản pháp luật: {slug}\n\nĐiều 1. Phạm vi điều chỉnh\nNội dung điều 1..."

    try:
        from ccba_ooxml import convert_md_to_docx

        convert_md_to_docx(md_body, output_path=temp_docx_path)
    except Exception:
        temp_docx_path.write_bytes(b"PK\x03\x04mock_docx")


def _stage_mock_assets(
    url: str, slug: str, category: str, doc_type: str, sandbox_path: Path
) -> None:
    """Generate synthetic mock DOCX/PDF and metadata in sandbox for offline testing."""
    _write_mock_docx(sandbox_path / f"{slug}.docx", slug, category, doc_type)
    (sandbox_path / f"{slug}.pdf").write_bytes(_MINIMAL_PDF_BYTES)
    issued_by = {
        "01_vbpl": "Chính phủ",
        "02_qcvn": "Bộ Xây dựng",
    }.get(category, "Bộ Khoa học và Công nghệ")
    meta_data = {
        "source_url": url,
        "id": slug,
        "doc_id": slug,
        "document_number": _infer_mock_doc_number(slug),
        "title": f"Mock Document {slug}",
        "category": category,
        "doc_type": doc_type,
        "status": "effective",
        "issued_by": issued_by,
        "signer": "Thủ tướng Chính phủ" if category == "01_vbpl" else "",
        "pdf_status": "verified",
    }
    (sandbox_path / "metadata_handoff.json").write_text(
        json.dumps(meta_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  [Mocked] Generated sandbox .docx and .pdf at {sandbox_path}")


def _copy_crawler_attachments(
    res: dict[str, object], target_spoke: Path, category: str, slug: str
) -> None:
    """Copy non-primary crawler attachments into Spoke bundle sources/attachments directory."""
    raw_atts = res.get("attachments")
    if not isinstance(raw_atts, list):
        return
    primary_paths = {
        Path(str(res["docx_path"])).resolve(),
        *([Path(str(res["pdf_path"])).resolve()] if res.get("pdf_path") else []),
    }
    spoke_att_dir = target_spoke / "legal_docs" / category / slug / "sources" / "attachments"
    for att in raw_atts:
        att_p = Path(str(att))
        if att_p.is_file() and att_p.resolve() not in primary_paths:
            spoke_att_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(att_p, spoke_att_dir / att_p.name)


def _crawl_live_assets(
    url: str,
    slug: str,
    explicit_slug: bool,
    cdp_port: int | None,
    sandbox_path: Path,
    target_spoke: Path,
    category: str,
) -> tuple[bool, str]:
    """Fetch live document via TVPLCrawler under session mutex and write handoff metadata."""
    crawler_success = False
    excluded = {"docx_path", "pdf_path", "attachments", "links", "content", "html", "raw_html"}
    try:
        from ccba_legal.crawler import TVPLCrawler, TVPLSessionMutex

        with TVPLSessionMutex():
            res = TVPLCrawler(port=cdp_port, output_dir=sandbox_path).fetch_document(url)
            if isinstance(res, dict) and res.get("docx_path"):
                if res.get("slug") and not explicit_slug:
                    slug = sanitize_doc_slug(str(res["slug"]))
                temp_docx, temp_pdf = sandbox_path / f"{slug}.docx", sandbox_path / f"{slug}.pdf"
                c_docx = Path(str(res["docx_path"]))
                if c_docx.exists() and c_docx.resolve() != temp_docx.resolve():
                    shutil.copy2(c_docx, temp_docx)
                if res.get("pdf_path") and Path(str(res["pdf_path"])).exists():
                    c_pdf = Path(str(res["pdf_path"]))
                    if c_pdf.resolve() != temp_pdf.resolve():
                        shutil.copy2(c_pdf, temp_pdf)
                _copy_crawler_attachments(res, target_spoke, category, slug)
                handoff_meta = {k: v for k, v in res.items() if k not in excluded}
                meta_str = json.dumps(handoff_meta, indent=2, ensure_ascii=False, default=str)
                (sandbox_path / "metadata_handoff.json").write_text(meta_str, encoding="utf-8")
                crawler_success = temp_docx.exists()
    except Exception as exc:
        print(f"  [Crawler Warning] Exception during crawl: {exc}")

    if not crawler_success:
        print(
            "  [ADR-0059 Acquisition Barrier] Live TVPL VIP binary download failed or unavailable.\n"
            "  Synthetic mock fallback is strictly prohibited in live mode (mock=False).",
            file=sys.stderr,
        )
    return crawler_success, slug


def _run_spoke_ingest_and_validate(
    spoke_cli: Path,
    target_spoke: Path,
    slug: str,
    category: str,
    doc_type: str,
    sandbox_path: Path,
) -> bool:
    """Delegate bundle ingestion and 15-Gate validation to target Spoke CLI."""
    print("\n[Step 2/4] Delegating ingestion to Spoke Ingestion Engine...")
    temp_docx, temp_pdf = sandbox_path / f"{slug}.docx", sandbox_path / f"{slug}.pdf"
    meta_json = sandbox_path / "metadata_handoff.json"
    cmd = [sys.executable, str(spoke_cli), "ingest", str(temp_docx), slug, "-c", category]
    cmd.extend(["-t", doc_type, "--metadata", str(meta_json)])
    if temp_pdf.exists():
        cmd.extend(["--pdf-path", str(temp_pdf)])

    run_res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(target_spoke))
    print(run_res.stdout)
    if run_res.returncode != 0:
        print(f"  [Spoke Ingest Error] {run_res.stderr}")
        return False

    print("\n[Step 3/4] Running Scoped 15-Gate Validator on Spoke...")
    val_cmd = [sys.executable, str(spoke_cli), "validate", "--bundle", slug]
    env_ci = {**os.environ, "CI": "true"}
    val_res = subprocess.run(
        val_cmd, capture_output=True, text=True, cwd=str(target_spoke), env=env_ci
    )
    print(val_res.stdout)
    if val_res.returncode != 0:
        print(f"  [Validation Error] Spoke integrity check failed:\n{val_res.stderr}")
        return False
    return True


def _trigger_cloud_sync_if_enabled(sync_cloud: bool) -> None:
    """Optionally trigger LegalSyncEngine cloud synchronization after ingestion."""
    if not sync_cloud:
        return
    print("\n[Cloud Sync] Triggering LegalSyncEngine to update NotebookLM...")
    try:
        from ccba_legal.sync import LegalSyncEngine

        _ = LegalSyncEngine()
        print("  [Cloud Sync] Registry synced successfully.")
    except Exception as e:
        print(f"  [Cloud Sync Warning] Cloud sync skipped: {e}")


def _run_sandbox_ingestion(
    url: str,
    target_spoke: Path,
    slug: str,
    category: str,
    doc_type: str,
    opts: tuple[bool, bool, str | Path | None, str | Path | None, int | None],
) -> bool:
    """Run sandbox asset acquisition, Spoke ingestion, and 15-Gate validation."""
    explicit_slug, mock, docx, pdf, cdp_port = opts
    with tempfile.TemporaryDirectory(prefix="ccba_legal_ingest_") as sandbox_dir:
        sandbox_path = Path(sandbox_dir)
        print("\n[Step 1/4] Acquiring document binary assets and metadata into sandbox...")
        if docx:
            ok = _stage_offline_assets(docx, pdf, url, slug, category, doc_type, sandbox_path)
        elif mock:
            _stage_mock_assets(url, slug, category, doc_type, sandbox_path)
            ok = True
        else:
            ok, slug = _crawl_live_assets(
                url, slug, explicit_slug, cdp_port, sandbox_path, target_spoke, category
            )

        spoke_cli = target_spoke / "scripts" / "spoke_cli.py"
        if not ok or not _run_spoke_ingest_and_validate(
            spoke_cli, target_spoke, slug, category, doc_type, sandbox_path
        ):
            return False
        print("\n[Step 4/4] Auto-purging sandbox temp files (Zero-Duplication SSOT)...")
    return True


def execute_ingest_legal(
    url: str,
    spoke_path: str | Path | None = None,
    category: str = "01_vbpl",
    doc_type: str = "vbpl",
    sync_cloud: bool = False,
    mock: bool = False,
    docx: str | Path | None = None,
    pdf: str | Path | None = None,
    slug: str | None = None,
    cdp_port: int | None = None,
) -> bool:
    """Execute 4-Step Autonomous Crawler-to-Spoke Ingestion Protocol (ADR 0039)."""
    target_spoke = Path(spoke_path) if spoke_path else resolve_default_legal_spoke()
    if not target_spoke.exists():
        print(f"[Error] Target legal spoke not found at: {target_spoke}")
        return False

    if category in ("02_qcvn", "03_tcvn") and doc_type == "vbpl":
        doc_type = "tcvn" if category == "03_tcvn" else "qcvn"

    resolved_slug = sanitize_doc_slug(slug) if slug else sanitize_doc_slug(url)
    print(f"Source URL   : {url}\nTarget Spoke : {target_spoke}\nDocument Slug: {resolved_slug}")
    print(f"Category     : {category}\nProfile Type : {doc_type}")
    opts = (bool(slug), mock, docx, pdf, cdp_port)
    if not _run_sandbox_ingestion(url, target_spoke, resolved_slug, category, doc_type, opts):
        return False

    _trigger_cloud_sync_if_enabled(sync_cloud)
    print("✅ SUCCESS: Document successfully ingested into OKF v2.4 Bundle!")
    return True


def _resolve_spoke_status(sp_path: str, last_sync_str: str, now: datetime) -> str:
    """Evaluate health badge for a single registered Spoke entry."""
    if not os.path.exists(sp_path):
        return "❌ MISSING"
    try:
        sync_dt = datetime.fromisoformat(last_sync_str)
        if (now - sync_dt).days > 30:
            return "⚠️ OUTDATED"
    except Exception:
        pass
    return "🟢 ACTIVE"


def display_spoke_health_dashboard(hub_root: Path | None = None) -> int:
    """Display health and sync status of all registered CCBA Spokes."""
    from scripts.spoke.decrypt_spoke_registry import get_registered_spokes

    spokes = get_registered_spokes(hub_root=hub_root or _ROOT_DIR)
    banner = "=" * 90
    print(f"{banner}\n                      🏛️  CCBA SPOKE HEALTH & DRIFT DASHBOARD\n{banner}")
    if not spokes:
        print("  Không tìm thấy Spoke nào được đăng ký trong Hub Registry.")
        print("  Gợi ý: Dùng '/ccba-init-spoke' hoặc '/ccba-spoke-adopter' để kết nối Spoke mới.")
        print(banner)
        return 0

    print(
        f"{'Tên Spoke':<22} | {'Loại Nghiệp Vụ':<16} | {'Lần Đồng Bộ Cuối':<20} | {'Trạng Thái':<12} | {'Đường Dẫn Vật Lý'}"
    )
    print("-" * 105)
    now = datetime.now()
    for sp in spokes:
        sp_name = sp.get("name", "Unknown")
        sp_type = sp.get("archetype") or sp.get("project_type", "Unknown")
        sp_path = sp.get("path", "")
        last_sync_str = sp.get("last_sync", "")
        status = _resolve_spoke_status(sp_path, last_sync_str, now)
        display_sync = last_sync_str[:19].replace("T", " ") if last_sync_str else "Chưa rõ"
        print(f"{sp_name:<22} | {sp_type:<16} | {display_sync:<20} | {status:<12} | {sp_path}")

    print("=" * 105)
    print(f"Tổng số: {len(spokes)} Spoke(s) đăng ký trong hệ sinh thái.")
    print("Gợi ý: Chạy 'python scripts/sync_spoke.py --all' để đồng bộ toàn bộ Spoke.")
    return 0


def _add_init_spoke_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register init-spoke subcommand arguments."""
    init_p = subparsers.add_parser("init-spoke", help="Initialize a deterministic CCBA Spoke")
    archetypes = [
        "project_delivery",
        "enterprise_governance",
        "knowledge_corpus",
        "specialized_extension",
    ]
    init_p.add_argument("spoke_path", nargs="?", default=None, help="Path to target spoke")
    init_p.add_argument("-p", "--path", dest="path_opt", default=None, help="Alternative path")
    init_p.add_argument("--name", default=None, help="Project name")
    init_p.add_argument("--archetype", default=None, choices=archetypes, help="Spoke Archetype")
    init_p.add_argument("--type", dest="project_type", default=None, help="CCBA project type")
    init_p.add_argument("--mode", default=None, help="Execution mode")
    init_p.add_argument("--sub-type", default=None, help="Sub-type for specialized_extension")
    for flag, help_text in (
        ("--dry-run", "Preview initialization steps"),
        ("--force", "Overwrite existing workspace_context.yaml"),
        ("--sync", "Synchronize skills immediately"),
        ("--bootstrap", "Bootstrap Python venv"),
        ("--init-git", "Initialize git repository if missing"),
    ):
        init_p.add_argument(flag, action="store_true", help=help_text)


def _add_adopt_and_bootstrap_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register adopt-spoke, bootstrap-spoke, and spoke-status subcommands."""
    adopt_p = subparsers.add_parser("adopt-spoke", help="Adopt an existing codebase as a Spoke")
    adopt_p.add_argument("spoke_path", nargs="?", default=".", help="Path to target spoke")
    adopt_p.add_argument("--archetype", default=None, help="Explicit CCBA Spoke Archetype")
    adopt_p.add_argument("--type", dest="project_type", default=None, help="Explicit project type")
    adopt_p.add_argument("--mode", default=None, help="Execution mode (software/delivery/hybrid)")
    adopt_p.add_argument("--dry-run", action="store_true", help="Display discovery matrix")
    adopt_p.add_argument("--force", action="store_true", help="Force re-adoption")

    boot_p = subparsers.add_parser("bootstrap-spoke", help="Bootstrap editable Hub package links")
    boot_p.add_argument("spoke_path", nargs="?", default=".", help="Path to target spoke")
    for flag, help_text in (
        ("--create-venv", "Automatically create .venv if missing"),
        ("--check-only", "Check status without installing"),
        ("--dry-run", "Preview changes without modifying files"),
        ("--force", "Force bootstrap on non-main Hub branch"),
    ):
        boot_p.add_argument(flag, action="store_true", help=help_text)
    subparsers.add_parser("spoke-status", help="Display CCBA Spoke Health Dashboard")


def _add_sync_spoke_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register sync-spoke subcommand arguments."""
    sync_p = subparsers.add_parser("sync-spoke", help="Synchronize skills to a spoke")
    sync_p.add_argument("spoke_path", nargs="?", default=".", help="Path to target spoke")
    sync_p.add_argument("--sync-item", default=None, help="Specific skill name")
    sync_p.add_argument("--apply", "-y", action="store_true", help="Apply changes to disk")
    sync_p.add_argument("--bootstrap", "-b", action="store_true", help="Bootstrap Python packages")
    for flag, help_text in (
        ("--all", "Batch sync all registered Spokes"),
        ("--dry-run", "Preview changes without modifying files"),
        ("--force", "Ignore uncommitted changes warning"),
        ("--include-sandboxes", "Include personal sandboxes"),
        ("--verify", "Run deterministic verify-patch post-sync"),
        ("--pull-assets", "Physically copy OKF legal document bundles into Spoke"),
    ):
        sync_p.add_argument(flag, action="store_true", help=help_text)


def _add_ingest_legal_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register ingest-legal subcommand arguments."""
    ingest_p = subparsers.add_parser("ingest-legal", help="Autonomous TVPL VIP Crawler to Spoke")
    ingest_p.add_argument("url", help="Target TVPL URL or Document Identifier")
    ingest_p.add_argument("--spoke", default=None, help="Path to legal spoke")
    ingest_p.add_argument(
        "-c",
        "--category",
        default="01_vbpl",
        choices=["01_vbpl", "02_qcvn", "03_tcvn"],
        help="Document category",
    )
    ingest_p.add_argument("-t", "--doc-type", "--type", default="vbpl", help="Profile type")
    ingest_p.add_argument("--sync-cloud", action="store_true", help="Trigger cloud sync")
    ingest_p.add_argument("--mock", action="store_true", help="Use mock crawler")
    ingest_p.add_argument("--docx", default=None, help="Path to local DOCX file")
    ingest_p.add_argument("--pdf", default=None, help="Path to local PDF file")
    ingest_p.add_argument("--slug", default=None, help="Explicit canonical document slug")
    ingest_p.add_argument("--cdp-port", default=None, type=int, help="Chrome DevTools port")


def _add_audit_and_cross_ref_parsers(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register doc-audit and validate-cross-ref subcommands."""
    doc_audit_p = subparsers.add_parser("doc-audit", help="Run 5-axis documentation audit")
    doc_audit_p.add_argument("--fix", action="store_true", help="Auto-fix trivial link issues")
    doc_audit_p.add_argument("--root", default=None, help="Custom project root directory")
    doc_audit_p.add_argument("--changed", action="store_true", help="Only validate changed files")

    cross_p = subparsers.add_parser("validate-cross-ref", help="Validate traceability matrix")
    cross_p.add_argument("--matrix", default=".md/data/cross_references.yaml", help="Matrix path")
    cross_p.add_argument("--fix", action="store_true", help="Auto-fix heading anchor drifts")


def _add_protect_repo_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register protect-repo subcommand arguments."""
    protect_p = subparsers.add_parser("protect-repo", help="Automated GitHub repository protection")
    protect_p.add_argument("--repo", "-r", default=None, help="Target repository 'owner/repo'")
    protect_p.add_argument("--branch", "-b", default=None, help="Branch to protect")
    protect_p.add_argument("--checks", "-c", nargs="*", default=None, help="Required CI checks")
    protect_p.add_argument("--approvals", "-a", type=int, default=0, help="Required PR approvals")
    protect_p.add_argument("--ruleset-name", default="Protect Main Branch", help="Ruleset name")
    protect_p.add_argument("--no-dependabot", action="store_true", help="Skip Dependabot")
    protect_p.add_argument("--dry-run", action="store_true", help="Preview planned API calls")


def _add_find_seam_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register find-seam subcommand arguments."""
    find_seam_p = subparsers.add_parser("find-seam", help="Search Public Deep Seams (ADR-0061)")
    find_seam_p.add_argument("keyword", nargs="?", default=None, help="Optional search keyword")
    find_seam_p.add_argument("--in", dest="in_types", nargs="+", default=None, help="Input types")
    find_seam_p.add_argument("--out", dest="out_types", nargs="+", default=None, help="Output")
    find_seam_p.add_argument("--hardware", type=str, default=None, help="Hardware constraint")
    find_seam_p.add_argument("--json", action="store_true", help="Output JSON receipt")
    find_seam_p.add_argument("--check", action="store_true", help="Validate seam-contracts.yaml")


def build_parser() -> argparse.ArgumentParser:
    """Build unified argument parser for ccba-platform."""
    parser = argparse.ArgumentParser(
        prog="ccba-platform",
        description="CCBA Agent Services Platform — Central Unified CLI Launcher",
    )
    subparsers = parser.add_subparsers(dest="command", help="Platform commands")
    _add_init_spoke_parser(subparsers)
    _add_adopt_and_bootstrap_parsers(subparsers)
    _add_sync_spoke_parser(subparsers)
    _add_ingest_legal_parser(subparsers)
    _add_audit_and_cross_ref_parsers(subparsers)
    _add_protect_repo_parser(subparsers)
    _add_find_seam_parser(subparsers)
    return parser


def _handle_init_spoke(args: argparse.Namespace) -> int:
    """Dispatch init-spoke command."""
    from scripts.spoke.spoke_initializer import init_project

    if (
        args.path_opt
        and args.spoke_path
        and Path(args.path_opt).resolve() != Path(args.spoke_path).resolve()
    ):
        print(
            f"❌ Error: Conflicting spoke paths specified: '{args.spoke_path}' (positional) vs '{args.path_opt}' (-p/--path).\n"
            "   Please specify only one destination path.",
            file=sys.stderr,
        )
        return 1
    target = args.path_opt or args.spoke_path or "."
    return init_project(
        target,
        _ROOT_DIR,
        args.name,
        args.archetype,
        args.project_type,
        args.mode,
        args.sub_type,
        args.dry_run,
        args.force,
        args.sync,
        args.bootstrap,
        args.init_git,
    )


def _handle_adopt_spoke(args: argparse.Namespace) -> int:
    """Dispatch adopt-spoke command."""
    from scripts.spoke.spoke_adopter import adopt_project

    return adopt_project(
        args.spoke_path, args.dry_run, args.project_type, args.mode, args.archetype, args.force
    )


def _handle_sync_spoke(args: argparse.Namespace) -> int:
    """Dispatch sync-spoke command."""
    dry_run = not args.apply if not args.dry_run else True
    common = {
        "sync_item": args.sync_item,
        "dry_run": dry_run,
        "force": args.force,
        "bootstrap": args.bootstrap,
        "verify": args.verify,
        "pull_assets": args.pull_assets,
    }
    if args.all:
        from scripts.spoke import sync_all_spokes

        return sync_all_spokes(
            hub_root=_ROOT_DIR, include_sandboxes=args.include_sandboxes, **common
        )
    from scripts.spoke import sync_project

    return sync_project(spoke_path=args.spoke_path, **common)


def _handle_bootstrap_spoke(args: argparse.Namespace) -> int:
    """Dispatch bootstrap-spoke command."""
    from scripts.spoke.spoke_bootstrap import SpokeBootstrapper

    bs = SpokeBootstrapper(spoke_path=args.spoke_path, hub_path=_ROOT_DIR)
    return bs.bootstrap(args.create_venv, args.dry_run, args.check_only, args.force)


def _handle_ingest_legal(args: argparse.Namespace) -> int:
    """Dispatch ingest-legal command."""
    ok = execute_ingest_legal(
        args.url,
        args.spoke,
        args.category,
        args.doc_type,
        args.sync_cloud,
        args.mock,
        args.docx,
        args.pdf,
        args.slug,
        args.cdp_port,
    )
    return 0 if ok else 1


def _handle_doc_audit(args: argparse.Namespace) -> int:
    """Dispatch doc-audit command."""
    from scripts.doc_auditor import DocumentAuditor

    auditor = DocumentAuditor(project_root=Path(args.root) if args.root else _ROOT_DIR)
    cli_args = (
        (["--fix"] if args.fix else [])
        + (["--changed"] if args.changed else [])
        + (["--root", str(args.root)] if args.root else [])
    )
    return int(auditor.run_docs_validation_cli(cli_args))


def _handle_validate_cross_ref(args: argparse.Namespace) -> int:
    """Dispatch validate-cross-ref command."""
    from scripts.governance.cross_ref_validator import validate_cross_references

    return validate_cross_references(
        yaml_path=Path(args.matrix), project_root=_ROOT_DIR, auto_fix=args.fix
    )


def _handle_protect_repo(args: argparse.Namespace) -> int:
    """Dispatch protect-repo command."""
    from scripts.governance.protect_repo import protect_repository

    return protect_repository(
        args.repo,
        args.branch,
        args.checks,
        args.approvals,
        args.no_dependabot,
        args.ruleset_name,
        args.dry_run,
    )


def _handle_find_seam(args: argparse.Namespace) -> int:
    """Dispatch find-seam command."""
    if getattr(args, "check", False):
        from scripts.governance.compile_catalog import validate_seam_contracts

        errors = validate_seam_contracts(hub_root=_ROOT_DIR)
        for err in errors:
            print(f"❌ {err}", file=sys.stderr)
        if not errors:
            print("✅ [OK] seam-contracts.yaml is valid.")
        return 1 if errors else 0

    from scripts.governance.compile_catalog import query_seam_contracts

    cwd = Path.cwd()
    has_local = (cwd / ".agents" / "cache" / "hub-catalog").exists() or (
        cwd / "seam-contracts.yaml"
    ).exists()
    exit_code, _ = query_seam_contracts(
        cwd if has_local else _ROOT_DIR,
        args.in_types,
        args.out_types,
        args.hardware,
        args.keyword,
        args.json,
    )
    return exit_code


_COMMAND_HANDLERS: dict[str, Callable[[argparse.Namespace], int]] = {
    "init-spoke": _handle_init_spoke,
    "adopt-spoke": _handle_adopt_spoke,
    "sync-spoke": _handle_sync_spoke,
    "bootstrap-spoke": _handle_bootstrap_spoke,
    "spoke-status": lambda _args: display_spoke_health_dashboard(hub_root=_ROOT_DIR),
    "ingest-legal": _handle_ingest_legal,
    "doc-audit": _handle_doc_audit,
    "validate-cross-ref": _handle_validate_cross_ref,
    "protect-repo": _handle_protect_repo,
    "find-seam": _handle_find_seam,
}


def main(argv: list[str] | None = None) -> int:
    """Main CLI entrypoint."""
    configure_utf8_output()
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = _COMMAND_HANDLERS.get(args.command)
    if handler is not None:
        return handler(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
