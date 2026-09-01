"""cdp.py - Chrome DevTools Protocol client, WebSocket communication, mock engine, and bot challenge handlers."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import requests
import websocket

from ccba_legal.session import get_tvpl_credentials, sleep_with_jitter


class ChromeCDPError(Exception):
    """Base exception for Chrome DevTools Protocol operations."""

    pass


class HeadlessEnvironmentError(RuntimeError):
    """Raised when running in a headless/CI environment where download is blocked."""

    pass


def _check_is_headless() -> bool:
    """Check if running in a headless or CI/CD environment."""
    for env_var in ["CI", "GITHUB_ACTIONS", "TVPL_HEADLESS", "HEADLESS"]:
        val = os.environ.get(env_var)
        if val is not None and val.strip().lower() not in ["false", "0", ""]:
            return True
    return False


class ChromeCDP:
    """Helper class to interact with Chrome via DevTools Protocol (CDP)."""

    def __init__(self, port: int = 9222) -> None:
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.ws: websocket.WebSocket | None = None

    def get_pages(self) -> list[dict[str, Any]]:
        """List all open page targets in Chrome, auto-launching instance if needed."""
        try:
            resp = requests.get(f"{self.base_url}/json", timeout=3)
            resp.raise_for_status()
            return [t for t in resp.json() if t.get("type") == "page"]
        except Exception:
            from ccba_legal.session import get_browser_executable_path

            browser_path = get_browser_executable_path()
            if browser_path and os.path.exists(browser_path):
                user_data = os.path.expanduser("~/.gemini/antigravity/chrome_vip")
                os.makedirs(user_data, exist_ok=True)
                import subprocess
                subprocess.Popen([
                    browser_path,
                    f"--remote-debugging-port={self.port}",
                    f"--user-data-dir={user_data}",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "https://thuvienphapluat.vn"
                ])
                time.sleep(3.0)
                try:
                    resp = requests.get(f"{self.base_url}/json", timeout=5)
                    resp.raise_for_status()
                    return [t for t in resp.json() if t.get("type") == "page"]
                except Exception as e:
                    raise ChromeCDPError(f"Failed to connect to Chrome on port {self.port} after launch: {e}") from e
            raise ChromeCDPError(f"Chrome not found at {chrome_path} to auto-launch on port {self.port}")

    def connect_tab(self, ws_url: str) -> None:
        """Connect to a specific tab via WebSockets with safe timeout."""
        try:
            self.ws = websocket.create_connection(ws_url, suppress_origin=True, timeout=8.0)
        except Exception as e:
            raise ChromeCDPError(f"Failed to connect to tab WebSocket: {e}") from e

    def send_command(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Send a generic CDP command and return the response payload with timeout handling."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        payload = {"id": random.randint(1, 100000), "method": method, "params": params}
        try:
            self.ws.send(json.dumps(payload))
            resp = self.ws.recv()
            return json.loads(resp)  # type: ignore[no-any-return]
        except websocket.WebSocketTimeoutException:
            return {"result": {"value": None}}
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
        except (websocket.WebSocketTimeoutException, websocket.WebSocketConnectionClosedException):
            return None
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
            sleep_with_jitter(1.5, 0.3, 1.2)
        except (websocket.WebSocketTimeoutException, websocket.WebSocketConnectionClosedException):
            sleep_with_jitter(1.5, 0.3, 1.2)
        except Exception as e:
            raise ChromeCDPError(f"Failed to trigger navigation: {e}") from e

    def wait_ready(self, timeout_sec: int = 15) -> None:
        """Wait for document readyState to be 'complete' or 'interactive'."""
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            try:
                state = self.evaluate_js("document.readyState")
                if state in ("complete", "interactive"):
                    return
            except ChromeCDPError:
                pass
            time.sleep(0.5)

    def handle_cloudflare(self, auto_wait_sec: int = 7) -> None:
        """Check for Cloudflare bot challenge, wait for silent auto-resolution, and bring window to front only if manual action is needed."""
        check_expr = """
        !!(document.title.includes("Cloudflare") ||
           document.title.includes("Just a moment") ||
           document.querySelector("div.cf-turnstile") ||
           document.querySelector("#challenge-running") ||
           document.querySelector("#challenge-stage"))
        """
        is_blocked = self.evaluate_js(check_expr)
        if is_blocked:
            print("[LegalIntel] Cloudflare verification in progress (auto-verifying in background)...")
            start_time = time.time()
            # Phase 1: Grace period for Chrome to auto-pass Cloudflare verification silently
            while time.time() - start_time < auto_wait_sec:
                sleep_with_jitter(1.0, 0.2, 0.4)
                try:
                    is_blocked = self.evaluate_js(check_expr)
                    if not is_blocked:
                        print("[LegalIntel] Cloudflare auto-verified successfully! Resuming...")
                        self.wait_ready()
                        return
                except ChromeCDPError:
                    pass

            # Phase 2: If still blocked after grace period, bring window to front for manual click
            try:
                self.send_command("Page.bringToFront", {})
            except Exception:
                pass
            print("[LegalIntel] Cloudflare requires manual confirmation. Chrome window brought to foreground.")
            while is_blocked:
                sleep_with_jitter(2.0, 0.5, 1.0)
                try:
                    is_blocked = self.evaluate_js(check_expr)
                except ChromeCDPError:
                    is_blocked = True
            print("[LegalIntel] Challenge solved! Resuming execution...")
            self.wait_ready()


    def set_download_behavior(self, download_path: Path | str) -> bool:
        """Configure Chrome CDP to allow downloading directly into a specific folder."""
        p = str(Path(download_path).resolve())
        try:
            self.send_command(
                "Browser.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": p, "eventsEnabled": True},
            )
            return True
        except Exception:
            try:
                self.send_command(
                    "Page.setDownloadBehavior",
                    {"behavior": "allow", "downloadPath": p},
                )
                return True
            except Exception:
                return False

    def handle_login(self) -> bool:
        """Detect login popup, fill in credentials, submit, handle multi-session warning, and return True if login was attempted."""
        try:
            username, password = get_tvpl_credentials()
        except OSError as e:
            print(f"  [Login] {e}")
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
            sleep_with_jitter(3.0, 0.5, 1.5)

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
                sleep_with_jitter(4.0, 0.5, 1.5)
            else:
                sleep_with_jitter(2.0, 0.5, 1.0)

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


class MockChromeCDP(ChromeCDP):
    """Mock implementation of ChromeCDP for offline testing without a live Chrome browser."""

    def __init__(self, port: int = 9222) -> None:
        super().__init__(port=port)
        self.connected = False
        self.current_url = ""
        self.mock_js_responses: dict[str, Any] = {
            "document.readyState": "complete",
            "document.title": "Mock Legal Document Title",
        }
        self.mock_html_content = (
            "<html><body><h1>Mock Document</h1><p>Test content</p></body></html>"
        )
        self.mock_body_text = "Nội dung chi tiết Luật PCCC số 55/2024/QH15"
        self.mock_links: list[dict[str, str]] = []
        self.mock_metadata: dict[str, Any] = {
            "Số hiệu": "55/2024/QH15",
            "Loại văn bản": "Luật",
            "Nơi ban hành": "Quốc hội",
            "Người ký": "Trần Thanh Mẫn",
            "Ngày ban hành": "27/11/2024",
            "Ngày hiệu lực": "01/07/2025",
            "Tình trạng": "Còn hiệu lực",
            "relations": {},
        }
        self.mock_login_attempted = False
        self.mock_popup_closed = False

    def get_pages(self) -> list[dict[str, Any]]:
        return [
            {
                "type": "page",
                "webSocketDebuggerUrl": f"ws://127.0.0.1:{self.port}/devtools/page/mock123",
            }
        ]

    def connect_tab(self, ws_url: str) -> None:
        self.connected = True

    def send_command(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.connected:
            raise ChromeCDPError("No active WebSocket connection.")
        return {"result": {"value": True}}

    def set_mock_js_response(self, expression: str, value: Any) -> None:
        self.mock_js_responses[expression] = value

    def set_mock_metadata(self, meta_dict: dict[str, Any]) -> None:
        raw = dict(meta_dict)
        if "document_number" in meta_dict and "Số hiệu" not in raw:
            raw["Số hiệu"] = meta_dict["document_number"]
        if "type" in meta_dict and "Loại văn bản" not in raw:
            raw["Loại văn bản"] = meta_dict["type"]
        if "issued_by" in meta_dict and "Nơi ban hành" not in raw:
            raw["Nơi ban hành"] = meta_dict["issued_by"]
        if "signer" in meta_dict and "Người ký" not in raw:
            raw["Người ký"] = meta_dict["signer"]
        if "issued_date" in meta_dict and "Ngày ban hành" not in raw:
            raw["Ngày ban hành"] = meta_dict["issued_date"]
        if "effective_date" in meta_dict and "Ngày hiệu lực" not in raw:
            raw["Ngày hiệu lực"] = meta_dict["effective_date"]
        if "published_date" in meta_dict and "Ngày đăng" not in raw:
            raw["Ngày đăng"] = meta_dict["published_date"]
        if "status" in meta_dict and "Tình trạng" not in raw:
            raw["Tình trạng"] = meta_dict["status"]
        self.mock_metadata = raw

    def set_mock_body_text(self, text: str) -> None:
        self.mock_body_text = text

    def set_mock_links(self, links: list[dict[str, str]]) -> None:
        self.mock_links = links

    def evaluate_js(self, expression: str) -> Any:
        if not self.connected:
            raise ChromeCDPError("No active WebSocket connection.")
        if expression in self.mock_js_responses:
            return self.mock_js_responses[expression]
        if "document.title" in expression:
            return self.mock_js_responses.get("document.title", "Mock Title")
        if "readyState" in expression:
            return "complete"
        if "relMap" in expression or "result['relations']" in expression:
            return self.mock_metadata
        if "divContentDoc" in expression or "cloneNode" in expression:
            return self.mock_body_text
        if "querySelectorAll('a')" in expression or "relationship" in expression:
            return self.mock_links
        if "innerHTML" in expression or "outerHTML" in expression:
            return self.mock_html_content
        return True

    def navigate(self, url: str) -> None:
        if not self.connected:
            raise ChromeCDPError("No active WebSocket connection.")
        self.current_url = url

    def wait_ready(self, timeout_sec: int = 30) -> None:
        pass

    def handle_cloudflare(self) -> None:
        pass

    def handle_login(self) -> bool:
        return self.mock_login_attempted

    def close_popup(self) -> bool:
        return self.mock_popup_closed

    def close(self) -> None:
        self.connected = False
