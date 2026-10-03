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

from ccba_legal.crawler.selectors import TVPLSelectors
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


def cleanup_zombie_locks(user_data_path: Path) -> None:
    """Safely remove orphaned Chrome lock files without killing foreign Chrome processes."""
    if not user_data_path.exists():
        return

    lock_file = user_data_path / "SingletonLock"
    if lock_file.exists() or lock_file.is_symlink():
        try:
            if lock_file.is_symlink():
                target = os.readlink(lock_file)
                # Formats: host-PID
                parts = target.split("-")
                is_dead = True
                if len(parts) >= 2 and parts[-1].isdigit():
                    pid = int(parts[-1])
                    try:
                        os.kill(pid, 0)
                        is_dead = False
                    except (ProcessLookupError, OSError):
                        is_dead = True
                if is_dead:
                    lock_file.unlink(missing_ok=True)
            else:
                try:
                    lock_file.unlink(missing_ok=True)
                except OSError:
                    pass
        except Exception:
            pass

    for extra_lock in ["SingletonCookie", "SingletonSocket"]:
        p = user_data_path / extra_lock
        if p.is_symlink() or p.exists():
            try:
                p.unlink(missing_ok=True)
            except OSError:
                pass


class ChromeCDP:
    """Helper class to interact with Chrome via DevTools Protocol (CDP)."""

    def __init__(self, port: int | None = None) -> None:
        if port is None:
            port = int(os.environ.get("TVPL_CDP_PORT", "9222"))
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self.ws: websocket.WebSocket | None = None

    def get_pages(self) -> list[dict[str, Any]]:
        """List all open page targets in Chrome, auto-launching instance or creating new tab if needed."""
        user_data = os.path.expanduser("~/.gemini/antigravity/chrome_vip")
        user_data_path = Path(user_data)
        cleanup_zombie_locks(user_data_path)

        try:
            resp = requests.get(f"{self.base_url}/json", timeout=3)
            resp.raise_for_status()
            pages = [t for t in resp.json() if t.get("type") == "page"]
            if not pages:
                try:
                    new_tab = requests.put(
                        f"{self.base_url}/json/new?https://thuvienphapluat.vn", timeout=3
                    )
                    if new_tab.ok:
                        pages = [new_tab.json()]
                except Exception:
                    pass
            return pages
        except Exception:
            # Check if default port 9222 is occupied by an unresponsive/non-CDP process
            if self.port == 9222 and not os.environ.get("TVPL_CDP_PORT"):
                import socket

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                port_busy = False
                try:
                    sock.bind(("127.0.0.1", 9222))
                    sock.close()
                except OSError:
                    port_busy = True

                if port_busy:
                    # Check if port 9222 actually has responsive Chrome instance
                    try:
                        resp = requests.get(f"{self.base_url}/json", timeout=2)
                        if resp.ok:
                            pages = [t for t in resp.json() if t.get("type") == "page"]
                            if pages:
                                return pages
                    except Exception:
                        pass

                    self.port = 9223
                    self.base_url = f"http://127.0.0.1:{self.port}"
                    try:
                        resp = requests.get(f"{self.base_url}/json", timeout=2)
                        resp.raise_for_status()
                        pages = [t for t in resp.json() if t.get("type") == "page"]
                        if pages:
                            return pages
                    except Exception:
                        pass

            from ccba_legal.session import get_browser_executable_path

            browser_path = get_browser_executable_path()
            if browser_path and os.path.exists(browser_path):
                os.makedirs(user_data, exist_ok=True)
                cleanup_zombie_locks(user_data_path)
                import subprocess

                subprocess.Popen(
                    [
                        browser_path,
                        f"--remote-debugging-port={self.port}",
                        "--remote-allow-origins=*",
                        f"--user-data-dir={user_data}",
                        "--no-first-run",
                        "--no-default-browser-check",
                        "https://thuvienphapluat.vn",
                    ],
                    start_new_session=True,
                )
                time.sleep(3.0)
                try:
                    resp = requests.get(f"{self.base_url}/json", timeout=5)
                    resp.raise_for_status()
                    return [t for t in resp.json() if t.get("type") == "page"]
                except Exception as e:
                    raise ChromeCDPError(
                        f"Failed to connect to Chrome on port {self.port} after launch: {e}"
                    ) from e
            raise ChromeCDPError(
                f"Chrome or compatible browser not found to auto-launch on port {self.port}"
            ) from None

    def connect_tab(self, ws_url: str) -> None:
        """Connect to a specific tab via WebSockets with safe timeout."""
        try:
            self.ws = websocket.create_connection(ws_url, suppress_origin=True, timeout=8.0)
        except Exception as e:
            raise ChromeCDPError(f"Failed to connect to tab WebSocket: {e}") from e

    def send_command(
        self, method: str, params: dict[str, Any], timeout: float = 15.0
    ) -> dict[str, Any]:
        """Send a generic CDP command and return the response payload with timeout handling."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        req_id = random.randint(1, 1000000)
        payload = {"id": req_id, "method": method, "params": params}
        start_time = time.time()
        try:
            self.ws.send(json.dumps(payload))
            while time.time() - start_time < timeout:
                remaining = max(0.1, timeout - (time.time() - start_time))
                self.ws.settimeout(remaining)
                try:
                    resp = self.ws.recv()
                except (websocket.WebSocketTimeoutException, TimeoutError):
                    break
                if not resp:
                    continue
                try:
                    data = json.loads(resp)
                except Exception:
                    continue
                if isinstance(data, dict) and data.get("id") == req_id:
                    return data
            return {"result": {"value": None}}
        except (websocket.WebSocketTimeoutException, TimeoutError):
            return {"result": {"value": None}}
        except websocket.WebSocketConnectionClosedException as e:
            raise ChromeCDPError(
                f"WebSocket connection closed while sending CDP command {method}: {e}"
            ) from e
        except Exception as e:
            raise ChromeCDPError(f"Failed to send CDP command {method}: {e}") from e

    def evaluate_js(self, expression: str) -> Any:
        """Evaluate a JavaScript expression in the connected tab."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        data = self.send_command(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True},
        )
        result_data = data.get("result", {})
        if "exceptionDetails" in result_data:
            exc = result_data["exceptionDetails"]
            raise ChromeCDPError(f"JS Exception: {exc.get('text')} - {exc.get('exception', {})}")

        return result_data.get("result", {}).get("value")

    def navigate(self, url: str) -> None:
        """Navigate to a URL and wait for the page to be ready."""
        if not self.ws:
            raise ChromeCDPError("No active WebSocket connection.")
        try:
            self.send_command("Page.navigate", {"url": url})
            sleep_with_jitter(1.5, 0.3, 1.2)
        except ChromeCDPError as e:
            if "WebSocket connection closed" in str(e):
                sleep_with_jitter(1.5, 0.3, 1.2)
            else:
                raise
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
        """Check for Cloudflare bot challenge, auto-click Turnstile if present, and resolve."""
        check_expr = """
        !!(document.title.includes("Cloudflare") ||
           document.title.includes("Just a moment") ||
           document.querySelector("div.cf-turnstile") ||
           document.querySelector("#challenge-running") ||
           document.querySelector("#challenge-stage") ||
           document.querySelector("input[name=cf-turnstile-response]"))
        """
        is_blocked = self.evaluate_js(check_expr)
        if is_blocked:
            print(
                "[LegalIntel] Cloudflare verification in progress (attempting auto-resolution)..."
            )
            start_time = time.time()
            # Phase 1: Grace period with synthetic Turnstile click attempt
            while time.time() - start_time < auto_wait_sec:
                turnstile_rect_js = """
                (() => {
                    let el = document.querySelector("#challenge-stage") ||
                             document.querySelector("div.cf-turnstile") ||
                             document.querySelector("input[name=cf-turnstile-response]")?.parentElement;
                    if (el) {
                        let r = el.getBoundingClientRect();
                        if (r.width > 0 && r.height > 0) {
                            return {x: r.x, y: r.y, width: r.width, height: r.height};
                        }
                    }
                    return null;
                })()
                """
                try:
                    rect = self.evaluate_js(turnstile_rect_js)
                    if rect and isinstance(rect, dict):
                        click_x = rect.get("x", 0) + 30
                        click_y = rect.get("y", 0) + min(35, rect.get("height", 70) / 2)
                        self.send_command(
                            "Input.dispatchMouseEvent",
                            {"type": "mouseMoved", "x": click_x, "y": click_y},
                        )
                        time.sleep(0.1)
                        self.send_command(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mousePressed",
                                "x": click_x,
                                "y": click_y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                        time.sleep(0.05)
                        self.send_command(
                            "Input.dispatchMouseEvent",
                            {
                                "type": "mouseReleased",
                                "x": click_x,
                                "y": click_y,
                                "button": "left",
                                "clickCount": 1,
                            },
                        )
                except Exception:
                    pass

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
            print(
                "[LegalIntel] Cloudflare requires manual confirmation. Chrome window brought to foreground."
            )
            manual_start = time.time()
            default_wait = 90.0 if not _check_is_headless() else 5.0
            max_manual_wait = float(os.environ.get("TVPL_CLOUDFLARE_WAIT", default_wait))
            print(
                f"[LegalIntel] Waiting for Cloudflare verification (hard timeout: {max_manual_wait:.0f}s)..."
            )
            while is_blocked:
                if time.time() - manual_start > max_manual_wait:
                    raise ChromeCDPError(
                        f"Cloudflare challenge timed out after {max_manual_wait:.0f}s without user interaction."
                    )
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
        # Try Browser Target first for modern Chrome versions
        try:
            resp = requests.get(f"{self.base_url}/json/version", timeout=3)
            if resp.ok:
                browser_ws = resp.json().get("webSocketDebuggerUrl")
                if browser_ws:
                    ws_b = websocket.create_connection(
                        browser_ws, suppress_origin=True, timeout=5.0
                    )
                    cmd = {
                        "id": random.randint(1, 100000),
                        "method": "Browser.setDownloadBehavior",
                        "params": {"behavior": "allow", "downloadPath": p, "eventsEnabled": True},
                    }
                    ws_b.send(json.dumps(cmd))
                    raw_b = ws_b.recv()
                    ws_b.close()
                    if raw_b:
                        data_b = json.loads(raw_b)
                        if "error" not in data_b:
                            return True
        except Exception:
            pass

        try:
            res = self.send_command(
                "Browser.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": p, "eventsEnabled": True},
            )
            if "error" not in res:
                return True
        except Exception:
            pass

        try:
            res = self.send_command(
                "Page.setDownloadBehavior",
                {"behavior": "allow", "downloadPath": p},
            )
            if "error" not in res:
                return True
        except Exception:
            pass

        return False

    def _check_file_stability(
        self,
        watch_dirs: list[Path],
        expected_exts: list[str],
        start_time: float,
        existing_files: set[str],
    ) -> Path | None:
        """Check whether a downloaded file in watch_dirs has finished writing and stabilized."""
        for d in watch_dirs:
            if not d.exists():
                continue
            try:
                candidates = [
                    f
                    for f in d.glob("*")
                    if f.is_file() and any(f.name.lower().endswith(ext) for ext in expected_exts)
                ]
            except OSError:
                continue

            for f in candidates:
                try:
                    resolved_str = str(f.resolve())
                    if f.name.endswith(".crdownload") or f.name.endswith(".tmp"):
                        continue
                    st = f.stat()
                    if resolved_str in existing_files and st.st_mtime < (start_time - 1.0):
                        continue
                    if st.st_size > 0 and st.st_mtime >= (start_time - 2.0):
                        sz1 = st.st_size
                        time.sleep(0.5)
                        sz2 = f.stat().st_size
                        if sz1 == sz2 and sz1 > 0:
                            return f
                except OSError:
                    continue
        return None

    def wait_for_download_completion(
        self,
        watch_dirs: list[Path],
        expected_exts: list[str],
        existing_files: set[str],
        timeout: float = 30.0,
        start_time: float | None = None,
    ) -> Path | None:
        """Deterministic two-tier download watcher: Layer-1 WebSocket events with Layer-2 File Stability Guard."""
        if start_time is None:
            start_time = time.time()

        ws = self.ws
        while time.time() - start_time < timeout:
            # Layer 1: WebSocket event inspection if active
            if ws:
                remaining = max(0.5, timeout - (time.time() - start_time))
                try:
                    ws.settimeout(min(2.0, remaining))
                    raw = ws.recv()
                    if raw:
                        msg = json.loads(raw)
                        method = msg.get("method", "")
                        params = msg.get("params", {})
                        if method == "Browser.downloadProgress":
                            state = params.get("state")
                            if state == "completed":
                                # Immediate file stability check upon event
                                found = self._check_file_stability(
                                    watch_dirs, expected_exts, start_time, existing_files
                                )
                                if found:
                                    return found
                            elif state == "canceled":
                                return None
                except (websocket.WebSocketTimeoutException, TimeoutError):
                    pass
                except Exception:
                    pass

            # Layer 2: File Stability Guard fallback
            found = self._check_file_stability(
                watch_dirs, expected_exts, start_time, existing_files
            )
            if found:
                return found

            time.sleep(0.5)

        return None

    def handle_login(self) -> bool:
        """Detect login popup, fill in credentials, submit, handle multi-session warning, and return True if login was attempted."""
        try:
            username, password = get_tvpl_credentials()
        except OSError as e:
            print(f"  [Login] {e}")
            return False

        inputs_js = TVPLSelectors.get_login_inputs_js()
        js = f"""
        (() => {{
            {inputs_js}
            if (user && pass && login_btn) {{
                user.value = "__USERNAME__";
                pass.value = "__PASSWORD__";
                user.dispatchEvent(new Event('input', {{ bubbles: true }}));
                user.dispatchEvent(new Event('change', {{ bubbles: true }}));
                pass.dispatchEvent(new Event('input', {{ bubbles: true }}));
                pass.dispatchEvent(new Event('change', {{ bubbles: true }}));
                login_btn.click();
                return "Attempted login click";
            }}
            return "Inputs not found";
        }})()
        """.replace("__USERNAME__", username).replace("__PASSWORD__", password)
        res = self.evaluate_js(js)
        if "Attempted login" in str(res):
            print("  [Login] Found login popup, autofilling credentials and submitting...")
            sleep_with_jitter(3.0, 0.5, 1.5)

            confirm_kw_js = json.dumps(TVPLSelectors.CONFIRM_KEYWORDS)
            warning_js = f"""
            (() => {{
                let keywords = {confirm_kw_js};
                let agree_btn = Array.from(document.querySelectorAll('input, button, a')).find(el => {{
                    let txt = (el.value || el.innerText || "").trim().toLowerCase();
                    return keywords.some(kw => txt.includes(kw));
                }});
                if (agree_btn) {{
                    agree_btn.click();
                    return "Clicked Dong y";
                }}
                return "No warning popup";
            }})()
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

    def send_command(
        self, method: str, params: dict[str, Any], timeout: float = 15.0
    ) -> dict[str, Any]:
        if not self.connected:
            raise ChromeCDPError("No active WebSocket connection.")
        return {"result": {"value": True}}

    def set_download_behavior(self, download_path: Path | str) -> bool:
        return True

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

    def handle_cloudflare(self, auto_wait_sec: int = 7) -> None:
        pass

    def handle_login(self) -> bool:
        return self.mock_login_attempted

    def close_popup(self) -> bool:
        return self.mock_popup_closed

    def wait_for_download_completion(
        self,
        watch_dirs: list[Path],
        expected_exts: list[str],
        existing_files: set[str],
        timeout: float = 30.0,
        start_time: float | None = None,
    ) -> Path | None:
        for d in watch_dirs:
            if not d.exists():
                continue
            for f in d.glob("*"):
                if f.is_file() and any(f.name.lower().endswith(ext) for ext in expected_exts):
                    try:
                        st = f.stat()
                        if str(f.resolve()) in existing_files and st.st_mtime < (
                            (start_time or 0) - 1.0
                        ):
                            continue
                        return f
                    except OSError:
                        continue
        return None

    def close(self) -> None:
        self.connected = False
