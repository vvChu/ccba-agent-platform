#!/usr/bin/env python3
"""Legal Intelligence Pipeline CLI wrapper.

Imports crawler, parser, and packager from `ccba_legal` and orchestrates them.
"""

import argparse
import json
import random
import sys
import time
from pathlib import Path

import requests
from ccba_legal import (
    ChromeCDP,
    LegalAnalysisEngine,
    OKFBundlePackager,
    get_concept_type,
    get_crawled_doc_data,
    is_guiding_link,
    trigger_download,
)

# Enforce UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")


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
        print("[LegalIntel] No page tabs found. Creating a new tab...")
        try:
            requests.get("http://127.0.0.1:9222/json/new")
            pages = cdp.get_pages()
        except Exception as e:
            print(f"[LegalIntel] Error creating new tab: {e}")
            sys.exit(1)

    ws_url = pages[0]["webSocketDebuggerUrl"]
    print(f"[LegalIntel] Connecting to tab WebSocket: {ws_url}")
    cdp.connect_tab(ws_url)

    try:
        # 2. Crawl Primary Law
        print(f"[LegalIntel] Crawling primary URL: {args.url}")
        main_title, main_text, main_links = get_crawled_doc_data(cdp, args.url)
        temp_packager = OKFBundlePackager(Path())
        slug = temp_packager.sanitize_slug(main_title)

        # We write locally to .md/ first, then package into the proper OKF layout
        md_dir = Path(args.output_dir or ".md")
        md_dir.mkdir(parents=True, exist_ok=True)
        packager = OKFBundlePackager(md_dir)

        if args.download_source:
            trigger_download(cdp, md_dir, slug)

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
        extracted_docs_dir = md_dir / "extracted_docs"
        extracted_docs_dir.mkdir(parents=True, exist_ok=True)
        with open(extracted_docs_dir / f"{slug}.txt", "w", encoding="utf-8") as f:
            f.write(main_text)

        # Save compliance checklist
        checklist_md = "## Compliance Checklist\n\n| Reference | Requirement | Verification Evidence | RACI |\n| --- | --- | --- | --- |\n"
        for req in checklist:
            raci_str = ", ".join(f"{k}:{v}" for k, v in req.get("raci", {}).items() if v)
            checklist_md += f"| {req.get('reference')} | {req.get('requirement')} | {req.get('evidence')} | {raci_str} |\n"

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
        guiding_slugs = []
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
                    time.sleep(2 + random.random() * 2)
                    sub_title, sub_text, sub_links = get_crawled_doc_data(cdp, current_url)
                    sub_metadata = analyzer.analyze_document(sub_text)
                    sub_slug = packager.sanitize_slug(sub_title)
                    concept_type = get_concept_type(current_url)

                    packager.write_concept(
                        f"{sub_slug}.md",
                        concept_type,
                        sub_metadata.get("title", sub_title),
                        sub_metadata.get("summary", ""),
                        sub_text,
                        resource_uri=current_url
                    )

                    if args.download_source:
                        trigger_download(cdp, md_dir, sub_slug)

                    # Save raw text of related document
                    with open(extracted_docs_dir / f"{sub_slug}.txt", "w", encoding="utf-8") as f:
                        f.write(sub_text)

                    related_docs.append({
                        "title": sub_metadata.get("title", sub_title),
                        "slug": f"{sub_slug}.md",
                        "summary": sub_metadata.get("summary", ""),
                        "type": concept_type,
                        "parent_slug": parent_slug,
                        "node_id": sub_slug,
                        "relationship": rel_type
                    })
                    guiding_slugs.append(sub_slug)
                    count += 1

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

        # 8. Organize into proper OKF Bundle directory under legal_docs/
        print("[LegalIntel] Formatting and organizing OKF Bundle directory structure...")
        packager.organize_bundle_structure(slug, guiding_slugs)

        print("[LegalIntel] Pipeline executed successfully.")

    finally:
        cdp.close()


if __name__ == "__main__":
    main()
