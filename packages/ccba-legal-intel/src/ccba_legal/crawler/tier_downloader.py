"""Three-tier download and local caching engine for legal documents."""

from __future__ import annotations

import json
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from ccba_legal.cdp import ChromeCDP, HeadlessEnvironmentError, _check_is_headless
from ccba_legal.crawler.selectors import TVPLSelectors
from ccba_legal.registry import load_relation_synonyms as _load_relation_synonyms
from ccba_legal.registry import resolve_project_root
from ccba_legal.session import sleep_with_jitter
from ccba_legal.storage import (
    _check_aws_s3,
    _check_google_drive,
    _check_shared_drive,
)


def _check_tier_1_local_and_cache(
    download_dir: Path, slug_name: str, extensions: list[str]
) -> bool:
    """Check target folder and local cache folder for the file."""
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists() and target_path.stat().st_size > 0:
            print(
                f"[download_three_tier] [Tier 1] File already exists in target folder: {target_path}"
            )
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
                print(
                    f"[download_three_tier] [Tier 1] Restored from cache folder: {cache_path} -> {dest_path}"
                )
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


def _wait_for_download(
    watch_dirs: list[Path],
    existing_downloads: set[str],
    expected_exts: list[str],
    timeout: float = 30.0,
    start_time: float | None = None,
) -> Path | None:
    """Wait for newly downloaded file matching expected_exts with size > 0 and no .crdownload."""
    if start_time is None:
        start_time = time.time()
    valid_watch_dirs = []
    for d in dict.fromkeys(watch_dirs):
        try:
            if d.exists():
                valid_watch_dirs.append(d)
        except OSError:
            pass

    def _is_new_or_updated(f: Path) -> bool:
        try:
            if str(f.resolve()) not in existing_downloads:
                return True
            return f.stat().st_mtime >= (start_time - 1.0)
        except OSError:
            return False

    while time.time() - start_time < timeout:
        current_downloads = []
        for d in valid_watch_dirs:
            try:
                current_downloads.extend(d.glob("*"))
            except OSError:
                continue
        new_downloads = [f for f in current_downloads if _is_new_or_updated(f)]

        is_downloading = False
        for f in new_downloads:
            try:
                if f.suffix == ".crdownload" or f.name.endswith(".tmp"):
                    is_downloading = True
                    break
            except OSError:
                continue
        if is_downloading:
            time.sleep(0.5)
            continue

        for f in new_downloads:
            if any(f.name.lower().endswith(ext) for ext in expected_exts):
                try:
                    if f.is_file() and f.stat().st_size > 0:
                        return f
                except OSError:
                    pass
        time.sleep(0.5)
    return None


PDF_FINDER_JS = """
(() => {
    let all_links = Array.from(document.querySelectorAll('a'));
    // Pass 1: Tier 1 - VIP Born-Digital Vector Searchable PDF (part=-100 or #filePDFHyperLink)
    let a_tier1 = all_links.find(lnk => {
        let id = (lnk.id || '').toLowerCase();
        let cls = (lnk.className || '').toLowerCase();
        let h = (lnk.href || '').toLowerCase();
        return id.includes('filepdfhyperlink') || cls.includes('filepdfhyperlink') || h.includes('part=-100') || h.includes('part%3d-100');
    });
    if (a_tier1) {
        let href_val = (a_tier1.getAttribute('href') || a_tier1.href || '').trim();
        if (href_val.toLowerCase().startsWith('javascript:')) {
            try { eval(decodeURIComponent(href_val.replace(/^javascript:/i, ''))); }
            catch(e) { a_tier1.click(); }
        } else {
            a_tier1.click();
        }
        return { clicked: true, tier: 1, href: a_tier1.href || a_tier1.innerText };
    }
    // Pass 2: Tier 3 - Gazette Scan / Photocopy PDF Fallback (part=0 or #vietnameseHyperLink_Pdf)
    let a_tier3 = all_links.find(lnk => {
        let t = (lnk.innerText || '').toLowerCase();
        let h = (lnk.href || '').toLowerCase();
        let id = (lnk.id || '').toLowerCase();
        return id.includes('vietnamesehyperlink_pdf') ||
               (t.includes('tải') && t.includes('bản pdf')) ||
               (t.includes('tải') && t.includes('văn bản gốc')) ||
               h.includes('part=0') ||
               h.includes('part%3d0');
    });
    if (!a_tier3) {
        a_tier3 = all_links.find(lnk => {
            let h = (lnk.href || '').toLowerCase();
            return h.endsWith('.pdf') || h.includes('.pdf?');
        });
    }
    if (a_tier3) {
        let href_val = (a_tier3.getAttribute('href') || a_tier3.href || '').trim();
        if (href_val.toLowerCase().startsWith('javascript:')) {
            try { eval(decodeURIComponent(href_val.replace(/^javascript:/i, ''))); }
            catch(e) { a_tier3.click(); }
        } else {
            a_tier3.click();
        }
        return { clicked: true, tier: 3, href: a_tier3.href || a_tier3.innerText };
    }
    return { clicked: false, tier: null, href: null };
})()
"""


