"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalIntelPipeline      — Crawl, parse, package legal documents end-to-end.
    LegalProcessor          — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine         — Cloud sync of legal registry to NotebookLM.
    LegislativeConsolidator — Automated OKF v2.0 AST Structural Patching & VBHN Merger.
    Cleaners                — OCR cleanup, DOCX table parsing, Markdown conversion.
    GoldStandardProcessor   — OKF v2.2 Gold standard normalizer, footnote & AST/QA generator.
    VisualParityAuditor     — CI Gate 4 visual & footnote formatting auditor.
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
from .consolidator import (
    ConsolidationResult,
    DocMode,
    DualModeASTParser,
    LegislativeConsolidator,
    ManifestGenerator,
    PatchItem,
    PatchManifest,
    load_manifest,
)
from .coordinator import (
    LegalIntelPipeline,
    LegalProcessor,
    LegalProcessResult,
)
from .crawler import (
    ChromeCDP,
    ChromeCDPError,
    CookieVault,
    MockChromeCDP,
    TVPLCrawler,
    TVPLCrawlFailedException,
    TVPLRateLimiter,
    TVPLSessionMutex,
    download_three_tier,
    get_crawled_doc_data,
    get_tvpl_credentials,
    get_tvpl_metadata,
    sleep_with_jitter,
    trigger_download,
)
from .gold_standard import (
    DocProfile,
    GoldStandardProcessor,
    clean_html_tables,
    clean_table_footnotes_and_superscripts,
    generate_bundle_ast_and_qa,
    get_doc_profile,
    inject_semantic_anchors,
    normalize_notes_and_lists,
    normalize_tvpl_formatting,
    strip_existing_anchors,
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
from .visual_parity import (
    VisualParityAuditor,
    audit_visual_parity,
)

__all__ = [
    # === Core Deep Seams (Public Interface) ===
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    "LegalGroundingGate",
    "LegislativeConsolidator",
    "ManifestGenerator",
    "OKFBundlePackager",
    "AppendixSplitter",
    "ASTParser",
    "DualModeASTParser",
    "VBHNEngine",
    "VBHNMerger",
    "TVPLCrawler",
    "TVPLRateLimiter",
    "TVPLCrawlFailedException",
    "sleep_with_jitter",
    "get_tvpl_credentials",
    "get_tvpl_metadata",
    "download_three_tier",
    "Cleaners",
    "ChromeCDP",
    "MockChromeCDP",
    "ChromeCDPError",
    "GoldStandardProcessor",
    "VisualParityAuditor",
    "audit_visual_parity",
    # === Core DTOs & Domain Models ===
    "ASTNode",
    "DeltaPatch",
    "DeltaPatchItem",
    "PatchAction",
    "PatchManifest",
    "PatchItem",
    "DocMode",
    "ConsolidationResult",
    "MergedLegalDocument",
    "DocProfile",
    # === Essential Public Helpers & Guards ===
    "verify_legal_grounding",
    "format_grounded_response",
    "format_citation",
    "load_legal_registry",
    "search_legal_registry",
    "load_manifest",
    "roman_to_decimal",
    "TVPLSessionMutex",
    "CookieVault",
    "LEGAL_DISCLAIMER",
    "download_three_tier",
    "get_crawled_doc_data",
    "trigger_download",
    "get_doc_profile",
    "strip_existing_anchors",
    "normalize_tvpl_formatting",
    "clean_html_tables",
    "clean_table_footnotes_and_superscripts",
    "normalize_notes_and_lists",
    "inject_semantic_anchors",
    "generate_bundle_ast_and_qa",
]
