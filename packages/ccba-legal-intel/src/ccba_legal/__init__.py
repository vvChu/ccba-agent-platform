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

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .appendices import (
        AppendixSplitter,
        roman_to_decimal,
    )
    from .ast_parser import (
        ASTParser,
        DeltaPatch,
        DeltaPatchItem,
    )
    from .cleaners import (
        Cleaners,
        normalize_legal_text,
    )
    from .compiler import compile_sharded_registry
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
    from .currency_resolver import (
        CurrencyCard,
        DynamicStatutoryResolver,
        StatutoryDocInfo,
        StatutoryRole,
        clear_resolver_cache,
        resolve_statutory_doc,
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
    from .federated_rag import (
        FederatedLegalEngine,
        query_ground_truth,
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
    from .normalizers import (
        NormalizerConfig,
        TextNormalizer,
        get_text_normalizer,
        normalize_chunk_text,
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
    from .sync import (
        LegalSyncEngine,
        sync_legal_assets,
    )
    from .validator import (
        validate_registry_sync,
        validate_template_and_table_integrity,
    )
    from .vbhn_engine import (
        MergedLegalDocument,
        VBHNEngine,
    )
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
    "TextNormalizer",
    "NormalizerConfig",
    "get_text_normalizer",
    "normalize_chunk_text",
    "normalize_legal_text",
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
    "normalize_clause_numbers",
    "classify_and_extract_tables",
    "validate_template_and_table_integrity",
    "validate_registry_sync",
    "compile_sharded_registry",
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
    # === Dynamic Statutory Resolver (ADR 0035, ADR 0050, ADR 0059) ===
    "StatutoryRole",
    "StatutoryDocInfo",
    "resolve_statutory_doc",
    "clear_resolver_cache",
    "DynamicStatutoryResolver",
    "CurrencyCard",
]

# Unannotated ast.Assign so check_init_lazy_exports_parity inspects all keys.
_LAZY_EXPORTS = {
    "AppendixSplitter": "ccba_legal.appendices",
    "roman_to_decimal": "ccba_legal.appendices",
    "ASTParser": "ccba_legal.ast_parser",
    "DeltaPatch": "ccba_legal.ast_parser",
    "DeltaPatchItem": "ccba_legal.ast_parser",
    "Cleaners": "ccba_legal.cleaners",
    "normalize_legal_text": "ccba_legal.cleaners",
    "compile_sharded_registry": "ccba_legal.compiler",
    "ConsolidationResult": "ccba_legal.consolidator",
    "DocMode": "ccba_legal.consolidator",
    "DualModeASTParser": "ccba_legal.consolidator",
    "LegislativeConsolidator": "ccba_legal.consolidator",
    "ManifestGenerator": "ccba_legal.consolidator",
    "PatchItem": "ccba_legal.consolidator",
    "PatchManifest": "ccba_legal.consolidator",
    "load_manifest": "ccba_legal.consolidator",
    "AST_CLAUSES_SCHEMA_VERSION": "ccba_legal.constants",
    "CURRENT_CONVERTER_VERSION": "ccba_legal.constants",
    "CURRENT_OKF_SCHEMA_URI": "ccba_legal.constants",
    "CURRENT_OKF_SPEC": "ccba_legal.constants",
    "CURRENT_OKF_VERSION": "ccba_legal.constants",
    "DIR_ANNEXES": "ccba_legal.constants",
    "DIR_FIGURES": "ccba_legal.constants",
    "DIR_SOURCES": "ccba_legal.constants",
    "DIR_TABLES": "ccba_legal.constants",
    "DIR_TEMPLATES": "ccba_legal.constants",
    "FIGURES_CATALOG_SCHEMA_VERSION": "ccba_legal.constants",
    "GATE_0_MIN_DOCX_PDF_PARITY": "ccba_legal.constants",
    "GATE_11_MIN_VERBATIM_PARITY": "ccba_legal.constants",
    "PATCH_MANIFEST_VERSION": "ccba_legal.constants",
    "QA_BENCHMARK_SCHEMA_VERSION": "ccba_legal.constants",
    "STANDARD_COMPARTMENTS": "ccba_legal.constants",
    "TABLES_CATALOG_SCHEMA_VERSION": "ccba_legal.constants",
    "DocxCanonicalSanitizer": "ccba_legal.converters",
    "load_bundle_formula_overrides": "ccba_legal.converters",
    "omml_to_latex": "ccba_legal.converters",
    "LegalIntelPipeline": "ccba_legal.coordinator",
    "LegalProcessor": "ccba_legal.coordinator",
    "LegalProcessResult": "ccba_legal.coordinator",
    "ChromeCDP": "ccba_legal.crawler",
    "ChromeCDPError": "ccba_legal.crawler",
    "CookieVault": "ccba_legal.crawler",
    "MockChromeCDP": "ccba_legal.crawler",
    "TVPLCrawler": "ccba_legal.crawler",
    "TVPLCrawlFailedException": "ccba_legal.crawler",
    "TVPLRateLimiter": "ccba_legal.crawler",
    "TVPLSessionMutex": "ccba_legal.crawler",
    "download_three_tier": "ccba_legal.crawler",
    "get_crawled_doc_data": "ccba_legal.crawler",
    "get_tvpl_credentials": "ccba_legal.crawler",
    "get_tvpl_metadata": "ccba_legal.crawler",
    "sleep_with_jitter": "ccba_legal.crawler",
    "trigger_download": "ccba_legal.crawler",
    "verify_tvpl_vip_status": "ccba_legal.crawler",
    "CurrencyCard": "ccba_legal.currency_resolver",
    "DynamicStatutoryResolver": "ccba_legal.currency_resolver",
    "StatutoryDocInfo": "ccba_legal.currency_resolver",
    "StatutoryRole": "ccba_legal.currency_resolver",
    "clear_resolver_cache": "ccba_legal.currency_resolver",
    "resolve_statutory_doc": "ccba_legal.currency_resolver",
    "classify_and_extract_tables": "ccba_legal.docx_converter",
    "convert_docx_to_okf_bundle": "ccba_legal.docx_converter",
    "detect_document_pipeline": "ccba_legal.docx_converter",
    "normalize_clause_numbers": "ccba_legal.docx_converter",
    "normalize_docx_markdown": "ccba_legal.docx_converter",
    "process_vbpl_bundle": "ccba_legal.docx_converter",
    "process_vbpl_bundle_okf_v22": "ccba_legal.docx_converter",
    "process_vbpl_bundle_okf_v24": "ccba_legal.docx_converter",
    "LegalKnowledgeEngine": "ccba_legal.engine",
    "canonicalize_clause_id": "ccba_legal.engine",
    "csv_to_markdown": "ccba_legal.engine",
    "FederatedLegalEngine": "ccba_legal.federated_rag",
    "query_ground_truth": "ccba_legal.federated_rag",
    "extract_docx_figures": "ccba_legal.figure_extractor",
    "extract_technical_figures": "ccba_legal.figure_extractor",
    "load_bundle_figures_overrides": "ccba_legal.figure_extractor",
    "render_markdown_figure_card": "ccba_legal.figure_extractor",
    "OKFStructureProcessor": "ccba_legal.formatter",
    "extract_parent_metadata": "ccba_legal.formatter",
    "extract_latex_from_image": "ccba_legal.formula_harvester",
    "harvest_docx_formula_images": "ccba_legal.formula_harvester",
    "harvest_pdf_formula_images": "ccba_legal.formula_harvester",
    "is_formula_image": "ccba_legal.formula_harvester",
    "DocProfile": "ccba_legal.gold_standard",
    "GoldStandardProcessor": "ccba_legal.gold_standard",
    "clean_html_tables": "ccba_legal.gold_standard",
    "clean_table_footnotes_and_superscripts": "ccba_legal.gold_standard",
    "generate_bundle_ast_and_qa": "ccba_legal.gold_standard",
    "get_doc_profile": "ccba_legal.gold_standard",
    "inject_semantic_anchors": "ccba_legal.gold_standard",
    "normalize_notes_and_lists": "ccba_legal.gold_standard",
    "normalize_tvpl_formatting": "ccba_legal.gold_standard",
    "strip_existing_anchors": "ccba_legal.gold_standard",
    "LEGAL_DISCLAIMER": "ccba_legal.grounding",
    "NATIONAL_FALLBACK_DISCLAIMER": "ccba_legal.grounding",
    "LegalGroundingGate": "ccba_legal.grounding",
    "format_grounded_response": "ccba_legal.grounding",
    "verify_legal_grounding": "ccba_legal.grounding",
    "AuthorityResolutionResult": "ccba_legal.jurisdiction",
    "expand_jurisdiction_queries": "ccba_legal.jurisdiction",
    "generate_jurisdiction_guardrail_card": "ccba_legal.jurisdiction",
    "get_default_ontology_path": "ccba_legal.jurisdiction",
    "load_administrative_ontology": "ccba_legal.jurisdiction",
    "normalize_jurisdiction": "ccba_legal.jurisdiction",
    "resolve_authority": "ccba_legal.jurisdiction",
    "validate_authority_naming": "ccba_legal.jurisdiction",
    "validate_tier_authority": "ccba_legal.jurisdiction",
    "ASTNode": "ccba_legal.models",
    "LegalDocStatus": "ccba_legal.models",
    "LegalLifecycleInfo": "ccba_legal.models",
    "PatchAction": "ccba_legal.models",
    "normalize_doc_status": "ccba_legal.models",
    "FigureAutoCompositor": "ccba_legal.modernize",
    "MathEquationConverter": "ccba_legal.modernize",
    "TableMatrixBuilder": "ccba_legal.modernize",
    "NormalizerConfig": "ccba_legal.normalizers",
    "TextNormalizer": "ccba_legal.normalizers",
    "get_text_normalizer": "ccba_legal.normalizers",
    "normalize_chunk_text": "ccba_legal.normalizers",
    "OKFBundlePackager": "ccba_legal.packager",
    "check_structure_alignment": "ccba_legal.provenance",
    "compute_docx_to_markdown_parity": "ccba_legal.provenance",
    "compute_text_parity": "ccba_legal.provenance",
    "extract_docx_data": "ccba_legal.provenance",
    "extract_pdf_data": "ccba_legal.provenance",
    "find_bundle_assets": "ccba_legal.provenance",
    "normalize_text": "ccba_legal.provenance",
    "verify_bundle_docx_vs_markdown": "ccba_legal.provenance",
    "verify_docx_against_markdown": "ccba_legal.provenance",
    "verify_docx_against_pdf": "ccba_legal.provenance",
    "LegalRegistryManager": "ccba_legal.registry",
    "discover_master_registry_path": "ccba_legal.registry",
    "format_citation": "ccba_legal.registry",
    "get_active_delegation_document": "ccba_legal.registry",
    "get_lifecycle": "ccba_legal.registry",
    "load_legal_registry": "ccba_legal.registry",
    "query": "ccba_legal.registry",
    "search_legal_registry": "ccba_legal.registry",
    "LegalSyncEngine": "ccba_legal.sync",
    "sync_legal_assets": "ccba_legal.sync",
    "validate_registry_sync": "ccba_legal.validator",
    "validate_template_and_table_integrity": "ccba_legal.validator",
    "MergedLegalDocument": "ccba_legal.vbhn_engine",
    "VBHNEngine": "ccba_legal.vbhn_engine",
    "VBHNMerger": "ccba_legal.vbhn_merger",
    "VisualParityAuditor": "ccba_legal.visual_parity",
    "audit_visual_parity": "ccba_legal.visual_parity",
    "lint_document": "ccba_legal.visual_parity",
}


def __getattr__(name: str) -> Any:
    """Lazy import module-level attributes per PEP 562."""
    module_name = _LAZY_EXPORTS.get(name)
    if module_name is not None:
        mod = importlib.import_module(module_name)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    """Expose dynamic attributes to introspection and language servers per PEP 562."""
    return sorted(set(globals().keys()) | set(__all__))
