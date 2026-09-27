"""Tests for declarative tuner hyperparameters externalization and 4-tier precedence (TICKET-006).

Verifies:
1. Declarative YAML loading for tuner configuration.
2. In-Memory Singleton caching performance (O(1) latency < 0.05 ms).
3. 4-tier configuration precedence:
   - Explicit Parameter > Environment Variable > Declarative YAML > Code Fallback.
4. TokenUsageTracker and RateLimiter declarative configuration integration.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from ccba_harness.evals.tuner import (
    DEFAULT_MUTATION_STRATEGIES_PATH,
    AdaptiveRateLimiter,
    GitRatchetOptimizer,
    RatchetConfig,
    TokenUsageTracker,
    load_mutation_strategies,
    load_tuner_config,
    reload_mutation_strategies,
    reload_tuner_config,
)


def test_load_tuner_config_valid() -> None:
    """Verifies that tuner_config.yaml loads properly with required sections."""
    cfg = reload_tuner_config()
    assert isinstance(cfg, dict)
    assert "ratchet" in cfg
    assert "tokens" in cfg
    assert "execution" in cfg
    assert "daemon" in cfg

    # Verify key default values
    assert cfg["ratchet"]["target_score"] == 90.0
    assert cfg["ratchet"]["max_iterations"] == 10
    assert cfg["ratchet"]["patience"] == 3
    assert cfg["tokens"]["budget_ceiling"] == 5_000_000
    assert cfg["tokens"]["per_skill_mutation_budget"] == 250_000
    assert cfg["tokens"]["hard_max_tokens_per_skill"] == 500_000
    assert cfg["execution"]["max_concurrency"] == 5
    assert cfg["execution"]["latency_threshold_s"] == 4.0


def test_tuner_config_singleton_cache_latency() -> None:
    """Confirms O(1) in-memory singleton cache lookup latency is < 0.05 ms."""
    load_tuner_config()

    iterations = 2000
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = load_tuner_config()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    avg_latency_ms = elapsed_ms / iterations

    assert avg_latency_ms < 0.05, (
        f"Singleton cache lookup too slow: {avg_latency_ms:.5f}ms >= 0.05ms"
    )


def test_token_usage_tracker_initializes_from_config() -> None:
    """Verifies TokenUsageTracker uses budget_ceiling from declarative config by default."""
    tracker = TokenUsageTracker()
    assert tracker.budget_ceiling == 5_000_000

    # User explicit override must take precedence
    custom_tracker = TokenUsageTracker(budget_ceiling=1_234_567)
    assert custom_tracker.budget_ceiling == 1_234_567


def test_rate_limiter_initializes_from_config() -> None:
    """Verifies AdaptiveRateLimiter defaults latency_threshold_s to config value."""
    limiter = AdaptiveRateLimiter()
    assert limiter.latency_threshold_s == 4.0

    # Explicit override takes precedence
    custom_limiter = AdaptiveRateLimiter(latency_threshold_s=8.5)
    assert custom_limiter.latency_threshold_s == 8.5


def test_ratchet_config_4_tier_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verifies complete 4-tier precedence: User > Env > YAML > Default."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Test Skill", encoding="utf-8")

    # Tier 1: User explicit parameter must NOT be overridden by env or YAML
    monkeypatch.setenv("CCBA_TUNER_TARGET_SCORE", "80.0")
    monkeypatch.setenv("CCBA_TUNER_MAX_ITERATIONS", "99")
    monkeypatch.setenv("CCBA_TUNER_CONCURRENCY", "12")

    cfg_tier1 = RatchetConfig(
        target_file=skill_file,
        target_score=95.5,
        max_iterations=5,
        max_concurrency=2,
    )
    assert cfg_tier1.target_score == 95.5
    assert cfg_tier1.max_iterations == 5
    assert cfg_tier1.max_concurrency == 2

    # Tier 2: Environment variables take precedence when user does not specify
    cfg_tier2 = RatchetConfig(target_file=skill_file)
    assert cfg_tier2.target_score == 80.0
    assert cfg_tier2.max_iterations == 99
    assert cfg_tier2.max_concurrency == 12

    # Tier 3: Declarative YAML takes precedence when env vars are absent
    monkeypatch.delenv("CCBA_TUNER_TARGET_SCORE", raising=False)
    monkeypatch.delenv("CCBA_TUNER_MAX_ITERATIONS", raising=False)
    monkeypatch.delenv("CCBA_TUNER_CONCURRENCY", raising=False)

    cfg_tier3 = RatchetConfig(target_file=skill_file)
    assert cfg_tier3.target_score == 90.0
    assert cfg_tier3.max_iterations == 10
    assert cfg_tier3.max_concurrency == 5
    assert cfg_tier3.patience == 3
    assert cfg_tier3.split_ratio == 0.7
    assert cfg_tier3.token_budget == 5_000_000


def test_load_mutation_strategies_all_17_archetypes() -> None:
    """Verifies that mutation_strategies.yaml loads all 17 archetypes plus general fallback."""
    assert DEFAULT_MUTATION_STRATEGIES_PATH.is_file()

    strategies = reload_mutation_strategies()
    assert isinstance(strategies, dict)

    expected_archetypes = {
        "academic",
        "bim_governance",
        "bim_rase",
        "bim",
        "coding",
        "orchestration",
        "tech_qc",
        "legal",
        "grilling",
        "adr",
        "risk",
        "skill_repair",
        "legal_tooling",
        "office",
        "visual_design",
        "visual",
        "platform_tooling",
        "general",
    }

    assert expected_archetypes.issubset(set(strategies.keys()))

    for arch in expected_archetypes:
        strat_list = strategies[arch]
        assert len(strat_list) >= 1, f"Archetype {arch} has no strategies"
        for name, content in strat_list:
            assert isinstance(name, str) and len(name) > 0
            assert isinstance(content, str) and len(content) > 0
            assert content.startswith("## ")


def test_load_mutation_strategies_singleton_caching_and_latency() -> None:
    """Verifies in-memory singleton caching and O(1) latency < 0.05 ms for mutation strategies."""
    s1 = load_mutation_strategies()
    s2 = load_mutation_strategies()
    assert s1 is s2

    iterations = 2000
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = load_mutation_strategies()
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    avg_latency_ms = elapsed_ms / iterations

    assert avg_latency_ms < 0.05, f"Singleton cache lookup too slow: {avg_latency_ms:.5f}ms"

    reloaded = reload_mutation_strategies()
    assert isinstance(reloaded, dict)
    assert reloaded == s1


def test_propose_mutation_declarative_and_general_fallback(tmp_path: Path) -> None:
    """Verifies propose_mutation uses declarative strategies and falls back to general for unmapped skills."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: unmapped-domain-skill\n---\n# Unmapped Skill\n"
    target.write_text(base_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=str(target), skill_name="unmapped-domain-skill")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    # Iteration 1 adds fallback Strategy 1 (Lean Structural Architecture & Progressive Disclosure)
    mut1 = tuner.propose_mutation(base_content, 1)
    assert "## Bộc Lộ Dần & Cấu Trúc Tinh Gọn (Progressive Disclosure)" in mut1

    # Iteration 2 adds fallback Strategy 2 (Operational Clarity & Verification Standard)
    mut2 = tuner.propose_mutation(mut1, 2)
    assert mut2 != mut1
    assert "## Chuẩn Mực Vận Hành & Khảo Sát Kiểm Chứng" in mut2

    # Iteration 3: All strategies applied -> returns unchanged
    mut3 = tuner.propose_mutation(mut2, 3)
    assert mut3 == mut2
