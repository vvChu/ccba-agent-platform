"""test_tuner_token_yield_sprint3.py - Unit tests for Sprint 3 Token Yield Optimization & Short-Circuit.

Tests:
1. remaining_strategies() pure function detection for unapplied vs exhausted skills.
2. 0-token short-circuit on exhausted skills in GitRatchetOptimizer.run() and run_async().
3. Baseline score preservation on short-circuit.
4. hard_max_tokens_per_skill ceiling that accounts for total session tokens (including baseline).
5. Daemon-level short-circuit and hash-based exclusion until mutation_strategies.yaml changes.
6. SSOT local model default routing ("qwen-local-primary").
7. skip_cooldown=True default in NightlyTunerDaemon.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ccba_harness.evals.daemon import (
    NightlyTunerDaemon,
    get_last_applied_strategies_hash,
    get_mutation_strategies_hash,
    save_applied_strategies_hash,
)
from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    LLMTaskAdapter,
    RatchetConfig,
    load_mutation_strategies,
    remaining_strategies,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_remaining_strategies_detection(tmp_path: Path) -> None:
    """Verify remaining_strategies identifies unapplied strategies and returns empty on exhausted skills."""
    # Case 1: Fresh minimal skill content
    fresh_skill = (
        "---\nname: fresh-skill\ndescription: Test\n---\n# Fresh Skill\n\nInstructions here.\n"
    )
    unapplied_fresh = remaining_strategies(fresh_skill, "ccba-test-skill")
    assert len(unapplied_fresh) > 0

    # Case 2: Exhausted skill prompt containing all coding strategies
    all_strategies = load_mutation_strategies()
    coding_strategies = all_strategies.get("coding", [])
    assert len(coding_strategies) > 0

    exhausted_content = (
        "---\nname: exhausted-skill\ndescription: Fully tuned\n---\n# Instructions\n\n"
    )
    for _s_name, s_content in coding_strategies:
        exhausted_content += f"\n\n{s_content}\n"

    unapplied_exhausted = remaining_strategies(exhausted_content, "ccba-file-stability-guard")
    assert unapplied_exhausted == []

    # Case 3: Real exhausted skill in repo: ccba-maskara
    maskara_path = Path(".agents/skills/ccba-maskara/SKILL.md")
    if maskara_path.exists():
        maskara_content = maskara_path.read_text(encoding="utf-8")
        unapplied_maskara = remaining_strategies(maskara_content, "ccba-maskara")
        assert unapplied_maskara == []


def test_zero_token_short_circuit_on_exhausted_skill_sync(tmp_path: Path) -> None:
    """Verify optimizer.run() short-circuits with exactly 0 tokens on exhausted skills."""
    all_strategies = load_mutation_strategies()
    coding_strategies = all_strategies.get("coding", [])

    skill_file = tmp_path / "SKILL.md"
    body = "# Exhausted Skill\n"
    for _, s_content in coding_strategies:
        body += f"\n{s_content}\n"
    skill_file.write_text(body, encoding="utf-8")

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-file-stability-guard",
        baseline_score=87.5,
    )
    optimizer = GitRatchetOptimizer(config, dry_run_git=True)

    report = optimizer.run()

    assert report.halt_reason == "HALT_NO_FURTHER_STRATEGIES"
    assert report.total_tokens == 0
    assert report.prompt_tokens == 0
    assert report.completion_tokens == 0
    assert report.total_iterations == 0
    assert report.kept_commits == 0
    assert report.initial_score == 87.5
    assert report.final_score == 87.5


@pytest.mark.asyncio
async def test_zero_token_short_circuit_on_exhausted_skill_async(tmp_path: Path) -> None:
    """Verify optimizer.run_async() parity: short-circuits with exactly 0 tokens on exhausted skills."""
    all_strategies = load_mutation_strategies()
    coding_strategies = all_strategies.get("coding", [])

    skill_file = tmp_path / "SKILL.md"
    body = "# Exhausted Skill Async\n"
    for _, s_content in coding_strategies:
        body += f"\n{s_content}\n"
    skill_file.write_text(body, encoding="utf-8")

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-file-stability-guard",
        baseline_score=92.0,
    )
    optimizer = GitRatchetOptimizer(config, dry_run_git=True)

    report = await optimizer.run_async()

    assert report.halt_reason == "HALT_NO_FURTHER_STRATEGIES"
    assert report.total_tokens == 0
    assert report.prompt_tokens == 0
    assert report.completion_tokens == 0
    assert report.total_iterations == 0
    assert report.initial_score == 92.0
    assert report.final_score == 92.0


def test_hard_max_token_ceiling_blocks_after_baseline(tmp_path: Path) -> None:
    """Verify optimizer halts before iteration 1 if baseline evaluation alone hits hard_max_tokens_per_skill."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Minimal Skill\n\nInstructions.\n", encoding="utf-8")

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="test-skill",
        hard_max_tokens_per_skill=100_000,
    )
    optimizer = GitRatchetOptimizer(config, dry_run_git=True)

    def mock_eval_sync(content: str, dataset: list[EvalItem] | None = None) -> EvalReport:
        # Simulate baseline evaluation consuming 120,000 tokens
        optimizer.token_tracker.record_usage(60_000, 60_000)
        return EvalReport(
            total_items=1,
            passed_items=1,
            failed_items=0,
            overall_score=80.0,
            pass_rate=100.0,
            item_results=[
                EvalItemResult(
                    item_id="item_01",
                    task_output="ok",
                    scores=[],
                    composite_score=80.0,
                    passed=True,
                )
            ],
        )

    optimizer._eval_sync = mock_eval_sync  # type: ignore[assignment]

    report = optimizer.run()

    assert report.halt_reason == "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"
    assert report.total_iterations == 0
    assert report.total_tokens == 120_000


