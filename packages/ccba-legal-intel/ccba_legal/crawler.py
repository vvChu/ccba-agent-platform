import json
import random
import shutil
import time
from pathlib import Path
from typing import Any

import requests
import websocket


class ChromeCDPError(Exception):
    """Base exception for Chrome DevTools Protocol operations."""

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
                user.value = "vuvanchu119";
                pass.value = "ccba@ibst";
                login_btn.click();
                return "Attempted login click";
            }
            return "Inputs not found";
        })()
        """
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

    title = cdp.evaluate_js("document.title")

    body_text_js = """
    (() => {
        let el = document.querySelector('#divContentDoc') ||
                 document.querySelector('.content1') ||
                 document.querySelector('.contentDoc') ||
                 document.body;
        return el.innerText;
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
