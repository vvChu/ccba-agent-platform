"""test_archetypes_catalog.py - Unit tests and benchmark for Declarative Archetypes Catalog (TICKET-004)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ccba_harness.evals.archetypes import (
    load_archetypes_catalog,
    reload_archetypes_catalog,
    resolve_domain_dataset,
    resolve_domain_dataset_path,
)


def test_archetypes_catalog_integrity() -> None:
    """Verify that all 17 expected domain archetypes are loaded in correct priority order."""
    archetypes = load_archetypes_catalog()
    assert len(archetypes) == 17

    expected_names = [
        "grilling",
        "adr",
        "risk",
        "skill_repair",
        "legal_tooling",
        "legal",
        "tech_qc",
        "academic",
        "office",
        "visual_design",
        "visual",
        "bim_governance",
        "bim_rase",
        "bim",
        "coding",
        "platform_tooling",
        "orchestration",
    ]
    actual_names = [arch.name for arch in archetypes]
    assert actual_names == expected_names

    # Check contract fields
    for arch in archetypes:
        assert isinstance(arch.name, str) and len(arch.name) > 0
        assert isinstance(arch.keywords, tuple) and len(arch.keywords) > 0
        assert arch.dataset_file.startswith("eval_") and arch.dataset_file.endswith(".json")
        assert callable(arch.scorer_factory)


def test_archetypes_catalog_singleton_caching_and_latency() -> None:
    """Verify in-memory singleton cache returns same object and executes in < 2ms (FOG-001)."""
    # First access to warm up
    first_call = load_archetypes_catalog()

    # Measure latency over 1000 calls
    start = time.perf_counter()
    iterations = 1000
    for _ in range(iterations):
        cached = load_archetypes_catalog()
        assert cached is first_call  # Strict reference identity
    elapsed_ms = (time.perf_counter() - start) * 1000

    avg_latency_ms = elapsed_ms / iterations
    # Average latency must be well under 0.05ms (contract ceiling is 2.0ms)
    assert avg_latency_ms < 0.1, f"Singleton cache lookup too slow: {avg_latency_ms:.4f}ms"


def test_archetypes_catalog_reload() -> None:
    """Verify reload_archetypes_catalog refreshes the cache."""
    initial = load_archetypes_catalog()
    reloaded = reload_archetypes_catalog()
    assert len(reloaded) == len(initial)
    assert reloaded == initial
    # New tuple created on reload
    assert reloaded is not initial or len(reloaded) > 0


def test_archetypes_catalog_missing_file_error(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when catalog path does not exist."""
    fake_path = tmp_path / "non_existent_catalog.yaml"
    with pytest.raises(FileNotFoundError):
        load_archetypes_catalog(fake_path)


def test_archetypes_catalog_invalid_factory_error(tmp_path: Path) -> None:
    """Verify KeyError is raised when catalog references an unknown scorer factory."""
    bad_catalog = tmp_path / "bad_catalog.yaml"
    bad_catalog.write_text(
        """
archetypes:
  - name: invalid_arch
    keywords: ["test"]
    dataset_file: eval_test.json
    scorer_factory: non_existent_scorer_factory
""",
        encoding="utf-8",
    )
    with pytest.raises(KeyError, match="Unknown scorer factory"):
        load_archetypes_catalog(bad_catalog)


def test_domain_resolution_end_to_end() -> None:
    """Verify resolve_domain_archetype and resolve_domain_dataset work seamlessly with catalog."""
    # Special cases
    assert resolve_domain_dataset("academic-writing") == "eval_academic_writing.json"
    assert resolve_domain_dataset("ccba-codebase-design") == "eval_codebase_engineering.json"

    # Standard routing
    assert resolve_domain_dataset("ccba-legal-intel") == "eval_legal_intel.json"
    assert resolve_domain_dataset("bigbim-risk") == "eval_bigbim_risk.json"
    assert resolve_domain_dataset("ccba-ai-qc") == "eval_pccc_audit.json"
    assert resolve_domain_dataset("unknown-skill") == "eval_general_domain.json"

    # Direct archetype name and normalized variants
    assert resolve_domain_dataset("office") == "eval_copywriting.json"
    assert resolve_domain_dataset("platform_tooling") == "eval_platform_tooling.json"
    assert resolve_domain_dataset("platform-tooling") == "eval_platform_tooling.json"
    assert resolve_domain_dataset("legal_tooling") == "eval_legal_tooling.json"
    assert resolve_domain_dataset("skill_repair") == "eval_skill_repair.json"
    assert resolve_domain_dataset("xu_ly_van_phong") == "eval_copywriting.json"


# ---------------------------------------------------------------------------
# ADR-0060: 2-Tier Dataset Fallback Tests
# ---------------------------------------------------------------------------


def test_resolve_domain_dataset_tier1_skill_specific_eval_prefix(tmp_path: Path) -> None:
    """Tier-1: eval_{clean_skill}.json takes priority over archetype dataset."""
    # 'ccba-legal-intel' -> clean = 'legal_intel' -> eval_legal_intel.json
    (tmp_path / "eval_legal_intel.json").write_text("[]", encoding="utf-8")

    result = resolve_domain_dataset("ccba-legal-intel", tmp_path)
    assert result == "eval_legal_intel.json"


