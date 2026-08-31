"""ccba-legal-intel — Unified Legal Intelligence Platform.

Public Deep Seams:
    LegalIntelPipeline      — Crawl, parse, package legal documents end-to-end.
    LegalProcessor          — Legal advisory, conflict analysis, dispatch drafts.
    LegalSyncEngine         — Cloud sync of legal registry to NotebookLM.
    LegislativeConsolidator — Automated OKF v2.0 AST Structural Patching & VBHN Merger.
    Cleaners                — OCR cleanup, DOCX table parsing, Markdown conversion.
    GoldStandardProcessor   — OKF v2.2 Gold standard normalizer, footnote & AST/QA generator.
    VisualParityAuditor     — CI Gate 4 visual & footnote formatting auditor.
    AIVisionFormulaHarvester — ADR 0031: Bóc tách công thức toán học từ ảnh sang KaTeX.
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
from .converters import (
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
    process_vbpl_bundle_okf_v22,
)
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
    LegalGroundingGate,
    format_grounded_response,
    verify_legal_grounding,
)
from .models import (
    ASTNode,
    PatchAction,
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
    format_citation,
    load_legal_registry,
    search_legal_registry,
)
from .sync import LegalSyncEngine
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
    "LegalIntelPipeline",
    "LegalProcessor",
    "LegalProcessResult",
    "LegalSyncEngine",
    "LegalRegistryManager",
    "LegalGroundingGate",
    "LegislativeConsolidator",
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
    # === DOCX Conversion & Classification ===
    "convert_docx_to_okf_bundle",
    "process_vbpl_bundle_okf_v22",
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
]
