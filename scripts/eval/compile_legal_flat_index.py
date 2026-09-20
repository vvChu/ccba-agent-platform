#!/usr/bin/env python3
"""compile_legal_flat_index.py - Autonomous Compiler for Legal Flat Index (ADR-0059).

Extracts statutory metadata, cryptographic SHA-256 signatures, gazette numbers,
cross-statute replacement relations, and statutory keys from ccba-legal-knowledge
into a lightweight flat index packaged directly within ccba-harness for CI parity.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("compile_legal_flat_index")

DEFAULT_KNOWLEDGE_DIR = Path("/home/vvc/ccba/ccba-legal-knowledge")
DEFAULT_OUTPUT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "packages"
    / "ccba-harness"
    / "src"
    / "ccba_harness"
    / "evals"
    / "datasets"
    / "legal_clauses_flat.json"
)

# Canonical replacement mappings for known statutory anti-traps
KNOWN_REPLACEMENTS: dict[str, str] = {
    "136/2020/NĐ-CP": "105/2025/NĐ-CP",
    "136/2020": "105/2025/NĐ-CP",
    "06:2020/BXD": "QCVN 06:2022/BXD",
    "QCVN 06:2020/BXD": "QCVN 06:2022/BXD",
    "06:2020": "QCVN 06:2022/BXD",
    "149/2020/TT-BCA": "105/2025/NĐ-CP",
    "50/2014/QH13": "135/2025/QH15",
    "50/2014": "135/2025/QH15",
    "175/2024/NĐ-CP": "217/2026/NĐ-CP",
    "175/2024": "217/2026/NĐ-CP",
    "15/2021/NĐ-CP": "217/2026/NĐ-CP",
    "15/2021": "217/2026/NĐ-CP",
}


def compile_flat_index(
    knowledge_dir: Path,
    output_file: Path,
    compact: bool = True,
) -> dict[str, Any]:
    """Compiles all legal bundles into a standalone flat index."""
    legal_docs_dir = knowledge_dir / "legal_docs"
    registry_file = knowledge_dir / "legal_registry.yaml"

    if not legal_docs_dir.exists():
        raise FileNotFoundError(f"Missing legal_docs directory at: {legal_docs_dir}")

    replaces_map = dict(KNOWN_REPLACEMENTS)
    if registry_file.exists():
        with open(registry_file, encoding="utf-8") as f:
            reg_meta = yaml.safe_load(f) or {}

        for group in ["laws", "standards"]:
            for doc_entry in reg_meta.get(group, []):
                doc_num = doc_entry.get("document_number")
                rels = doc_entry.get("relations", {}) or {}
                rep = rels.get("replaces")
                if rep and doc_num:
                    if isinstance(rep, list):
                        for r in rep:
                            replaces_map[str(r).strip()] = str(doc_num).strip()
                    else:
                        replaces_map[str(rep).strip()] = str(doc_num).strip()

    documents: dict[str, Any] = {}
    total_keys = 0

    for clause_file in sorted(legal_docs_dir.glob("**/clauses.json")):
        if "sources" in str(clause_file):
            continue

        bundle_dir = clause_file.parent
        meta_path = bundle_dir / "metadata.yaml"
        meta: dict[str, Any] = {}
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = yaml.safe_load(f) or {}

        doc_num = meta.get("document_number") or bundle_dir.name
        with open(clause_file, encoding="utf-8") as f:
            raw_clauses = json.load(f)

        keys: set[str] = set()
        for c in raw_clauses:
            cid = c.get("clause_id") or c.get("anchor", "")
            title = c.get("title", "").strip()
            if cid:
                keys.add(cid.lower())
            m = re.match(
                r"^(Điều\s+\d+|Mục\s+[\d\.]+|\d+\.[\d\.]+|Bảng\s+[A-Za-z0-9\.]+|Phụ\s+lục\s+[A-Za-z0-9\.]+)",
                title,
                re.IGNORECASE,
            )
            if m:
                keys.add(m.group(1).strip().lower())

        total_keys += len(keys)
        doc_id = meta.get("id", bundle_dir.name)
        documents[doc_num] = {
            "id": doc_id,
            "document_number": doc_num,
            "title": meta.get("title", ""),
            "status": meta.get("status", "active"),
            "effective_date": str(meta.get("effective_date", "")),
            "cong_bao_number": meta.get("cong_bao_number", ""),
            "pdf_sha256": meta.get("pdf_sha256", ""),
            "statutory_keys": sorted(keys),
        }

    # Include Decree 30/2020/ND-CP (Clerical work & official document formatting)
    if "30/2020/NĐ-CP" not in documents:
        nd30_keys: list[str] = []
        for i in range(1, 39):
            nd30_keys.extend([f"dieu-{i}", f"điều {i}"])
        for pl in ["i", "ii", "iii", "iv", "v", "vi"]:
            nd30_keys.extend([f"phu-luc-{pl}", f"phụ lục {pl}"])
        documents["30/2020/NĐ-CP"] = {
            "id": "nghi_dinh_30_2020_nd_cp",
            "document_number": "30/2020/NĐ-CP",
            "title": "Nghị định 30/2020/NĐ-CP về công tác văn thư",
            "status": "active",
            "effective_date": "2020-03-05",
            "cong_bao_number": "265+266",
            "pdf_sha256": "b0b2e8a7c1e56b4618e4726f5872957bcf61245841029daff9da53e20e89e023",
            "statutory_keys": sorted(nd30_keys),
        }
        total_keys += len(nd30_keys)

    flat_index: dict[str, Any] = {
        "schema_version": "1.0.0",
        "standard": "ADR-0059-Legal-Verbatim-Grounding",
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "total_documents": len(documents),
        "total_statutory_keys": total_keys,
        "replaces_map": replaces_map,
        "documents": documents,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        if compact:
            json.dump(flat_index, f, ensure_ascii=False, separators=(",", ":"))
        else:
            json.dump(flat_index, f, ensure_ascii=False, indent=2)

    size_kb = output_file.stat().st_size / 1024
    logger.info(
        f"✅ Biên dịch thành công {output_file} ({size_kb:.1f} KB): "
        f"{len(documents)} văn bản, {total_keys:,} statutory keys, {len(replaces_map)} replaces mappings."
    )
    return flat_index


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile legal flat index (ADR-0059)")
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=DEFAULT_KNOWLEDGE_DIR,
        help="Path to ccba-legal-knowledge spoke root",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Path to output legal_clauses_flat.json file",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write indented JSON instead of compact JSON",
    )
    args = parser.parse_args()

    compile_flat_index(
        knowledge_dir=args.knowledge_dir,
        output_file=args.output,
        compact=not args.pretty,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
