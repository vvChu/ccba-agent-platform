"""base.py - Base abstractions and simulation context for domain mock simulators.

Defines SimulationContext for pre-computed metadata and BaseDomainSimulator protocol.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ..models import EvalItem


@dataclass(frozen=True)
class SimulationContext:
    """Pre-computed context and metadata derived from evaluated content and skill name."""

    content: str
    skill_name: str
    has_legal_grounding: bool
    is_legal_advisory: bool
    has_xml: bool
    has_guardrail: bool
    has_pccc_guardrail: bool
    has_academic_grounding: bool
    has_academic_bibtex: bool
    has_cars_stems: bool
    has_progressive_links: bool

    @classmethod
    def from_content_and_skill(cls, content: str, skill_name: str = "") -> SimulationContext:
        """Builds SimulationContext by pre-computing boolean flags from content and skill_name."""
        has_legal_grounding = bool(
            re.search(r"\b(Nghị định|Thông tư|VBHN)\b|(?<!Kỷ\s)Luật\s", content)
        )
        is_legal_advisory = any(
            k in skill_name for k in ("legal-advisor", "legal-intel", "vbpl-digest", "legal")
        ) and not any(
            k in skill_name
            for k in (
                "copywriting",
                "markdown",
                "pptx",
                "seminar",
                "van-phong",
                "office",
                "design",
                "crawler",
                "vip",
                "ingest",
                "tracker",
                "checklist",
                "hsht",
                "bigbim",
                "coding",
                "gateway",
                "pdf-preprocessor",
                "repair",
                "adr",
                "grill",
                "orchestration",
                "platform",
            )
        )
        has_xml = is_legal_advisory and (
            "<legal_" in content or ("XML" in content and has_legal_grounding)
        )
        has_guardrail = "105/2025" in content or "Hard Floor" in content or "bị thay thế" in content
        has_pccc_guardrail = "QCVN 06" in content and (
            "Map 1" in content or "Bảng H.1" in content or "Quy trình" in content
        )
        has_academic_grounding = "IMRAD" in content or "CARS" in content or "Yale" in content
        has_academic_bibtex = "BibTeX" in content and "APA" in content
        has_cars_stems = "Sentence Stems" in content or "Khung Mẫu CARS 3-Move Chi Tiết" in content
        has_progressive_links = bool(
            re.search(
                r"\[([^\]]+)\]\(([^)]+)\)|progressive disclosure|references/|tham chiếu",
                content,
                re.IGNORECASE,
            )
        )

        return cls(
            content=content,
            skill_name=skill_name,
            has_legal_grounding=has_legal_grounding,
            is_legal_advisory=is_legal_advisory,
            has_xml=has_xml,
            has_guardrail=has_guardrail,
            has_pccc_guardrail=has_pccc_guardrail,
            has_academic_grounding=has_academic_grounding,
            has_academic_bibtex=has_academic_bibtex,
            has_cars_stems=has_cars_stems,
            has_progressive_links=has_progressive_links,
        )

    def wrap_response(self, core_text: str) -> str:
        """Wraps core simulated response with XML context tags and progressive disclosure links if applicable."""
        parts: list[str] = []
        if self.has_xml:
            parts.append(
                "<legal_context>\nPhân tích và đối soát văn bản quy phạm pháp luật theo quy định hiện hành.\n</legal_context>"
            )

        parts.append(core_text)

        if self.has_xml:
            parts.append(
                "<legal_citation>\nTrích dẫn chính xác Điều khoản và thẩm quyền ban hành.\n</legal_citation>"
            )
            parts.append(
                "<compliance_verdict>\nĐạt chuẩn tuân thủ và không có vi phạm rào chắn.\n</compliance_verdict>"
            )

        if self.has_progressive_links:
            parts.append("Tham chiếu chi tiết: [Hướng dẫn thực hiện](references/guide.md).")

        return "\n\n".join(parts)


@runtime_checkable
class BaseDomainSimulator(Protocol):
    """Protocol defining the interface for domain-specific LLM output simulators."""

    archetype_name: str

    def can_handle(self, item: EvalItem, ctx: SimulationContext) -> bool:
        """Determines if this simulator can handle the item via content or prompt anchors (fallback tier)."""
        ...

    def simulate(self, item: EvalItem, ctx: SimulationContext) -> str | None:
        """Simulates grounded LLM output for the item. Returns None if item cannot be simulated by this domain."""
        ...
