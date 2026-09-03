"""Legal document providers (Mock and VIP Live via CDP)."""

from __future__ import annotations

import json
import urllib.parse
from pathlib import Path
from typing import Any

from ccba_legal.cdp import ChromeCDP
from ccba_legal.crawler.selectors import TVPLSelectors
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


def resolve_tvpl_url(cdp: ChromeCDP, query: str) -> str:
    """Resolve document query (doc_number, title, or partial string) to exact TVPL URL.

    Strategy:
    - Tier 1: Google Site Search ('site:thuvienphapluat.vn "<query>"') -> 99%+ canonical accuracy.
    - Tier 2: TVPL Internal Search ('/page/tim-van-ban.aspx?keyword=...') -> Direct fallback.
    - Tier 3: Direct slug URL fallback.
    """
    if query.startswith("http://") or query.startswith("https://"):
        return query

    query_clean = query.strip()
    print(f"[TVPLVIPDocProvider] Resolving TVPL URL for '{query_clean}'...")

    # =========================================================================
    # Tier 1: Universal Google Site Search (Fast, Canonical & Immune to TVPL category noise)
    # =========================================================================
    try:
        g_query = urllib.parse.quote(f'site:thuvienphapluat.vn "{query_clean}"')
        cdp.navigate(f"https://www.google.com/search?q={g_query}&hl=vi")
        cdp.wait_ready()

        g_js = """
        (() => {
            let links = [];
            document.querySelectorAll('a').forEach(a => {
                let h = a.href;
                let txt = (a.innerText || a.textContent || '').trim();
                if (h.includes('thuvienphapluat.vn/') && (h.includes('/van-ban/') || h.includes('/TCVN/')) && h.endsWith('.aspx')) {
                    if (!h.includes('tim-van-ban') && !h.includes('/page/')) {
                        links.push({
                            title: txt,
                            url: h.split('?')[0].split('#')[0]
                        });
                    }
                }
            });
            return links.length > 0 ? links[0] : null;
        })()
        """
        g_match = cdp.evaluate_js(g_js)
        if g_match and isinstance(g_match, dict) and g_match.get("url"):
            resolved = str(g_match["url"])
            print(
                f"[TVPLVIPDocProvider] Tier 1 Google match found: [{g_match.get('title', '')}] -> {resolved}"
            )
            return resolved
    except Exception as e:
        print(
            f"[TVPLVIPDocProvider] Tier 1 Google search encountered error: {e}. Falling back to Tier 2..."
        )

    # =========================================================================
    # Tier 2: TVPL Unified Search Fallback (covers /van-ban/ and /TCVN/)
    # =========================================================================
    search_keywords = [query_clean]
    clean_no_punct = query_clean.replace("/", " ").replace(":", " ").replace("-", " ")
    if clean_no_punct != query_clean:
        search_keywords.append(clean_no_punct)

    for kw in search_keywords:
        safe_kw = kw.replace("/", " ").replace(":", " ")
        enc = urllib.parse.quote_plus(safe_kw)
        s_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={enc}"
        cdp.navigate(s_url)
        cdp.wait_ready()
        cdp.handle_cloudflare()
        sleep_with_jitter(2.5, 0.5, 1.0)

        find_js = f"""
        (() => {{
            let matches = [];
            let q_clean = "{safe_kw.lower()}".replace(/[^a-z0-9]/g, '');
            document.querySelectorAll('p.nqTitle a, div.content-0 a, a[href*="/van-ban/"], a[href*="/TCVN/"]').forEach(a => {{
                let href = a.href;
                let txt = (a.innerText || a.textContent || '').trim();
                let txt_clean = txt.toLowerCase().replace(/[^a-z0-9]/g, '');
                let href_clean = href.toLowerCase().replace(/[^a-z0-9]/g, '');
                if ((href.includes('/van-ban/') || href.includes('/TCVN/')) && href.endsWith('.aspx') && !href.includes('tim-van-ban')) {{
                    if (txt_clean.includes(q_clean) || href_clean.includes(q_clean)) {{
                        matches.push({{title: txt, url: href.split('?')[0].split('#')[0]}});
                    }}
                }}
            }});
            return matches.length > 0 ? matches[0] : null;
        }})()
        """
        match = cdp.evaluate_js(find_js)
        if match and isinstance(match, dict) and match.get("url"):
            resolved = str(match["url"])
            print(
                f"[TVPLVIPDocProvider] Tier 2 TVPL match found: [{match.get('title', '')}] -> {resolved}"
            )
            return resolved

    print(
        f"[TVPLVIPDocProvider] [WARNING] Multi-tier resolution could not find exact match for '{query_clean}'."
    )
    return f"https://thuvienphapluat.vn/van-ban/{query_clean}.aspx"


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

        user_query_js = TVPLSelectors.get_user_js_query()
        check_login_js = f"""
        (() => {{
            let user_lbl = {user_query_js};
            if (user_lbl && user_lbl.innerText.trim().length > 0) {{
                return user_lbl.innerText.trim();
            }}
            return null;
        }})()
        """
        user = cdp.evaluate_js(check_login_js)
        if user:
            print(f"[TVPLVIPDocProvider] Already logged in as: {user}")
            return

        print(f"[TVPLVIPDocProvider] Logging in as: {username[:3]}***...")
        inputs_js = TVPLSelectors.get_login_inputs_js()
        login_js = f"""
        (() => {{
            {inputs_js}
            if (user && pass && login_btn) {{
                user.value = "{username}";
                pass.value = "{password}";
                user.dispatchEvent(new Event('input', {{ bubbles: true }}));
                user.dispatchEvent(new Event('change', {{ bubbles: true }}));
                pass.dispatchEvent(new Event('input', {{ bubbles: true }}));
                pass.dispatchEvent(new Event('change', {{ bubbles: true }}));
                login_btn.click();
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

        confirm_kw_js = json.dumps(TVPLSelectors.CONFIRM_KEYWORDS)
        confirm_js = f"""
        (() => {{
            let keywords = {confirm_kw_js};
            let btns = Array.from(document.querySelectorAll('.ui-dialog-buttonpane button, .ui-dialog-buttonset button, input[type="button"], button'));
            let dong_y = btns.find(b => {{
                let txt = (b.innerText || b.value || '').trim().toLowerCase();
                return keywords.some(kw => txt.includes(kw));
            }});
            if (dong_y) {{
                dong_y.click();
                return 'Clicked: ' + (dong_y.innerText || dong_y.value);
            }}
            if (typeof ContinueLogin === 'function') {{
                ContinueLogin();
                return 'Called ContinueLogin()';
            }}
            return 'No multi-session warning';
        }})()
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

            # Resolve URL dynamically (Multi-tier resolution)
            url = resolve_tvpl_url(cdp, doc_id_or_url)

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
        """Search legal documents on TVPL via Chrome CDP (both VBPL and TCVN)."""
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
            search_url = f"https://thuvienphapluat.vn/page/tim-van-ban.aspx?keyword={encoded_query}&match=False&area=0"
            cdp.navigate(search_url)
            cdp.wait_ready()
            cdp.handle_cloudflare()
            search_js = f"""
            (() => {{
                let items = Array.from(document.querySelectorAll('.results-item, .item-doc, .content-item'));
                if (items.length === 0) {{
                    items = Array.from(document.querySelectorAll('a[href*="/van-ban/"], a[href*="/TCVN/"]'));
                }}
                return items.slice(0, {max_results}).map(item => {{
                    let a = (item.tagName === 'A') ? item : (item.querySelector('a[href*="/van-ban/"], a[href*="/TCVN/"]') || item.querySelector('a'));
                    if (!a || !a.href || (!a.href.includes('/van-ban/') && !a.href.includes('/TCVN/'))) return null;
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
