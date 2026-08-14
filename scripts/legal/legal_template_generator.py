"""Thin CLI Delegate for Decree 30/2020/NĐ-CP Legal Document Generation.

Delegates document generation logic to the deep seam in ``ccba_legal.templates``.
Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

import sys
from typing import Any

from ccba_legal.templates import (
    ND30_HEADER,
    SUPPORTED_DOC_TYPES,
    generate_legal_document,
)

__all__ = [
    "generate_legal_document",
    "SUPPORTED_DOC_TYPES",
    "ND30_HEADER",
    "main",
]


def main() -> None:
    """CLI test entry point for legal document templates."""
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    sample_data: dict[str, Any] = {
        "project_name": "Dự án Thí Điểm CCBA Office",
        "subject": "Tư vấn Tuân thủ Quy chuẩn PCCC",
        "advisory_content": "Căn cứ quy định tại [NĐ 105/2025/NĐ-CP], công trình đáp ứng tiêu chuẩn an toàn.",
        "retrieved_docs": [{"short_name": "NĐ 105/2025", "document_number": "105/2025/NĐ-CP"}],
        "author": "Đội ngũ Pháp lý CCBA",
    }

    doc = generate_legal_document("compliance_report", sample_data)
    print("=== MẪU BÁO CÁO NĐ 30/2020/NĐ-CP ===")
    print(doc)


if __name__ == "__main__":
    main()