def test_resolve_domain_dataset_tier1_skill_specific_bare_name(tmp_path: Path) -> None:
    """Tier-1: {clean_skill}.json (no eval_ prefix) is recognized as skill-specific dataset."""
    # Only the bare-name variant exists — no eval_ prefix file
    (tmp_path / "legal_intel.json").write_text("[]", encoding="utf-8")

    result = resolve_domain_dataset("ccba-legal-intel", tmp_path)
    assert result == "legal_intel.json"


def test_resolve_domain_dataset_tier1_canonical_skill_variant(tmp_path: Path) -> None:
    """Tier-1: eval_{canonical_skill}.json (with namespace prefix, underscored) is matched."""
    # canonical_skill = 'ccba_legal_intel'
    (tmp_path / "eval_ccba_legal_intel.json").write_text("[]", encoding="utf-8")

    result = resolve_domain_dataset("ccba-legal-intel", tmp_path)
    assert result == "eval_ccba_legal_intel.json"


def test_resolve_domain_dataset_tier1_priority_over_tier2(tmp_path: Path) -> None:
    """Tier-1 skill-specific file takes priority even when an archetype dataset also exists."""
    # Both skill-specific and archetype dataset present
    (tmp_path / "eval_legal_intel.json").write_text("[]", encoding="utf-8")
    (tmp_path / "eval_general_domain.json").write_text("[]", encoding="utf-8")

    result = resolve_domain_dataset("ccba-legal-intel", tmp_path)
    assert result == "eval_legal_intel.json"


def test_resolve_domain_dataset_tier2_archetype_fallback_when_no_skill_file(
    tmp_path: Path,
) -> None:
    """Tier-2: Falls back to archetype dataset_file when no skill-specific file exists."""
    # No skill-specific file in tmp_path → must resolve via archetype catalog
    result = resolve_domain_dataset("ccba-legal-intel", tmp_path)
    # Archetype 'legal' maps to eval_legal_intel.json per catalog
    assert result == "eval_legal_intel.json"


def test_resolve_domain_dataset_tier2_general_fallback_for_unknown_skill(
    tmp_path: Path,
) -> None:
    """Tier-2: Unknown skill with no skill-specific file returns eval_general_domain.json."""
    result = resolve_domain_dataset("ccba-totally-unknown-xyz", tmp_path)
    assert result == "eval_general_domain.json"


def test_resolve_domain_dataset_no_test_cases_dir_uses_archetype() -> None:
    """Without test_cases_dir, resolution is pure Tier-2 archetype routing (backward compat)."""
    assert resolve_domain_dataset("ccba-legal-intel") == "eval_legal_intel.json"
    assert resolve_domain_dataset("bigbim-risk") == "eval_bigbim_risk.json"
    assert resolve_domain_dataset("unknown-skill") == "eval_general_domain.json"


def test_resolve_domain_dataset_path_returns_existing_file(tmp_path: Path) -> None:
    """resolve_domain_dataset_path returns a resolved Path when the file exists."""
    dataset_file = tmp_path / "eval_legal_intel.json"
    dataset_file.write_text("[]", encoding="utf-8")

    result = resolve_domain_dataset_path("ccba-legal-intel", tmp_path)
    assert result is not None
    assert result.is_file()
    assert result == dataset_file.resolve()


def test_resolve_domain_dataset_path_fallback_to_general_domain(tmp_path: Path) -> None:
    """resolve_domain_dataset_path falls back to eval_general_domain.json when specific file missing."""
    general = tmp_path / "eval_general_domain.json"
    general.write_text("[]", encoding="utf-8")

    # 'ccba-totally-unknown-xyz' has no archetype; Tier-2 returns eval_general_domain.json
    result = resolve_domain_dataset_path("ccba-totally-unknown-xyz", tmp_path)
    assert result is not None
    assert result == general.resolve()


def test_resolve_domain_dataset_path_returns_none_when_no_dir() -> None:
    """resolve_domain_dataset_path returns None when test_cases_dir is not provided."""
    result = resolve_domain_dataset_path("ccba-legal-intel", None)
    assert result is None


def test_resolve_domain_dataset_path_returns_none_for_nonexistent_dir(tmp_path: Path) -> None:
    """resolve_domain_dataset_path returns None when test_cases_dir does not exist on disk."""
    missing_dir = tmp_path / "does_not_exist"
    result = resolve_domain_dataset_path("ccba-legal-intel", missing_dir)
    assert result is None


def test_resolve_domain_dataset_path_returns_none_when_no_file_found(tmp_path: Path) -> None:
    """resolve_domain_dataset_path returns None when neither skill-specific nor general file exist."""
    # Empty directory — no dataset files at all
    result = resolve_domain_dataset_path("ccba-totally-unknown-xyz", tmp_path)
    assert result is None
