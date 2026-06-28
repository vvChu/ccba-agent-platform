#!/usr/bin/env python3
"""Legal Intelligence Pipeline for ccba-agent-platform.

This script automates data acquisition of legal documents from Thư Viện Pháp Luật (TVPL),
analyzes them using Spark LiteLLM via ccba_ai, and packages the outputs as an
Open Knowledge Format (OKF) Bundle.
"""

import argparse
import json
import random
import re
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import requests
import websocket

from ccba_ai import ai

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


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
        payload = {
            "id": random.randint(1, 100000),
            "method": method,
            "params": params
        }
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
            "params": {
                "expression": expression,
                "returnByValue": True
            }
        }
        try:
            self.ws.send(json.dumps(payload))
            resp = self.ws.recv()
            data = json.loads(resp)

            # Handle standard protocol errors or execution errors
            result_data = data.get("result", {})
            if "exceptionDetails" in result_data:
                exc = result_data["exceptionDetails"]
                raise ChromeCDPError(f"JS Exception: {exc.get('text')} - {exc.get('exception', {})}")

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
            "params": {"url": url}
        }
        try:
            self.ws.send(json.dumps(payload))
            # Wait for command response
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
                    # Occurs if reloading/navigating
                    is_blocked = True
            print("[LegalIntel] Challenge solved! Resuming execution...")
            self.wait_ready()

    def close(self) -> None:
        """Close WebSocket connection."""
        if self.ws:
            try:
                self.ws.close()
            except Exception:
                pass
            self.ws = None


