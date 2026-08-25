"""Recursive Hierarchy and Batch Crawler for TVPL."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ccba_legal.crawler.engine import TVPLCrawlerEngine
from ccba_legal.registry import LegalRegistryManager


class TVPLBatchCrawler:
    """Crawls legal document hierarchy tree recursively (guiding decrees, circulars)."""

    def __init__(
        self,
        crawler_engine: TVPLCrawlerEngine | None = None,
        registry_path: Path | None = None,
    ) -> None:
        self.engine = crawler_engine or TVPLCrawlerEngine()
        self.registry_path = registry_path or Path("legal_registry.yaml")

    def crawl_hierarchy(
        self,
        root_doc_id_or_url: str,
        max_depth: int = 2,
        relation_filter: list[str] | None = None,
    ) -> dict[str, Any]:
        """Crawl root document and its guiding documents recursively."""
        visited: set[str] = set()
        crawled_docs: dict[str, Any] = {}
        queue: list[tuple[str, int]] = [(root_doc_id_or_url, 0)]
        reg_mgr = LegalRegistryManager(self.registry_path) if self.registry_path.exists() else None

        while queue:
            current_id, depth = queue.pop(0)
            if current_id in visited or depth > max_depth:
                continue
            visited.add(current_id)
            print(f"[TVPLBatchCrawler] Crawling (depth {depth}): {current_id}")
            try:
                doc_data = self.engine.fetch_doc(current_id)
                doc_slug = doc_data.get("slug", current_id)
                crawled_docs[doc_slug] = doc_data
                if reg_mgr:
                    reg_mgr.register_document(doc_slug, doc_data)

                if depth < max_depth:
                    relations = doc_data.get("relations", {})
                    for rel_type, rel_docs in relations.items():
                        if relation_filter and rel_type not in relation_filter:
                            continue
                        for r_item in rel_docs:
                            r_url = r_item.get("url") or r_item.get("document_number")
                            if r_url and r_url not in visited:
                                queue.append((r_url, depth + 1))
            except Exception as e:
                print(f"[TVPLBatchCrawler] [Error] Failed to crawl {current_id}: {e}")

        return crawled_docs