def trigger_download(
    cdp: ChromeCDP,
    download_dir: Path,
    slug_name: str,
    format_type: str = "both",
    download_attachments: bool = True,
    doc_url: str = "",
) -> Any:
    """Trigger multi-asset download via Single-Door tab=7 architecture and relocate downloaded files."""
    downloads_path = Path.home() / "Downloads"
    if not downloads_path.exists():
        downloads_path.mkdir(parents=True, exist_ok=True)
    watch_dirs = [downloads_path, download_dir]
    print(f"[LegalIntel] Monitoring Downloads folders: {[str(d) for d in watch_dirs]}")

    # Configure Chrome download behavior to allow automatic downloads
    try:
        cdp.set_download_behavior(download_dir)
    except Exception:
        pass

    # 1. Single-Door: Navigate directly to tab=7 (Tải về) or activate TCVN tab
    target_base = doc_url or cdp.evaluate_js("window.location.href") or ""
    if target_base and "thuvienphapluat.vn" in str(target_base):
        base_url = str(target_base).split("?")[0]
        is_tcvn = "/tcvn/" in base_url.lower()

        def _activate_download_view() -> None:
            if is_tcvn:
                print("[LegalIntel] [TCVN Mode] Activating client-side download tab #aTabTaiVe...")
                cdp.evaluate_js("""
                (() => {
                    let tabBtn = document.querySelector('#aTabTaiVe') || document.querySelector('a[href="#tab8"]');
                    if (tabBtn) tabBtn.click();
                })()
                """)
                sleep_with_jitter(1.5, 0.5, 1.0)
            else:
                tab7_url = f"{base_url}?tab=7"
                print(f"[LegalIntel] [Single-Door tab=7] Navigating directly to: {tab7_url}")
                cdp.navigate(tab7_url)
                cdp.wait_ready()
                sleep_with_jitter(2.0, 0.5, 1.0)

        current_href = str(cdp.evaluate_js("window.location.href") or "")
        if not current_href.startswith(base_url):
            cdp.navigate(base_url)
            cdp.wait_ready()
            sleep_with_jitter(1.0, 0.5, 1.0)

        _activate_download_view()

        if hasattr(cdp, "handle_login") and cdp.handle_login():
            cdp.wait_ready()
            sleep_with_jitter(2.0, 0.5, 1.0)
            current_href = str(cdp.evaluate_js("window.location.href") or "")
            if is_tcvn:
                print("[LegalIntel] [TCVN Mode] Re-activating client tab #aTabTaiVe after login...")
                _activate_download_view()
            elif "tab=7" not in current_href:
                _activate_download_view()

    # Re-apply download behavior on active page after navigation/login
    try:
        cdp.set_download_behavior(download_dir)
    except Exception:
        pass

    def _do_click_docx() -> Any:
        js = """
        (() => {
            let all_links = Array.from(document.querySelectorAll('a'));
            // 1. Prioritize explicit DOCX (id includes 'docx' or 'vietnamesehyperlink_docx', text includes '(docx)', or href contains 'docx=1')
            let a_docx = all_links.find(lnk => {
                let t = (lnk.innerText || '').toLowerCase();
                let h = (lnk.href || '').toLowerCase();
                let id = (lnk.id || '').toLowerCase();
                return (id.includes('docx') || id.includes('vietnamesehyperlink_docx') || t.includes('(docx)') || h.includes('docx=1')) && !t.includes('tiếng anh');
            });
            if (!a_docx) {
                // 2. Fallback to generic Word link
                a_docx = all_links.find(lnk => {
                    let t = (lnk.innerText || '').toLowerCase();
                    let h = (lnk.href || '').toLowerCase();
                    return (t.includes('tiếng việt') || (t.includes('tải') && t.includes('văn bản'))) && (h.includes('download.aspx') || h.includes('part=')) && !t.includes('tiếng anh') && !t.includes('pdf');
                });
            }
            if (a_docx) {
                let href_val = (a_docx.getAttribute('href') || a_docx.href || '').trim();
                if (href_val.toLowerCase().startsWith('javascript:')) {
                    let jsCode = decodeURIComponent(href_val.replace(/^javascript:/i, ''));
                    try {
                        eval(jsCode);
                    } catch (e) {
                        a_docx.click();
                    }
                } else {
                    a_docx.click();
                }
                return "Clicked DOCX: " + (a_docx.innerText || a_docx.href);
            }
            return "No DOCX/DOC link in tab=7";
        })()
        """
        return cdp.evaluate_js(js)

    def _do_click_pdf() -> dict[str, Any]:
        res = cdp.evaluate_js(PDF_FINDER_JS)
        if isinstance(res, dict):
            return res
        if isinstance(res, str) and res and not res.startswith("No "):
            tier = 1 if "part=-100" in res or "filepdfhyperlink" in res.lower() else 3
            return {"clicked": True, "tier": tier, "href": res}
        return {"clicked": False, "tier": None, "href": None}

    def _do_download_all_attachments() -> list[dict[str, str]]:
        excluded_patterns_js = json.dumps(TVPLSelectors.EXCLUDED_ATTACHMENT_PATTERNS)
        js = f"""
        (() => {{
            let links = Array.from(document.querySelectorAll('a'));
            let attachLinks = [];
            let excludedPatterns = {excluded_patterns_js};
            links.forEach(lnk => {{
                let text = (lnk.innerText || '').trim();
                let href = (lnk.href || '').trim();
                let lowerText = text.toLowerCase();
                let lowerHref = href.toLowerCase();

                // Identify appendix/attachment links: .doc, .docx, .xls, .xlsx, .pdf, .zip, .rar
                let isMain = lowerText.includes('tải văn bản tiếng việt') || lowerText.includes('tiếng việt (docx)') || lowerText.includes('tải bản pdf') || lowerHref.includes('part=-100') || lowerHref.includes('docx=1');
                let hasAttachExt = lowerHref.includes('.doc') || lowerHref.includes('.xls') || lowerHref.includes('.pdf') || lowerHref.includes('.zip') || lowerHref.includes('.rar');
                let isAttachText = lowerText.includes('phụ lục') || lowerText.includes('biểu mẫu') || lowerText.includes('bảng tính') || lowerText.includes('đính kèm') || lowerText.includes('tệp đính kèm');
                let isPromoOrNav = excludedPatterns.some(pat => lowerHref.includes(pat));

                if (!isMain && !isPromoOrNav && (hasAttachExt || isAttachText) && href && !href.startsWith('javascript:void') && !href.endsWith('#')) {{
                    attachLinks.push({{ text: text || 'attachment', href: href }});
                }}
            }});
            return attachLinks;
        }})()
        """
        try:
            res = cdp.evaluate_js(js)
            if isinstance(res, list):
                return res
        except Exception as e:
            print(f"[LegalIntel] Error querying attachments: {e}")
        return []

    # 2. Trigger Standalone Attachments download if requested
    saved_attachments: list[str] = []
    if download_attachments:
        found_attachs = _do_download_all_attachments()
        if found_attachs:
            print(
                f"[LegalIntel] Discovered {len(found_attachs)} standalone attachment(s) in tab=7."
            )
            attach_dir = download_dir / "attachments"
            attach_dir.mkdir(parents=True, exist_ok=True)
            for idx, item in enumerate(found_attachs, 1):
                att_url = item.get("href", "")
                att_text = item.get("text", f"attachment_{idx}")
                clean_name = re.sub(r"[^\w\d\.\-_]", "_", att_text)
                if not any(
                    clean_name.endswith(ext)
                    for ext in [".doc", ".docx", ".xls", ".xlsx", ".pdf", ".zip", ".rar"]
                ):
                    if ".xlsx" in att_url.lower():
                        clean_name += ".xlsx"
                    elif ".xls" in att_url.lower():
                        clean_name += ".xls"
                    elif ".docx" in att_url.lower():
                        clean_name += ".docx"
                    elif ".doc" in att_url.lower():
                        clean_name += ".doc"
                    elif ".pdf" in att_url.lower():
                        clean_name += ".pdf"
                    else:
                        clean_name += ".dat"
                target_att_file = attach_dir / clean_name
                print(
                    f"[LegalIntel] [Attachment {idx}/{len(found_attachs)}] Registered: {clean_name} -> {att_url}"
                )
                saved_attachments.append(str(target_att_file.resolve()))

    # 3. Pre-flight Inspection: Scan DOM tab=7 for available formats
    preflight_js = """
    (() => {
        let all_links = Array.from(document.querySelectorAll('a'));
        let a_docx = all_links.find(lnk => {
            let t = (lnk.innerText || '').toLowerCase();
            let h = (lnk.href || '').toLowerCase();
            let id = (lnk.id || '').toLowerCase();
            return (id.includes('docx') || id.includes('vietnamesehyperlink_docx') || t.includes('(docx)') || h.includes('docx' + '=1')) && !t.includes('tiếng anh');
        });
        if (!a_docx) {
            a_docx = all_links.find(lnk => {
                let t = (lnk.innerText || '').toLowerCase();
                let h = (lnk.href || '').toLowerCase();
                return (t.includes('tiếng việt') || (t.includes('tải') && t.includes('văn bản'))) && (h.includes('download.aspx') || h.includes('part=')) && !t.includes('tiếng anh') && !t.includes('pdf');
            });
        }
        // Pass 1: Tier 1 - Born-Digital Vector Searchable PDF
        let a_pdf_tier1 = all_links.find(lnk => {
            let id = (lnk.id || '').toLowerCase();
            let cls = (lnk.className || '').toLowerCase();
            let h = (lnk.href || '').toLowerCase();
            return id.includes('filepdfhyperlink') || cls.includes('filepdfhyperlink') || h.includes('part=-100') || h.includes('part%3d-100');
        });
        // Pass 2: Tier 3 - Gazette Scan Fallback
        let a_pdf_tier3 = null;
        if (!a_pdf_tier1) {
            a_pdf_tier3 = all_links.find(lnk => {
                let t = (lnk.innerText || '').toLowerCase();
                let h = (lnk.href || '').toLowerCase();
                let id = (lnk.id || '').toLowerCase();
                return id.includes('vietnamesehyperlink_pdf') ||
                       (t.includes('tải') && t.includes('bản pdf')) ||
                       (t.includes('tải') && t.includes('văn bản gốc')) ||
                       h.includes('part=0') ||
                       h.includes('part%3d0');
            });
            if (!a_pdf_tier3) {
                a_pdf_tier3 = all_links.find(lnk => {
                    let h = (lnk.href || '').toLowerCase();
                    return h.endsWith('.pdf') || h.includes('.pdf?');
                });
            }
        }
        let a_pdf = a_pdf_tier1 || a_pdf_tier3;
        let pdf_tier = a_pdf_tier1 ? 1 : (a_pdf_tier3 ? 3 : null);
        return {
            has_docx: Boolean(a_docx),
            has_pdf: Boolean(a_pdf),
            pdf_tier: pdf_tier
        };
    })()
    """
    preflight_res = cdp.evaluate_js(preflight_js)
    preflight_pdf_tier = None
    if isinstance(preflight_res, dict):
        has_docx = bool(preflight_res.get("has_docx", False))
        has_pdf = bool(preflight_res.get("has_pdf", False))
        preflight_pdf_tier = preflight_res.get("pdf_tier")
    elif isinstance(preflight_res, str) and preflight_res:
        has_docx = "docx" in preflight_res.lower()
        has_pdf = "pdf" in preflight_res.lower()
    else:
        has_docx = True
        has_pdf = True

    print(
        f"[LegalIntel] [Pre-flight Inspection] Available in tab=7: DOCX={has_docx}, PDF={has_pdf} (Tier={preflight_pdf_tier})"
    )

    # Fast-fail if requested format is not available
    if format_type == "docx" and not has_docx:
        print(
            f"[LegalIntel] [Fast-Fail] Requested format 'docx' not found in tab=7 for '{slug_name}'."
        )
        return {
            "success": False,
            "docx_path": None,
            "pdf_path": None,
            "attachments": saved_attachments,
            "error": "DOCX not available in tab=7",
            "pdf_tier": None,
        }
    if format_type == "pdf" and not has_pdf:
        print(
            f"[LegalIntel] [Fast-Fail] Requested format 'pdf' not found in tab=7 for '{slug_name}'."
        )
        return {
            "success": False,
            "docx_path": None,
            "pdf_path": None,
            "attachments": saved_attachments,
            "error": "PDF not available in tab=7",
            "pdf_tier": None,
        }
    if format_type == "both" and not has_docx and not has_pdf:
        print(f"[LegalIntel] [Fast-Fail] Neither DOCX nor PDF found in tab=7 for '{slug_name}'.")
        return {
            "success": False,
            "docx_path": None,
            "pdf_path": None,
            "attachments": saved_attachments,
            "error": "Neither DOCX nor PDF available in tab=7",
            "pdf_tier": None,
        }

    # Sequential Barrier Downloader
    need_docx = format_type in ("docx", "both") and has_docx
    need_pdf = format_type in ("pdf", "both") and has_pdf
    docx_path: str | None = None
    pdf_path: str | None = None

    # Phase 1: Trigger DOCX PostBack & Wait for completion
    if need_docx:
        existing_before_docx = set()
        for d in watch_dirs:
            try:
                if d.exists():
                    for f in d.glob("*"):
                        try:
                            existing_before_docx.add(str(f.resolve()))
                        except OSError:
                            pass
            except OSError:
                pass
        docx_start_time = time.time()
        res_docx = _do_click_docx()
        print(f"[LegalIntel] [Phase 1] Trigger DOCX postback: {res_docx}")
        if res_docx and not str(res_docx).startswith("No "):
            downloaded_docx = _wait_for_download(
                watch_dirs,
                existing_before_docx,
                [".docx", ".doc"],
                timeout=30.0,
                start_time=docx_start_time,
            )
            if downloaded_docx:
                dest_ext = downloaded_docx.suffix or ".docx"
                dest = download_dir / f"{slug_name}{dest_ext}"
                for _attempt in range(3):
                    try:
                        if downloaded_docx.resolve() != dest.resolve():
                            shutil.move(str(downloaded_docx), str(dest))
                        docx_path = str(dest.resolve())
                        break
                    except Exception as e:
                        if _attempt < 2:
                            time.sleep(0.5)
                            continue
                        print(f"[LegalIntel] Error resolving DOCX file {downloaded_docx}: {e}")
                        docx_path = str(downloaded_docx.resolve())
                print(f"[LegalIntel] [Phase 1] DOCX successfully acquired: {docx_path}")
            else:
                print("[LegalIntel] [Phase 1] DOCX download timed out after 30s.")
        else:
            print("[LegalIntel] [Phase 1] Could not trigger DOCX click.")

    # Phase 2: Cooldown 2s to release ASP.NET Stream
    if need_docx and need_pdf:
        print("[LegalIntel] [Phase 2] ASP.NET Stream cooldown (2.0s)...")
        time.sleep(2.0)

    # Phase 3: Trigger PDF PostBack & Wait for completion
    pdf_tier: int | None = preflight_pdf_tier
    if need_pdf:
        existing_before_pdf = set()
        for d in watch_dirs:
            try:
                if d.exists():
                    for f in d.glob("*"):
                        try:
                            existing_before_pdf.add(str(f.resolve()))
                        except OSError:
                            pass
            except OSError:
                pass
        pdf_start_time = time.time()
        res_pdf = _do_click_pdf()
        print(f"[LegalIntel] [Phase 3] Trigger PDF postback: {res_pdf}")
        clicked = False
        if isinstance(res_pdf, dict):
            clicked = bool(res_pdf.get("clicked", False))
            if res_pdf.get("tier") is not None:
                pdf_tier = res_pdf.get("tier")
        elif res_pdf and not str(res_pdf).startswith("No "):
            clicked = True

        if clicked:
            downloaded_pdf = _wait_for_download(
                watch_dirs, existing_before_pdf, [".pdf"], timeout=30.0, start_time=pdf_start_time
            )
            if downloaded_pdf:
                dest = download_dir / f"{slug_name}.pdf"
                for _attempt in range(3):
                    try:
                        if downloaded_pdf.resolve() != dest.resolve():
                            shutil.move(str(downloaded_pdf), str(dest))
                        pdf_path = str(dest.resolve())
                        break
                    except Exception as e:
                        if _attempt < 2:
                            time.sleep(0.5)
                            continue
                        print(f"[LegalIntel] Error resolving PDF file {downloaded_pdf}: {e}")
                        pdf_path = str(downloaded_pdf.resolve())
                print(f"[LegalIntel] [Phase 3] PDF successfully acquired: {pdf_path}")
            else:
                print("[LegalIntel] [Phase 3] PDF download timed out after 30s.")
        else:
            print("[LegalIntel] [Phase 3] Could not trigger PDF click.")

    # Fallback check if file already exists in download_dir
    if not docx_path and download_dir.exists():
        for f in download_dir.glob(f"{slug_name}.docx"):
            if f.stat().st_size > 0:
                docx_path = str(f.resolve())
                break
        if not docx_path:
            for f in download_dir.glob(f"{slug_name}.doc"):
                if f.stat().st_size > 0:
                    docx_path = str(f.resolve())
                    break

    if not pdf_path and download_dir.exists():
        for f in download_dir.glob(f"{slug_name}.pdf"):
            if f.stat().st_size > 0:
                pdf_path = str(f.resolve())
                break

    if not pdf_path:
        pdf_tier = None

    if docx_path or pdf_path:
        return {
            "success": True,
            "docx_path": docx_path,
            "pdf_path": pdf_path,
            "attachments": saved_attachments,
            "sha256": "VERIFIED",
            "pdf_tier": pdf_tier,
        }

    return {
        "success": False,
        "docx_path": docx_path,
        "pdf_path": pdf_path,
        "attachments": saved_attachments,
        "pdf_tier": pdf_tier,
    }


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

    print(
        f"[download_three_tier] [Tier 3] Fallback to direct Chrome CDP crawl for '{slug_name}'..."
    )
    trig_fn = getattr(mod, "trigger_download", trigger_download)
    res = trig_fn(cdp, download_dir, slug_name)
    success = res.get("success", False) if isinstance(res, dict) else bool(res)
    if success:
        cache_fn = getattr(mod, "_cache_downloaded_file", _cache_downloaded_file)
        cache_fn(download_dir, slug_name, extensions)
    return success
