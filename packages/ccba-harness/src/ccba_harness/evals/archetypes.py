"""archetypes.py - Single Source of Truth (SSOT) for Domain Archetypes (ADR-0023, ADR-0057, ADR-0058).

This module centralizes all Archetype definitions, Disjoint keyword tuples, evaluation dataset mappings,
and domain scorer factories across CCBA Evals Engine (Tuner, Daemon, Runner).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from .scorers import (
    BaseScorer,
    get_academic_scorers,
    get_adr_lifecycle_scorers,
    get_bigbim_governance_scorers,
    get_bigbim_rase_scorers,
    get_bigbim_risk_scorers,
    get_bim_classification_scorers,
    get_coding_scorers,
    get_grilling_scorers,
    get_lean_structural_scorers,
    get_legal_scorers,
    get_office_scorers,
    get_orchestration_scorers,
    get_pccc_scorers,
    get_skill_repair_scorers,
    get_visual_diagram_scorers,
)

# ---------------------------------------------------------------------------
# Disjoint Subdomain & Domain Keyword Tuples (SSOT)
# ---------------------------------------------------------------------------
# Specialized Subdomains (Separated from parent domains to prevent collision)
GRILLING_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("grill", "stresstest", "stress-test")
ADR_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("adr", "architecture-decision")
RISK_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("risk", "conflict")
SKILL_REPAIR_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("skill-repair", "repair-skill")

# Statutory and Regulatory Engineering Domains
LEGAL_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "legal",
    "luat",
    "tvpl",
    "vbpl",
    "advisor",
    "checklist",
    "hsht",
    "phap-ly",
    "ingest",
)
TECH_QC_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("pccc", "qc", "audit", "thamdinh")

# Creative, Office, Visual & Academic Domains
OFFICE_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "van-phong",
    "docx",
    "pptx",
    "presentation",
    "markdown-document",
    "seminar",
    "typography",
    "copywriting",
    "vietbai",
    "truyenthong",
)
VISUAL_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("mermaid", "excalidraw", "diagram")
ACADEMIC_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("academic", "khoahoc")

# BIM Specialized Subdomains (Separated from general BIM classification)
BIM_GOVERNANCE_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "governance",
    "soi-chi-vang",
    "soi-chi-do",
    "golden-thread",
    "red-thread",
    "unique-id",
)
BIM_RASE_ARCHETYPE_KEYWORDS: tuple[str, ...] = ("rase", "pset", "qto")

# BIM Classification Domain (Disjoint: "risk" -> RISK_ARCHETYPE_KEYWORDS, "vbpl" -> LEGAL)
BIM_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "bim",
    "uniclass",
    "classification",
    "iso12006",
    "openbim",
    "ifc",
)

# Engineering & Codebase Architecture Domains
CODING_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "code",
    "bug",
    "diagnos",
    "implement",
    "tdd",
    "codebase-design",
    "refactor",
    "engineering",
    "sdk",
    "circuit-breaker",
    "logger",
    "stability-guard",
    "rag",
    "pipeline-patterns",
    "maskara",
    "testing",
    "modeling",
    "feature",
    "iac",
    "to-spec",
    "docs",
    "pdf-prep",
    "preprocessor",
)

# Agent Orchestration Domain (Disjoint: "grill" and "adr" are extracted to specialized subdomains)
ORCHESTRATION_ARCHETYPE_KEYWORDS: tuple[str, ...] = (
    "teamwork",
    "orchestrat",
    "platform",
    "handoff",
    "issue-tree",
    "ask",
    "xia",
    "wayfinder",
    "spoke",
    "upstream",
    "hub",
    "pr",
    "guardrails",
    "proposal",
    "retrospective",
    "knowledge",
    "research",
    "notebooklm",
    "youtube",
    "build-skill",
    "setup-skills",
    "eval-gate",
    "rd",
    "graduate",
)


# ---------------------------------------------------------------------------
# Declarative Domain Archetype Registry
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DomainArchetype:
    """Immutable metadata contract for a domain archetype."""

    name: str
    keywords: tuple[str, ...]
    dataset_file: str
    scorer_factory: Callable[[], list[BaseScorer]]


# Deterministic search order: Specialized subdomains first, general foundations last
DOMAIN_ARCHETYPES: tuple[DomainArchetype, ...] = (
    DomainArchetype(
        "grilling", GRILLING_ARCHETYPE_KEYWORDS, "eval_grilling.json", get_grilling_scorers
    ),
    DomainArchetype(
        "adr", ADR_ARCHETYPE_KEYWORDS, "eval_adr_lifecycle.json", get_adr_lifecycle_scorers
    ),
    DomainArchetype(
        "risk", RISK_ARCHETYPE_KEYWORDS, "eval_bigbim_risk.json", get_bigbim_risk_scorers
    ),
    DomainArchetype(
        "skill_repair",
        SKILL_REPAIR_ARCHETYPE_KEYWORDS,
        "eval_skill_repair.json",
        get_skill_repair_scorers,
    ),
    DomainArchetype("legal", LEGAL_ARCHETYPE_KEYWORDS, "eval_legal_intel.json", get_legal_scorers),
    DomainArchetype(
        "tech_qc", TECH_QC_ARCHETYPE_KEYWORDS, "eval_pccc_audit.json", get_pccc_scorers
    ),
    DomainArchetype(
        "academic", ACADEMIC_ARCHETYPE_KEYWORDS, "eval_academic_writing.json", get_academic_scorers
    ),
    DomainArchetype(
        "office", OFFICE_ARCHETYPE_KEYWORDS, "eval_copywriting.json", get_office_scorers
    ),
    DomainArchetype(
        "visual", VISUAL_ARCHETYPE_KEYWORDS, "eval_visual_diagram.json", get_visual_diagram_scorers
    ),
    DomainArchetype(
        "bim_governance",
        BIM_GOVERNANCE_ARCHETYPE_KEYWORDS,
        "eval_bigbim_governance.json",
        get_bigbim_governance_scorers,
    ),
    DomainArchetype(
        "bim_rase",
        BIM_RASE_ARCHETYPE_KEYWORDS,
        "eval_bigbim_rase.json",
        get_bigbim_rase_scorers,
    ),
    DomainArchetype(
        "bim",
        BIM_ARCHETYPE_KEYWORDS,
        "eval_bigbim_classification.json",
        get_bim_classification_scorers,
    ),
    DomainArchetype(
        "coding", CODING_ARCHETYPE_KEYWORDS, "eval_codebase_engineering.json", get_coding_scorers
    ),
    DomainArchetype(
        "orchestration",
        ORCHESTRATION_ARCHETYPE_KEYWORDS,
        "eval_agent_orchestration.json",
        get_orchestration_scorers,
    ),
)


# ---------------------------------------------------------------------------
# SSOT Resolution Functions
# ---------------------------------------------------------------------------
def resolve_domain_archetype(skill_name: str) -> DomainArchetype | None:
    """Resolves the first matching DomainArchetype for a given skill name.

    Args:
        skill_name: Name of the skill (e.g., 'ccba-legal-intel', 'ccba-mermaid-diagram').

    Returns:
        DomainArchetype instance if matched, or None if fallback general domain.
    """
    sname = skill_name.strip().lower()

    # Special case alias handling for exact legacy conventions
    if "academic-writing" in sname:
        for arch in DOMAIN_ARCHETYPES:
            if arch.name == "academic":
                return arch

    # Strip project/namespace prefix so 'bigbim-*' does not false-positive on 'bim' keyword
    sname_core = re.sub(r"^(ccba|bigbim)-", "", sname)

    for arch in DOMAIN_ARCHETYPES:
        if any(k in sname_core for k in arch.keywords):
            return arch
    return None


def resolve_domain_dataset(skill_name: str) -> str:
    """Resolves the canonical evaluation dataset filename for a skill.

    Args:
        skill_name: Name of the skill.

    Returns:
        Dataset filename string (e.g. 'eval_visual_diagram.json', 'eval_legal_intel.json').
    """
    arch = resolve_domain_archetype(skill_name)
    return arch.dataset_file if arch else "eval_general_domain.json"


def get_default_domain_scorers(skill_name: str) -> list[BaseScorer]:
    """Provides domain-aligned default scorers based on target skill name.

    Args:
        skill_name: Name of the skill.

    Returns:
        List of initialized BaseScorer instances.
    """
    arch = resolve_domain_archetype(skill_name)
    return arch.scorer_factory() if arch else get_lean_structural_scorers()
