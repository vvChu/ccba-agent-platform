"""Document Archetype Scanner for Vietnamese Legal and Technical Documents."""

from __future__ import annotations

import re
from enum import Enum
from pathlib import Path


class DocumentArchetype(str, Enum):
    """Document Archetypes in Vietnamese Construction Legal & Technical Repository."""
    VBPL_ADMIN = "VBPL_ADMIN"                     # Luật, Nghị định, Quyết định TTg
    CIRCULAR_COST_NORM = "CIRCULAR_COST_NORM"     # Thông tư Định mức, Đơn giá, Suất vốn
    TECHNICAL_QCVN = "TECHNICAL_QCVN"             # Quy chuẩn kỹ thuật quốc gia
    TECHNICAL_TCVN = "TECHNICAL_TCVN"             # Tiêu chuẩn quốc gia / cơ sở
    INTERNATIONAL_ISO = "INTERNATIONAL_ISO"       # Tiêu chuẩn quốc tế (ISO, BS EN)


class FullDocStructuralScanner:
    """Performs deep full-document structural skimming to detect document archetype."""

    def __init__(self, docx_path: Path, doc_num_str: str = "", doc_type_str: str = "") -> None:
        self.docx_path = docx_path
        self.doc_num = doc_num_str.upper()
        self.doc_type = doc_type_str.upper()

    def scan(self) -> DocumentArchetype:
        """Scan 100% of document elements and return detected Archetype."""
        # 1. Fast path by doc number / doc type
        if "QCVN" in self.doc_num or "QUY CHUẨN" in self.doc_type:
            return DocumentArchetype.TECHNICAL_QCVN
        if "TCVN" in self.doc_num or "TIÊU CHUẨN" in self.doc_type or "TCCS" in self.doc_num:
            return DocumentArchetype.TECHNICAL_TCVN
        if "ISO" in self.doc_num or "BS" in self.doc_num:
            return DocumentArchetype.INTERNATIONAL_ISO

        # 2. Deep XML traversal scan
        try:
            from docx import Document
            doc = Document(str(self.docx_path))
        except Exception:
            return DocumentArchetype.VBPL_ADMIN

        total_p = len(doc.paragraphs)
        decimal_sec_count = 0
        admin_article_count = 0
        norm_code_count = 0

        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            if re.match(r"^([1-9]\.[0-9]+(?:\.[0-9]+)*)\s+", text):
                decimal_sec_count += 1
            if re.match(r"^(?:Điều\s+\d+|Chương\s+[IVXLCDM\d]+)", text, re.IGNORECASE):
                admin_article_count += 1
            if re.search(r"[A-Z]{2}\.\d{5}", text):
                norm_code_count += 1

        if norm_code_count >= 5:
            return DocumentArchetype.CIRCULAR_COST_NORM

        if decimal_sec_count > admin_article_count and decimal_sec_count >= 10:
            if "QCVN" in self.doc_num:
                return DocumentArchetype.TECHNICAL_QCVN
            return DocumentArchetype.TECHNICAL_TCVN

        return DocumentArchetype.VBPL_ADMIN


def detect_document_pipeline(
    target_bundle_dir: Path,
    doc_type: str | None = None,
    registry_file: Path | None = None,
) -> str:
    """Determine document pipeline type."""
    scanner = FullDocStructuralScanner(
        docx_path=target_bundle_dir,
        doc_num_str=target_bundle_dir.name,
        doc_type_str=doc_type or "",
    )
    arch = scanner.scan()
    return "qcvn" if arch in (DocumentArchetype.TECHNICAL_TCVN, DocumentArchetype.TECHNICAL_QCVN) else "vbpl"
