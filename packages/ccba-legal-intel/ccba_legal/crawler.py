import json
import os
import random
import shutil
import time
from pathlib import Path
from typing import Any

import requests
import websocket

from ccba_harness import FileMutexLock
from ccba_legal.registry import load_relation_synonyms as _load_relation_synonyms
from ccba_legal.registry import resolve_project_root


class TVPLSessionMutex(FileMutexLock):
    """Context manager for TVPL VIP session mutex lock to prevent concurrent sessions.

    Inherits from the unified FileMutexLock in ccba_harness.
    """

    def __init__(
        self, lock_path: Path | None = None, timeout: int = 180, retry_interval: float = 5.0
    ) -> None:
        lock_path_resolved = lock_path or (
            resolve_project_root() / ".md" / "data" / "tvpl_vip_session.lock"
        )
        super().__init__(
            lock_path=lock_path_resolved,
            timeout=timeout,
            retry_interval=retry_interval,
            expire_seconds=300.0,
        )


def load_relation_synonyms() -> dict[str, str]:
    return _load_relation_synonyms(resolve_project_root())


class ChromeCDPError(Exception):
    """Base exception for Chrome DevTools Protocol operations."""

    pass


class HeadlessEnvironmentError(RuntimeError):
    """Raised when running in a headless/CI environment where download is blocked."""

    pass


