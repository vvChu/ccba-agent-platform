"""session.py - Authentication, persistent profile, session mutex, rate limiting, and audit logging."""

from __future__ import annotations

import json
import os
import random
import time
from pathlib import Path
from typing import Any

import requests

from ccba_harness import FileMutexLock
from ccba_legal.registry import resolve_project_root


class TVPLCrawlFailedException(Exception):
    """Raised when TVPLCrawlerEngine fails to fetch or parse a legal document."""

    pass


class TVPLSessionMutex(FileMutexLock):
    """Context manager for TVPL VIP session mutex lock to prevent concurrent sessions."""

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


def sleep_with_jitter(base_sec: float, jitter_min: float = 0.5, jitter_max: float = 2.0) -> float:
    """Sleep for base_sec + uniform random jitter to prevent static bot timing fingerprint."""
    jitter = random.uniform(jitter_min, jitter_max)
    total = max(0.1, base_sec + jitter)
    time.sleep(total)
    return total


class TVPLRateLimiter:
    """Rate limiter with request cap, randomized delays, and session quotas to protect TVPL VIP access."""

    def __init__(
        self,
        max_requests_per_session: int = 10,
        min_request_interval_sec: float = 3.0,
    ) -> None:
        self.max_requests_per_session = max_requests_per_session
        self.min_request_interval_sec = min_request_interval_sec
        self.session_request_count = 0
        self.last_request_time = 0.0

    def check_and_throttle(self) -> None:
        """Enforce rate limits, interval spacing, and session caps before each request."""
        if self.session_request_count >= self.max_requests_per_session:
            raise TVPLCrawlFailedException(
                f"Rate limit exceeded: Session request cap ({self.max_requests_per_session}) reached. "
                "Please wait or restart session to prevent TVPL VIP account throttling."
            )

        elapsed = time.time() - self.last_request_time
        if self.last_request_time > 0 and elapsed < self.min_request_interval_sec:
            wait_time = self.min_request_interval_sec - elapsed + random.uniform(0.5, 2.0)
            time.sleep(wait_time)

        self.session_request_count += 1
        self.last_request_time = time.time()
        log_session_audit(
            "RateLimiter",
            f"Request #{self.session_request_count}/{self.max_requests_per_session} dispatched.",
        )

    def reset_session(self) -> None:
        """Reset session request counter."""
        self.session_request_count = 0
        self.last_request_time = 0.0


