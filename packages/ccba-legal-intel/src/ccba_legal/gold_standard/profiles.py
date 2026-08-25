"""Document Profiles for Semantic Anchor Injection."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class DocProfile:
    """Document processing profile defining regex patterns for anchor injection & QA generation."""

    name: str
    dieu_pattern: re.Pattern = field(
        default_factory=lambda: re.compile(r"^#*\s*(Điều\s+(\d+)\.?[^\n]*)", re.IGNORECASE)
    )
    khoan_pattern: re.Pattern = field(
        default_factory=lambda: re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)")
    )
    sec_pattern: re.Pattern = field(
        default_factory=lambda: re.compile(
            r"^#*\s*(?:<a[^>]+></a>\s*)?(((?:[A-Z]\.)?\d+(?:\.\d+)*|[A-Z]\.\d+)\s+([^\n]+))"
        )
    )
    section_prefix: str = "muc"


def get_doc_profile(doc_type: str | None = "vbpl") -> DocProfile:
    """Factory to return DocProfile by document type."""
    normalized = (doc_type or "vbpl").lower().strip()
    if "qcvn" in normalized or "tcvn" in normalized:
        return DocProfile(
            name="qcvn",
            dieu_pattern=re.compile(r"^#*\s*(Điều\s+(\d+)\.?[^\n]*)", re.IGNORECASE),
            khoan_pattern=re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)"),
            sec_pattern=re.compile(
                r"^#*\s*(?:<a[^>]+></a>\s*)?(((?:[A-Z]\.)?\d+(?:\.\d+)*|[A-Z]\.\d+)\s+([^\n]+))"
            ),
            section_prefix="muc",
        )
    return DocProfile(
        name="vbpl",
        dieu_pattern=re.compile(r"^#*\s*(Điều\s+(\d+)\.?[^\n]*)", re.IGNORECASE),
        khoan_pattern=re.compile(r"^(?:\*\*(\d+)\.\*\*|(\d+)\.)\s+([^\n]+)"),
        sec_pattern=re.compile(r"^#*\s*((\d+\.\d+(\.\d+)?)\s+([^\n]+))"),
        section_prefix="muc",
    )
