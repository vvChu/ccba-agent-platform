"""Tests for declarative scorers hyperparameters externalization (TICKET-005).

Verifies:
1. Declarative YAML loading for all 18 evaluation suites.
2. In-Memory Singleton caching performance (O(1) latency < 0.05 ms).
3. Override precedence hierarchy:
   - Custom override dict > YAML config > code defaults.
4. Dynamic per-item metadata overrides (BaseScorer.get_effective_weight, get_effective_is_critical).
5. Dynamic length bounds override on LengthBoundsScorer.
"""

from __future__ import annotations

import time

import pytest

from ccba_harness.evals.models import EvalItem
from ccba_harness.evals.scorers import (
    LengthBoundsScorer,
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
    get_scorer_params,
    get_skill_repair_scorers,
    get_visual_design_scorers,
    get_visual_diagram_scorers,
    load_scorers_config,
    reload_scorers_config,
)


def test_load_scorers_config_all_18_suites() -> None:
    """Verifies that all 18 suites are defined in scorers_config.yaml with valid structures."""
    config = reload_scorers_config()
    assert isinstance(config, dict)
    assert len(config) >= 18

    expected_suites = [
        "orchestration",
        "coding",
        "lean_structural",
        "legal",
        "legal_tooling",
        "platform_tooling",
        "office",
        "visual_diagram",
        "pccc",
        "bim_classification",
        "academic",
        "bigbim_risk",
        "bigbim_governance",
        "bigbim_rase",
        "grilling",
        "adr_lifecycle",
        "skill_repair",
        "visual_design",
    ]

    for suite in expected_suites:
        assert suite in config, f"Suite '{suite}' missing from scorers_config.yaml"
        suite_scorers = config[suite]
        assert isinstance(suite_scorers, dict)
        assert len(suite_scorers) >= 2, f"Suite '{suite}' must have at least 2 scorers"

        # Check weights sum approximately to 1.0 (within 0.05 tolerance)
        total_weight = sum(
            scorer_params.get("weight", 0.0)
            for scorer_params in suite_scorers.values()
            if isinstance(scorer_params, dict)
        )
        assert 0.95 <= total_weight <= 1.05, (
            f"Suite '{suite}' weights sum to {total_weight}, expected ~1.0"
        )


def test_scorers_config_singleton_cache_latency() -> None:
    """Confirms O(1) in-memory singleton retrieval satisfies FOG-002 latency requirement (< 0.05 ms)."""
    # Prime cache
    load_scorers_config()

    iterations = 2000
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = load_scorers_config()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    avg_latency_ms = elapsed_ms / iterations

    # Latency of cached dictionary lookup must be under 0.05ms (typically < 0.001ms)
    assert avg_latency_ms < 0.05, (
        f"Singleton cache lookup too slow: {avg_latency_ms:.5f}ms >= 0.05ms"
    )


def test_scorer_hyperparameter_override_precedence() -> None:
    """Verifies 3-level priority: override_config > YAML > code defaults."""
    # 1. Fallback to code defaults when suite not in config
    p_fallback = get_scorer_params(
        "non_existent_suite",
        "dummy_scorer",
        {"weight": 0.42, "is_critical": False},
        override_config=None,
    )
    assert p_fallback["weight"] == 0.42
    assert p_fallback["is_critical"] is False

    # 2. YAML config takes precedence over code defaults
    p_yaml = get_scorer_params(
        "coding",
        "hard_completion_lock",
        {"weight": 0.10, "is_critical": False},
        override_config=None,
    )
    # in YAML: weight: 0.40, is_critical: true
    assert p_yaml["weight"] == 0.40
    assert p_yaml["is_critical"] is True

    # 3. override_config takes top precedence over YAML config
    custom_override = {"hard_completion_lock": {"weight": 0.85, "is_critical": False}}
    p_override = get_scorer_params(
        "coding",
        "hard_completion_lock",
        {"weight": 0.10, "is_critical": False},
        override_config=custom_override,
    )
    assert p_override["weight"] == 0.85
    assert p_override["is_critical"] is False


def test_factory_accepts_override_config() -> None:
    """Verifies that all factory functions accept an override_config and update weights."""
    custom_override = {
        "depth": {"weight": 0.99, "min_length": 50, "max_length": 1000},
    }
    scorers = get_coding_scorers(override_config=custom_override)
    depth_scorer = next(s for s in scorers if s.name == "depth")
    assert isinstance(depth_scorer, LengthBoundsScorer)
    assert depth_scorer.weight == 0.99
    assert depth_scorer.min_length == 50
    assert depth_scorer.max_length == 1000


def test_dynamic_per_item_metadata_overrides() -> None:
    """Verifies BaseScorer dynamic weight and critical resolution via item.metadata['scorer_config']."""
    scorers = get_orchestration_scorers()
    single_writer = next(s for s in scorers if s.name == "single_writer_invariant")

    # Default item without metadata override
    item_default = EvalItem(id="item-1", input_prompt="test")
    assert single_writer.get_effective_weight(item_default) == single_writer.weight
    assert single_writer.get_effective_is_critical(item_default) == single_writer.is_critical

    # Item with metadata override
    item_override = EvalItem(
        id="item-2",
        input_prompt="test",
        metadata={
            "scorer_config": {
                "single_writer_invariant": {
                    "weight": 0.77,
                    "is_critical": False,
                }
            }
        },
    )
    assert single_writer.get_effective_weight(item_override) == 0.77
    assert single_writer.get_effective_is_critical(item_override) is False


@pytest.mark.asyncio
async def test_length_bounds_scorer_per_item_override() -> None:
    """Verifies LengthBoundsScorer respects per-item metadata overrides during score()."""
    scorer = LengthBoundsScorer(name="depth", min_length=100, max_length=500, weight=0.2)

    # Standard item: text with 50 chars fails default min_length=100
    short_text = "A" * 50
    item_standard = EvalItem(id="len-1", input_prompt="test")
    res_standard = await scorer.score(short_text, item_standard)
    assert res_standard.score == 0.0  # Under length penalty

    # Item with relaxed min_length in metadata: 50 chars passes min_length=40
    item_relaxed = EvalItem(
        id="len-2",
        input_prompt="test",
        metadata={
            "scorer_config": {
                "depth": {
                    "min_length": 40,
                    "max_length": 500,
                }
            }
        },
    )
    res_relaxed = await scorer.score(short_text, item_relaxed)
    assert res_relaxed.score == 1.0


def test_all_18_scorer_factories_instantiate_cleanly() -> None:
    """Verifies that all 18 scorer factory functions return valid BaseScorer lists."""
    factories = [
        get_orchestration_scorers,
        get_coding_scorers,
        get_lean_structural_scorers,
        get_legal_scorers,
        get_legal_tooling_scorers,
        get_platform_tooling_scorers,
        get_office_scorers,
        get_visual_diagram_scorers,
        get_pccc_scorers,
        get_bim_classification_scorers,
        get_academic_scorers,
        get_bigbim_risk_scorers,
        get_bigbim_governance_scorers,
        get_bigbim_rase_scorers,
        get_grilling_scorers,
        get_adr_lifecycle_scorers,
        get_skill_repair_scorers,
        get_visual_design_scorers,
    ]

    for factory in factories:
        scorers = factory()
        assert len(scorers) >= 2
        for s in scorers:
            assert s.weight > 0.0
            assert isinstance(s.is_critical, bool)
