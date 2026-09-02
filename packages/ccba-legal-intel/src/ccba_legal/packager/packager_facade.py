"""OKFBundlePackager Facade Class."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from ccba_legal.packager.bundle_writer import (
    package_bundle,
    package_bundle_v2,
    write_concept,
    write_logs_and_index,
    write_logs_and_index_v2,
)
from ccba_legal.packager.clause_indexer import (
    generate_clauses_json,
    write_qa_benchmark,
)
from ccba_legal.packager.link_standardizer import (
    integrate_tables,
    organize_bundle_structure,
    standardize_bundle_links,
)
from ccba_legal.packager.slug_utils import sanitize_slug


class OKFBundlePackager:
    """Manages creation, writing, and directory structure organization of OKF Bundles."""

    def __init__(
        self,
        root_dir: Path,
        formula_standardizer: Callable[[str], str] | None = None,
        amendment_processor: Callable[[str, str, str], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.root_dir = root_dir
        self.formula_standardizer = formula_standardizer
        self.amendment_processor = amendment_processor

    def sanitize_slug(self, text: str) -> str:
        """Create a clean directory slug from URL or title."""
        return sanitize_slug(text)

    def package_bundle(self, doc_id: str, content: str, metadata: dict[str, Any]) -> Path:
        """Create and structure an OKF bundle for a document."""
        return package_bundle(self.root_dir, doc_id, content, metadata)

    def package_bundle_v2(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any],
        qa_items: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> Path:
        """Create a strictly flat, zero-redundancy OKF v2.0 bundle."""
        return package_bundle_v2(
            self.root_dir, doc_id, content, metadata, qa_items=qa_items, **kwargs
        )

    def write_concept(
        self,
        relative_path: str,
        concept_type: str,
        title: str,
        description: str,
        content: str,
        resource_uri: str = "",
    ) -> None:
        """Write a concept file with valid OKF YAML frontmatter."""
        write_concept(
            self.root_dir, relative_path, concept_type, title, description, content, resource_uri
        )

    def organize_bundle_structure(self, bundle_slug: str, guiding_files: list[str]) -> None:
        """Move generated primary and guiding files into an isolated OKF Bundle directory."""
        organize_bundle_structure(
            root_dir=self.root_dir,
            bundle_slug=bundle_slug,
            guiding_files=guiding_files,
            formula_standardizer=self.formula_standardizer,
            amendment_processor=self.amendment_processor,
        )

    def _write_logs_and_index(
        self, bundle_dir: Path, bundle_slug: str, guiding_files: list[str]
    ) -> None:
        """Create and update index.md, log.md, and dead_ends.md in the root of the OKF Bundle."""
        write_logs_and_index(bundle_dir, bundle_slug, guiding_files)

    def _write_logs_and_index_v2(
        self, bundle_dir: Path, bundle_slug: str, metadata: dict[str, Any]
    ) -> None:
        """Write lightweight OKF v2.0 index and logs."""
        write_logs_and_index_v2(bundle_dir, bundle_slug, metadata)

    def standardize_bundle_links(self, bundle_dir: Path) -> None:
        """Walk every markdown file in bundle_dir and rewrite links to be relative/bundle-safe."""
        standardize_bundle_links(bundle_dir)

    def generate_clauses_json(self, bundle_or_text: Any, output_dir: Path | None = None) -> Any:
        """Generate structured clauses.json containing atomic clause-level metadata."""
        return generate_clauses_json(bundle_or_text, output_dir)

    def write_qa_benchmark(self, bundle_or_qa: Any, target_dir: Path | None = None) -> Path:
        """Generate qa_benchmark.json ground truth pairs for evaluation."""
        return write_qa_benchmark(bundle_or_qa, target_dir)

    def integrate_tables(self, bundle_or_docx: Any, tables_or_dir: Any = None) -> Any:
        """Save structured table payloads inside the tables/ subdirectory or extract from docx."""
        return integrate_tables(bundle_or_docx, tables_or_dir)
