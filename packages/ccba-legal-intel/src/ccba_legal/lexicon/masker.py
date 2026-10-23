"""Immutable Span Masker for CCILF (ADR-0059, COND-15).

Protects statutory citations, verbatim legal quotes, registered entity brands,
and markdown formatting spans before terminology normalization or NLP replacement.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProtectedSpan:
    """Represents a protected textual interval."""

    start: int
    end: int
    text: str
    span_type: str


class ImmutableSpanMasker:
    """Masks and unmasks immutable statutory citations, quotes, and entity brands."""

    _LAW_NAMES = (
        r"(?:Xây dựng|Đấu thầu|Đất đai|Nhà ở|PCCC(?: và CNCH)?|Kinh doanh bất động sản|"
        r"[A-Z0-9_-]+)"
    )

    _ARTICLE_CLAUSE = (
        r"(?:(?:Điều\s+\d+[a-zđ]?(?:\s+Khoản\s+\d+[a-zđ]?)?)|"
        r"(?:Khoản\s+\d+[a-zđ]?(?:\s+Điều\s+\d+[a-zđ]?)?)|"
        r"(?:Điểm\s+[a-zđ](?:\s+Khoản\s+\d+[a-zđ]?)?(?:\s+Điều\s+\d+[a-zđ]?)?))"
    )

    CITATION_PATTERN = re.compile(
        rf"\b{_ARTICLE_CLAUSE}"
        rf"(?:\s+(?:của\s+)?(?:Luật|Nghị định|Thông tư|Quyết định|QCVN|TCVN)\s+{_LAW_NAMES}(?:\s+(?:năm\s+)?\d{{4}}|\s+số\s+[\w/:-]+)?)?",
        re.IGNORECASE,
    )
    STANDARDS_PATTERN = re.compile(
        r"\b(?:QCVN|TCVN)\s*[\w:./-]+",
        re.IGNORECASE,
    )
    LEGAL_ACT_PATTERN = re.compile(
        r"\b(?:Luật|Nghị định|Thông tư|Quyết định)\s+(?:số\s+)?\d+[\w/:-]+",
        re.IGNORECASE,
    )
    QUOTED_TEXT_PATTERN = re.compile(
        r'(?:"[^"\n]+"|“[^”\n]+”|«[^»\n]+»)',
    )
    CODE_SPAN_PATTERN = re.compile(
        r"(?:```[\s\S]*?```|`[^`\n]+`)",
    )
    MARKDOWN_LINK_PATTERN = re.compile(
        r"!?\[[^\]]*\]\([^)]+\)",
    )
    BRAND_ENTITY_PATTERN = re.compile(
        r"\b(?:IBST\s*-\s*CCBA|IDOP-CCBA-WAY|CCBA-WAY)\b",
        re.IGNORECASE,
    )

    def __init__(self, placeholder_prefix: str = "__CCBA_MASK_SPAN_") -> None:
        """Initializes masker with configurable placeholder prefix."""
        self.placeholder_prefix = placeholder_prefix

    def _collect_candidate_spans(self, text: str) -> list[ProtectedSpan]:
        """Collects all candidate protected spans from text."""
        candidates: list[ProtectedSpan] = []

        patterns: list[tuple[re.Pattern[str], str]] = [
            (self.CODE_SPAN_PATTERN, "code"),
            (self.MARKDOWN_LINK_PATTERN, "link"),
            (self.CITATION_PATTERN, "citation"),
            (self.STANDARDS_PATTERN, "standard"),
            (self.LEGAL_ACT_PATTERN, "legal_act"),
            (self.QUOTED_TEXT_PATTERN, "quote"),
            (self.BRAND_ENTITY_PATTERN, "brand"),
        ]

        for pattern, span_type in patterns:
            for match in pattern.finditer(text):
                candidates.append(
                    ProtectedSpan(
                        start=match.start(),
                        end=match.end(),
                        text=match.group(0),
                        span_type=span_type,
                    )
                )

        return candidates

    def _resolve_non_overlapping_spans(
        self, candidates: list[ProtectedSpan]
    ) -> list[ProtectedSpan]:
        """Resolves overlapping candidates by preferring earlier and longer spans."""
        # Sort by start asc, length desc
        sorted_candidates = sorted(candidates, key=lambda s: (s.start, -(s.end - s.start)))
        non_overlapping: list[ProtectedSpan] = []
        last_end = 0

        for span in sorted_candidates:
            if span.start >= last_end:
                non_overlapping.append(span)
                last_end = span.end

        return non_overlapping

    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        """Masks protected spans and returns masked text with span registry.

        Args:
            text: Input text containing potential protected citations and entities.

        Returns:
            Tuple of (masked_text, span_registry) where span_registry maps
            placeholder token to original raw span.
        """
        candidates = self._collect_candidate_spans(text)
        spans = self._resolve_non_overlapping_spans(candidates)

        if not spans:
            return text, {}

        span_registry: dict[str, str] = {}
        masked_chunks: list[str] = []
        curr_idx = 0

        for idx, span in enumerate(spans):
            placeholder = f"{self.placeholder_prefix}{idx}__"
            masked_chunks.append(text[curr_idx : span.start])
            masked_chunks.append(placeholder)
            span_registry[placeholder] = span.text
            curr_idx = span.end

        masked_chunks.append(text[curr_idx:])
        return "".join(masked_chunks), span_registry

    def unmask(self, text: str, span_registry: dict[str, str]) -> str:
        """Restores original spans from placeholders in masked text.

        Args:
            text: Masked text with placeholders.
            span_registry: Mapping of placeholder to original raw span.

        Returns:
            Restored text with original verbatim citations and quotes.
        """
        if not span_registry:
            return text

        pattern = re.compile(re.escape(self.placeholder_prefix) + r"\d+__")
        return pattern.sub(lambda m: span_registry.get(m.group(0), m.group(0)), text)
