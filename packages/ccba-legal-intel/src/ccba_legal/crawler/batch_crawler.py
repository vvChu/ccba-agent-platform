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
        crawler_engine: TVPLCrawlerEngine | Any | None = None,
        registry_path: Path | None = None,
        output_dir: Path | None = None,
    ) -> None:
        if isinstance(crawler_engine, (Path, str)):
            if output_dir is None:
                output_dir = Path(crawler_engine)
            crawler_engine = None

        if output_dir is not None:
            self.output_dir = Path(output_dir)
        elif hasattr(crawler_engine, "output_dir"):
            self.output_dir = Path(crawler_engine.output_dir)
        elif hasattr(getattr(crawler_engine, "provider", None), "output_dir"):
            self.output_dir = Path(crawler_engine.provider.output_dir)
        else:
            self.output_dir = Path(".md/extracted_docs")

        self.registry_path = registry_path or Path("legal_registry.yaml")
        from ccba_legal.crawler.engine import TVPLCrawler

        if crawler_engine is not None:
            if isinstance(crawler_engine, TVPLCrawler):
                self.engine = crawler_engine.engine
            else:
                self.engine = crawler_engine
        else:
            self.engine = TVPLCrawler(output_dir=self.output_dir).engine

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
                if hasattr(self.engine, "fetch_doc"):
                    doc_data = self.engine.fetch_doc(current_id)
                elif hasattr(self.engine, "fetch_document"):
                    doc_data = self.engine.fetch_document(current_id)
                else:
                    raise AttributeError(
                        f"Crawler engine {type(self.engine)} has neither fetch_doc nor fetch_document"
                    )
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
