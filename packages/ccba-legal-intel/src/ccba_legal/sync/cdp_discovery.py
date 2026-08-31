"""Chrome CDP Auto-Discovery and Downloader."""

from __future__ import annotations

import urllib.parse
from pathlib import Path

from ccba_legal.sync.utils import ensure_chrome_debug_port

try:
    from ccba_legal.crawler import ChromeCDP, trigger_download
except ImportError:
    ChromeCDP = None  # type: ignore[assignment, misc]
    trigger_download = None  # type: ignore[assignment]


def search_thuvienphapluat_via_cdp(query: str) -> str | None:
    """Search for a legal document URL on thuvienphapluat.vn via Google Search using Chrome CDP."""
    if ChromeCDP is None:
        return None

    if not ensure_chrome_debug_port():
        print("[Auto-Discovery Warning] Không thể kích hoạt hoặc kết nối tới cổng debug Chrome.")
        return None

    print(f"[Auto-Discovery] Đang tìm kiếm link Thư viện Pháp luật cho: {query}")
    try:
        cdp = ChromeCDP(port=9222)
        pages = cdp.get_pages()
        if not pages:
            print("[Auto-Discovery Warning] Không tìm thấy tab Chrome nào đang mở.")
            return None

        cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])
        search_query = f'site:thuvienphapluat.vn "{query}"'
        search_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(search_query)}"

        cdp.navigate(search_url)
        cdp.wait_ready()
        cdp.handle_cloudflare()

        js_extract_link = """
        (() => {
            let links = Array.from(document.querySelectorAll('a'))
                .map(a => a.href || "")
                .filter(href => href.includes('thuvienphapluat.vn/van-ban/'));
            return links.length > 0 ? links[0] : null;
        })()
        """
        link = cdp.evaluate_js(js_extract_link)
        if link:
            link_clean = link.split("?")[0].split("#")[0]
            print(f"[Auto-Discovery Success] Tìm thấy liên kết: {link_clean}")
            return str(link_clean)

        print("[Auto-Discovery Info] Không tìm thấy link Thư viện Pháp luật trên Google.")
        return None
    except Exception as e:
        print(f"[Auto-Discovery Warning] Lỗi tìm kiếm Google CDP: {e}")
        return None


def download_via_cdp_or_client(url: str, dest_path: Path) -> bool:
    """Download a file using Chrome CDP (preferred) or urllib fallback."""
    if ChromeCDP is not None and trigger_download is not None:
        try:
            ensure_chrome_debug_port()
            print(f"[CDP] Thử kết nối Chrome CDP trên port 9222 để tải: {url}")
            cdp = ChromeCDP(port=9222)
            pages = cdp.get_pages()
            if pages:
                cdp.connect_tab(pages[0]["webSocketDebuggerUrl"])
                cdp.navigate(url)
                cdp.wait_ready()
                cdp.handle_cloudflare()
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                success = trigger_download(cdp, dest_path.parent, dest_path.stem)
                if success:
                    print(f"[CDP] Tải file thành công: {dest_path.name}")
                    return True
        except Exception as e:
            print(f"[CDP Warning] Lỗi kết nối hoặc thực thi Chrome CDP: {e}")
            print("[CDP Warning] Thử fallback sang client tải trực tiếp...")

    try:
        import urllib.request
        print(f"[Urllib] Tải trực tiếp từ URL: {url}")
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        print(f"[Urllib] Tải file thành công: {dest_path.name}")
        return True
    except Exception as e:
        print(f"[Error] Tải file từ internet thất bại: {e}")
        return False
