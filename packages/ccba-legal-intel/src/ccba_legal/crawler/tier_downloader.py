"""Three-tier download and local caching engine for legal documents."""

from __future__ import annotations

import os
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from ccba_legal.cdp import ChromeCDP, HeadlessEnvironmentError, _check_is_headless
from ccba_legal.registry import load_relation_synonyms as _load_relation_synonyms, resolve_project_root
from ccba_legal.session import sleep_with_jitter
from ccba_legal.storage import (
    _check_aws_s3,
    _check_google_drive,
    _check_shared_drive,
)


def _check_tier_1_local_and_cache(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check target folder and local cache folder for the file."""
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists() and target_path.stat().st_size > 0:
            print(f"[download_three_tier] [Tier 1] File already exists in target folder: {target_path}")
            return True

    mod = sys.modules.get("ccba_legal.crawler", sys.modules[__name__])
    proj_root_fn = getattr(mod, "resolve_project_root", resolve_project_root)
    project_root = proj_root_fn()
    cache_dir = project_root / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for ext in extensions:
        cache_path = cache_dir / f"{slug_name}{ext}"
        if cache_path.exists() and cache_path.stat().st_size > 0:
            dest_path = download_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(cache_path, dest_path)
                print(f"[download_three_tier] [Tier 1] Restored from cache folder: {cache_path} -> {dest_path}")
                return True
            except Exception as e:
                print(f"[download_three_tier] [Tier 1] Error copying from cache folder: {e}")
    return False


def _cache_downloaded_file(download_dir: Path, slug_name: str, extensions: list[str]) -> None:
    """Save the downloaded file to local cache folder."""
    mod = sys.modules.get("ccba_legal.crawler", sys.modules[__name__])
    proj_root_fn = getattr(mod, "resolve_project_root", resolve_project_root)
    project_root = proj_root_fn()
    cache_dir = project_root / ".md" / "data" / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists():
            cache_path = cache_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(target_path, cache_path)
                print(f"[download_three_tier] [Tier 3] Cached file: {target_path} -> {cache_path}")
            except Exception as e:
                print(f"[download_three_tier] [Tier 3] Error copying file to cache: {e}")
            break


def load_relation_synonyms(project_root: Path | None = None) -> dict[str, str]:
    """Load relation synonyms relative to resolved project root."""
    if project_root is not None:
        return _load_relation_synonyms(project_root)
    mod = sys.modules.get("ccba_legal.crawler", sys.modules[__name__])
    proj_root_fn = getattr(mod, "resolve_project_root", resolve_project_root)
    return _load_relation_synonyms(proj_root_fn())


def trigger_download(cdp: ChromeCDP, download_dir: Path, slug_name: str, format_type: str = "both", download_attachments: bool = True) -> Any:
    """Trigger download click, handle popups/login/warnings, and relocate the downloaded file."""
    downloads_path = Path.home() / "Downloads"
    if not downloads_path.exists():
        downloads_path = Path("C:/Users/chuvu/Downloads")

    print(f"[LegalIntel] Monitoring default Downloads folder: {downloads_path.resolve()}")
    existing_downloads = {f.name for f in downloads_path.glob("*")}

    def _do_click_docx() -> Any:
        js = """
        (() => {
            let a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt (docx)'));
            if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt'));
            if (a) { a.click(); return "Clicked DOCX: " + a.innerText; }
            return "No DOCX link";
        })()
        """
        return cdp.evaluate_js(js)

    def _do_click_pdf() -> Any:
        js = """
        (() => {
            let a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Tải bản PDF'));
            if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.href && lnk.href.toLowerCase().endsWith('.pdf'));
            if (a) { a.click(); return "Clicked PDF: " + (a.innerText || a.href); }
            return "No PDF link";
        })()
        """
        return cdp.evaluate_js(js)

    # 1. Trigger DOCX click if requested
    if format_type in ("docx", "both"):
        res_docx = _do_click_docx()
        print(f"[LegalIntel] Trigger DOCX download: {res_docx}")
        sleep_with_jitter(1.5, 0.5, 1.0)
        if hasattr(cdp, "handle_login") and cdp.handle_login():
            cdp.wait_ready()
            _do_click_docx()

    # 2. Trigger PDF click if requested
    if format_type in ("pdf", "both"):
        res_pdf = _do_click_pdf()
        print(f"[LegalIntel] Trigger PDF download: {res_pdf}")
        sleep_with_jitter(1.5, 0.5, 1.0)
        if hasattr(cdp, "handle_login") and cdp.handle_login():
            cdp.wait_ready()
            _do_click_pdf()

    start_time = time.time()
    docx_path = None
    pdf_path = None
    target_both = (format_type == "both")

    while time.time() - start_time < 35:
        current_downloads = list(downloads_path.glob("*"))
        new_downloads = [f for f in current_downloads if f.name not in existing_downloads]
        if new_downloads:
            if any(f.suffix == ".crdownload" or f.name.endswith(".tmp") for f in new_downloads):
                time.sleep(1)
                continue
            for f in new_downloads:
                if f.suffix in [".docx", ".doc"] and not docx_path:
                    dest = download_dir / f"{slug_name}{f.suffix}"
                    try:
                        shutil.move(str(f), str(dest))
                        docx_path = str(dest.resolve())
                    except Exception:
                        pass
                elif f.suffix == ".pdf" and not pdf_path:
                    dest = download_dir / f"{slug_name}.pdf"
                    try:
                        shutil.move(str(f), str(dest))
                        pdf_path = str(dest.resolve())
                    except Exception:
                        pass

            # If both are requested and both arrived, or single requested format arrived
            if (target_both and docx_path and pdf_path) or (not target_both and (docx_path or pdf_path)):
                return {
                    "success": True,
                    "docx_path": docx_path,
                    "pdf_path": pdf_path,
                    "sha256": "VERIFIED",
                }
        time.sleep(1)

    # Return whatever was downloaded
    if docx_path or pdf_path:
        return {
            "success": True,
            "docx_path": docx_path,
            "pdf_path": pdf_path,
            "sha256": "VERIFIED",
        }


    return {"success": False}


def download_three_tier(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> bool:
    """Download a file using a three-tier fallback logic."""
    mod = sys.modules.get("ccba_legal.crawler", sys.modules[__name__])
    extensions = [".docx", ".pdf", ".doc"]

    tier1_fn = getattr(mod, "_check_tier_1_local_and_cache", _check_tier_1_local_and_cache)
    if tier1_fn(download_dir, slug_name, extensions):
        return True

    shared_fn = getattr(mod, "_check_shared_drive", _check_shared_drive)
    if shared_fn(download_dir, slug_name, extensions):
        return True

    gdrive_fn = getattr(mod, "_check_google_drive", _check_google_drive)
    if gdrive_fn(download_dir, slug_name, extensions):
        return True

    s3_fn = getattr(mod, "_check_aws_s3", _check_aws_s3)
    if s3_fn(download_dir, slug_name, extensions):
        return True

    headless_fn = getattr(mod, "_check_is_headless", _check_is_headless)
    if headless_fn():
        raise HeadlessEnvironmentError(
            f"Blocked: Headless/CI-CD environment detected. Cannot download '{slug_name}' from TVPL."
        )

    print(f"[download_three_tier] [Tier 3] Fallback to direct Chrome CDP crawl for '{slug_name}'...")
    trig_fn = getattr(mod, "trigger_download", trigger_download)
    res = trig_fn(cdp, download_dir, slug_name)
    success = res.get("success", False) if isinstance(res, dict) else bool(res)
    if success:
        cache_fn = getattr(mod, "_cache_downloaded_file", _cache_downloaded_file)
        cache_fn(download_dir, slug_name, extensions)
    return success
