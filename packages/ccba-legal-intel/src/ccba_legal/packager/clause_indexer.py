"""AST Clause Generator and QA Benchmark Writer."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def generate_clauses_json(bundle_or_text: Path | str, output_dir: Path | None = None) -> list[dict[str, Any]] | Path:
    """Generate structured clauses.json containing atomic clause-level metadata or AST."""
    if isinstance(bundle_or_text, str) or (isinstance(bundle_or_text, Path) and not bundle_or_text.is_dir() and output_dir is not None):
        content = bundle_or_text if isinstance(bundle_or_text, str) else bundle_or_text.read_text(encoding="utf-8")
        out_dir = output_dir or Path(".")
        lines = content.splitlines()
        clauses: list[dict[str, Any]] = []

        current_chapter: str | None = None
        current_section: str | None = None
        current_article: str | None = None
        current_clause: str | None = None

        for idx, line in enumerate(lines, 1):
            stripped = line.strip()

            # Chapter: # Chương I hoặc ## Chương I
            m_chap = re.match(r"^#+\s*(Chương\s+([IVXLCDM0-9]+)[\.:\s-]*.*)$", stripped, re.IGNORECASE)
            if m_chap:
                roman = m_chap.group(2).lower()
                c_id = f"chuong-{roman}"
                current_chapter = c_id
                current_section = None
                current_article = None
                current_clause = None
                clauses.append({
                    "clause_id": c_id,
                    "title": m_chap.group(1).strip(),
                    "node_type": "chapter",
                    "parent_id": None,
                    "line_start": idx,
                    "line_end": idx,
                })
                continue

            # Section: ### Mục 1
            m_sec = re.match(r"^#+\s*(Mục\s+(\d+)[\.:\s-]*.*)$", stripped, re.IGNORECASE)
            if m_sec:
                sec_num = m_sec.group(2)
                s_id = f"muc-{sec_num}"
                current_section = s_id
                current_article = None
                current_clause = None
                clauses.append({
                    "clause_id": s_id,
                    "title": m_sec.group(1).strip(),
                    "node_type": "section",
                    "parent_id": current_chapter,
                    "line_start": idx,
                    "line_end": idx,
                })
                continue

            # Article: ### Điều 1. Phạm vi
            m_art = re.match(r"^#+\s*(Điều\s+(\d+)[\.:\s-]+(.*))$", stripped, re.IGNORECASE)
            if m_art:
                art_num = m_art.group(2)
                a_id = f"dieu-{art_num}"
                current_article = a_id
                current_clause = None
                parent = current_section or current_chapter
                clauses.append({
                    "clause_id": a_id,
                    "title": m_art.group(1).strip(),
                    "node_type": "article",
                    "parent_id": parent,
                    "line_start": idx,
                    "line_end": idx,
                })
                continue

            # Clause: 1. Nội dung
            m_k = re.match(r"^(\d+)\.\s+(.*)$", stripped)
            if m_k and current_article:
                k_num = m_k.group(1)
                k_id = f"{current_article}-khoan-{k_num}"
                current_clause = k_id
                clauses.append({
                    "clause_id": k_id,
                    "title": f"Khoản {k_num}",
                    "node_type": "clause",
                    "parent_id": current_article,
                    "line_start": idx,
                    "line_end": idx,
                })
                continue

            # Point: a) Điểm
            m_pt = re.match(r"^([a-zđĐ])\)\s+(.*)$", stripped, re.IGNORECASE)
            if m_pt and current_clause:
                pt_char = m_pt.group(1).lower()
                p_id = f"{current_clause}-diem-{pt_char}"
                clauses.append({
                    "clause_id": p_id,
                    "title": f"Điểm {pt_char}",
                    "node_type": "point",
                    "parent_id": current_clause,
                    "line_start": idx,
                    "line_end": idx,
                })
                continue

        out_file = out_dir / "clauses.json"
        out_file.write_text(json.dumps(clauses, ensure_ascii=False, indent=2), encoding="utf-8")
        return clauses

    bundle_dir = Path(bundle_or_text)
    md_files = list(bundle_dir.glob("*.md"))
    primary_md = None
    for f in md_files:
        if f.name not in ["index.md", "log.md", "dead_ends.md", "compliance_checklist.md", "diff_report.md", "relationship_chart.md"]:
            primary_md = f
            break

    if not primary_md or not primary_md.exists():
        fallback_clauses = bundle_dir / "clauses.json"
        fallback_clauses.write_text("[]", encoding="utf-8")
        return fallback_clauses

    return generate_clauses_json(primary_md.read_text(encoding="utf-8"), bundle_dir)


def write_qa_benchmark(bundle_or_qa: Any, target_dir: Path | None = None) -> Path:
    """Generate qa_benchmark.json ground truth pairs for evaluation with 5-field validation."""
    if isinstance(bundle_or_qa, list):
        qa_pairs = bundle_or_qa
        out_dir = target_dir or Path(".")
    else:
        out_dir = Path(bundle_or_qa)
        qa_pairs = target_dir if isinstance(target_dir, list) else []

    required_fields = ["question", "answer", "anchor", "citation", "ground_truth_context"]
    for idx, item in enumerate(qa_pairs):
        if not isinstance(item, dict):
            raise ValueError(f"QA item at index {idx} must be a dict.")
        for field in required_fields:
            if not item.get(field):
                raise ValueError(f"QA item at index {idx} has missing or empty required fields: '{field}'")

    qa_path = out_dir / "qa_benchmark.json"
    qa_path.write_text(json.dumps(qa_pairs, ensure_ascii=False, indent=2), encoding="utf-8")
    return qa_path
