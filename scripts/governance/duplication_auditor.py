"""Duplication Auditor for CCBA Agent Platform.

Enforces Zero-Duplication SSOT Architecture on Hub by automatically detecting
forbidden Spoke domain files and directories (legal docs, governance constitutions,
and raw scraped law corpora).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts.governance.base import AuditIssue, BaseAuditor

# Directory paths that exclusively belong to Spokes and must NOT exist on Hub
FORBIDDEN_DIRECTORIES: dict[str, dict[str, str]] = {
    ".md/legal_docs": {
        "owner_spoke": "ccba-legal-knowledge",
        "pointer_syntax": "[legal_knowledge_path]/legal_docs/",
        "catalog_group": "legal_knowledge_kb",
        "description": "Văn bản pháp luật, QCVN, TCVN và phụ lục biểu mẫu",
    },
    ".md/governance_constitution": {
        "owner_spoke": "idop-ccba-way",
        "pointer_syntax": "[idop_path]/.md/governance_constitution/",
        "catalog_group": "ccba_operations_kb",
        "description": "Văn bản quy chế thể chế vận hành CCBA (QCTK 2815, QCCTNB 3209)",
    },
    ".md/system_blueprint": {
        "owner_spoke": "idop-ccba-way",
        "pointer_syntax": "[idop_path]/.md/system_blueprint/",
        "catalog_group": "ccba_operations_kb",
        "description": "Sơ đồ kiến trúc và danh mục Lists hệ thống IDOP",
    },
    "specs/modules": {
        "owner_spoke": "idop-ccba-way (hoặc Spoke chuyên biệt)",
        "pointer_syntax": "[idop_path]/specs/modules/",
        "catalog_group": "ccba_operations_kb",
        "description": "Đặc tả kỹ thuật Specs 21 Modules chi tiết",
    },
}

# Regex patterns for raw scraped law text files that should not clutter Hub
FORBIDDEN_RAW_SCRAPE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(luat|nghi_dinh|thong_tu|quyet_dinh|qcvn|tcvn)_.+\.txt$", re.IGNORECASE),
    re.compile(r"^(decree|circular)_.+\.txt$", re.IGNORECASE),
    re.compile(r"^thu_vien_phap_luat_.+\.txt$", re.IGNORECASE),
]


class DuplicationAuditor(BaseAuditor):
    """Sub-auditor detecting duplicate Spoke data on Hub."""

    def __init__(self, project_root: Path | str | None = None) -> None:
        """Initialize DuplicationAuditor with project root."""
        if project_root is None:
            project_root = Path(__file__).resolve().parent.parent.parent
        self.project_root = Path(project_root).resolve()

    def audit(self, target: Any = None) -> list[AuditIssue]:
        """Audit workspace for forbidden Spoke-exclusive duplicate files."""
        issues: list[AuditIssue] = []

        # 1. Check for Forbidden Directories on Hub
        for dir_rel, meta in FORBIDDEN_DIRECTORIES.items():
            dir_path = self.project_root / dir_rel
            if dir_path.exists():
                owner = meta["owner_spoke"]
                ptr = meta["pointer_syntax"]
                grp = meta["catalog_group"]
                desc = meta["description"]

                issues.append(
                    AuditIssue(
                        line_number=0,
                        subject="Zero-Duplication Violation",
                        message=(
                            f"Phát hiện thư mục vi phạm nguyên tắc SSOT: '{dir_rel}' ({desc}).\n"
                            f"   • Dữ liệu này thuộc về Spoke: '{owner}'.\n"
                            f"   • Vui lòng KHÔNG lưu trực tiếp trên Hub. Hãy sử dụng con trỏ động:\n"
                            f"     knowledge_path: '{ptr}' (nhóm '{grp}') trong catalog.yaml."
                        ),
                        category="anti_duplication",
                        file_path=str(dir_rel),
                    )
                )

        # 2. Check for Raw Scraped Law Texts in .md/extracted_docs/
        extracted_dir = self.project_root / ".md" / "extracted_docs"
        if extracted_dir.exists():
            for file_path in extracted_dir.glob("*.txt"):
                file_name = file_path.name
                for pattern in FORBIDDEN_RAW_SCRAPE_PATTERNS:
                    if pattern.match(file_name):
                        issues.append(
                            AuditIssue(
                                line_number=0,
                                subject="Raw Scraped Law Text on Hub",
                                message=(
                                    f"Phát hiện tệp cào thô văn bản pháp luật '{file_name}' trên Hub.\n"
                                    "   • Văn bản pháp luật đã được chuẩn hóa OKF v2.0 tại Spoke 'ccba-legal-knowledge'.\n"
                                    "   • Vui lòng xóa tệp thô này khỏi Hub và sử dụng con trỏ [legal_knowledge_path]."
                                ),
                                category="anti_duplication",
                                file_path=f".md/extracted_docs/{file_name}",
                            )
                        )
                        break

        return issues
