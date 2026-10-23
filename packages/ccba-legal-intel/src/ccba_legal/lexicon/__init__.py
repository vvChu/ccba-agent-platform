"""CCBA Canonical Construction & Internal Lexicon Framework (CCILF) package."""

from ccba_legal.lexicon.disambiguation import (
    DisambiguationResult,
    FacetedDisambiguationEngine,
)
from ccba_legal.lexicon.generator import compile_taxonomy_to_py
from ccba_legal.lexicon.harvester import (
    DEFAULT_RESOURCE_PATH,
    LexiconHarvester,
    compute_sha256,
)
from ccba_legal.lexicon.loader import (
    get_canonical_terms,
    load_canonical_taxonomy,
)
from ccba_legal.lexicon.masker import (
    ImmutableSpanMasker,
    ProtectedSpan,
)
from ccba_legal.lexicon.models import (
    CanonicalTerm,
    ProvenanceRecord,
    TermFacet,
    TermTemporal,
)
from ccba_legal.lexicon.normalizer import (
    CanonicalTermNormalizer,
    NormalizationReport,
    TermReplacement,
)

__all__ = [
    "DEFAULT_RESOURCE_PATH",
    "CanonicalTerm",
    "CanonicalTermNormalizer",
    "DisambiguationResult",
    "FacetedDisambiguationEngine",
    "ImmutableSpanMasker",
    "LexiconHarvester",
    "NormalizationReport",
    "ProtectedSpan",
    "ProvenanceRecord",
    "TermFacet",
    "TermReplacement",
    "TermTemporal",
    "compile_taxonomy_to_py",
    "compute_sha256",
    "get_canonical_terms",
    "load_canonical_taxonomy",
]
