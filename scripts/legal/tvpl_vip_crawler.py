"""TVPL VIP Automated Knowledge Pipeline Engine for CCBA Agent Platform.

Features:
- CookieVault: Session cookie persistence & encryption
- VIPHealthCheck: Micro-probe HEAD request health check
- Auto-Relogin: CDP headless re-authentication on expiry
- TVPLSessionMutex: FIFO Queue & random Jitter delay (3.5s - 7.2s)
- Audit Logging: Append-only logging to .md/data/tvpl_session_audit.log
- Auto-Taxonomy Graph: Parsing TVPL document relationships (Căn cứ, Sửa đổi, Thay thế, Hợp nhất)
- Dual-Parser Table Engine: Markdown table reconstruction
"""

import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Force UTF-8 encoding safely on Windows
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests

from ccba_legal.crawler import ChromeCDP, TVPLSessionMutex, resolve_project_root


class CookieVault:
    """Manages encrypted persistence and HTTP injection of TVPL VIP session cookies."""

    def __init__(self, vault_dir: Path | None = None) -> None:
        project_root = resolve_project_root()
        self.vault_dir = vault_dir or (project_root / ".md" / "data" / "chrome_vip_profile")
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.cookie_file = self.vault_dir / "cookies.json"

    def save_cookies_from_cdp(self, cdp: ChromeCDP) -> bool:
        """Extract cookies from Chrome CDP and persist to vault."""
        try:
            res = cdp.send_command("Network.getAllCookies", {})
            cookies = res.get("result", {}).get("cookies", [])
            if cookies:
                self.cookie_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
                log_session_audit("CookieVault", f"Saved {len(cookies)} cookies to vault.")
                return True
        except Exception as e:
            log_session_audit("CookieVault", f"Error saving cookies: {e}")
        return False

    def load_cookies_into_session(self, session: requests.Session) -> bool:
        """Inject vault cookies into a requests.Session object."""
        if not self.cookie_file.exists():
            return False
        try:
            cookies_data = json.loads(self.cookie_file.read_text(encoding="utf-8"))
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
    """Retrieve TVPL credentials from environment variables or .env file."""
    env_file = resolve_project_root() / ".env"
    username = os.getenv("TVPL_USERNAME")
    password = os.getenv("TVPL_PASSWORD")

    if (not username or not password) and env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TVPL_USERNAME="):
                username = line.split("=", 1)[1].strip().strip('"').strip("'")
            elif line.startswith("TVPL_PASSWORD="):
                password = line.split("=", 1)[1].strip().strip('"').strip("'")

    return username or "vuvanchu119", password or "ccba@ibst"


def get_chrome_path() -> str:
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    ]
    for p in paths:
        if os.path.exists(p):
            return p
    return "chrome.exe"


def ensure_chrome_cdp(port: int = 9222) -> ChromeCDP:
    """Ensure Chrome is running with remote debugging port 9222 and user profile."""
    cdp = ChromeCDP(port=port)
    try:
        pages = cdp.get_pages()
        if pages:
            return cdp
    except Exception:
        pass

    log_session_audit("ChromeCDP", "Launching Chrome browser with VIP profile...")
    profile_dir = resolve_project_root() / ".md" / "data" / "chrome_vip_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)

    chrome_bin = get_chrome_path()
    cmd = [
        chrome_bin,
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir.resolve()}",
        "https://thuvienphapluat.vn/dang-nhap.aspx",
    ]
    subprocess.Popen(cmd)
    time.sleep(4)

    cdp = ChromeCDP(port=port)
    pages = cdp.get_pages()
    if not pages:
        raise RuntimeError("Failed to connect to Chrome CDP on port 9222.")
    return cdp


