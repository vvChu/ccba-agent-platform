"""GoldStandardProcessor Facade Class."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import yaml

from ccba_legal.gold_standard.anchor_injector import inject_semantic_anchors
from ccba_legal.gold_standard.ast_qa_generator import generate_bundle_ast_and_qa
from ccba_legal.gold_standard.profiles import get_doc_profile
from ccba_legal.gold_standard.sanitizers import normalize_notes_and_lists


class GoldStandardProcessor:
    """High-level Facade for OKF v2.2 Gold Standard document processing."""

    @staticmethod
    def process_bundle(bundle_dir: Path, doc_type: str | None = None) -> dict[str, Any]:
        """Process an OKF bundle directory to meet Gold Standard OKF v2.2."""
        if not bundle_dir.exists() or not bundle_dir.is_dir():
            return {
                "status": "error",
                "message": f"Bundle dir {bundle_dir} does not exist.",
            }

        core_files = [
            f for f in bundle_dir.glob("*.md")
            if f.name not in ("index.md", "dead_ends.md", "log.md")
        ]
        annexes_dir = bundle_dir / "annexes"
        annex_files = sorted(annexes_dir.glob("*.md")) if annexes_dir.exists() else []

        profile = get_doc_profile(doc_type)
        for md_path in core_files + annex_files:
            raw_text = md_path.read_text(encoding="utf-8")
            norm_text = normalize_notes_and_lists(raw_text)
            if '<a id="' not in norm_text:
                norm_text = inject_semantic_anchors(norm_text, profile)
            if norm_text != raw_text:
                md_path.write_text(norm_text, encoding="utf-8")

        meta_path = bundle_dir / "metadata.yaml"
        doc_title = bundle_dir.name
        cong_bao_num = None
        if meta_path.exists():
            try:
                with open(meta_path, encoding="utf-8") as f:
                    meta = yaml.safe_load(f)
                    if isinstance(meta, dict):
                        if meta.get("title"):
                            doc_title = meta["title"].split("—")[0].strip()
                        cong_bao_num = meta.get("cong_bao_number") or (
                            meta.get("pdf_source", {}).get("cong_bao")
                            if isinstance(meta.get("pdf_source"), dict)
                            else None
                        )
            except Exception:
                pass

        clauses, qa_benchmark = generate_bundle_ast_and_qa(
            bundle_dir, doc_title=doc_title, cong_bao_number=cong_bao_num
        )

        clauses_file = bundle_dir / "clauses.json"
        clauses_file.write_text(json.dumps(clauses, ensure_ascii=False, indent=2), encoding="utf-8")

        qa_file = bundle_dir / "qa_benchmark.json"
        qa_file.write_text(json.dumps(qa_benchmark, ensure_ascii=False, indent=2), encoding="utf-8")

        return {
            "status": "success",
            "bundle": bundle_dir.name,
            "clauses_count": len(clauses),
            "qa_count": len(qa_benchmark),
        }


def process_okf_bundle(bundle_dir: Path, doc_type: str | None = None) -> dict[str, Any]:
    """Compatibility wrapper for GoldStandardProcessor.process_bundle."""
    return GoldStandardProcessor.process_bundle(bundle_dir, doc_type=doc_type)