class ChromeCDP:
    """Helper class to interact with Chrome via DevTools Protocol (CDP)."""

    def __init__(self, port: int = 9222) -> None:
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.ws: websocket.WebSocket | None = None

    def get_pages(self) -> list[dict[str, Any]]:
        """List all open page targets in Chrome."""
        try:
            resp = requests.get(f"{self.base_url}/json", timeout=5)
            resp.raise_for_status()
            return [t for t in resp.json() if t.get("type") == "page"]
        except Exception as e:
            raise ChromeCDPError(f"Failed to connect to Chrome on port {self.port}: {e}") from e

    def connect_tab(self, ws_url: str) -> None:
        """Connect to a specific tab via WebSockets."""
        try:
            self.ws = websocket.create_connection(ws_url, suppress_origin=True)
        except Exception as e:
            raise ChromeCDPError(f"Failed to connect to tab WebSocket: {e}") from e

    def send_command(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a generic CDP command and return the response payload."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        payload = {"id": random.randint(1, 100000), "method": method, "params": params}
        try:
            self.ws.send(json.dumps(payload))
            resp = self.ws.recv()
            return json.loads(resp)
        except Exception as e:
            raise ChromeCDPError(f"Failed to send CDP command {method}: {e}") from e

    def evaluate_js(self, expression: str) -> Any:
        """Evaluate a JavaScript expression in the connected tab."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        payload = {
            "id": random.randint(1, 100000),
            "method": "Runtime.evaluate",
            "params": {"expression": expression, "returnByValue": True},
        }
        try:
            self.ws.send(json.dumps(payload))
            resp = self.ws.recv()
            data = json.loads(resp)

            result_data = data.get("result", {})
            if "exceptionDetails" in result_data:
                exc = result_data["exceptionDetails"]
                raise ChromeCDPError(
                    f"JS Exception: {exc.get('text')} - {exc.get('exception', {})}"
                )

            return result_data.get("result", {}).get("value")
        except Exception as e:
            raise ChromeCDPError(f"Failed to evaluate JS: {e}") from e

    def navigate(self, url: str) -> None:
        """Navigate to a URL and wait for the page to be ready."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        payload = {
            "id": random.randint(1, 100000),
            "method": "Page.navigate",
            "params": {"url": url},
        }
        try:
            self.ws.send(json.dumps(payload))
            self.ws.recv()
            # Wait a brief moment to let the browser start loading the new page
            # so that readyState of the old page isn't mistakenly read as complete.
            time.sleep(1.5)
        except Exception as e:
            raise ChromeCDPError(f"Failed to trigger navigation: {e}") from e

    def wait_ready(self, timeout_sec: int = 30) -> None:
        """Wait for document readyState to be 'complete'."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                state = self.evaluate_js("document.readyState")
                if state == "complete":
                    return
            except ChromeCDPError:
                pass
            time.sleep(0.5)
        raise ChromeCDPError("Timeout waiting for page readyState 'complete'.")

    def handle_cloudflare(self) -> None:
        """Check for Cloudflare bot challenge and pause for user completion if found."""
        check_expr = """
        !!(document.title.includes("Cloudflare") ||
           document.title.includes("Just a moment") ||
           document.querySelector("div.cf-turnstile") ||
           document.querySelector("#challenge-running") ||
           document.querySelector("#challenge-stage"))
        """
        is_blocked = self.evaluate_js(check_expr)
        if is_blocked:
            print("[LegalIntel] Cloudflare Challenge detected! PAUSED.")
            print("[LegalIntel] PLEASE MANUALLY SOLVE THE CAPTCHA IN THE OPEN CHROME WINDOW.")
            while is_blocked:
                time.sleep(2)
                try:
                    is_blocked = self.evaluate_js(check_expr)
                except ChromeCDPError:
                    is_blocked = True
            print("[LegalIntel] Challenge solved! Resuming execution...")
            self.wait_ready()

    def handle_login(self) -> bool:
        """Detect login popup, fill in credentials, submit, handle multi-session warning, and return True if login was attempted."""
        username = os.environ.get("TVPL_USERNAME")
        password = os.environ.get("TVPL_PASSWORD")
        if not username or not password:
            print(
                "  [Login] Missing TVPL_USERNAME or TVPL_PASSWORD env variable. Cannot perform auto-login."
            )
            return False

        js = """
        (() => {
            let tb = document.querySelector('#TB_window');
            if (!tb || tb.style.display === 'none') return "No popup";

            let inputs = Array.from(tb.querySelectorAll('input'));
            let text_inputs = inputs.filter(i => i.type === 'text');
            let pass_inputs = inputs.filter(i => i.type === 'password');
            let buttons = Array.from(tb.querySelectorAll('input[type="submit"], input[type="button"], button'));

            let user = text_inputs[0];
            let pass = pass_inputs[0];
            let login_btn = buttons.find(b => (b.value && b.value.includes('Đăng nhập')) || (b.innerText && b.innerText.includes('Đăng nhập')));

            if (user && pass && login_btn) {
                user.value = "__USERNAME__";
                pass.value = "__PASSWORD__";
                login_btn.click();
                return "Attempted login click";
            }
            return "Inputs not found";
        })()
        """.replace("__USERNAME__", username).replace("__PASSWORD__", password)
        res = self.evaluate_js(js)
        if "Attempted login" in str(res):
            print("  [Login] Found login popup, autofilling credentials and submitting...")
            time.sleep(3)  # Wait for login action to trigger warning or reload

            # Check for multi-session login warning popup
            warning_js = """
            (() => {
                let agree_btn = Array.from(document.querySelectorAll('input, button, a')).find(el => {
                    let txt = el.value || el.innerText || "";
                    return txt.trim().toLowerCase() === 'đồng ý';
                });
                if (agree_btn) {
                    agree_btn.click();
                    return "Clicked Dong y";
                }
                return "No warning popup";
            })()
            """
            warn_res = self.evaluate_js(warning_js)
            print(f"  [Login Warning Check] Result: {warn_res}")
            if "Clicked Dong y" in str(warn_res):
                time.sleep(4)  # Wait for page reload after warning confirmation
            else:
                time.sleep(2)  # Wait for standard reload

            return True
        return False

    def close_popup(self) -> bool:
        """Close any open ThickBox popup on the page."""
        js = """
        (() => {
            let closed = false;
            if (typeof tb_remove === 'function') {
                tb_remove();
                closed = true;
            } else {
                let tbClose = document.querySelector('#TB_closeWindowButton') || document.querySelector('[id*="TB_close"]');
                if (tbClose) {
                    tbClose.click();
                    closed = true;
                }
            }
            let tb = document.querySelector('#TB_window');
            if (tb && tb.style.display !== 'none') {
                tb.style.display = 'none';
                let overlay = document.querySelector('#TB_overlay');
                if (overlay) overlay.style.display = 'none';
                closed = true;
            }
            return closed;
        })()
        """
        return bool(self.evaluate_js(js))

    def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None


def get_crawled_doc_data(cdp: ChromeCDP, url: str) -> tuple[str, str, list[dict[str, str]]]:
    """Retrieve title, clean innerText, and list of links from active browser tab."""
    cdp.navigate(url)
    cdp.wait_ready()
    cdp.handle_cloudflare()

    # Handle login/popup if present
    if cdp.handle_login():
        print("  [Login] Submitted credentials, waiting for reload...")
        cdp.wait_ready()
        cdp.handle_cloudflare()
    elif cdp.close_popup():
        print("  [Popup] Closed window, retrying...")

    title = cdp.evaluate_js("document.title")

    body_text_js = """
    (() => {
        let el = document.querySelector('#divContentDoc') ||
                 document.querySelector('.content1') ||
                 document.querySelector('.contentDoc') ||
                 document.body;
        if (!el) return "";
        let clone = el.cloneNode(true);
        let tables = Array.from(clone.querySelectorAll('table')).filter(t => {
            let parent = t.parentElement;
            while (parent) {
                if (parent.tagName === 'TABLE') return false;
                parent = parent.parentElement;
            }
            return true;
        });
        let tableHTMLs = tables.map(t => t.outerHTML);
        tables.forEach((table, index) => {
            let placeholder = document.createTextNode("\\n\\n__TABLE_PLACEHOLDER_" + index + "__\\n\\n");
            table.parentNode.replaceChild(placeholder, table);
        });
        let text = clone.innerText;
        tableHTMLs.forEach((html, index) => {
            text = text.replace("__TABLE_PLACEHOLDER_" + index + "__", html);
        });
        return text;
    })()
    """
    body_text = cdp.evaluate_js(body_text_js)

    links_js = """
    (() => {
        return Array.from(document.querySelectorAll('a'))
          .map(a => {
              let text = a.innerText.trim();
              let href = a.href || "";
              let lower_text = text.toLowerCase();
              let lower_href = href.toLowerCase();
              let rel = "Guides";

              if (lower_href.includes('hop-nhat') || lower_href.includes('vbhn') || lower_text.includes('hợp nhất') || lower_text.includes('vbhn')) {
                  rel = "Consolidation";
              } else if (lower_text.includes('thay thế') || lower_text.includes('bị thay thế')) {
                  rel = "Replacement";
              } else if (lower_text.includes('đính chính')) {
                  rel = "Rectification";
              } else if (lower_text.includes('sửa đổi') || lower_text.includes('bổ sung')) {
                  rel = "Amendment";
              }

              return { text: text, href: href, relationship: rel };
          })
          .filter(a => a.href && a.href.includes('thuvienphapluat.vn/van-ban/'));
    })()
    """
    raw_links = cdp.evaluate_js(links_js) or []
    seen = set()
    links = []
    for lnk in raw_links:
        h = lnk["href"].split("?")[0].split("#")[0]
        if h not in seen and h != url:
            seen.add(h)
            links.append({"text": lnk["text"], "href": h, "relationship": lnk["relationship"]})

    return title, body_text, links


def trigger_download(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> bool:
    """Trigger download click, handle popups/login/warnings, and relocate the downloaded file."""
    downloads_path = Path.home() / "Downloads"
    if not downloads_path.exists():
        downloads_path = Path("C:/Users/chuvu/Downloads")

    print(f"[LegalIntel] Monitoring default Downloads folder: {downloads_path.resolve()}")
    existing_downloads = {f.name for f in downloads_path.glob("*")}

    click_js = """
    (() => {
        let a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt (docx)'));
        if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Văn bản tiếng Việt'));
        if (!a) a = Array.from(document.querySelectorAll('a')).find(lnk => lnk.innerText && lnk.innerText.includes('Tải bản PDF'));
        if (a) {
            a.click();
            return "Clicked: " + a.innerText;
        }
        return "No download link found";
    })()
    """
    res = cdp.evaluate_js(click_js)
    print(f"[LegalIntel] Trigger download action: {res}")
    if "No download" in str(res):
        return False

    time.sleep(2)
    # Check if login is required
    if cdp.handle_login():
        print("  [Action] Login submitted after click, waiting for reload...")
        cdp.wait_ready()
        cdp.handle_cloudflare()
        print("  [Action] Retrying click...")
        res_retry = cdp.evaluate_js(click_js)
        print(f"  [Action] Retry click result: {res_retry}")
    elif cdp.close_popup():
        print("  [Action] Closed popup detected after click, retrying click...")
        cdp.evaluate_js(click_js)

    # Monitor Downloads folder
    start_time = time.time()
    while time.time() - start_time < 35:
        current_downloads = list(downloads_path.glob("*"))
        new_downloads = [f for f in current_downloads if f.name not in existing_downloads]
        if new_downloads:
            if any(f.suffix == ".crdownload" or f.name.endswith(".tmp") for f in new_downloads):
                time.sleep(1)
                continue

            completed_files = [f for f in new_downloads if f.suffix in [".docx", ".pdf", ".doc"]]
            if completed_files:
                target_file = completed_files[0]
                dest_file = download_dir / f"{slug_name}{target_file.suffix}"
                print(
                    f"[LegalIntel] Moving and standardizing file: {target_file.name} -> {dest_file.resolve()}"
                )
                try:
                    shutil.move(str(target_file), str(dest_file))
                    print(
                        f"[LegalIntel] Download completed successfully: {slug_name}{target_file.suffix}"
                    )
                    return True
                except Exception as e:
                    print(f"[LegalIntel] Error moving file: {e}")
                return False
        time.sleep(1)

    print("[LegalIntel] Warning: Download timed out.")
    return False


def _check_tier_1_local_and_cache(
    download_dir: Path, slug_name: str, extensions: list[str]
) -> bool:
    """Check target folder and local cache folder for the file.

    Returns True if the file was restored/found, False otherwise.
    """
    # 1a. Check target folder
    for ext in extensions:
        target_path = download_dir / f"{slug_name}{ext}"
        if target_path.exists() and target_path.stat().st_size > 0:
            print(
                f"[download_three_tier] [Tier 1] File already exists in target folder: {target_path}"
            )
            return True

    # 1b. Check local cache folder
    project_root = resolve_project_root()
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


def _check_shared_drive(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check SHARED_DRIVE_DIR env path for the file."""
    shared_drive_env = os.environ.get("SHARED_DRIVE_DIR")
    if not shared_drive_env:
        return False
    shared_drive_path = Path(shared_drive_env)
    if not shared_drive_path.exists():
        return False

    for ext in extensions:
        src_file = shared_drive_path / f"{slug_name}{ext}"
        if src_file.exists() and src_file.stat().st_size > 0:
            dest_path = download_dir / f"{slug_name}{ext}"
            try:
                shutil.copy2(src_file, dest_path)
                print(
                    f"[download_three_tier] [Tier 2] Copied from SHARED_DRIVE_DIR: {src_file} -> {dest_path}"
                )
                return True
            except Exception as e:
                print(f"[download_three_tier] [Tier 2] Error copying from SHARED_DRIVE_DIR: {e}")
    return False


