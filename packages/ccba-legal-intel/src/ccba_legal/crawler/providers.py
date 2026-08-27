"""Legal document providers (Mock and VIP Live via CDP)."""

from __future__ import annotations

import urllib.parse
from pathlib import Path
from typing import Any

from ccba_legal.cdp import ChromeCDP
from ccba_legal.crawler.tier_downloader import trigger_download
from ccba_legal.session import (
    TVPLCrawlFailedException,
    get_tvpl_credentials,
    sleep_with_jitter,
    verify_tvpl_vip_status,
)
from ccba_legal.tvpl_parser import (
    _derive_doc_slug,
    get_crawled_doc_data,
    get_tvpl_metadata,
)


class LegalDocProvider:
    """Abstract base provider for fetching legal documents."""

    def fetch_doc(self, doc_id_or_url: str) -> dict[str, Any]:
        """Fetch legal document by ID or URL."""
        raise NotImplementedError("Subclasses must implement fetch_doc()")


class MockLegalDocProvider(LegalDocProvider):
    """Mock provider returning pre-registered or default test fixtures."""

    def __init__(self, fixtures: dict[str, dict[str, Any]] | None = None) -> None:
        self.fixtures: dict[str, dict[str, Any]] = fixtures or {}

    def add_fixture(self, doc_id: str, data: dict[str, Any]) -> None:
        """Register a custom test fixture."""
        self.fixtures[doc_id] = data

    def fetch_doc(self, doc_id_or_url: str) -> dict[str, Any]:
        """Fetch mock document data."""
        if doc_id_or_url in self.fixtures:
            return self.fixtures[doc_id_or_url]
        return {
            "document_number": doc_id_or_url,
            "type": "Nghị định",
            "issued_by": "Chính phủ",
            "status": "Còn hiệu lực",
            "content": f"Mock content for {doc_id_or_url}",
        }

    def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Mock search for legal documents."""
        return [
            {
                "document_number": f"Mock {query} 01",
                "title": f"Mock Title for {query}",
                "status": "Còn hiệu lực",
            }
        ]


class TVPLVIPDocProvider(LegalDocProvider):
    """Live VIP provider connecting via Chrome CDP to fetch metadata, full text, DOCX, and PDF."""

    def __init__(self, port: int = 9222, output_dir: Path | None = None) -> None:
        self.port = port
        self.output_dir = output_dir or Path(".md/extracted_docs")

    def _ensure_logged_in(self, cdp: ChromeCDP) -> None:
        """Check if logged in; if not, navigate to dangnhap.aspx and log in."""
        try:
            username, password = get_tvpl_credentials()
        except OSError:
            return

        check_login_js = """
        (() => {
            let user_lbl = document.querySelector('#ctl00_Header_lblTenDangNhap') ||
                           document.querySelector('.user-name') ||
                           document.querySelector('a[href*="thong-tin-ca-nhan"]');
            if (user_lbl && user_lbl.innerText.trim().length > 0) {
                return user_lbl.innerText.trim();
            }
            return null;
        })()
        """
        user = cdp.evaluate_js(check_login_js)
        if user:
            print(f"[TVPLVIPDocProvider] Already logged in as: {user}")
            return

        print(f"[TVPLVIPDocProvider] Logging in as: {username[:3]}***...")
        login_js = f"""
        (() => {{
            let u = document.querySelector('#usernameTextBox') ||
                    document.querySelector('#txtUserName') ||
                    document.querySelector('input[placeholder*="Tên đăng nhập"]');
            let p = document.querySelector('#passwordTextBox') ||
                    document.querySelector('#txtPassword') ||
                    document.querySelector('input[placeholder*="Mật khẩu"]');
            let btn = document.querySelector('#loginButton') ||
                       document.querySelector('#btLogin') ||
                       document.querySelector('input[value="Đăng nhập"]');
            if (u && p && btn) {{
                u.value = "{username}";
                p.value = "{password}";
                u.dispatchEvent(new Event('input', {{ bubbles: true }}));
                p.dispatchEvent(new Event('input', {{ bubbles: true }}));
                btn.click();
                return "Submitted login";
            }}
            return "Login inputs not found";
        }})()
        """
        res_login = cdp.evaluate_js(login_js)
        if "not found" in str(res_login).lower():
            cdp.navigate("https://thuvienphapluat.vn")
            cdp.wait_ready()
            cdp.handle_cloudflare()
            cdp.evaluate_js(login_js)

        sleep_with_jitter(2.5, 0.5, 1.5)
        cdp.wait_ready()
        cdp.handle_cloudflare()

        confirm_js = """
        (() => {
            let btns = Array.from(document.querySelectorAll('.ui-dialog-buttonpane button, .ui-dialog-buttonset button, input[type="button"], button'));
            let dong_y = btns.find(b => {
                let txt = (b.innerText || b.value || '').trim().toLowerCase();
                return txt.includes('đồng ý') || txt.includes('tiếp tục') || txt.includes('dong y');
            });
            if (dong_y) {
                dong_y.click();
                return 'Clicked: ' + (dong_y.innerText || dong_y.value);
            }
            if (typeof ContinueLogin === 'function') {
                ContinueLogin();
                return 'Called ContinueLogin()';
            }
            return 'No multi-session warning';
        })()
        """
        res_conf = cdp.evaluate_js(confirm_js)
        print(f"[TVPLVIPDocProvider] Multi-session confirmation: {res_conf}")
        sleep_with_jitter(2.0, 0.5, 1.0)

    def fetch_doc(self, doc_id_or_url: str) -> dict[str, Any]:
        """Connect to Chrome via CDP, fetch document text, metadata, download DOCX and PDF."""
        cdp = ChromeCDP(port=self.port)
        pages = cdp.get_pages()
        if not pages:
            raise TVPLCrawlFailedException(
                f"No open Chrome pages found on port {self.port}. Please launch Chrome with remote debugging."
            )
        ws_url = pages[0].get("webSocketDebuggerUrl")
        if not ws_url:
            raise TVPLCrawlFailedException("Failed to obtain WebSocket Debugger URL from Chrome.")

        cdp.connect_tab(ws_url)
        try:
            self._ensure_logged_in(cdp)
            if not verify_tvpl_vip_status(cdp):
                print("[TVPLVIPDocProvider] [WARNING] VIP Pro session is not active.")
            url = doc_id_or_url if doc_id_or_url.startswith("http") else f"https://thuvienphapluat.vn/van-ban/{doc_id_or_url}.aspx"
            metadata = get_tvpl_metadata(cdp, url)
            title, body_text, links = get_crawled_doc_data(cdp, url)
            doc_number = metadata.get("document_number") or ""
            doc_type = metadata.get("type") or ""
            slug = _derive_doc_slug(doc_number, doc_type, url)
            doc_out_dir = self.output_dir / slug
            doc_out_dir.mkdir(parents=True, exist_ok=True)
            download_res = trigger_download(
                cdp,
                download_dir=doc_out_dir,
                slug_name=slug,
                format_type="both",
                download_attachments=True,
                doc_url=url,
            )

            return {
                "title": title,
                "url": url,
                "slug": slug,
                "document_number": doc_number,
                "type": doc_type,
                "issued_by": metadata.get("issued_by", ""),
                "signer": metadata.get("signer", ""),
                "issued_date": metadata.get("issued_date", ""),
                "effective_date": metadata.get("effective_date", ""),
                "published_date": metadata.get("published_date", ""),
                "status": metadata.get("status", "Còn hiệu lực"),
                "relations": metadata.get("relations", {}),
                "content": body_text,
                "links": links,
                "docx_path": download_res.get("docx_path"),
                "pdf_path": download_res.get("pdf_path"),
                "sha256": download_res.get("sha256"),
                "pdf_sha256": download_res.get("pdf_sha256"),
                "cong_bao_number": download_res.get("cong_bao_number"),
                "cong_bao_date": download_res.get("cong_bao_date"),
                "attachments": download_res.get("attachments", []),
            }
        finally:
            cdp.close()

    def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search legal documents on TVPL via Chrome CDP."""
        cdp = ChromeCDP(port=self.port)
        pages = cdp.get_pages()
        if not pages:
            return []
        ws_url = pages[0].get("webSocketDebuggerUrl")
        if not ws_url:
            return []
        cdp.connect_tab(ws_url)
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://thuvienphapluat.vn/tim-van-ban.aspx?keyword={encoded_query}"
            cdp.navigate(search_url)
            cdp.wait_ready()
            cdp.handle_cloudflare()
            search_js = f"""
            (() => {{
                let items = Array.from(document.querySelectorAll('.results-item, .item-doc, .content-item'));
                if (items.length === 0) {{
                    items = Array.from(document.querySelectorAll('a[href*="/van-ban/"]'));
                }}
                return items.slice(0, {max_results}).map(item => {{
                    let a = item.tagName === 'A' ? item : item.querySelector('a[href*="/van-ban/"]');
                    if (!a) return null;
                    return {{
                        title: a.innerText.trim(),
                        url: a.href.split('?')[0].split('#')[0]
                    }};
                }}).filter(Boolean);
            }})()
            """
            results = cdp.evaluate_js(search_js) or []
            return results
        finally:
            cdp.close()
