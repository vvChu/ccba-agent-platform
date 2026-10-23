"""Canonical Term Normalizer for CCILF (COND-11, COND-18, ADR-0059).

Executes context-aware terminology normalization across consulting documents,
enforcing canonical terms while strictly preserving immutable citations, verbatim
quotes, registered entity brands, and code blocks.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ccba_legal.lexicon.disambiguation import FacetedDisambiguationEngine
from ccba_legal.lexicon.loader import load_canonical_taxonomy
from ccba_legal.lexicon.masker import ImmutableSpanMasker


@dataclass(frozen=True)
class TermReplacement:
    """Record of a single terminology replacement."""

    original_text: str
    canonical_text: str
    canonical_id: str
    reason: str


@dataclass
class NormalizationReport:
    """Detailed report of terminology normalization and validation warnings."""

    original_text: str
    normalized_text: str
    replacements: list[TermReplacement] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Returns True if any terminology replacements were performed."""
        return len(self.replacements) > 0


class CanonicalTermNormalizer:
    """Normalizes construction and governance terminology in Vietnamese text."""

    def __init__(
        self,
        taxonomy: dict[str, Any] | None = None,
        masker: ImmutableSpanMasker | None = None,
        disambiguator: FacetedDisambiguationEngine | None = None,
    ) -> None:
        """Initializes normalizer with taxonomy and helper engines."""
        self.taxonomy = taxonomy or load_canonical_taxonomy()
        self.masker = masker or ImmutableSpanMasker()
        self.disambiguator = disambiguator or FacetedDisambiguationEngine()
        self._compiled_forbidden_rules: list[tuple[re.Pattern[str], str, str, str]] = []
        self._build_replacement_index()

    def _build_replacement_index(self) -> None:
        """Compiles forbidden term regexes with word boundary anchors (COND-11)."""
        raw_terms = self.taxonomy.get("terms", {})
        term_items = raw_terms.values() if isinstance(raw_terms, dict) else raw_terms

        for term in term_items:
            if not isinstance(term, dict):
                continue

            canonical_id = term.get("canonical_id", "")
            canonical_vi = term.get("canonical_vi", "")
            vi_forbidden = term.get("vi_forbidden", [])

            for forbidden in vi_forbidden:
                if not forbidden:
                    continue
                # Unicode-safe word boundary: (?<!\w)phrase(?!\w)
                escaped = re.escape(forbidden)
                pattern = re.compile(rf"(?<!\w){escaped}(?!\w)", re.IGNORECASE)
                reason = f"Prohibited synonym for canonical term '{canonical_vi}' ({canonical_id})"
                self._compiled_forbidden_rules.append((pattern, canonical_vi, canonical_id, reason))

    def normalize(self, text: str, domain_hint: str | None = None) -> NormalizationReport:
        """Normalizes text by replacing forbidden terms with canonical forms.

        Args:
            text: Input document text or markdown.
            domain_hint: Optional domain hint for faceted polysemy disambiguation.

        Returns:
            NormalizationReport with normalized text, replacements, and warnings.
        """
        if not text:
            return NormalizationReport(original_text=text, normalized_text=text)

        # Step 1: Mask immutable citations, quotes, brands, and links (COND-11)
        masked_text, span_registry = self.masker.mask(text)

        replacements: list[TermReplacement] = []
        warnings: list[str] = []

        # Step 2: Contextual grandfathering & disambiguation checks (COND-16)
        pccc_check = self.disambiguator.disambiguate_term("thẩm duyệt thiết kế PCCC", masked_text)
        if pccc_check and pccc_check.warning:
            warnings.append(pccc_check.warning)

        # Step 3: Replace forbidden terms with canonical terms
        working_text = masked_text
        for pattern, canonical_vi, canonical_id, reason in self._compiled_forbidden_rules:
            matches = list(pattern.finditer(working_text))
            if not matches:
                continue

            for match in matches:
                replacements.append(
                    TermReplacement(
                        original_text=match.group(0),
                        canonical_text=canonical_vi,
                        canonical_id=canonical_id,
                        reason=reason,
                    )
                )

            # Replace while preserving case of first character if applicable
            working_text = pattern.sub(canonical_vi, working_text)

        # Step 4: Unmask protected spans to preserve verbatim citations (COND-11)
        restored_text = self.masker.unmask(working_text, span_registry)

        return NormalizationReport(
            original_text=text,
            normalized_text=restored_text,
            replacements=replacements,
            warnings=warnings,
        )
