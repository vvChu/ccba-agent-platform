"""registry_auditor.py - Sub-Auditor for Legal Registry consistency & OKF bundle orphan scanning.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .base import AuditIssue, BaseAuditor
from .link_auditor import LinkAuditor


class RegistryAuditor(BaseAuditor):
    """Deep Sub-Auditor for Legal Document Registry mapping and OKF orphan files scanning."""

    def __init__(self, project_root: Path | None = None) -> None:
        super().__init__(project_root)
        self._link_auditor = LinkAuditor(project_root)

    def load_legal_registry(self) -> dict[str, Any]:
        """Load legal document registry from workspace YAML."""
        registry_path = self.project_root / ".md" / "data" / "legal_registry.yaml"
        if not registry_path.exists():
            return {}
        try:
            with open(registry_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def build_markdown_to_doc_map(
        self, registry: dict[str, Any] | None = None
    ) -> dict[Path, dict[str, Any]]:
        """Map resolved markdown file paths to document definitions in legal registry."""
        if registry is None:
            registry = self.load_legal_registry()
        mapping = {}
        for _cat, docs in registry.items():
            if not isinstance(docs, list):
                continue
            for doc in docs:
                if not isinstance(doc, dict):
                    continue
                potential_paths = []

                if "markdown_path" in doc:
                    potential_paths.append(self.project_root / doc["markdown_path"])

                if "file_path" in doc:
                    fp = self.project_root / doc["file_path"]
                    potential_paths.append(fp.with_suffix(".md"))
                    potential_paths.append(fp.parent / "full_text.md")

                doc_id = doc.get("id", "")
                if doc_id:
                    slug = doc_id.lower().replace("-", "_")
                    legal_docs_dir = self.project_root / ".md" / "legal_docs"
                    if legal_docs_dir.exists():
                        for p in legal_docs_dir.rglob("*.md"):
                            if p.name == "full_text.md" and slug in p.parent.name.lower():
                                potential_paths.append(p)
                            if p.stem.lower() == slug:
                                potential_paths.append(p)

                for p in potential_paths:
                    try:
                        resolved = p.resolve()
                        if resolved.exists():
                            mapping[resolved] = doc
                    except Exception:
                        pass
        return mapping

    def scan_orphan_files(self, bundle_root: Path) -> list[Path]:
        """Scan for unreferenced markdown files under a bundle directory."""
        exclude_dirs = {".git", "node_modules", ".venv", "venv", ".pytest_cache"}
        all_files = []
        for p in bundle_root.rglob("*.md"):
            if p.is_file() and not any(ex in p.parts for ex in exclude_dirs):
                all_files.append(p.resolve())

        if not all_files:
            return []

        referenced = set()
        for filepath in all_files:
            try:
                with open(filepath, encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            links = self._link_auditor.extract_internal_links(content)
            for _line_num, _text, href in links:
                base_href = href.split("#")[0]
                if not base_href:
                    continue
                if base_href.startswith("/"):
                    resolved = (bundle_root / base_href.lstrip("/")).resolve()
                else:
                    resolved = (filepath.parent / base_href).resolve()
                referenced.add(resolved)

            frontmatter, _ = self._link_auditor.parse_frontmatter(content)
            if frontmatter and isinstance(frontmatter, dict):
                parent_doc = frontmatter.get("parent_document")
                if parent_doc and isinstance(parent_doc, str):
                    if parent_doc.startswith("/"):
                        parent_path = (bundle_root / parent_doc.lstrip("/")).resolve()
                    else:
                        parent_path = (filepath.parent / parent_doc).resolve()

                    if parent_path.exists() and parent_path.is_file():
                        try:
                            is_inside = parent_path.is_relative_to(bundle_root)
                        except ValueError:
                            is_inside = False
                        if is_inside:
                            referenced.add(filepath)

        orphans = []
        for filepath in all_files:
            if filepath.name in ("index.md", "full_text.md"):
                continue
            if filepath not in referenced:
                orphans.append(filepath)

        return orphans

    def audit(self, bundle_root: Path) -> list[AuditIssue]:
        """Audit OKF bundle and return list of orphan file issues."""
        orphans = self.scan_orphan_files(bundle_root)
        issues: list[AuditIssue] = []
        for o in orphans:
            rel_o = str(
                o.relative_to(self.project_root) if o.is_relative_to(self.project_root) else o
            )
            issues.append(
                AuditIssue(
                    line_number=1,
                    subject="Orphan File",
                    message=f"File {rel_o} is not referenced by any other markdown file in the bundle.",
                    category="orphan_files",
                    file_path=rel_o,
                )
            )
        return issues