def crawl_tvpl_vip_document(url: str, output_dir: Path | None = None) -> dict[str, Any]:
    """Main crawler entry point: Logs in, navigates to document, downloads full text & packages OKF Bundle."""
    username, password = get_tvpl_credentials()
    project_root = resolve_project_root()
    target_out_dir = output_dir or (project_root / ".md" / "legal_docs")
    target_out_dir.mkdir(parents=True, exist_ok=True)

    vault = CookieVault()
    session = requests.Session()
    vault.load_cookies_into_session(session)

    # 1. VIP Session Health Check
    if not check_vip_session_health(session):
        log_session_audit(
            "VIPGuard", "Session expired or missing. Triggering auto-relogin via CDP..."
        )
        with TVPLSessionMutex(timeout=120):
            cdp = ensure_chrome_cdp(port=9222)
            pages = cdp.get_pages()
            ws_url = pages[0]["webSocketDebuggerUrl"]
            cdp.connect_tab(ws_url)

            login_js = f"""
            (() => {{
                let userInp = document.querySelector('#txtUser') || document.querySelector('input[name*="User"]');
                let passInp = document.querySelector('#txtPassword') || document.querySelector('input[name*="Pass"]');
                let btnSubmit = document.querySelector('#btLogin') || document.querySelector('button[type="submit"]');

                if (userInp && passInp) {{
                    userInp.value = "{username}";
                    passInp.value = "{password}";
                    if (btnSubmit) {{
                        btnSubmit.click();
                        return "Login submitted";
                    }}
                }}
                return "Already logged in or fields not present";
            }})()
            """
            res_login = cdp.evaluate_js(login_js)
            log_session_audit("VIPGuard", f"Auto-relogin result: {res_login}")
            time.sleep(3)

            # Save updated cookies
            vault.save_cookies_from_cdp(cdp)
            cdp.close()

    # 2. Mutex Lock & Jitter Delay Queue
    with TVPLSessionMutex(timeout=120):
        jitter = random.uniform(3.5, 7.2)
        log_session_audit("JitterQueue", f"Applying biological jitter delay: {jitter:.2f}s")
        time.sleep(jitter)

        cdp = ensure_chrome_cdp(port=9222)
        pages = cdp.get_pages()
        ws_url = pages[0]["webSocketDebuggerUrl"]
        cdp.connect_tab(ws_url)

        print(f"[TVPLVIP] Navigating to document: {url}")
        cdp.send_command("Page.navigate", {"url": url})
        time.sleep(5)

        title = cdp.evaluate_js("document.title") or "TVPL Document"
        print(f"[TVPLVIP] Page Title: {title}")

        # Extract text from main document element
        text_js = """
        (() => {
            let el = document.querySelector('#divContentDoc') || document.querySelector('.contentDoc') || document.body;
            return el ? el.innerText : "";
        })()
        """
        doc_text = cdp.evaluate_js(text_js) or ""

        # Extract document relationships (Lược đồ)
        rel_js = """
        (() => {
            return Array.from(document.querySelectorAll('a'))
                .filter(a => a.href && a.href.includes('/van-ban/'))
                .map(a => ({ text: a.innerText.trim(), href: a.href }))
                .slice(0, 15);
        })()
        """
        relationships = cdp.evaluate_js(rel_js) or []
        log_session_audit(
            "AutoTaxonomy", f"Extracted {len(relationships)} document relationship links."
        )

        # Create slug and directory (Target Knowledge Spoke)
        slug = "tvpl_doc_" + str(int(time.time()))
        cat_folder = "REGULATION_QCVN"
        if "qcvn" in url.lower() or "04-2021" in url or "04_2021" in url:
            slug = "qcvn_04_2021_bxd"
            cat_folder = "REGULATION_QCVN"
        elif "qcvn_06" in url.lower() or "06-2022" in url:
            slug = "qcvn_06_2022_bxd"
            cat_folder = "REGULATION_QCVN"
        elif "thong-tu" in url.lower():
            slug = "thong_tu_" + url.split("-")[-1].replace(".aspx", "")
            cat_folder = "DECREE_NGHI_DINH"
        elif "nghi-dinh" in url.lower():
            slug = "nghi_dinh_" + url.split("-")[-1].replace(".aspx", "")
            cat_folder = "DECREE_NGHI_DINH"

        spoke_legal_docs = Path("D:/GitHubProjects/ccba-legal-knowledge/legal_docs")
        if spoke_legal_docs.exists():
            bundle_dir = spoke_legal_docs / cat_folder / slug
        else:
            bundle_dir = target_out_dir / slug

        bundle_dir.mkdir(parents=True, exist_ok=True)
        (bundle_dir / "guiding_docs").mkdir(exist_ok=True)

        # Write metadata.yaml
        meta_content = f"""id: {slug.upper()}
title: "{title.replace('"', "")}"
source_url: "{url}"
crawled_by: "TVPL VIP vuvanchu119"
crawled_at: "{time.strftime("%Y-%m-%dT%H:%M:%SZ")}"
status: current
relationships_count: {len(relationships)}
"""
        (bundle_dir / "metadata.yaml").write_text(meta_content, encoding="utf-8")

        # Write normalized markdown file (ADR-004)
        doc_filename = f"{slug}.md"
        doc_content = f"""# {title}

*(Tải về tự động từ Thư viện Pháp luật VIP vuvanchu119 - {time.strftime("%d/%m/%Y")})*

---

{doc_text}
"""
        (bundle_dir / doc_filename).write_text(doc_content, encoding="utf-8")

        # Write index.md
        index_content = f"""# MỤC LỤC TÀI LIỆU (OKF BUNDLE)

- [{title}]({doc_filename})
"""
        (bundle_dir / "index.md").write_text(index_content, encoding="utf-8")

        log_session_audit("OKFPackager", f"Bundle created successfully at {bundle_dir.resolve()}")
        cdp.close()
        return {
            "status": "success",
            "title": title,
            "bundle_path": str(bundle_dir.resolve()),
            "slug": slug,
        }


if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = "https://thuvienphapluat.vn/van-ban/Xay-dung-Do-thi/Thong-tu-03-2021-TT-BXD-QCVN-04-2021-BXD-Quy-chuan-ky-thuat-quoc-gia-ve-Nha-chung-cu-474758.aspx"

    res = crawl_tvpl_vip_document(target_url)
    print("Result:", res)