def test_hard_max_token_ceiling_includes_baseline_in_early_stop(tmp_path: Path) -> None:
    """Verify _check_budget_and_early_stop accounts for baseline tokens in total session count."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Skill\n", encoding="utf-8")

    config = RatchetConfig(
        target_file=skill_file,
        hard_max_tokens_per_skill=300_000,
    )
    optimizer = GitRatchetOptimizer(config, dry_run_git=True)

    # Baseline consumed 250,000 tokens
    optimizer.token_tracker.record_usage(150_000, 100_000)
    baseline_tokens = 250_000

    from ccba_harness.evals.tuner import _RatchetLoopState

    state = _RatchetLoopState(best_score=75.0, best_content="# Skill\n")

    # Mutation consumed 60,000 tokens -> total_tokens = 310,000 >= 300,000 hard ceiling
    optimizer.token_tracker.record_usage(30_000, 30_000)

    should_stop, reason = optimizer._check_budget_and_early_stop(
        iter_idx=1,
        effective_patience=3,
        baseline_tokens=baseline_tokens,
        state=state,
    )

    assert should_stop is True
    assert reason == "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"


def test_daemon_skips_exhausted_skills_until_yaml_hash_changes(tmp_path: Path) -> None:
    """Verify daemon skips exhausted skills when mutation_strategies.yaml hash is unchanged."""
    root = tmp_path / "repo"
    skills_dir = root / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    maskara_dir = skills_dir / "ccba-maskara"
    maskara_dir.mkdir(parents=True, exist_ok=True)

    all_strategies = load_mutation_strategies()
    coding_strategies = all_strategies.get("coding", [])

    maskara_skill = maskara_dir / "SKILL.md"
    body = "---\nname: ccba-maskara\n---\n# Maskara\n"
    for _, s_content in coding_strategies:
        body += f"\n{s_content}\n"
    maskara_skill.write_text(body, encoding="utf-8")

    # Record current hash as already applied
    current_hash = get_mutation_strategies_hash()
    assert current_hash != ""
    save_applied_strategies_hash(root, current_hash)
    assert get_last_applied_strategies_hash(root) == current_hash

    daemon = NightlyTunerDaemon(root=root, target_skills=["ccba-maskara"], skip_cooldown=True)
    discovered = daemon.discover_skills_and_datasets()
    assert len(discovered) == 1
    assert discovered[0]["is_exhausted"] is True
    assert discovered[0]["strat_hash_unchanged"] is True

    # Run batch (dry_run=True)
    report = daemon.run_nightly_batch(dry_run=True)
    assert report.total_skills_scanned == 1
    assert report.total_tokens == 0
    assert report.total_commits == 0
    assert report.results[0].status == "HALT_NO_FURTHER_STRATEGIES"


def test_daemon_does_not_skip_exhausted_when_yaml_hash_changes(tmp_path: Path) -> None:
    """Verify daemon does NOT skip exhausted skills if mutation_strategies.yaml hash changed."""
    root = tmp_path / "repo"
    skills_dir = root / ".agents" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    maskara_dir = skills_dir / "ccba-maskara"
    maskara_dir.mkdir(parents=True, exist_ok=True)

    all_strategies = load_mutation_strategies()
    coding_strategies = all_strategies.get("coding", [])

    maskara_skill = maskara_dir / "SKILL.md"
    body = "---\nname: ccba-maskara\n---\n# Maskara\n"
    for _, s_content in coding_strategies:
        body += f"\n{s_content}\n"
    maskara_skill.write_text(body, encoding="utf-8")

    # Save an outdated hash
    save_applied_strategies_hash(root, "outdated_hash_value_12345")

    daemon = NightlyTunerDaemon(root=root, target_skills=["ccba-maskara"], skip_cooldown=True)
    discovered = daemon.discover_skills_and_datasets()
    assert len(discovered) == 1
    assert discovered[0]["is_exhausted"] is True
    # Because current hash != outdated hash, strat_hash_unchanged is False
    assert discovered[0]["strat_hash_unchanged"] is False


def test_local_model_default_routing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify default model resolves to qwen-local-primary without requiring env vars."""
    monkeypatch.delenv("CCBA_TUNER_MODEL", raising=False)
    config = RatchetConfig(target_file=Path("SKILL.md"))
    assert config.llm_model == "qwen-local-primary"

    mock_client = MagicMock()
    adapter = LLMTaskAdapter(client=mock_client)
    assert adapter.model == "qwen-local-primary"


def test_skip_cooldown_default_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify skip_cooldown defaults to True in NightlyTunerDaemon and respects CCBA_TUNER_SKIP_COOLDOWN."""
    monkeypatch.delenv("CCBA_TUNER_SKIP_COOLDOWN", raising=False)
    daemon = NightlyTunerDaemon()
    assert daemon.skip_cooldown is True

    monkeypatch.setenv("CCBA_TUNER_SKIP_COOLDOWN", "0")
    daemon_override = NightlyTunerDaemon()
    assert daemon_override.skip_cooldown is False