class Cleaners:
    """Helper utilities to clean up text and extract JSON from LLM responses."""

    _THINK_PATTERN = re.compile(r"<think>.*?</think>\n*", re.DOTALL | re.IGNORECASE)
    _THINK_UNCLOSED = re.compile(r"<think>.*", re.DOTALL | re.IGNORECASE)
    _ORPHAN_END = re.compile(r"^.*?</think>\n*", re.DOTALL | re.IGNORECASE)

    @classmethod
    def strip_think_tags(cls, text: str) -> str:
        """Strip <think>...</think> tags and their contents from reasoning models."""
        text = cls._THINK_PATTERN.sub("", text)
        text = cls._THINK_UNCLOSED.sub("", text)
        text = cls._ORPHAN_END.sub("", text)
        return text.strip()

    @classmethod
    def extract_json(cls, raw: str) -> Any:
        """Extract JSON dictionary or list from raw text containing Markdown fences."""
        clean = cls.strip_think_tags(raw)
        # Try extracting from code block (supports both {} and [])
        match = re.search(r"```(?:json)?\s*([\{\[].*?[\}\]])\s*```", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Fallback: try raw JSON string
        match = re.search(r"([\{\[].*[\}\]])", clean, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return None

    @classmethod
    def remove_ocr_artifacts(cls, text: str) -> str:
        """Remove long uppercase lines commonly created by page headers/footers in OCR."""
        return re.sub(r'^[A-ZÀ-Ỹ][A-ZÀ-Ỹ\s_]{14,}\.?\s*$', '', text, flags=re.MULTILINE).strip()


class LegalAnalysisEngine:
    """Module responsible for calling Spark LiteLLM to analyze law texts."""

    def __init__(self, model: str = "gemini-3.1-pro-high") -> None:
        self.model = model

    def analyze_document(self, text: str) -> dict[str, Any]:
        """Extract metadata and summarize key properties of the document."""
        clean_text = Cleaners.remove_ocr_artifacts(text)[:80000]  # Safe budget limit
        prompt = f"""
Analyze the following Vietnamese legal text. Extract metadata and summarize key properties.
Return ONLY a JSON object (inside a markdown json code block) with the following keys:
- title: string (Human-readable official name, e.g. "Luật Xây dựng 2025")
- doc_number: string (Official document number, e.g. "135/2025/QH15")
- issuing_body: string (e.g. "Quốc hội", "Chính phủ")
- signing_date: string (ISO 8601 date YYYY-MM-DD or empty)
- effective_date: string (ISO 8601 date YYYY-MM-DD or empty)
- summary: string (Brief 3-4 sentence summary of scope and main changes)

Law text:
{clean_text}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if not res:
            # Basic fallback
            res = {
                "title": "Unknown Legal Document",
                "doc_number": "Unknown",
                "issuing_body": "Unknown",
                "signing_date": "",
                "effective_date": "",
                "summary": "Could not parse summary from LLM."
            }
        return res

    def generate_checklist(self, text: str) -> list[dict[str, Any]]:
        """Identify key compliance requirements and build a RACI checklist."""
        clean_text = Cleaners.remove_ocr_artifacts(text)[:60000]
        prompt = f"""
Parse the following construction law/regulation text and extract key compliance requirements.
For each requirement, provide:
- reference: string (e.g., "Điều 45 Khoản 1")
- requirement: string (Vietnamese text of the rule/requirement)
- evidence: string (Evidence needed to verify compliance)
- raci: dict (Role assignments for: Owner, Contractor, Supervisor. Use values: R (Responsible), A (Accountable), C (Consulted), I (Informed), or None)

Return ONLY a JSON list of objects (inside a markdown json code block). Max 10 most critical requirements.

Text:
{clean_text}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if isinstance(res, list):
            return res
        if isinstance(res, dict) and "requirements" in res:
            return res["requirements"]
        return []

    def perform_diff(self, old_text: str, new_text: str) -> dict[str, Any]:
        """Perform semantic diff between old and new law versions."""
        clean_old = Cleaners.remove_ocr_artifacts(old_text)[:40000]
        clean_new = Cleaners.remove_ocr_artifacts(new_text)[:40000]
        prompt = f"""
Compare the older construction law text with the newer version.
Extract the key updates, deleted rules, and added provisions.
Return ONLY a JSON object (inside a markdown json code block) with:
- changes_summary: string (Overview of differences)
- comparison_table: list of dicts (with keys: item, old_provision, new_provision, effect)

Old law sample:
{clean_old}

New law sample:
{clean_new}
"""
        reply = ai.chat(prompt, model=self.model, temperature=0.1, max_tokens=8192)
        res = Cleaners.extract_json(reply)
        if not res:
            res = {
                "changes_summary": "Failed to extract diff summary.",
                "comparison_table": []
            }
        return res


class OKFBundlePackager:
    """Manages creation and writing of Open Knowledge Format (OKF) Bundles."""

    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir

    def sanitize_slug(self, text: str) -> str:
        """Create a clean directory slug from URL or title."""
        text = text.lower()
        # Replace slashes and dots with spaces
        text = text.replace('/', ' ').replace('\\', ' ').replace('.', ' ')
        # Remove accents
        accents = {
            'a': 'áàảãạăắằẳẵặâấầẩẫậ',
            'd': 'đ',
            'e': 'éèẻẽẹêếềểễệ',
            'i': 'íìỉĩị',
            'o': 'óòỏõọôốồổỗộơớờởỡợ',
            'u': 'úùủũụưứừửữự',
            'y': 'ýỳỷỹỵ'
        }
        for char, group in accents.items():
            for g in group:
                text = text.replace(g, char)
        text = re.sub(r'[^a-z0-9\s_-]', '', text)
        text = re.sub(r'[\s_-]+', '_', text).strip('_')
        return text

    def write_concept(self, relative_path: str, concept_type: str, title: str,
                      description: str, content: str, resource_uri: str = "") -> None:
        """Write a concept file with valid OKF YAML frontmatter."""
        dest = self.root_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = f"""---
type: {concept_type}
title: {title}
description: {description}
resource: {resource_uri}
timestamp: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}
---

{content}
"""
        with open(dest, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        print(f"[OKF Packager] Wrote concept to {dest}")


def is_guiding_link(url: str) -> bool:
    """Check if the URL points to a guiding or related document (including VBHN)."""
    url_lower = url.lower()
    keywords = ["nghi-dinh", "thong-tu", "quyet-dinh", "cong-van", "van-ban-hop-nhat", "vbhn"]
    return any(k in url_lower for k in keywords)


def get_concept_type(url: str) -> str:
    """Map a URL to its corresponding OKF concept type."""
    url_lower = url.lower()
    if "nghi-dinh" in url_lower:
        return "Decree"
    if "thong-tu" in url_lower:
        return "Circular"
    if "quyet-dinh" in url_lower:
        return "Decision"
    if "cong-van" in url_lower:
        return "Official Letter"
    if "van-ban-hop-nhat" in url_lower or "vbhn" in url_lower:
        return "Consolidated Document"
    return "Guiding Document"


def get_crawled_doc_data(cdp: ChromeCDP, url: str) -> tuple[str, str, list[dict[str, str]]]:
    """Retrieve title, clean innerText, and list of links from active browser tab."""
    cdp.navigate(url)
    cdp.wait_ready()
    cdp.handle_cloudflare()

    title = cdp.evaluate_js("document.title")

    # Target only the actual law content container to avoid website headers/footers/sidebars
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

    # Extract related TVPL links from document-wide anchors (highly robust across tabs)
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
        h = lnk['href'].split('?')[0].split('#')[0]
        if h not in seen and h != url:
            seen.add(h)
            links.append({"text": lnk["text"], "href": h, "relationship": lnk["relationship"]})

    return title, body_text, links


def trigger_download(cdp: ChromeCDP, download_dir: Path, slug_name: str) -> None:
    """Trigger download click and move the downloaded file to the project folder, renaming it to match the concept slug."""
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
        return

    # Wait for the download to complete in the Downloads folder
    start_time = time.time()
    while time.time() - start_time < 35:
        current_downloads = list(downloads_path.glob("*"))
        new_downloads = [f for f in current_downloads if f.name not in existing_downloads]
        if new_downloads:
            # Check for temporary download files
            if any(f.suffix == ".crdownload" or f.name.endswith(".tmp") for f in new_downloads):
                time.sleep(1)
                continue

            completed_files = [f for f in new_downloads if f.suffix in [".docx", ".pdf", ".doc"]]
            if completed_files:
                target_file = completed_files[0]
                dest_file = download_dir / f"{slug_name}{target_file.suffix}"
                print(f"[LegalIntel] Moving and standardizing file: {target_file.name} -> {dest_file.resolve()}")
                try:
                    shutil.move(str(target_file), str(dest_file))
                    print(f"[LegalIntel] Download completed successfully: {slug_name}{target_file.suffix}")
                except Exception as e:
                    print(f"[LegalIntel] Error moving file: {e}")
                return
        time.sleep(1)
    print("[LegalIntel] Warning: Download timed out after 35 seconds.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Legal Intelligence Pipeline CLI")
    parser.add_argument("--url", required=True, help="URL of the TVPL law page")
    parser.add_argument("--output-dir", help="Output directory for OKF bundle")
    parser.add_argument("--extract-related", action="store_true", help="Crawler guiding docs recursively")
    parser.add_argument("--limit", type=int, default=3, help="Max guiding docs to crawl")
    parser.add_argument("--max-depth", type=int, default=2, help="Max recursion depth for related docs")
    parser.add_argument("--compare-with", help="URL of predecessor law to diff against")
    parser.add_argument("--download-source", action="store_true", help="Download original Word/PDF files into the bundle")
    args = parser.parse_args()

    print("[LegalIntel] Initiating pipeline execution...")

    # 1. Connect to browser via CDP
    cdp = ChromeCDP()
    pages = cdp.get_pages()
    if not pages:
        # Open a new tab
        print("[LegalIntel] No page tabs found. Creating a new tab...")
        try:
            requests.get("http://127.0.0.1:9222/json/new")
            pages = cdp.get_pages()
        except Exception as e:
            print(f"[LegalIntel] Error creating new tab: {e}")
            sys.exit(1)

    # Connect to the first page tab
    ws_url = pages[0]["webSocketDebuggerUrl"]
    print(f"[LegalIntel] Connecting to tab WebSocket: {ws_url}")
    cdp.connect_tab(ws_url)

    try:
        # 2. Crawl Primary Law
        print(f"[LegalIntel] Crawling primary URL: {args.url}")
        main_title, main_text, main_links = get_crawled_doc_data(cdp, args.url)
        slug = OKFBundlePackager(Path()).sanitize_slug(main_title)
        out_path = Path(args.output_dir or f".md/legal_docs/{slug}")
        out_path.mkdir(parents=True, exist_ok=True)
        packager = OKFBundlePackager(out_path)

        if args.download_source:
            trigger_download(cdp, out_path, slug)

        # 3. Analyze Primary Law
        print("[LegalIntel] Performing LLM analysis on primary document...")
        analyzer = LegalAnalysisEngine()
        metadata = analyzer.analyze_document(main_text)
        checklist = analyzer.generate_checklist(main_text)

        # Save primary law concept
        packager.write_concept(
            f"{slug}.md",
            "Law",
            metadata.get("title", main_title),
            metadata.get("summary", ""),
            main_text,
            resource_uri=args.url
        )

        # Save raw text to .md/extracted_docs/<slug>.txt
        extracted_docs_dir = Path(".md/extracted_docs")
        extracted_docs_dir.mkdir(parents=True, exist_ok=True)
        with open(extracted_docs_dir / f"{slug}.txt", "w", encoding="utf-8") as f:
            f.write(main_text)

        # Save compliance checklist
        checklist_md = "## Compliance Checklist\n\n| Reference | Requirement | Verification Evidence | RACI |\n| --- | --- | --- | --- |\n"
        for req in checklist:
            raci_str = ", ".join(f"{k}:{v}" for k, v in req.get("raci", {}).items() if v)
            checklist_md += f"| {req.get('reference')} | {req.get('requirement')} | {req.get('evidence')} | {raci_str} |\n"

        # Also embed YAML list inside block
        checklist_md += "\n\n### Raw YAML Configuration\n```yaml\n"
        checklist_md += json.dumps(checklist, indent=2, ensure_ascii=False)
        checklist_md += "\n```\n"

        packager.write_concept(
            "compliance_checklist.md",
            "Compliance Checklist",
            f"Compliance Checklist - {metadata.get('title')}",
            "Extracted legal compliance criteria and RACI matrices.",
            checklist_md
        )

        # 4. Crawl and link Guiding Documents
        related_docs = []
        if args.extract_related:
            print("[LegalIntel] Crawling related guiding documents recursively...")
            normalized_main_url = args.url.split('?')[0].split('#')[0]
            crawled_urls = {normalized_main_url}

            queue = []
            for lnk in main_links:
                h = lnk["href"].split('?')[0].split('#')[0]
                if is_guiding_link(h) and h not in crawled_urls:
                    queue.append((lnk["href"], lnk["text"], 1, slug, lnk.get("relationship", "Guides")))

            count = 0
            while queue and count < args.limit:
                current_url, label, depth, parent_slug, rel_type = queue.pop(0)
                norm_url = current_url.split('?')[0].split('#')[0]
                if norm_url in crawled_urls:
                    continue
                crawled_urls.add(norm_url)

                if rel_type == "Consolidation":
                    print(f"\n[LegalIntel] NOTICE: Consolidated Document (VBHN) detected: {label} ({current_url})")
                    print("[LegalIntel] It is highly recommended to review this VBHN file for merged amendments.\n")

                print(f"[LegalIntel] Crawling (depth={depth}): {label} ({current_url})")
                try:
                    time.sleep(2 + random.random() * 2)  # Smart delay
                    sub_title, sub_text, sub_links = get_crawled_doc_data(cdp, current_url)
                    sub_metadata = analyzer.analyze_document(sub_text)
                    sub_slug = packager.sanitize_slug(sub_title)
                    concept_type = get_concept_type(current_url)

                    packager.write_concept(
                        f"guiding_docs/{sub_slug}.md",
                        concept_type,
                        sub_metadata.get("title", sub_title),
                        sub_metadata.get("summary", ""),
                        sub_text,
                        resource_uri=current_url
                    )

                    if args.download_source:
                        trigger_download(cdp, out_path / "guiding_docs", sub_slug)

                    # Save raw text of related document
                    with open(extracted_docs_dir / f"{sub_slug}.txt", "w", encoding="utf-8") as f:
                        f.write(sub_text)

                    related_docs.append({
                        "title": sub_metadata.get("title", sub_title),
                        "slug": f"guiding_docs/{sub_slug}.md",
                        "summary": sub_metadata.get("summary", ""),
                        "type": concept_type,
                        "parent_slug": parent_slug,
                        "node_id": sub_slug,
                        "relationship": rel_type
                    })
                    count += 1

                    # If we haven't hit max depth, add newly discovered links to the queue
                    if depth < args.max_depth:
                        for sl in sub_links:
                            sh = sl["href"].split('?')[0].split('#')[0]
                            if is_guiding_link(sh) and sh not in crawled_urls:
                                queue.append((sl["href"], sl["text"], depth + 1, sub_slug, sl.get("relationship", "Guides")))

                except Exception as ex:
                    print(f"[LegalIntel] Error crawling {label}: {ex}")

        # 5. Diffing Predecessor Law (if specified)
        if args.compare_with:
            print(f"[LegalIntel] Crawling predecessor URL: {args.compare_with}")
            old_title, old_text, _ = get_crawled_doc_data(cdp, args.compare_with)
            print("[LegalIntel] Running semantic diff...")
            diff_data = analyzer.perform_diff(old_text, main_text)

            diff_md = f"## Comparative Analysis\n\n### Summary of Changes\n{diff_data.get('changes_summary')}\n\n### Provision Comparison Table\n\n| Item | Old Provision | New Provision | Effect |\n| --- | --- | --- | --- |\n"
            for row in diff_data.get("comparison_table", []):
                diff_md += f"| {row.get('item')} | {row.get('old_provision')} | {row.get('new_provision')} | {row.get('effect')} |\n"

            packager.write_concept(
                "diff_report.md",
                "Comparative Report",
                f"Diff Report - {metadata.get('title')}",
                "Semantic changes and side-by-side comparison tables against previous version.",
                diff_md,
                resource_uri=args.compare_with
            )

        # 6. Mermaid Relationship Chart
        chart_md = "## Relationship Diagram\n\n```mermaid\ngraph TD\n"
        chart_md += f'    Main["{metadata.get("title")}"]\n'
        for rd in related_docs:
            p_node = "Main" if rd["parent_slug"] == slug else f'Sub_{rd["parent_slug"][:10]}'
            c_node = f'Sub_{rd["node_id"][:10]}'
            rel = rd.get("relationship", "Guides")

            if rel == "Consolidation":
                line = "== Consolidated ==>"
            elif rel == "Replacement":
                line = "-. Replaces .->"
            elif rel == "Rectification":
                line = "-. Rectifies .->"
            elif rel == "Amendment":
                line = "-. Amends .->"
            else:
                line = "-->|guides|"

            chart_md += f'    {p_node} {line} {c_node}["{rd["title"]}"]\n'
        chart_md += "```\n"

        packager.write_concept(
            "relationship_chart.md",
            "Visual Diagram",
            f"Relationship Chart - {metadata.get('title')}",
            "Mermaid relationship visualization graph of law and guiding documents.",
            chart_md
        )

        # 7. Write index.md (Bundle Index)
        index_md = f"# OKF Bundle Index - {metadata.get('title')}\n\n"
        index_md += f"{metadata.get('summary')}\n\n"
        index_md += "## Bundle Concepts\n\n"
        index_md += f"- [{metadata.get('title')}]({slug}.md) (type: `Law`)\n"
        index_md += "- [Compliance Checklist](compliance_checklist.md) (type: `Compliance Checklist`)\n"
        index_md += "- [Relationship Chart](relationship_chart.md) (type: `Visual Diagram`)\n"
        if args.compare_with:
            index_md += "- [Comparative Analysis (Diff Report)](diff_report.md) (type: `Comparative Report`)\n"
        if related_docs:
            index_md += "\n### Guiding Documents\n\n"
            for rd in related_docs:
                index_md += f"- [{rd['title']}]({rd['slug']}) (type: `{rd.get('type', 'Guiding Document')}`)\n"

        packager.write_concept(
            "index.md",
            "Bundle Index",
            f"OKF Index - {metadata.get('title')}",
            "Directory listing of all legal intelligence concepts in this bundle.",
            index_md
        )

        print("[LegalIntel] Pipeline executed successfully.")

    finally:
        cdp.close()


if __name__ == "__main__":
    main()