class CookieVault:
    """Manages persistent VIP session cookies with unified file and CDP extraction."""

    def __init__(self, vault_path: Path | None = None) -> None:
        project_root = resolve_project_root()
        self.vault_path = vault_path or (
            project_root / ".md" / "data" / "chrome_vip_profile" / "cookies.json"
        )
        self.vault_dir = self.vault_path.parent
        self.cookie_file = self.vault_path

    def save_cookies(self, cookies: list[dict[str, Any]]) -> None:
        """Save cookies to vault JSON file."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        with open(self.vault_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, indent=2, ensure_ascii=False)

    def load_cookies(self) -> list[dict[str, Any]]:
        """Load cookies from vault."""
        if not self.vault_path.exists():
            return []
        try:
            with open(self.vault_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def get_cookie_dict(self) -> dict[str, str]:
        """Return dict mapping cookie name to value for thuvienphapluat.vn."""
        cookies = self.load_cookies()
        return {
            c["name"]: c["value"] for c in cookies if "thuvienphapluat.vn" in c.get("domain", "")
        }

    def save_cookies_from_cdp(self, cdp: Any) -> bool:
        """Extract cookies from Chrome CDP and persist to vault."""
        try:
            res = cdp.send_command("Network.getAllCookies", {})
            cookies = res.get("result", {}).get("cookies", [])
            if cookies:
                self.save_cookies(cookies)
                log_session_audit("CookieVault", f"Saved {len(cookies)} cookies to vault.")
                return True
        except Exception as e:
            log_session_audit("CookieVault", f"Error saving cookies: {e}")
        return False

    def load_cookies_into_session(self, session: requests.Session) -> bool:
        """Inject vault cookies into a requests.Session object."""
        if not self.vault_path.exists():
            return False
        try:
            cookies_data = self.load_cookies()
            for c in cookies_data:
                session.cookies.set(
                    c["name"], c["value"], domain=c.get("domain", "thuvienphapluat.vn")
                )
            return True
        except Exception as e:
            log_session_audit("CookieVault", f"Error loading cookies into session: {e}")
        return False


def log_session_audit(event_type: str, message: str) -> None:
    """Append-only logging for VIP session audit trail."""
    project_root = resolve_project_root()
    log_file = project_root / ".md" / "data" / "tvpl_session_audit.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"[{timestamp}] [{event_type}] {message}\n"
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception:
        pass


def check_vip_session_health(session: requests.Session) -> bool:
    """Send a micro-probe HEAD request to TVPL to verify active VIP session."""
    probe_url = "https://thuvienphapluat.vn/thong-tin-ca-nhan.aspx"
    try:
        resp = session.head(probe_url, allow_redirects=False, timeout=5)
        if resp.status_code == 200:
            log_session_audit("VIPHealthCheck", "Session status: ACTIVE (200 OK)")
            return True
        elif resp.status_code in (301, 302):
            loc = resp.headers.get("Location", "")
            if "dang-nhap" in loc:
                log_session_audit("VIPHealthCheck", "Session status: EXPIRED (Redirected to login)")
                return False
    except Exception as e:
        log_session_audit("VIPHealthCheck", f"Probe failed: {e}")
    return False


def get_tvpl_credentials() -> tuple[str, str]:
    """Retrieve TVPL credentials from environment variables, local .env, or Hub root .env."""
    username = os.getenv("TVPL_USERNAME")
    password = os.getenv("TVPL_PASSWORD")

    if username and password:
        return username, password

    candidate_dirs = [
        Path.cwd(),
        resolve_project_root(),
    ]
    for parent in resolve_project_root().parents:
        candidate_dirs.append(parent)

    ws_ctx = Path.cwd() / ".md" / "workspace_context.yaml"
    if ws_ctx.exists():
        try:
            import yaml

            with open(ws_ctx, encoding="utf-8") as f:
                ctx_data = yaml.safe_load(f) or {}
            hub_path_str = ctx_data.get("hub_path")
            if hub_path_str:
                candidate_dirs.append(Path(hub_path_str))
        except Exception:
            pass

    for directory in candidate_dirs:
        env_file = directory / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("TVPL_USERNAME=") and not username:
                        username = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("TVPL_PASSWORD=") and not password:
                        password = line.split("=", 1)[1].strip().strip('"').strip("'")
                if username and password:
                    os.environ["TVPL_USERNAME"] = username
                    os.environ["TVPL_PASSWORD"] = password
                    return username, password
            except Exception:
                continue

    if not username or not password:
        raise OSError(
            "TVPL VIP credentials not configured. Please set TVPL_USERNAME and "
            "TVPL_PASSWORD in environment variables or .env file."
        )

    return username, password


def verify_tvpl_vip_status(cdp: Any) -> bool:
    """Verify if the connected Chrome CDP session has an active TVPL VIP Pro login."""
    from ccba_legal.crawler.selectors import TVPLSelectors

    labels_check = " || ".join(f"document.querySelector('{s}') !== null" for s in TVPLSelectors.USER_LABELS)
    js = f"""
    (() => {{
        let txt = document.body ? document.body.innerText : '';
        let has_user = txt.includes('Tài khoản :') ||
                       txt.includes('vuvanchu119') ||
                       {labels_check};
        return has_user ? 'VIP_PRO_ACTIVE' : 'GUEST';
    }})()
    """
    try:
        status = cdp.evaluate_js(js)
        is_vip = status == "VIP_PRO_ACTIVE"
        log_session_audit("VIPStatusCheck", f"Status: {status} (VIP: {is_vip})")
        return is_vip
    except Exception as e:
        log_session_audit("VIPStatusCheck", f"Error evaluating status: {e}")
        return False


def get_browser_executable_path() -> str | None:
    """Discover browser executable path across common Windows, macOS, and Linux locations."""
    import shutil

    # 1. Check environment variables
    env_browser = os.environ.get("CHROME_PATH") or os.environ.get("BROWSER_PATH")
    if env_browser and os.path.exists(env_browser):
        return env_browser

    # 2. Check PATH
    for cmd in ["google-chrome", "chrome", "chromium", "brave", "msedge"]:
        path = shutil.which(cmd)
        if path:
            return path

    # 3. Standard Windows locations
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"),
    ]

    for p in candidates:
        if os.path.exists(p):
            return p

    # 4. Standard macOS locations
    mac_candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for p in mac_candidates:
        if os.path.exists(p):
            return p

    return None
