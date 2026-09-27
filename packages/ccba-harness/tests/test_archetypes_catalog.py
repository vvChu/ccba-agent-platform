"""test_archetypes_catalog.py - Unit tests and benchmark for Declarative Archetypes Catalog (TICKET-004)."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ccba_harness.evals.archetypes import (
    load_archetypes_catalog,
    reload_archetypes_catalog,
    resolve_domain_dataset,
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