def _check_google_drive(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check Google Drive for the file and download if found."""
    try:
        import sys

        project_root = resolve_project_root()
        if str(project_root) not in sys.path:
            sys.path.append(str(project_root))
        from scripts.legal_sync import GOOGLE_API_AVAILABLE, get_drive_service

        if not GOOGLE_API_AVAILABLE:
            return False

        drive_service = get_drive_service()
        drive_folder_id = os.environ.get("DRIVE_FOLDER_ID", "1b9vm_1KQ8Fg8Crr1Q-i2xmE62UIHy-_2")
        for ext in extensions:
            file_name = f"{slug_name}{ext}"
            q = f"name = '{file_name}' and trashed = false"
            if drive_folder_id:
                q += f" and '{drive_folder_id}' in parents"

            results = drive_service.files().list(q=q, fields="files(id, name)").execute()
            files = results.get("files", [])
            if not files:
                continue

            file_id = files[0]["id"]
            dest_path = download_dir / file_name
            print(
                f"[download_three_tier] [Tier 2] Downloading {file_name} from Google Drive (ID: {file_id}) -> {dest_path}"
            )

            from googleapiclient.http import MediaIoBaseDownload

            request = drive_service.files().get_media(fileId=file_id)
            try:
                with open(dest_path, "wb") as f:
                    downloader = MediaIoBaseDownload(f, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                print(
                    f"[download_three_tier] [Tier 2] Successfully downloaded {file_name} from Google Drive."
                )
                return True
            except Exception as e:
                if dest_path.exists():
                    try:
                        dest_path.unlink()
                    except Exception:
                        pass
                raise e
    except Exception as e:
        print(f"[download_three_tier] [Tier 2] Google Drive API check failed: {e}")
    return False


def _check_aws_s3(download_dir: Path, slug_name: str, extensions: list[str]) -> bool:
    """Check AWS S3 bucket for the file and download if found."""
    try:
        import boto3
        from botocore.exceptions import ClientError

        bucket_name = os.environ.get("AWS_BUCKET_NAME") or os.environ.get("S3_BUCKET")
        if not bucket_name:
            return False

        s3_client = boto3.client("s3")
        for ext in extensions:
            file_name = f"{slug_name}{ext}"
            dest_path = download_dir / file_name
            try:
                print(
                    f"[download_three_tier] [Tier 2] Checking S3 bucket '{bucket_name}' for key '{file_name}'..."
                )
                s3_client.download_file(bucket_name, file_name, str(dest_path))
                print(
                    f"[download_three_tier] [Tier 2] Successfully downloaded {file_name} from S3."
                )
                return True
            except ClientError as ce:
                if ce.response["Error"]["Code"] in ["404", "NoSuchKey"]:
                    continue
                print(f"[download_three_tier] [Tier 2] S3 download error: {ce}")
    except ImportError:
        pass
    except Exception as e:
        print(f"[download_three_tier] [Tier 2] S3 check failed: {e}")
    return False


def _check_is_headless() -> bool:
    """Check if running in a headless or CI/CD environment."""
    for env_var in ["CI", "GITHUB_ACTIONS", "TVPL_HEADLESS", "HEADLESS"]:
        val = os.environ.get(env_var)
        if val is not None and val.strip().lower() not in ["false", "0", ""]:
            return True
    return False


def _cache_downloaded_file(download_dir: Path, slug_name: str, extensions: list[str]) -> None:
    """Save the downloaded file to local cache folder."""
    project_root = resolve_project_root()
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


def download_three_tier(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> bool:
    """Download a file using a three-tier fallback logic.

    Tier 1: Check if the file (with .docx, .pdf, or .doc extension) already exists
            in the target `download_dir` or in the local cache directory (.md/data/cache/).
    Tier 2: Check if the file is available in the shared drive directory (SHARED_DRIVE_DIR),
            Google Drive (via Drive API), or AWS S3.
    Tier 3: Fall back to performing a direct Chrome CDP crawl, unless a headless/CI
            environment is detected (which will raise HeadlessEnvironmentError).

    Args:
        cdp: ChromeCDP instance.
        download_dir: The directory where the file should be saved.
        slug_name: The base name (slug) of the file to download.

    Returns:
        bool: True if the file was successfully downloaded or found in cache, False otherwise.
    """
    extensions = [".docx", ".pdf", ".doc"]

    # --- Tier 1: Local & Cache Directory ---
    if _check_tier_1_local_and_cache(download_dir, slug_name, extensions):
        return True

    # --- Tier 2: Shared Drive, Google Drive & AWS S3 ---
    if _check_shared_drive(download_dir, slug_name, extensions):
        return True
    if _check_google_drive(download_dir, slug_name, extensions):
        return True
    if _check_aws_s3(download_dir, slug_name, extensions):
        return True

    # --- Tier 3: Direct Chrome CDP Crawl with Headless/CI-CD Exit Guard ---
    if _check_is_headless():
        raise HeadlessEnvironmentError(
            f"Blocked: Headless/CI-CD environment detected. Cannot download '{slug_name}' from TVPL."
        )

    print(
        f"[download_three_tier] [Tier 3] Fallback to direct Chrome CDP crawl for '{slug_name}'..."
    )
    success = trigger_download(cdp, download_dir, slug_name)
    if success:
        _cache_downloaded_file(download_dir, slug_name, extensions)
    return success


METADATA_EXTRACTION_JS_TEMPLATE = r"""
(() => {
    let result = {};
    let tables = Array.from(document.querySelectorAll('table'));
    let targetTable = tables.find(t => t.innerText.includes('Số hiệu') && t.innerText.includes('Ngày ban hành'));
    if (targetTable) {
        let rows = Array.from(targetTable.querySelectorAll('tr'));
        rows.forEach(row => {
            let cols = Array.from(row.querySelectorAll('td'));
            if (cols.length >= 2) {
                let key = cols[0].innerText.trim().replace(':', '');
                let val = cols[1].innerText.trim();
                if (key && val) {
                    result[key] = val;
                }
            }
        });
    }
    if (Object.keys(result).length === 0) {
        let cells = Array.from(document.querySelectorAll('td, th, div'));
        let keys = ['Số hiệu', 'Loại văn bản', 'Lĩnh vực', 'Nơi ban hành', 'Người ký', 'Ngày ban hành', 'Ngày hiệu lực', 'Ngày đăng', 'Tình trạng'];
        keys.forEach(k => {
            let matchingCell = cells.find(c => c.innerText && c.innerText.trim().startsWith(k + ':'));
            if (matchingCell) {
                let parts = matchingCell.innerText.split(':');
                if (parts.length >= 2) {
                    result[k] = parts.slice(1).join(':').trim();
                }
            }
        });
    }

    // Extract all relationships from diagram page
    let relations = {};
    let relMap = __REL_MAP_JSON__;

    Object.keys(relMap).forEach(key => {
        let normalizedKey = key.replace(/,/g, '').replace(/\s+/g, ' ').trim();
        let els = Array.from(document.querySelectorAll('div, td, th, strong, b'));
        let headerEl = els.find(el => {
            let txt = (el.innerText || "").replace(/,/g, '').replace(/\s+/g, ' ').trim();
            return txt.startsWith(normalizedKey);
        });
        if (headerEl) {
            let container = headerEl.closest('td, tr, div, table');
            if (container) {
                let links = Array.from(container.querySelectorAll('a'))
                    .map(a => {
                        return {
                            title: a.innerText.trim(),
                            url: a.href ? a.href.split('?')[0].split('#')[0] : ""
                        };
                    })
                    .filter(l => l.title && l.title !== headerEl.innerText.trim() && l.url.includes('/van-ban/'));

                if (links.length > 0) {
                    let ccbaKey = relMap[key];
                    if (!relations[ccbaKey]) {
                        relations[ccbaKey] = [];
                    }
                    links.forEach(l => {
                        if (!relations[ccbaKey].some(ex => ex.url === l.url)) {
                            relations[ccbaKey].push(l);
                        }
                    });
                }
            }
        }
    });

    result['relations'] = relations;
    return result;
})()
"""


def _parse_tvpl_date(date_str: str) -> str:
    """Parse a TVPL date string of format DD/MM/YYYY to YYYY-MM-DD."""
    if not date_str:
        return ""
    try:
        parts = date_str.split("/")
        if len(parts) == 3:
            d, m, y = parts
            return f"{y.strip()}-{m.strip().zfill(2)}-{d.strip().zfill(2)}"
    except Exception:
        pass
    return date_str


def get_tvpl_metadata(
    cdp: ChromeCDP, url: str, relation_map: dict[str, str] | None = None
) -> dict[str, Any]:
    """Retrieve structured metadata from the TVPL 'Lược đồ' tab page.

    Args:
        cdp: ChromeCDP instance.
        url: The document page URL.
        relation_map: The optional synonyms mapping dictionary.

    Returns:
        dict[str, Any]: Parsed metadata dictionary.
    """
    base_url = url.split("?")[0].split("#")[0]
    luoc_do_url = f"{base_url}?Tab=LuocDo"

    print(f"[Crawler] Navigating to 'Luoc do' page: {luoc_do_url}")
    cdp.navigate(luoc_do_url)
    cdp.wait_ready()
    cdp.handle_cloudflare()
    time.sleep(2.0)

    mapping = relation_map if relation_map is not None else load_relation_synonyms()
    mapping_json = json.dumps(mapping, ensure_ascii=False)
    metadata_js = METADATA_EXTRACTION_JS_TEMPLATE.replace("__REL_MAP_JSON__", mapping_json)

    raw_meta = cdp.evaluate_js(metadata_js) or {}

    metadata = {
        "document_number": raw_meta.get("Số hiệu", ""),
        "type": raw_meta.get("Loại văn bản", ""),
        "issued_by": raw_meta.get("Nơi ban hành", ""),
        "signer": raw_meta.get("Người ký", ""),
        "issued_date": _parse_tvpl_date(raw_meta.get("Ngày ban hành", "")),
        "effective_date": _parse_tvpl_date(raw_meta.get("Ngày hiệu lực", "")),
        "published_date": _parse_tvpl_date(raw_meta.get("Ngày đăng", "")),
        "status": raw_meta.get("Tình trạng", ""),
        "relations": raw_meta.get("relations", {}),
    }
    return metadata
