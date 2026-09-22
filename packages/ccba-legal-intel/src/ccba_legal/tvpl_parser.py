"""tvpl_parser.py - HTML DOM parsing, Gazette metadata extraction, and legal relationship graph mapping."""

from __future__ import annotations

import json
import re
from typing import Any

from ccba_legal.cdp import ChromeCDP
from ccba_legal.registry import load_relation_synonyms as _load_relation_synonyms
from ccba_legal.registry import resolve_project_root
from ccba_legal.session import sleep_with_jitter


def _derive_doc_slug(doc_num: str, doc_type: str, url: str) -> str:
    """Generate a clean snake_case slug from document number or URL."""
    if doc_num:
        s = re.sub(r"([a-zA-Z]+)(\d+)", r"\1_\2", doc_num)
        clean = re.sub(r"[^\w\d]+", "_", s.lower()).strip("_")
        if clean:
            return clean
    parts = url.rstrip("/").split("/")[-1].replace(".aspx", "")
    return re.sub(r"[^\w\d]+", "_", parts.lower()).strip("_")


def load_relation_synonyms() -> dict[str, str]:
    """Load synonyms mapping for legal relationship diagram."""
    return _load_relation_synonyms(resolve_project_root())


def _extract_gazette_metadata(cdp: ChromeCDP) -> dict[str, str | None]:
    """Extract Cong bao number and publication date from Tab TaiVe DOM."""
    gazette_js = """
    (() => {
        let text = document.body.innerText;
        let cb_match = text.match(/Công báo số[:\\s]+([0-9\\+\\/]+)/i) ||
                       text.match(/Số Công báo[:\\s]+([0-9\\+\\/]+)/i) ||
                       text.match(/Số[:\\s]+([0-9\\+\\/]+)\\s*\\(Công báo\\)/i);
        let date_match = text.match(/Ngày đăng Công báo[:\\s]+([0-9\\/]+)/i) ||
                         text.match(/Đăng Công báo ngày[:\\s]+([0-9\\/]+)/i);
        return {
            cong_bao_number: cb_match ? cb_match[1].trim() : null,
            cong_bao_date: date_match ? date_match[1].trim() : null
        };
    })()
    """
    try:
        res = cdp.evaluate_js(gazette_js)
        return res if isinstance(res, dict) else {}
    except Exception:
        return {}


def get_crawled_doc_data(cdp: ChromeCDP, url: str) -> tuple[str, str, list[dict[str, str]]]:
    """Retrieve title, clean innerText, and list of links from active browser tab."""
    cdp.navigate(url)
    cdp.wait_ready()
    cdp.handle_cloudflare()

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


METADATA_EXTRACTION_JS_TEMPLATE = r"""
(() => {
    let result = {};
    let propertyContainer = document.querySelector('#divThuocTinh') ||
                            document.querySelector('#ctl00_Content_Tab_ThuocTinh') ||
                            document.querySelector('.properties') ||
                            document.querySelector('#divContentDoc') ||
                            document;
    let tables = Array.from(propertyContainer.querySelectorAll('table'));
    let targetTable = tables.find(t => {
        let txt = t.innerText || '';
        return (txt.includes('Số hiệu') || txt.includes('Số hiệu:')) &&
               (txt.includes('Ngày ban hành') || txt.includes('Nơi ban hành') || txt.includes('Cơ quan ban hành'));
    }) || tables.find(t => t.innerText.includes('Số hiệu'));

    if (targetTable) {
        let rows = Array.from(targetTable.querySelectorAll('tr'));
        rows.forEach(row => {
            let cols = Array.from(row.querySelectorAll('td, th'));
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
        let keys = [
            'Số hiệu', 'Loại văn bản', 'Lĩnh vực', 'Nơi ban hành', 'Cơ quan ban hành',
            'Người ký', 'Người ký/ Chức danh', 'Người ký / Chức danh',
            'Ngày ban hành', 'Ngày hiệu lực', 'Ngày có hiệu lực',
            'Ngày đăng', 'Ngày đăng công báo',
            'Tình trạng', 'Tình trạng hiệu lực', 'Hiệu lực'
        ];
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
    """Retrieve structured metadata from the TVPL 'Lược đồ' tab page."""
    base_url = url.split("?")[0].split("#")[0]
    luoc_do_url = f"{base_url}?Tab=LuocDo"

    print(f"[Crawler] Navigating to 'Luoc do' page: {luoc_do_url}")
    cdp.navigate(luoc_do_url)
    cdp.wait_ready()
    cdp.handle_cloudflare()
    sleep_with_jitter(2.0, 0.5, 1.5)

    mapping = relation_map if relation_map is not None else load_relation_synonyms()
    mapping_json = json.dumps(mapping, ensure_ascii=False)
    metadata_js = METADATA_EXTRACTION_JS_TEMPLATE.replace("__REL_MAP_JSON__", mapping_json)

    raw_meta = cdp.evaluate_js(metadata_js) or {}

    def _find_field(aliases: list[str]) -> str:
        for a in aliases:
            val = raw_meta.get(a)
            if val:
                return str(val).strip()
        for rk, rv in raw_meta.items():
            for a in aliases:
                if a.lower() in rk.lower() and rv:
                    return str(rv).strip()
        return ""

    raw_status = _find_field(["Tình trạng", "Tình trạng hiệu lực", "Hiệu lực"])
    status_mapped = "Còn hiệu lực"
    if "hết hiệu lực" in raw_status.lower() or "bị thay thế" in raw_status.lower():
        status_mapped = "Hết hiệu lực"

    metadata = {
        "document_number": _find_field(["Số hiệu"]),
        "type": _find_field(["Loại văn bản"]),
        "issued_by": _find_field(["Nơi ban hành", "Cơ quan ban hành"]),
        "signer": _find_field(["Người ký", "Người ký/ Chức danh", "Người ký / Chức danh"]),
        "issued_date": _parse_tvpl_date(_find_field(["Ngày ban hành"])),
        "effective_date": _parse_tvpl_date(_find_field(["Ngày hiệu lực", "Ngày có hiệu lực"])),
        "expiration_date": _parse_tvpl_date(
            _find_field(["Ngày hết hiệu lực", "Hết hiệu lực", "Ngày hết hiệu lực:"])
        ),
        "published_date": _parse_tvpl_date(_find_field(["Ngày đăng", "Ngày đăng công báo"])),
        "status": status_mapped,
        "relations": raw_meta.get("relations", {}),
    }
    return metadata
