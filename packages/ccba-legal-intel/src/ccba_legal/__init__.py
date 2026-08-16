"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalIntelPipeline  — Crawl, parse, package legal documents end-to-end.
    LegalProcessor      — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine     — Cloud sync of legal registry to NotebookLM.
    Cleaners            — OCR cleanup, DOCX table parsing, Markdown conversion.
"""

from .appendices import AppendixSplitter, roman_to_decimal
from .ast_parser import (
    ASTNode,
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
    PatchAction,
)
from .cleaners import Cleaners
from .coordinator import (
    LegalIntelPipeline,
    LegalProcessor,
    LegalProcessResult,
)
from .crawler import (
    CookieVault,
    TVPLCrawler,
    TVPLSessionMutex,
)
from .grounding import (
    LEGAL_DISCLAIMER,
    LegalGroundingGate,
    format_grounded_response,
    verify_legal_grounding,
)
from .packager import OKFBundlePackager
from .registry import (
    LegalRegistryManager,
    format_citation,
    load_legal_registry,
    search_legal_registry,
)
from .sync import LegalSyncEngine
from .vbhn_engine import MergedLegalDocument, VBHNEngine
from .vbhn_merger import VBHNMerger

__all__ = [
    # === Core Deep Seams (Public Interface) ===
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    "LegalGroundingGate",
    "OKFBundlePackager",
    "AppendixSplitter",
    "ASTParser",
    "VBHNEngine",
    "VBHNMerger",
    "TVPLCrawler",
    "Cleaners",
    # === Core DTOs & Domain Models ===
    "ASTNode",
    "DeltaPatch",
    "DeltaPatchItem",
    "PatchAction",
    "MergedLegalDocument",
    # === Essential Public Helpers & Guards ===
    "verify_legal_grounding",
    "format_grounded_response",
    "format_citation",
    "load_legal_registry",
    "search_legal_registry",
    "roman_to_decimal",
    "TVPLSessionMutex",
    "CookieVault",
    "LEGAL_DISCLAIMER",
]
