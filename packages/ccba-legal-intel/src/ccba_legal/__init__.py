"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalKnowledgeEngine    — Universal legal knowledge engine, tier-aware AST clause & table extraction.
    LegalIntelPipeline      — Crawl, parse, package legal documents end-to-end.
    LegalProcessor          — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine         — Cloud sync of legal registry to NotebookLM.
    LegislativeConsolidator — Automated OKF v2.0 AST Structural Patching & VBHN Merger.
    Cleaners                — OCR cleanup, DOCX table parsing, Markdown conversion.
    GoldStandardProcessor   — OKF v2.2 Gold standard normalizer, footnote & AST/QA generator.
    VisualParityAuditor     — CI Gate 4 visual & footnote formatting auditor.
    AIVisionFormulaHarvester — ADR 0031: Bóc tách công thức toán học từ ảnh sang KaTeX.
    DocxCanonicalSanitizer  — ADR 0042: Canonical OpenXML Pre-Sanitizer & Hybrid Dual-Engine.
"""

from .appendices import AppendixSplitter, roman_to_decimal
from .ast_parser import (
    ASTParser,
    DeltaPatch,
    DeltaPatchItem,
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
from .constants import (
    AST_CLAUSES_SCHEMA_VERSION,
    CURRENT_CONVERTER_VERSION,
    CURRENT_OKF_SCHEMA_URI,
    CURRENT_OKF_SPEC,
    CURRENT_OKF_VERSION,
    DIR_ANNEXES,
    DIR_FIGURES,
    DIR_SOURCES,
    DIR_TABLES,
    DIR_TEMPLATES,
    FIGURES_CATALOG_SCHEMA_VERSION,
    GATE_0_MIN_DOCX_PDF_PARITY,
    GATE_11_MIN_VERBATIM_PARITY,
    PATCH_MANIFEST_VERSION,
    QA_BENCHMARK_SCHEMA_VERSION,
    STANDARD_COMPARTMENTS,
    TABLES_CATALOG_SCHEMA_VERSION,
)
from .converters import (
    DocxCanonicalSanitizer,
    load_bundle_formula_overrides,
    omml_to_latex,
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
    verify_tvpl_vip_status,
)
from .docx_converter import (
    classify_and_extract_tables,
    convert_docx_to_okf_bundle,
    detect_document_pipeline,
    normalize_clause_numbers,
    normalize_docx_markdown,
    process_vbpl_bundle,
    process_vbpl_bundle_okf_v22,
    process_vbpl_bundle_okf_v24,
)
from .engine import (
    LegalKnowledgeEngine,
    canonicalize_clause_id,
    csv_to_markdown,
)
from .federated_rag import FederatedLegalEngine, query_ground_truth
from .figure_extractor import (
    extract_docx_figures,
    extract_technical_figures,
    load_bundle_figures_overrides,
    render_markdown_figure_card,
)
from .formatter import (
    OKFStructureProcessor,
    extract_parent_metadata,
)
from .formula_harvester import (
    extract_latex_from_image,
    harvest_docx_formula_images,
    harvest_pdf_formula_images,
    is_formula_image,
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
    NATIONAL_FALLBACK_DISCLAIMER,
    LegalGroundingGate,
    format_grounded_response,
    verify_legal_grounding,
)
from .jurisdiction import (
    AuthorityResolutionResult,
    expand_jurisdiction_queries,
    generate_jurisdiction_guardrail_card,
    get_default_ontology_path,
    load_administrative_ontology,
    normalize_jurisdiction,
    resolve_authority,
    validate_authority_naming,
    validate_tier_authority,
)
from .models import (
    ASTNode,
    LegalDocStatus,
    LegalLifecycleInfo,
    PatchAction,
    normalize_doc_status,
)
from .modernize import (
    FigureAutoCompositor,
    MathEquationConverter,
    TableMatrixBuilder,
)
from .packager import OKFBundlePackager
from .provenance import (
    check_structure_alignment,
    compute_docx_to_markdown_parity,
    compute_text_parity,
    extract_docx_data,
    extract_pdf_data,
    find_bundle_assets,
    normalize_text,
    verify_bundle_docx_vs_markdown,
    verify_docx_against_markdown,
    verify_docx_against_pdf,
)
from .registry import (
    LegalRegistryManager,
    discover_master_registry_path,
    format_citation,
    get_active_delegation_document,
    get_lifecycle,
    load_legal_registry,
    query,
    search_legal_registry,
)
from .sync import LegalSyncEngine, sync_legal_assets
from .validator import validate_template_and_table_integrity
from .vbhn_engine import MergedLegalDocument, VBHNEngine
from .vbhn_merger import VBHNMerger
from .visual_parity import (
    VisualParityAuditor,
    audit_visual_parity,
    lint_document,
)

__all__ = [
    # === Modernize Annex Primitives (OKF v2.3) ===
    "FigureAutoCompositor",
    "TableMatrixBuilder",
    "MathEquationConverter",
    # === Core Deep Seams (Public Interface) ===
    "LegalKnowledgeEngine",
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    "LegalGroundingGate",
    "LegislativeConsolidator",
    "FederatedLegalEngine",
    "query_ground_truth",
    "ManifestGenerator",
    "OKFBundlePackager",
    "OKFStructureProcessor",
    "extract_parent_metadata",
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
    "lint_document",
    # === Core DTOs & Domain Models ===
    "ASTNode",
    "DeltaPatch",
    "DeltaPatchItem",
    "PatchAction",
    "LegalDocStatus",
    "LegalLifecycleInfo",
    "normalize_doc_status",
    "PatchManifest",
    "PatchItem",
    "DocMode",
    "ConsolidationResult",
    "MergedLegalDocument",
    "DocProfile",
    # === Essential Public Helpers & Guards ===
    "verify_tvpl_vip_status",
    "verify_legal_grounding",
    "format_grounded_response",
    "format_citation",
    "load_legal_registry",
    "discover_master_registry_path",
    "search_legal_registry",
    "get_lifecycle",
    "get_active_delegation_document",
    "query",
    "canonicalize_clause_id",
    "csv_to_markdown",
    "sync_legal_assets",
    "load_manifest",
    "roman_to_decimal",
    "TVPLSessionMutex",
    "CookieVault",
    "LEGAL_DISCLAIMER",
    "NATIONAL_FALLBACK_DISCLAIMER",
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
    # === OKF Specification & Constants ===
    "CURRENT_OKF_VERSION",
    "CURRENT_OKF_SPEC",
    "CURRENT_OKF_SCHEMA_URI",
    "CURRENT_CONVERTER_VERSION",
    "DIR_SOURCES",
    "DIR_TABLES",
    "DIR_FIGURES",
    "DIR_ANNEXES",
    "DIR_TEMPLATES",
    "STANDARD_COMPARTMENTS",
    "GATE_0_MIN_DOCX_PDF_PARITY",
    "GATE_11_MIN_VERBATIM_PARITY",
    "PATCH_MANIFEST_VERSION",
    "TABLES_CATALOG_SCHEMA_VERSION",
    "FIGURES_CATALOG_SCHEMA_VERSION",
    "AST_CLAUSES_SCHEMA_VERSION",
    "QA_BENCHMARK_SCHEMA_VERSION",
    # === DOCX Conversion & Classification ===
    "DocxCanonicalSanitizer",
    "convert_docx_to_okf_bundle",
    "process_vbpl_bundle",
    "process_vbpl_bundle_okf_v22",
    "process_vbpl_bundle_okf_v24",
    "detect_document_pipeline",
    "normalize_docx_markdown",
    "format_all_qcvn_md_tables",
    "normalize_clause_numbers",
    "classify_and_extract_tables",
    "validate_template_and_table_integrity",
    # === Technical Figure Extraction & Centered Cards (ADR 0030 / ADR 0034) ===
    "extract_docx_figures",
    "extract_technical_figures",
    "render_markdown_figure_card",
    "load_bundle_figures_overrides",
    # === Formula Harvesting & OMML (ADR 0030 / ADR 0031) ===
    "omml_to_latex",
    "load_bundle_formula_overrides",
    "extract_latex_from_image",
    "harvest_docx_formula_images",
    "harvest_pdf_formula_images",
    "is_formula_image",
    # === Ingestion Provenance & Verification (Gate 0 / Gate 11 / ADR 0016) ===
    "verify_docx_against_pdf",
    "verify_docx_against_markdown",
    "verify_bundle_docx_vs_markdown",
    "compute_docx_to_markdown_parity",
    "find_bundle_assets",
    "extract_docx_data",
    "extract_pdf_data",
    "check_structure_alignment",
    "compute_text_parity",
    "normalize_text",
    # === Administrative Succession & Jurisdiction (Issue #276) ===
    "AuthorityResolutionResult",
    "expand_jurisdiction_queries",
    "get_default_ontology_path",
    "load_administrative_ontology",
    "normalize_jurisdiction",
    "resolve_authority",
    "validate_authority_naming",
    "validate_tier_authority",
    "generate_jurisdiction_guardrail_card",
]
