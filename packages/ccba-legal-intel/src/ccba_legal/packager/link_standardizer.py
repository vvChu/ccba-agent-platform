"""Link and Bundle Directory Structure Standardizer."""

from __future__ import annotations

import csv
import json
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ccba_legal.packager.bundle_writer import write_logs_and_index
from ccba_legal.packager.slug_utils import sanitize_slug


@dataclass
class ExtractedTable:
    """Represents an extracted table with attribute-accessible properties."""
    table_id: str
    rows: int = 0
    cols: int = 0


def standardize_bundle_links(bundle_dir: Path) -> None:
    """Walk every markdown file in bundle_dir and rewrite links to be relative/bundle-safe."""
    all_md_files = list(bundle_dir.glob("**/*.md"))
    for md_file in all_md_files:
        content = md_file.read_text(encoding="utf-8")
        original = content
        # Standardize relative paths with or without leading ../ or ./
        content = re.sub(r"\[([^\]]+)\]\((?:\.\./|\./)?guiding_docs/([^\)]+)\)", r"[\1](/guiding_docs/\2)", content)
        content = re.sub(r"\[([^\]]+)\]\((?:\.\./|\./)?appendices/([^\)]+)\)", r"[\1](/appendices/\2)", content)
        content = re.sub(r"\[([^\]]+)\]\((?:\.\./|\./)?sections/([^\)]+)\)", r"[\1](/sections/\2)", content)
        content = re.sub(r"\[([^\]]+)\]\((?:\.\./|\./)?(index\.md|full_text\.md)\)", r"[\1](/\2)", content)
        if content != original:
            md_file.write_text(content, encoding="utf-8")
            print(f"[OKF Packager] Standardized relative links in {md_file.name}")


def organize_bundle_structure(
    root_dir: Path,
    bundle_slug: str,
    guiding_files: list[str],
    formula_standardizer: Callable[[str], str] | None = None,
    amendment_processor: Callable[[str, str, str], list[dict[str, Any]]] | None = None,
) -> None:
    """Move generated primary and guiding files into an isolated OKF Bundle directory under legal_docs/."""
    from ccba_legal.formatter import OKFStructureProcessor

    processor = OKFStructureProcessor(formula_standardizer)
    md_dir = root_dir
    bundle_dir = md_dir / "legal_docs" / bundle_slug
    guiding_dir = bundle_dir / "guiding_docs"
    guiding_dir.mkdir(parents=True, exist_ok=True)

    for rel_path in guiding_files:
        src = md_dir / rel_path
        if src.exists():
            dest = guiding_dir / src.name
            shutil.move(str(src), str(dest))
            content = dest.read_text(encoding="utf-8")
            formatted = processor.format_content(content, bundle_dir)
            dest.write_text(formatted, encoding="utf-8")

    primary_candidates = [
        md_dir / f"{bundle_slug}.md",
        md_dir / f"{bundle_slug.replace('_', '-')}.md",
    ]
    primary_src = None
    for cand in primary_candidates:
        if cand.exists():
            primary_src = cand
            break

    if primary_src and primary_src.exists():
        primary_dest = bundle_dir / f"{bundle_slug}.md"
        shutil.move(str(primary_src), str(primary_dest))
        content = primary_dest.read_text(encoding="utf-8")
        formatted = processor.format_content(content, bundle_dir)
        primary_dest.write_text(formatted, encoding="utf-8")

        sections_dir = bundle_dir / "sections"
        processor.split_by_chapters(formatted, sections_dir)
        processor.split_concept_appendices(primary_dest)

        for sec_file in sections_dir.glob("*.md"):
            sec_content = sec_file.read_text(encoding="utf-8")
            sec_formatted = processor.format_content(sec_content, bundle_dir)
            sec_file.write_text(sec_formatted, encoding="utf-8")

    write_logs_and_index(bundle_dir, bundle_slug, guiding_files)
    standardize_bundle_links(bundle_dir)
    print(f"[OKF Packager] Organized bundle structure in {bundle_dir}")


def integrate_tables(arg1: Path | str, arg2: Any = None) -> list[ExtractedTable] | None:
    """Save structured table payloads inside the tables/ subdirectory or extract from docx."""
    p1 = Path(arg1)
    if p1.is_file() and p1.suffix in [".docx", ".doc"]:
        docx_file = p1
        target_bundle = Path(arg2) if arg2 else docx_file.parent
        tables_dir = target_bundle / "tables"
        tables_dir.mkdir(parents=True, exist_ok=True)
        csv_dir = tables_dir / "csv"
        csv_dir.mkdir(parents=True, exist_ok=True)
        json_dir = tables_dir / "json"
        json_dir.mkdir(parents=True, exist_ok=True)

        try:
            from docx import Document
            doc = Document(str(docx_file))
            extracted_tables = []

            titles = []
            for p in doc.paragraphs:
                p_text = p.text.strip()
                if p_text.lower().startswith("bảng"):
                    titles.append(p_text)

            for idx, table in enumerate(doc.tables, 1):
                t_title = titles[idx - 1] if idx - 1 < len(titles) else f"Bảng {idx}"
                m_title = re.search(r"Bảng\s+(\d+)\s*[-–:]*\s*(.*)", t_title, re.IGNORECASE)
                if m_title:
                    num = int(m_title.group(1))
                    name = sanitize_slug(m_title.group(2)) if m_title.group(2).strip() else ""
                    t_id = f"bang_{num:02d}_{name}".rstrip("_")
                else:
                    t_id = f"table_{idx:02d}"

                matrix = []
                for row in table.rows:
                    matrix.append([c.text.strip() for c in row.cells])
                if matrix:
                    csv_path = csv_dir / f"{t_id}.csv"
                    with open(csv_path, "w", encoding="utf-8", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerows(matrix)

                    json_path = json_dir / f"{t_id}.json"
                    headers = matrix[0]
                    rows = [dict(zip(headers, r)) for r in matrix[1:]]
                    json_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

                    extracted_tables.append(ExtractedTable(
                        table_id=t_id,
                        rows=len(matrix),
                        cols=len(matrix[0]) if matrix else 0,
                    ))
            return extracted_tables
        except Exception as e:
            print(f"[integrate_tables] Error extracting docx tables: {e}")
            return []

    target_bundle = p1
    tables = arg2 if isinstance(arg2, list) else []
    tables_dir = target_bundle / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    for t in tables:
        t_id = t.get("id") or t.get("table_id") or "table"
        if "csv" in t:
            (tables_dir / f"{t_id}.csv").write_text(t["csv"], encoding="utf-8")
        if "json" in t:
            (tables_dir / f"{t_id}.json").write_text(json.dumps(t["json"], ensure_ascii=False, indent=2), encoding="utf-8")
    return None
