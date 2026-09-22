"""AST Clause and Ground Truth QA Benchmark Generator."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _clean_markdown_syntax(text: str) -> str:
    """Remove markdown bold/italic syntax (** and __), HTML tags, and excessive markers."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"^[#\s]+", "", text)
    return text.strip(" *_\t\r\n")


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
    meta_file = target_bundle / "metadata.yaml"
    if meta_file.exists() and (not cong_bao_number or not doc_title):
        try:
            import yaml

            m_data = yaml.safe_load(meta_file.read_text(encoding="utf-8"))
            if isinstance(m_data, dict):
                if not cong_bao_number and m_data.get("cong_bao_number"):
                    cong_bao_number = m_data["cong_bao_number"]
                if not doc_title and m_data.get("title"):
                    doc_title = m_data["title"]
        except Exception:
            pass
    core_files = [
        f
        for f in target_bundle.glob("*.md")
        if f.name not in ("index.md", "dead_ends.md", "log.md")
    ]
    annexes_dir = target_bundle / "annexes"
    annex_files = sorted(annexes_dir.glob("*.md")) if annexes_dir.exists() else []
    all_files = core_files + annex_files
    seen_anchors: set[str] = set()
    clauses: list[dict[str, Any]] = []
    qa_list: list[dict[str, Any]] = []
    anchor_pattern = re.compile(r'<a\s+(?:id|name)="([^"]+)"')
    title_prefix = doc_title or target_bundle.name
    clean_prefix = _clean_markdown_syntax(title_prefix)

    for md_path in all_files:
        rel_path = str(md_path.relative_to(target_bundle)).replace("\\", "/")
        content = md_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        num_lines = len(lines)
        in_toc = False

        file_anchors: list[tuple[int, str, str]] = []
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
                file_anchors.append((idx, anc_id, stripped))

        for idx, anc_id, stripped in file_anchors:
            line_end = num_lines
            for next_idx in range(idx + 1, num_lines + 1):
                cur_line = lines[next_idx - 1].strip()
                if anchor_pattern.search(cur_line):
                    line_end = next_idx - 1
                    break
                if next_idx > idx + 1 and (cur_line.startswith("# ") or cur_line.startswith("## ")):
                    line_end = next_idx - 1
                    break

            while line_end > idx and not lines[line_end - 1].strip():
                line_end -= 1

            clean_title = _clean_markdown_syntax(stripped)
            if not clean_title:
                for lookahead in range(idx, min(idx + 5, num_lines)):
                    candidate = lines[lookahead].strip()
                    if anchor_pattern.search(candidate):
                        break
                    candidate_clean = _clean_markdown_syntax(candidate)
                    if candidate_clean:
                        clean_title = candidate_clean
                        break
            if not clean_title:
                clean_title = anc_id

            jurisdiction = "CQXD"
            if any(
                k in anc_id.lower()
                for k in ["chua-chay", "cuu-nan", "cap-nuoc", "muc-5", "muc-6", "phu-luc-i"]
            ):
                jurisdiction = "CONG_AN"

            clause_item: dict[str, Any] = {
                "clause_id": anc_id,
                "anchor": anc_id,
                "title": clean_title,
                "source_file": rel_path,
                "jurisdiction": jurisdiction,
                "line_start": idx,
                "line_end": line_end,
            }
            if cong_bao_number:
                clause_item["cong_bao_number"] = cong_bao_number
            clauses.append(clause_item)
            qa_list.append(
                {
                    "question": f"Quy định tại {clean_title} của {clean_prefix} là gì?",
                    "answer": f"Xem chi tiết nội dung quy chuẩn tại {clean_title} ({rel_path}#{anc_id}).",
                    "anchor": anc_id,
                    "source_file": rel_path,
                    "jurisdiction": jurisdiction,
                }
            )

    if out_dir.exists():
        (out_dir / "clauses.json").write_text(
            json.dumps(clauses, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / "qa_benchmark.json").write_text(
            json.dumps(qa_list, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    return clauses, qa_list


def generate_clauses_ast(text: str) -> list[dict[str, Any]]:
    """Extract AST clauses list from anchored Markdown text."""
    anchor_pattern = re.compile(r'<a\s+(?:id|name)="([^"]+)"')
    lines = text.splitlines()
    num_lines = len(lines)
    clauses: list[dict[str, Any]] = []
    seen: set[str] = set()
    file_anchors: list[tuple[int, str, str]] = []
    for idx, line in enumerate(lines, 1):
        m = anchor_pattern.search(line)
        if m:
            anc_id = m.group(1)
            if anc_id in seen:
                continue
            seen.add(anc_id)
            file_anchors.append((idx, anc_id, line.strip()))

    for idx, anc_id, stripped in file_anchors:
        line_end = num_lines
        for next_idx in range(idx + 1, num_lines + 1):
            cur_line = lines[next_idx - 1].strip()
            if anchor_pattern.search(cur_line):
                line_end = next_idx - 1
                break
            if next_idx > idx + 1 and (cur_line.startswith("# ") or cur_line.startswith("## ")):
                line_end = next_idx - 1
                break

        while line_end > idx and not lines[line_end - 1].strip():
            line_end -= 1

        title = _clean_markdown_syntax(stripped)
        if not title:
            for lookahead in range(idx, min(idx + 5, num_lines)):
                candidate = lines[lookahead].strip()
                if anchor_pattern.search(candidate):
                    break
                candidate_clean = _clean_markdown_syntax(candidate)
                if candidate_clean:
                    title = candidate_clean
                    break
        if not title:
            title = anc_id

        clauses.append(
            {
                "clause_id": anc_id,
                "anchor": anc_id,
                "title": title,
                "line_start": idx,
                "line_end": line_end,
            }
        )
    return clauses


def extract_tables_and_formulas(text: str) -> dict[str, Any]:
    """Extract tables and formula references from text."""
    tables = re.findall(r"###\s*Bảng\s+([A-Z0-9\.\-]+)\s*[-–:]\s*([^\n]+)", text)
    formulas = re.findall(r"\(([A-Z0-9\.\-]+)\)\s*$", text, re.MULTILINE)
    return {
        "tables": [{"table_id": t[0], "title": t[1]} for t in tables],
        "formulas": formulas,
    }
