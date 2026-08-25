"""AST Clause and Ground Truth QA Benchmark Generator."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def generate_bundle_ast_and_qa(
    bundle_dir: Path | str,
    output_dir: Path | None = None,
    doc_title: str | None = None,
    cong_bao_number: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Extract deduplicated AST and QA Benchmark across Active Core and Modular Annexes."""
    target_bundle = Path(bundle_dir)
    if not target_bundle.is_dir() and target_bundle.is_file():
        target_bundle = target_bundle.parent
    out_dir = output_dir or target_bundle
    core_files = [
        f for f in target_bundle.glob("*.md") if f.name not in ("index.md", "dead_ends.md", "log.md")
    ]
    annexes_dir = target_bundle / "annexes"
    annex_files = sorted(annexes_dir.glob("*.md")) if annexes_dir.exists() else []
    all_files = core_files + annex_files
    seen_anchors: set[str] = set()
    clauses: list[dict[str, Any]] = []
    qa_list: list[dict[str, Any]] = []
    anchor_pattern = re.compile(r'<a\s+(?:id|name)="([^"]+)"')
    title_prefix = doc_title or target_bundle.name
    for md_path in all_files:
        rel_path = str(md_path.relative_to(target_bundle)).replace("\\", "/")
        content = md_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        in_toc = False
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if "## MỤC LỤC" in stripped:
                in_toc = True
                continue
            if in_toc and stripped.startswith("## ") and "MỤC LỤC" not in stripped:
                in_toc = False
            if in_toc:
                continue
            m_anc = anchor_pattern.search(stripped)
            if m_anc:
                anc_id = m_anc.group(1)
                if anc_id in seen_anchors:
                    continue
                seen_anchors.add(anc_id)
                clean_title = re.sub(r"<[^>]+>", "", stripped).strip("# *").strip()
                if not clean_title and idx < len(lines):
                    clean_title = re.sub(r"<[^>]+>", "", lines[idx]).strip("# *").strip()
                jurisdiction = "CQXD"
                if any(k in anc_id.lower() for k in ["chua-chay", "cuu-nan", "cap-nuoc", "muc-5", "muc-6", "phu-luc-i"]):
                    jurisdiction = "CONG_AN"
                clause_item: dict[str, Any] = {
                    "clause_id": anc_id,
                    "anchor": anc_id,
                    "title": clean_title,
                    "source_file": rel_path,
                    "jurisdiction": jurisdiction,
                    "line_start": idx,
                    "line_end": idx,
                }
                if cong_bao_number:
                    clause_item["cong_bao_number"] = cong_bao_number
                clauses.append(clause_item)
                qa_list.append({
                    "question": f"Quy định tại {clean_title} của {title_prefix} là gì?",
                    "answer": f"Xem chi tiết nội dung quy chuẩn tại {clean_title} ({rel_path}#{anc_id}).",
                    "anchor": anc_id,
                    "source_file": rel_path,
                    "jurisdiction": jurisdiction,
                })
    if out_dir.exists():
        (out_dir / "clauses.json").write_text(json.dumps(clauses, ensure_ascii=False, indent=2), encoding="utf-8")
        (out_dir / "qa_benchmark.json").write_text(json.dumps(qa_list, ensure_ascii=False, indent=2), encoding="utf-8")
    return clauses, qa_list


def generate_clauses_ast(text: str) -> list[dict[str, Any]]:
    """Extract AST clauses list from anchored Markdown text."""
    anchor_pattern = re.compile(r'<a\s+(?:id|name)="([^"]+)"')
    lines = text.splitlines()
    clauses: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, line in enumerate(lines, 1):
        m = anchor_pattern.search(line)
        if m:
            anc_id = m.group(1)
            if anc_id in seen:
                continue
            seen.add(anc_id)
            title = re.sub(r"<[^>]+>", "", line).strip("# *").strip()
            if not title and idx < len(lines):
                for next_line in lines[idx : idx + 3]:
                    clean_next = re.sub(r"<[^>]+>", "", next_line).strip("# *").strip()
                    if clean_next:
                        title = clean_next
                        break
            clauses.append({
                "clause_id": anc_id,
                "anchor": anc_id,
                "title": title,
                "line_start": idx,
                "line_end": idx,
            })
    return clauses


def extract_tables_and_formulas(text: str) -> dict[str, Any]:
    """Extract tables and formula references from text."""
    tables = re.findall(r"###\s*Bảng\s+([A-Z0-9\.\-]+)\s*[-–:]\s*([^\n]+)", text)
    formulas = re.findall(r"\(([A-Z0-9\.\-]+)\)\s*$", text, re.MULTILINE)
    return {
        "tables": [{"table_id": t[0], "title": t[1]} for t in tables],
        "formulas": formulas,
    }
