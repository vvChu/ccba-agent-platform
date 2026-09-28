"""archetypes.py - Single Source of Truth (SSOT) for Domain Archetypes (ADR-0023, ADR-0057, ADR-0058).

This module centralizes all Archetype definitions, Disjoint keyword tuples, evaluation dataset mappings,
and domain scorer factories across CCBA Evals Engine (Tuner, Daemon, Runner).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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
    get_legal_tooling_scorers,
    get_office_scorers,
    get_orchestration_scorers,
    get_pccc_scorers,
    get_platform_tooling_scorers,
    get_skill_repair_scorers,
    get_visual_design_scorers,
    get_visual_diagram_scorers,
)


# ---------------------------------------------------------------------------
# Declarative Domain Archetype Registry Contract
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DomainArchetype:
    """Immutable metadata contract for a domain archetype."""

    name: str
    keywords: tuple[str, ...]
    dataset_file: str
    scorer_factory: Callable[[], list[BaseScorer]]


# Scorer factory mapping registry
SCORER_FACTORIES: dict[str, Callable[[], list[BaseScorer]]] = {
    "get_academic_scorers": get_academic_scorers,
    "get_adr_lifecycle_scorers": get_adr_lifecycle_scorers,
    "get_bigbim_governance_scorers": get_bigbim_governance_scorers,
    "get_bigbim_rase_scorers": get_bigbim_rase_scorers,
    "get_bigbim_risk_scorers": get_bigbim_risk_scorers,
    "get_bim_classification_scorers": get_bim_classification_scorers,
    "get_coding_scorers": get_coding_scorers,
    "get_grilling_scorers": get_grilling_scorers,
    "get_lean_structural_scorers": get_lean_structural_scorers,
    "get_legal_scorers": get_legal_scorers,
    "get_legal_tooling_scorers": get_legal_tooling_scorers,
    "get_office_scorers": get_office_scorers,
    "get_orchestration_scorers": get_orchestration_scorers,
    "get_pccc_scorers": get_pccc_scorers,
    "get_platform_tooling_scorers": get_platform_tooling_scorers,
    "get_skill_repair_scorers": get_skill_repair_scorers,
    "get_visual_design_scorers": get_visual_design_scorers,
    "get_visual_diagram_scorers": get_visual_diagram_scorers,
}

DEFAULT_CATALOG_PATH = Path(__file__).resolve().parent / "archetypes_catalog.yaml"
_CACHED_DOMAIN_ARCHETYPES: tuple[DomainArchetype, ...] | None = None


def load_archetypes_catalog(
    catalog_path: Path | str | None = None,
) -> tuple[DomainArchetype, ...]:
    """Loads domain archetypes from the declarative YAML catalog.

    Uses an in-memory singleton cache to ensure O(1) subsequent access and < 2ms latency.

    Args:
        catalog_path: Optional path to the archetypes_catalog.yaml file. If None,
            uses the default bundled archetypes_catalog.yaml.

    Returns:
        Immutable tuple of DomainArchetype instances preserving priority ordering.
    """
    global _CACHED_DOMAIN_ARCHETYPES
    if _CACHED_DOMAIN_ARCHETYPES is not None and catalog_path is None:
        return _CACHED_DOMAIN_ARCHETYPES

    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Archetypes catalog not found at: {path}")

    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}

    archetypes_list: list[DomainArchetype] = []
    for item in data.get("archetypes", []):
        factory_name = item.get("scorer_factory")
        if factory_name not in SCORER_FACTORIES:
            raise KeyError(
                f"Unknown scorer factory '{factory_name}' for archetype '{item.get('name')}'"
            )
        archetypes_list.append(
            DomainArchetype(
                name=item["name"],
                keywords=tuple(item["keywords"]),
                dataset_file=item["dataset_file"],
                scorer_factory=SCORER_FACTORIES[factory_name],
            )
        )

    result = tuple(archetypes_list)
    if catalog_path is None:
        _CACHED_DOMAIN_ARCHETYPES = result
    return result


def reload_archetypes_catalog(
    catalog_path: Path | str | None = None,
) -> tuple[DomainArchetype, ...]:
    """Forces reloading of the archetypes catalog, bypassing the in-memory cache."""
    global _CACHED_DOMAIN_ARCHETYPES
    _CACHED_DOMAIN_ARCHETYPES = None
    return load_archetypes_catalog(catalog_path)


# ---------------------------------------------------------------------------
# Declarative SSOT Constants (Exported for Backward Compatibility)
# ---------------------------------------------------------------------------
DOMAIN_ARCHETYPES: tuple[DomainArchetype, ...] = load_archetypes_catalog()
_ARCHETYPE_MAP: dict[str, DomainArchetype] = {arch.name: arch for arch in DOMAIN_ARCHETYPES}

GRILLING_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["grilling"].keywords
ADR_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["adr"].keywords
RISK_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["risk"].keywords
SKILL_REPAIR_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["skill_repair"].keywords
LEGAL_TOOLING_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["legal_tooling"].keywords
LEGAL_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["legal"].keywords
TECH_QC_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["tech_qc"].keywords
ACADEMIC_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["academic"].keywords
OFFICE_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["office"].keywords
VISUAL_DESIGN_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["visual_design"].keywords
VISUAL_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["visual"].keywords
BIM_GOVERNANCE_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["bim_governance"].keywords
BIM_RASE_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["bim_rase"].keywords
BIM_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["bim"].keywords
CODING_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["coding"].keywords
PLATFORM_TOOLING_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["platform_tooling"].keywords
ORCHESTRATION_ARCHETYPE_KEYWORDS: tuple[str, ...] = _ARCHETYPE_MAP["orchestration"].keywords


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
    sname_core_hyphen = sname_core.replace("_", "-")
    sname_hyphen = sname.replace("_", "-")

    # Disjoint routing: Exclude 'codebase-design' from visual_design keyword collision (RULE-2.5)
    if "codebase-design" in sname_core_hyphen or "codebase-design" in sname_hyphen:
        for arch in DOMAIN_ARCHETYPES:
            if arch.name == "coding":
                return arch

    sname_norm = sname_core.replace("-", "_")
    for arch in DOMAIN_ARCHETYPES:
        if arch.name == sname_norm:
            return arch

    for arch in DOMAIN_ARCHETYPES:
        if arch.name == "visual_design" and (
            "codebase-design" in sname_core_hyphen or "codebase-design" in sname_hyphen
        ):
            continue
        if any(k in sname_core or k in sname_core_hyphen for k in arch.keywords):
            return arch
    return None


def resolve_domain_dataset(
    skill_name: str,
    test_cases_dir: Path | str | None = None,
) -> str:
    """Resolves the canonical evaluation dataset filename for a skill (ADR-0060: 2-tier fallback).

    Resolution order:
      Tier 1 (Skill-Specific): If test_cases_dir is provided and a skill-specific dataset file
        exists (eval_{clean_skill}.json, {clean_skill}.json, or eval_{canonical_skill}.json),
        that filename is returned with priority.
      Tier 2 (Archetype Fallback): Falls back to the archetype dataset via
        resolve_domain_archetype(), or 'eval_general_domain.json' if unmatched.

    Args:
        skill_name: Name of the skill (e.g. 'ccba-legal-intel').
        test_cases_dir: Optional directory to search for skill-specific dataset files.

    Returns:
        Dataset filename string (e.g. 'eval_legal_intel.json', 'eval_general_domain.json').
    """
    # Tier 1: Skill-Specific dataset lookup
    if test_cases_dir is not None:
        dir_path = Path(test_cases_dir)
        if dir_path.is_dir():
            clean_skill = (
                skill_name.strip()
                .lower()
                .removeprefix("ccba-")
                .removeprefix("bigbim-")
                .replace("-", "_")
            )
            canonical_skill = skill_name.strip().lower().replace("-", "_")
            for candidate in [
                f"eval_{clean_skill}.json",
                f"{clean_skill}.json",
                f"eval_{canonical_skill}.json",
            ]:
                if (dir_path / candidate).is_file():
                    return candidate

    # Tier 2: Archetype Fallback
    arch = resolve_domain_archetype(skill_name)
    return arch.dataset_file if arch else "eval_general_domain.json"


def resolve_domain_dataset_path(
    skill_name: str,
    test_cases_dir: Path | str | None = None,
) -> Path | None:
    """Resolves the absolute Path of an existing evaluation dataset file for a skill (ADR-0060).

    Resolution order:
      1. Skill-specific dataset in test_cases_dir (eval_{clean_skill}.json, etc.).
      2. Archetype dataset file in test_cases_dir.
      3. eval_general_domain.json in test_cases_dir.

    Args:
        skill_name: Name of the skill (e.g. 'ccba-legal-intel').
        test_cases_dir: Directory where dataset files reside.  If None, returns None.

    Returns:
        Path object pointing to the first existing dataset file, or None if test_cases_dir is not
        provided or no file is found.
    """
    if test_cases_dir is None:
        return None

    dir_path = Path(test_cases_dir)
    if not dir_path.is_dir():
        return None

    filename = resolve_domain_dataset(skill_name, test_cases_dir)
    candidate = dir_path / filename
    if candidate.is_file():
        return candidate.resolve()

    # Final fallback: eval_general_domain.json
    fallback = dir_path / "eval_general_domain.json"
    if fallback.is_file():
        return fallback.resolve()

    return None


def get_default_domain_scorers(skill_name: str) -> list[BaseScorer]:
    """Provides domain-aligned default scorers based on target skill name.

    Args:
        skill_name: Name of the skill.

    Returns:
        List of initialized BaseScorer instances.
    """
    arch = resolve_domain_archetype(skill_name)
    return arch.scorer_factory() if arch else get_lean_structural_scorers()
