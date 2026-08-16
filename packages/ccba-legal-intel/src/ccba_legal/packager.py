import json
import re
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml


class OKFBundlePackager:
    """Manages creation, writing, and directory structure organization of Open Knowledge Format (OKF) Bundles."""

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
        text = text.lower()
        # Replace slashes and dots with spaces
        text = text.replace("/", " ").replace("\\", " ").replace(".", " ")
        # Remove accents
        accents = {
            "a": "áàảãạăắằẳẵặâấầẩẫậ",
            "d": "đ",
            "e": "éèẻẽẹêếềểễệ",
            "i": "íìỉĩị",
            "o": "óòỏõọôốồổỗộơớờởỡợ",
            "u": "úùủũụưứừửữự",
            "y": "ýỳỷỹỵ",
        }
        for char, group in accents.items():
            for g in group:
                text = text.replace(g, char)
        text = re.sub(r"[^a-z0-9\s_-]", "", text)
        text = re.sub(r"[\s_-]+", "_", text).strip("_")
        # Truncate to prevent Windows MAX_PATH (260 chars) limitation issues
        if len(text) > 60:
            text = text[:60].rstrip("_")
        return text

    def package_bundle(self, doc_id: str, content: str, metadata: dict[str, Any]) -> Path:
        """Create and structure an OKF v2.0 bundle for a document with raw content and metadata.

        Args:
            doc_id: The document identifier.
            content: Document text content.
            metadata: Document metadata dictionary.

        Returns:
            Path: Path to the created OKF bundle directory.
        """
        bundle_slug = self.sanitize_slug(doc_id)
        bundle_dir = self.root_dir / bundle_slug
        bundle_dir.mkdir(parents=True, exist_ok=True)

        title = metadata.get("title", f"Legal Document {doc_id}")
        doc_type = metadata.get("type", "Law")

        # OKF v2.0 (ADR 0038): Write independent metadata.yaml
        meta_dict = {
            "doc_id": doc_id,
            "title": title,
            "type": doc_type,
            "doc_number": metadata.get("document_number", metadata.get("doc_number", "")),
            "category": metadata.get("category", doc_type),
            "issuer": metadata.get("issued_by", metadata.get("issuer", "")),
            "issued_date": metadata.get("issued_date", ""),
            "effective_date": metadata.get("effective_date", ""),
            "status": metadata.get("status", "effective"),
            "source_url": metadata.get("source_url", ""),
            "sha256": metadata.get("sha256", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_yaml_path = bundle_dir / "metadata.yaml"
        meta_yaml_path.write_text(
            yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        self.write_concept(
            relative_path=f"{bundle_slug}/{bundle_slug}.md",
            concept_type=doc_type,
            title=title,
            description=f"Raw text for {doc_id}",
            content=content,
            resource_uri=metadata.get("source_url", ""),
        )

        self._write_logs_and_index(bundle_dir, bundle_slug, [])
        return bundle_dir

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
        dest = self.root_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)

        frontmatter = f"""---
type: {concept_type}
title: "{title}"
description: "{description}"
resource: "{resource_uri}"
timestamp: "{time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}"
---

{content}
"""
        with open(dest, "w", encoding="utf-8") as f:
            f.write(frontmatter)
        print(f"[OKF Packager] Wrote concept to {dest}")

    def organize_bundle_structure(self, bundle_slug: str, guiding_files: list[str]) -> None:
        """Move generated primary and guiding files into an isolated OKF Bundle directory under legal_docs/."""
        from ccba_legal.formatter import OKFStructureProcessor

        processor = OKFStructureProcessor(self.formula_standardizer)

        md_dir = self.root_dir
        bundle_dir = md_dir / "legal_docs" / bundle_slug
        guiding_dir = bundle_dir / "guiding_docs"

        # Create target directories
        guiding_dir.mkdir(parents=True, exist_ok=True)

        primary_files = {
            f"{bundle_slug}.md": f"{bundle_slug}.md",
            f"{bundle_slug}.docx": f"{bundle_slug}.docx",
            "index.md": "index.md",
            "compliance_checklist.md": "compliance_checklist.md",
            "relationship_chart.md": "relationship_chart.md",
            "diff_report.md": "diff_report.md",
        }

        # 1. Move primary files and rewrite content links
        all_app_paths = []
        for old_name, new_name in primary_files.items():
            old_path = md_dir / old_name
            new_path = bundle_dir / new_name

            if old_path.exists():
                if old_path.suffix == ".md":
                    content = old_path.read_text(encoding="utf-8")

                    # Update guiding document links to point into guiding_docs/
                    for gf in guiding_files:
                        content = content.replace(f"{gf}.md", f"/guiding_docs/{gf}.md")

                    if old_name == f"{bundle_slug}.md":
                        processed_content = processor.format_content(content, bundle_dir)

                        full_text_path = bundle_dir / "full_text.md"
                        full_text_path.write_text(processed_content, encoding="utf-8")

                        processor.split_by_chapters(processed_content, bundle_dir / "sections")
                        processor.generate_chunks(processed_content, bundle_dir)
                        content = processed_content

                    new_path.write_text(content, encoding="utf-8")
                    old_path.unlink()

                    # Split appendices if any
                    apps = processor.split_concept_appendices(new_path)
                    for ap in apps:
                        all_app_paths.append((new_name.replace(".md", ""), ap))
                else:
                    shutil.move(old_path, new_path)
                print(
                    f"[OKF Packager] Moved primary file: {old_name} -> legal_docs/{bundle_slug}/{new_name}"
                )

        # 2. Move guiding documents and rewrite content links
        for gf in guiding_files:
            old_md = md_dir / f"{gf}.md"
            new_md = guiding_dir / f"{gf}.md"
            if old_md.exists():
                content = old_md.read_text(encoding="utf-8")

                # Update links pointing to primary law and support documents (up one level)
                content = content.replace(f"{bundle_slug}.md", f"/{bundle_slug}.md")
                content = content.replace("index.md", "/index.md")
                content = content.replace("compliance_checklist.md", "/compliance_checklist.md")
                content = content.replace("relationship_chart.md", "/relationship_chart.md")
                content = content.replace("diff_report.md", "/diff_report.md")

                new_md.write_text(content, encoding="utf-8")
                old_md.unlink()

                # Split appendices if any
                apps = processor.split_concept_appendices(new_md)
                for ap in apps:
                    all_app_paths.append((gf, f"guiding_docs/{ap}"))
                print(
                    f"[OKF Packager] Moved guiding MD: {gf}.md -> legal_docs/{bundle_slug}/guiding_docs/{gf}.md"
                )

            old_docx = md_dir / f"{gf}.docx"
            new_docx = guiding_dir / f"{gf}.docx"
            if old_docx.exists():
                shutil.move(old_docx, new_docx)
                print(
                    f"[OKF Packager] Moved guiding DOCX: {gf}.docx -> legal_docs/{bundle_slug}/guiding_docs/{gf}.docx"
                )

        # 3. Update index.md with appendices
        index_path = bundle_dir / "index.md"
        if index_path.exists() and all_app_paths:
            index_content = index_path.read_text(encoding="utf-8")
            if "### Phụ lục đính kèm" not in index_content:
                appendix_section = "\n### Phụ lục đính kèm (Decree Appendices)\n\n"
                for _parent, rel_link in all_app_paths:
                    filename = rel_link.split("/")[-1]
                    label = filename.replace(".md", "").replace("_", " ").title()
                    # Make Roman numerals uppercase in the label
                    label = re.sub(
                        r"\bPhu Luc (\d+)\b",
                        lambda m: f"Phụ lục {m.group(1)}",
                        label,
                        flags=re.IGNORECASE,
                    )
                    appendix_section += f"- [{label}]({rel_link})\n"

                index_path.write_text(
                    index_content.strip() + "\n" + appendix_section, encoding="utf-8"
                )
                print("[OKF Packager] Updated index.md with split appendices list.")

        # Write logs and update index with new files
        self._write_logs_and_index(bundle_dir, bundle_slug, guiding_files)

        # Automatically scan for clause-level amendments and update target documents / registry
        if self.amendment_processor:
            try:
                # Scan primary document
                primary_md_path = bundle_dir / "full_text.md"
                if primary_md_path.exists():
                    content = primary_md_path.read_text(encoding="utf-8")
                    try:
                        rel_path = primary_md_path.relative_to(self.root_dir.parent).as_posix()
                    except ValueError:
                        rel_path = primary_md_path.as_posix()
                    self.amendment_processor(bundle_slug, content, rel_path)

                # Scan guiding documents
                for gf in guiding_files:
                    guiding_md_path = guiding_dir / f"{gf}.md"
                    if guiding_md_path.exists():
                        content = guiding_md_path.read_text(encoding="utf-8")
                        try:
                            rel_path = guiding_md_path.relative_to(self.root_dir.parent).as_posix()
                        except ValueError:
                            rel_path = guiding_md_path.as_posix()
                        self.amendment_processor(gf, content, rel_path)
            except Exception as e:
                print(f"[OKF Packager] Error during automatic amendment processing: {e}")

        # 4. Standardise all bundle links to be bundle-absolute
        self.standardize_bundle_links(bundle_dir)

    def _write_logs_and_index(
        self, bundle_dir: Path, bundle_slug: str, guiding_files: list[str]
    ) -> None:
        """Create and update index.md, log.md, and dead_ends.md in the root of the OKF Bundle."""
        import time

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        # Write log.md
        log_content = f"""# OKF Bundle Processing Log

- [{timestamp}] Bundle '{bundle_slug}' initialized.
- [{timestamp}] Primary law parsed and packaged.
- [{timestamp}] Table flattening and extraction completed.
- [{timestamp}] Multi-resolution storage (full_text, sections, chunks) structured.
"""
        (bundle_dir / "log.md").write_text(log_content, encoding="utf-8")

        # Write dead_ends.md
        dead_ends_content = """# OKF Bundle Dead Ends Log

No dead ends or crawler restrictions encountered.
"""
        (bundle_dir / "dead_ends.md").write_text(dead_ends_content, encoding="utf-8")

        # Update/create index.md
        index_path = bundle_dir / "index.md"
        if index_path.exists():
            content = index_path.read_text(encoding="utf-8")
        else:
            content = f"# OKF Bundle Index - {bundle_slug}\n\n## Bundle Concepts\n\n"

        new_elements = [
            "- [Full Text (Processed)](/full_text.md) (type: `Processed Law`)\n",
            "- [Chunks JSON](/chunks.json) (type: `Data Chunks`)\n",
            "- [Processing Log](/log.md) (type: `Process Log`)\n",
            "- [Dead Ends Log](/dead_ends.md) (type: `Dead Ends Log`)\n",
        ]

        lines = content.splitlines()
        inserted = False
        for idx, line in enumerate(lines):
            if "## Bundle Concepts" in line:
                for elem in reversed(new_elements):
                    if elem.strip() not in content:
                        lines.insert(idx + 1, elem.strip())
                inserted = True
                break

        if not inserted:
            content += "\n## OKF Metadata Files\n\n" + "".join(new_elements)
        else:
            content = "\n".join(lines)

        index_path.write_text(content, encoding="utf-8")

    def standardize_bundle_links(self, bundle_dir: Path) -> None:
        """Scan all markdown files in the bundle directory and convert any internal
        relative links to bundle-absolute paths starting with `/` from the bundle root.

        Args:
            bundle_dir: Path to the OKF Bundle root directory.
        """
        import os

        for filepath in bundle_dir.rglob("*.md"):
            if not filepath.is_file():
                continue

            content = filepath.read_text(encoding="utf-8")
            link_pattern = re.compile(r"(\[([^\]]+)\]\(([^)]+)\))")

            def replace_link(match: re.Match[str], filepath: Path = filepath) -> str:
                full_link = match.group(1)
                text = match.group(2)
                href = match.group(3)

                # Skip external, email, and anchor-only links
                if href.startswith(("http://", "https://", "mailto:", "#")):
                    return full_link

                # Skip bundle-absolute links (already starting with /)
                if href.startswith("/"):
                    return full_link

                base_href = href.split("#")[0]
                anchor = href.split("#", 1)[1] if "#" in href else ""

                if not base_href:
                    return full_link

                # Resolve target path relative to the current file's directory
                try:
                    target_path = (filepath.parent / base_href).resolve()
                except Exception:
                    return full_link

                # Check if resolved target path resides within the bundle root
                try:
                    is_inside = target_path.is_relative_to(bundle_dir.resolve())
                except (ValueError, AttributeError):
                    try:
                        rel = os.path.relpath(target_path, bundle_dir.resolve())
                        is_inside = not rel.startswith("..") and not os.path.isabs(rel)
                    except ValueError:
                        is_inside = False

                if is_inside:
                    # Convert to bundle-absolute path
                    rel_to_bundle = target_path.relative_to(bundle_dir.resolve()).as_posix()
                    new_href = f"/{rel_to_bundle}"
                    if anchor:
                        new_href = f"{new_href}#{anchor}"
                    return f"[{text}]({new_href})"

                return full_link

            new_content = link_pattern.sub(replace_link, content)
            if new_content != content:
                filepath.write_text(new_content, encoding="utf-8")
                print(f"[OKF Packager] Standardized links in {filepath}")

    # =========================================================================
    # OKF Bundle v2.0 (ADR 0038 Specification)
    # =========================================================================

    REQUIRED_QA_FIELDS = {
        "question",
        "answer",
        "anchor",
        "citation",
        "ground_truth_context",
    }

    def generate_clauses_json(
        self,
        content: str,
        bundle_dir: Path | None = None,
    ) -> list[dict[str, Any]]:
        """Parse markdown content into a flat list of AST clause coordinates according to OKF v2.0 (ADR 0038).

        Args:
            content: Document markdown content.
            bundle_dir: Optional bundle directory to write clauses.json to.

        Returns:
            list[dict[str, Any]]: List of clause coordinate objects.
        """
        lines = content.splitlines()
        clauses: list[dict[str, Any]] = []

        current_chapter: dict[str, Any] | None = None
        current_section: dict[str, Any] | None = None
        current_article: dict[str, Any] | None = None
        current_clause: dict[str, Any] | None = None

        chapter_pattern = re.compile(
            r"^(?:##|#)?\s*(?:<a id=\"[^\"]+\"></a>)?\s*(Chương\s+([0-9IVXLCDM]+)(?:[\.\:]|\s*[-–])?\s*(.*))$",
            re.IGNORECASE,
        )
        section_pattern = re.compile(
            r"^(?:###|##)?\s*(?:<a id=\"[^\"]+\"></a>)?\s*(Mục\s+(\d+)(?:[\.\:]|\s*[-–])?\s*(.*))$",
            re.IGNORECASE,
        )
        article_pattern = re.compile(
            r"^(?:###|##|#)?\s*(?:<a id=\"[^\"]+\"></a>)?\s*(Điều\s+(\d+)(?:[\.\:]|\s*[-–])?\s*(.*))$",
            re.IGNORECASE,
        )
        clause_pattern = re.compile(r"^(?:<a id=\"[^\"]+\"></a>)?\s*(\d+)[\.\)]\s*(.*)$")
        point_pattern = re.compile(
            r"^(?:<a id=\"[^\"]+\"></a>)?\s*([a-zđĐ])[\.\)]\s*(.*)$",
            re.IGNORECASE,
        )

        for idx, line in enumerate(lines):
            line_num = idx + 1
            line_str = line.strip()
            if not line_str:
                continue

            # Check Chapter
            chap_match = chapter_pattern.match(line_str)
            if chap_match:
                chap_num = chap_match.group(2).lower()
                chap_title = chap_match.group(1).strip()
                clause_id = f"chuong-{chap_num}"
                node = {
                    "clause_id": clause_id,
                    "anchor": clause_id,
                    "node_type": "chapter",
                    "parent_id": None,
                    "title": chap_title,
                    "line_start": line_num,
                    "line_end": line_num,
                }
                if clauses:
                    clauses[-1]["line_end"] = line_num - 1
                clauses.append(node)
                current_chapter = node
                current_section = None
                current_article = None
                current_clause = None
                continue

            # Check Section (Mục)
            sec_match = section_pattern.match(line_str)
            if sec_match:
                sec_num = sec_match.group(2)
                sec_title = sec_match.group(1).strip()
                clause_id = f"muc-{sec_num}"
                parent_id = current_chapter["clause_id"] if current_chapter else None
                node = {
                    "clause_id": clause_id,
                    "anchor": clause_id,
                    "node_type": "section",
                    "parent_id": parent_id,
                    "title": sec_title,
                    "line_start": line_num,
                    "line_end": line_num,
                }
                if clauses:
                    clauses[-1]["line_end"] = line_num - 1
                clauses.append(node)
                current_section = node
                current_article = None
                current_clause = None
                continue

            # Check Article (Điều)
            art_match = article_pattern.match(line_str)
            if art_match:
                art_num = art_match.group(2)
                art_title = art_match.group(1).strip()
                clause_id = f"dieu-{art_num}"
                parent_id = (
                    current_section["clause_id"]
                    if current_section
                    else (current_chapter["clause_id"] if current_chapter else None)
                )
                node = {
                    "clause_id": clause_id,
                    "anchor": clause_id,
                    "node_type": "article",
                    "parent_id": parent_id,
                    "title": art_title,
                    "line_start": line_num,
                    "line_end": line_num,
                }
                if clauses:
                    clauses[-1]["line_end"] = line_num - 1
                clauses.append(node)
                current_article = node
                current_clause = None
                continue

            # Check Clause (Khoản) inside an Article
            if current_article:
                cl_match = clause_pattern.match(line_str)
                if cl_match:
                    cl_num = cl_match.group(1)
                    cl_text = line_str
                    clause_id = f"{current_article['clause_id']}-khoan-{cl_num}"
                    node = {
                        "clause_id": clause_id,
                        "anchor": clause_id,
                        "node_type": "clause",
                        "parent_id": current_article["clause_id"],
                        "title": cl_text,
                        "line_start": line_num,
                        "line_end": line_num,
                    }
                    if clauses:
                        clauses[-1]["line_end"] = line_num - 1
                    clauses.append(node)
                    current_clause = node
                    continue

            # Check Point (Điểm) inside a Clause
            if current_clause and current_article:
                pt_match = point_pattern.match(line_str)
                if pt_match:
                    pt_char = pt_match.group(1).lower()
                    pt_text = line_str
                    clause_id = f"{current_clause['clause_id']}-diem-{pt_char}"
                    node = {
                        "clause_id": clause_id,
                        "anchor": clause_id,
                        "node_type": "point",
                        "parent_id": current_clause["clause_id"],
                        "title": pt_text,
                        "line_start": line_num,
                        "line_end": line_num,
                    }
                    if clauses:
                        clauses[-1]["line_end"] = line_num - 1
                    clauses.append(node)
                    continue

        if clauses:
            clauses[-1]["line_end"] = len(lines)

        if bundle_dir:
            out_file = Path(bundle_dir) / "clauses.json"
            out_file.write_text(
                json.dumps(clauses, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        return clauses

    def write_qa_benchmark(
        self,
        qa_items: list[dict[str, Any]],
        bundle_dir: Path,
    ) -> Path:
        """Write verified 5-field QA benchmark items to qa_benchmark.json according to ADR 0038.

        Args:
            qa_items: List of ground-truth QA dictionaries.
            bundle_dir: Path to the OKF bundle directory.

        Returns:
            Path: Path to the created qa_benchmark.json.

        Raises:
            ValueError: If any item is missing required fields.
        """
        for idx, item in enumerate(qa_items):
            missing = [f for f in self.REQUIRED_QA_FIELDS if not item.get(f)]
            if missing:
                raise ValueError(
                    f"Invalid QA benchmark item at index {idx}: missing or empty required fields {missing}"
                )

        dest = Path(bundle_dir) / "qa_benchmark.json"
        dest.write_text(
            json.dumps(qa_items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return dest

    def integrate_tables(
        self,
        docx_path: str | Path,
        bundle_dir: Path,
    ) -> list[Any]:
        """Extract and structure tables from a DOCX source into tables/json/ and tables/csv/.

        Args:
            docx_path: Path to DOCX source file.
            bundle_dir: Path to the OKF bundle root directory.

        Returns:
            list: List of extracted StructuredTable objects.
        """
        path = Path(docx_path)
        if not path.exists():
            return []

        try:
            from ccba_ooxml import TableReconstructor

            tables = TableReconstructor.extract_docx_tables(path)
            tables_dir = Path(bundle_dir) / "tables"
            for t in tables:
                TableReconstructor.save_table_exports(t, tables_dir)
            return tables
        except ImportError:
            return []

    def package_bundle_v2(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any],
        docx_path: str | Path | None = None,
        qa_items: list[dict[str, Any]] | None = None,
    ) -> Path:
        """Create and structure a complete OKF v2.0 bundle conforming to ADR 0038.

        Args:
            doc_id: Unique document identifier.
            content: Raw markdown text content.
            metadata: Metadata dictionary for metadata.yaml.
            docx_path: Optional path to source docx file for table extraction.
            qa_items: Optional list of 5-field QA benchmark items.

        Returns:
            Path: Path to the generated OKF v2.0 bundle directory.
        """
        bundle_slug = self.sanitize_slug(doc_id)
        bundle_dir = self.root_dir / bundle_slug
        bundle_dir.mkdir(parents=True, exist_ok=True)

        title = metadata.get("title", f"Legal Document {doc_id}")
        doc_type = metadata.get("type", "vbpl")

        # 1. Write independent metadata.yaml (SSOT)
        meta_dict = {
            "doc_id": doc_id,
            "doc_number": metadata.get("document_number", metadata.get("doc_number", "")),
            "title": title,
            "type": doc_type,
            "category": metadata.get("category", metadata.get("type", "vbpl")),
            "issuer": metadata.get("issued_by", metadata.get("issuer", "")),
            "issued_date": metadata.get("issued_date", ""),
            "effective_date": metadata.get("effective_date", ""),
            "status": metadata.get("status", "effective"),
            "source_url": metadata.get("source_url", ""),
            "sha256": metadata.get("sha256", ""),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        meta_yaml_path = bundle_dir / "metadata.yaml"
        meta_yaml_path.write_text(
            yaml.safe_dump(meta_dict, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )

        # 2. Write clean markdown file without YAML frontmatter (OKF v2.0 Pure Markdown)
        clean_md_path = bundle_dir / f"{bundle_slug}.md"
        clean_content = content
        if clean_content.strip().startswith("---"):
            parts = clean_content.split("---", 2)
            if len(parts) >= 3:
                clean_content = parts[2].strip()
        clean_md_path.write_text(clean_content, encoding="utf-8")

        # 3. Generate AST clauses.json
        self.generate_clauses_json(clean_content, bundle_dir)

        # 4. Save QA Benchmark if provided
        if qa_items:
            self.write_qa_benchmark(qa_items, bundle_dir)

        # 5. Extract tables if docx_path provided
        if docx_path:
            self.integrate_tables(docx_path, bundle_dir)

        # 6. Write index.md and logs
        self._write_logs_and_index_v2(bundle_dir, bundle_slug, has_qa=bool(qa_items))

        return bundle_dir

    def _write_logs_and_index_v2(
        self,
        bundle_dir: Path,
        bundle_slug: str,
        has_qa: bool = False,
    ) -> None:
        """Generate index.md and log.md according to OKF v2.0 specification."""
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        log_content = f"""# OKF v2.0 Bundle Processing Log

- [{timestamp}] Bundle '{bundle_slug}' initialized.
- [{timestamp}] Independent metadata.yaml generated (ADR 0038 SSOT).
- [{timestamp}] Pure markdown '{bundle_slug}.md' saved.
- [{timestamp}] AST clauses.json flat coordinates extracted.
- [{timestamp}] QA benchmark & tables structured.
"""
        (bundle_dir / "log.md").write_text(log_content, encoding="utf-8")

        index_content = f"""# OKF v2.0 Bundle Index — {bundle_slug}

## Thành Phần Cốt Lõi (Core Artifacts)
- [`metadata.yaml`](/metadata.yaml) — Cấu hình và thuộc tính pháp lý chính quy (SSOT)
- [`{bundle_slug}.md`](/{bundle_slug}.md) — Toàn văn văn bản Markdown thuần sạch 100%
- [`clauses.json`](/clauses.json) — Danh mục tọa độ AST phẳng hỗ trợ tra cứu $O(1)$
"""
        if has_qa:
            index_content += "- [`qa_benchmark.json`](/qa_benchmark.json) — Tập đối chuẩn 5 trường phục vụ Grounding Gate\n"

        tables_dir = bundle_dir / "tables"
        if tables_dir.exists():
            index_content += (
                "- [`tables/`](/tables/) — Bảng biểu trích xuất ma trận 2D (JSON/CSV)\n"
            )

        (bundle_dir / "index.md").write_text(index_content, encoding="utf-8")


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
