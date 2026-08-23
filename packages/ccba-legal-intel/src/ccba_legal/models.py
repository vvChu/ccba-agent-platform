"""models.py - Canonical AST & Patch Action Data Models for Legal Intelligence.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PatchAction(str, Enum):
    """Canonical actions applicable to AST nodes during patching adhering to OKF v2.0."""

    REPLACE = "REPLACE"
    INSERT_AFTER = "INSERT_AFTER"
    INSERT_BEFORE = "INSERT_BEFORE"
    APPEND = "APPEND"
    INSERT_RANGE_AFTER = "INSERT_RANGE_AFTER"
    REPEAL = "REPEAL"
    ABROGATE = "ABROGATE"  # Backward-compatible alias for REPEAL
    SUSPEND = "SUSPEND"
    SUBSTITUTE_PHRASE = "SUBSTITUTE_PHRASE"


@dataclass
class ASTNode:
    """Canonical Abstract Syntax Tree node for structured legal documents (OKF v2.0)."""

    node_id: str
    node_type: str  # "chapter", "section", "clause", "article", "point", "table", "appendix", "header_block"
    title: str = ""
    content: str = ""
    clause_number: str = ""
    anchor: str = ""
    parent_id: str | None = None
    children: list[ASTNode] = field(default_factory=list)
    heading_level: int = 3
    heading_prefix: str = "###"
    raw_header_line: str = ""

    # Metadata fields conforming to OKF v2.0
    jurisdiction: str | None = "CQXD"
    grace_period_end: str | None = None
    source_pdf_page: int | None = None
    cong_bao_number: str | None = None
    compliance_severity: str = "CRITICAL_DEFECT"
    normative_status: str = "MANDATORY"
    legal_enforceability: str = "DIRECTLY_ENFORCEABLE"
    citation: str | None = None
    is_amended: bool = False
    is_repealed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert ASTNode to dictionary representation."""
        res: dict[str, Any] = {
            "node_id": self.node_id,
            "node_type": self.node_type,
            "title": self.title,
            "clause_number": self.clause_number,
            "anchor": self.anchor or self.node_id,
            "content": self.content,
            "parent_id": self.parent_id,
            "jurisdiction": self.jurisdiction or "CQXD",
            "compliance_severity": self.compliance_severity,
            "normative_status": self.normative_status,
            "legal_enforceability": self.legal_enforceability,
            "children": [c.to_dict() for c in self.children],
        }
        if self.grace_period_end:
            res["grace_period_end"] = self.grace_period_end
        if self.source_pdf_page:
            res["source_pdf_page"] = self.source_pdf_page
        if self.cong_bao_number:
            res["cong_bao_number"] = self.cong_bao_number
        return res

    def to_clause_dict(self) -> dict[str, Any]:
        """Convert to atomic clauses.json schema entry."""
        cid = self.anchor or self.node_id
        res: dict[str, Any] = {
            "id": cid,
            "clause_number": self.clause_number or (self.title.split()[0] if self.title else ""),
            "title": self.title,
            "content": self.content,
            "jurisdiction": self.jurisdiction or "CQXD",
            "compliance_severity": self.compliance_severity,
            "normative_status": self.normative_status,
            "legal_enforceability": self.legal_enforceability,
            "clause_id": cid,
            "anchor": cid,
        }
        if self.grace_period_end:
            res["grace_period_end"] = self.grace_period_end
        if self.source_pdf_page:
            res["source_pdf_page"] = self.source_pdf_page
        if self.cong_bao_number:
            res["cong_bao_number"] = self.cong_bao_number
        return res


__all__ = [
    "PatchAction",
    "ASTNode",
]
