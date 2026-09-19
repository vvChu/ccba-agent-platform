"""models.py - Canonical AST & Patch Action Data Models for Legal Intelligence.

Created by CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LegalDocStatus(str, Enum):
    """Canonical lifecycle validity status for legal documents (ADR 0050)."""

    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    PARTIALLY_AMENDED = "PARTIALLY_AMENDED"
    PENDING_EFFECTIVE = "PENDING_EFFECTIVE"
    DRAFT = "DRAFT"
    UNVERIFIED = "UNVERIFIED"


def normalize_doc_status(raw_status: str | None) -> LegalDocStatus:
    """Normalize raw/legacy status string into canonical LegalDocStatus enum.

    Handles legacy string values like 'current', 'enacted', 'superseded', 'expired', 'draft'.
    """
    if not raw_status:
        return LegalDocStatus.ACTIVE

    s = raw_status.strip().upper()
    if s in {"ACTIVE", "CURRENT", "ENACTED", "IN_FORCE", "VALID", "HIỆU LỰC", "HIEU_LUC"}:
        return LegalDocStatus.ACTIVE
    if s in {"SUPERSEDED", "EXPIRED", "REPEALED", "ABROGATED", "HẾT HIỆU LỰC", "HET_HIEU_LUC"}:
        return LegalDocStatus.SUPERSEDED
    if s in {"PARTIALLY_AMENDED", "AMENDED", "SỬA ĐỔI BỔ SUNG", "SUA_DOI"}:
        return LegalDocStatus.PARTIALLY_AMENDED
    if s in {"PENDING_EFFECTIVE", "PENDING", "NOT_YET_IN_FORCE", "CHƯA HIỆU LỰC"}:
        return LegalDocStatus.PENDING_EFFECTIVE
    if s in {"DRAFT", "DỰ THẢO", "DU_THAO"}:
        return LegalDocStatus.DRAFT
    if s in {"UNVERIFIED", "UNKNOWN", "CHƯA XÁC MINH", "CHUA_XAC_MINH"}:
        return LegalDocStatus.UNVERIFIED

    return LegalDocStatus.ACTIVE


@dataclass
class LegalLifecycleInfo:
    """Encapsulates document lifecycle status, validity dates, relationships and warnings (ADR 0050)."""

    doc_id: str
    document_number: str = ""
    title: str = ""
    short_name: str = ""
    status: LegalDocStatus = LegalDocStatus.ACTIVE
    effective_date: str | None = None
    superseded_date: str | None = None
    supersedes: list[str] = field(default_factory=list)
    superseded_by: str | None = None
    amended_by: list[str] = field(default_factory=list)
    guiding_docs: list[str] = field(default_factory=list)
    territory: str = "VN"
    hierarchy_level: str = "national"
    temporal_context: dict[str, Any] | None = None
    successor_entity: str | None = None
    warning: str | None = None
    suggested_replacement: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        res: dict[str, Any] = {
            "doc_id": self.doc_id,
            "document_number": self.document_number,
            "title": self.title,
            "short_name": self.short_name,
            "status": self.status.value,
            "territory": self.territory,
            "hierarchy_level": self.hierarchy_level,
        }
        if self.effective_date:
            res["effective_date"] = self.effective_date
        if self.superseded_date:
            res["superseded_date"] = self.superseded_date
        if self.supersedes:
            res["supersedes"] = self.supersedes
        if self.superseded_by:
            res["superseded_by"] = self.superseded_by
        if self.amended_by:
            res["amended_by"] = self.amended_by
        if self.guiding_docs:
            res["guiding_docs"] = self.guiding_docs
        if self.temporal_context:
            res["temporal_context"] = self.temporal_context
        if self.successor_entity:
            res["successor_entity"] = self.successor_entity
        res["warning"] = self.warning
        res["suggested_replacement"] = self.suggested_replacement
        return res


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
    "LegalDocStatus",
    "LegalLifecycleInfo",
    "normalize_doc_status",
    "PatchAction",
    "ASTNode",
]
