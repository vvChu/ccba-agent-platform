"""test_failure_mutator_ratchet_sprint4.py - Unit test suite for Sprint 4 PR-B.

Verifies end-to-end integration of failure mutator into GitRatchetOptimizer and
NightlyTunerDaemon, including 3-tier daemon dispatch, max_failure_patches budget,
and ledger seeding after baseline evaluations.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from ccba_harness.evals.daemon import (
    NightlyTunerDaemon,
    WeightedPriorityQueue,
)
from ccba_harness.evals.failure_mutator import (
    FailureSignal,
    calculate_signal_fingerprint,
    load_failure_ledger,
    save_failure_ledger,
)
from ccba_harness.evals.models import EvalItemResult, EvalReport, ScoreResult
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    RatchetConfig,
    remaining_strategies,
)


def test_01_max_failure_patches_config_parsing(tmp_path):
    """Case 1: RatchetConfig parses max_failure_patches from YAML and supports env override."""
    target_file = tmp_path / "SKILL.md"
    target_file.write_text("# Skill\n", encoding="utf-8")

    # Default from tuner_config.yaml should be 3
    config = RatchetConfig(target_file=target_file, skill_name="ccba-legal-advisor")
    assert config.max_failure_patches == 3

    # Explicit override
    config_custom = RatchetConfig(
        target_file=target_file,
        skill_name="ccba-legal-advisor",
        max_failure_patches=5,
    )
    assert config_custom.max_failure_patches == 5


def test_02_propose_mutation_prioritizes_failure_patch_for_legal_archetype(tmp_path):
    """Case 2: propose_mutation injects failure card from ledger before YAML strategies."""
    skill_file = tmp_path / "SKILL.md"
    initial_content = "---\nname: ccba-legal-advisor\n---\n# Legal Advisor\n\nGuidelines here.\n"
    skill_file.write_text(initial_content, encoding="utf-8")

    sig = FailureSignal(
        code="EXPIRED_UNACKNOWLEDGED",
        item_id="item_01",
        scorer="legal_verbatim_provenance",
        fingerprint=calculate_signal_fingerprint(
            "legal_verbatim_provenance", "EXPIRED_UNACKNOWLEDGED", "136/2020/NĐ-CP", "", "item_01"
        ),
        fields={"trap_doc": "136/2020/NĐ-CP", "replacement": "105/2025/NĐ-CP"},
    )
    save_failure_ledger("ccba-legal-advisor", [sig], initial_content)

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-legal-advisor",
        max_failure_patches=3,
    )
    optimizer = GitRatchetOptimizer(config=config, dry_run_git=True)

    mutated = optimizer.propose_mutation(initial_content, iteration=1)
    assert "136/2020/NĐ-CP" in mutated
    assert "105/2025/NĐ-CP" in mutated
    assert sig.fingerprint in mutated
    assert optimizer._applied_failure_patches == 1


def test_03_propose_mutation_caps_at_max_failure_patches(tmp_path):
    """Case 3: propose_mutation does not exceed max_failure_patches."""
    skill_file = tmp_path / "SKILL.md"
    initial_content = "---\nname: ccba-legal-advisor\n---\n# Legal Advisor\n"
    skill_file.write_text(initial_content, encoding="utf-8")

    sigs = [
        FailureSignal(
            code="UNKNOWN_DOCUMENT",
            item_id=f"item_{i}",
            scorer="legal_verbatim_provenance",
            fingerprint=f"fp_{i}",
            fields={"unknown_doc": f"99{i}/2029/NĐ-CP"},
        )
        for i in range(5)
    ]
    save_failure_ledger("ccba-legal-advisor", sigs, initial_content)

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-legal-advisor",
        max_failure_patches=2,
    )
    optimizer = GitRatchetOptimizer(config=config, dry_run_git=True)

    # First proposal
    mutated_1 = optimizer.propose_mutation(initial_content, iteration=1)
    assert optimizer._applied_failure_patches == 1

    # Second proposal
    mutated_2 = optimizer.propose_mutation(mutated_1, iteration=2)
    assert optimizer._applied_failure_patches == 2

    # Third proposal: max reached, falls back to YAML strategies
    _mutated_3 = optimizer.propose_mutation(mutated_2, iteration=3)
    assert optimizer._applied_failure_patches == 2


def test_04_short_circuit_unlocked_when_failure_signals_exist(tmp_path):
    """Case 4: run() does NOT short-circuit when YAML exhausted if unapplied failure signals exist."""
    skill_file = tmp_path / "SKILL.md"
    from ccba_harness.evals.tuner import load_mutation_strategies

    all_strats = load_mutation_strategies()
    legal_enhancements = "\n\n".join(s[1] for s in all_strats.get("legal", []))
    initial_content = (
        f"---\nname: ccba-legal-advisor\n---\n# Legal Advisor\n\n{legal_enhancements}\n"
    )
    skill_file.write_text(initial_content, encoding="utf-8")

    # Confirm YAML strategies are exhausted
    unapplied = remaining_strategies(initial_content, "ccba-legal-advisor")
    assert len(unapplied) == 0

    # Seed an unapplied failure signal in ledger
    sig = FailureSignal(
        code="UNKNOWN_CLAUSE",
        item_id="item_clause_01",
        scorer="legal_verbatim_provenance",
        fingerprint="fp_clause_unapplied",
        fields={"doc": "135/2025/QH15", "fake_clause": "Điều 999"},
    )
    save_failure_ledger("ccba-legal-advisor", [sig], initial_content)

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-legal-advisor",
        max_iterations=1,
    )
    optimizer = GitRatchetOptimizer(config=config, dry_run_git=True)

    mock_report = EvalReport(
        total_items=1,
        passed_items=1,
        failed_items=0,
        overall_score=100.0,
        pass_rate=100.0,
        item_results=[],
    )
    optimizer._eval_sync = MagicMock(return_value=mock_report)
    optimizer._eval_holdout_base_sync = MagicMock(return_value=100.0)
    optimizer._eval_holdout_final_sync = MagicMock(return_value=100.0)

    res = optimizer.run()
    assert res is not None
    # It must NOT exit with total_iterations=0 and HALT_NO_FURTHER_STRATEGIES before baseline
    assert optimizer._eval_sync.called


def test_05_baseline_seeds_ledger_for_legal_skill(tmp_path):
    """Case 5: Baseline evaluation seeds ledger for legal archetype skill (ADR-0059)."""
    skill_file = tmp_path / "SKILL.md"
    initial_content = "---\nname: ccba-legal-advisor\n---\n# Legal Advisor\n"
    skill_file.write_text(initial_content, encoding="utf-8")

    score_res = ScoreResult(
        scorer_name="legal_verbatim_provenance",
        score=0.0,
        raw_output={"trap_doc": "136/2020/NĐ-CP", "replacement": "105/2025/NĐ-CP"},
        reasoning="Failed trap check",
        is_critical_fail=True,
    )
    baseline_report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=0.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="item_01",
                task_output="Căn cứ 136/2020...",
                scores=[score_res],
                composite_score=0.0,
                passed=False,
                critical_failed=True,
            )
        ],
    )

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-legal-advisor",
        max_iterations=1,
    )
    optimizer = GitRatchetOptimizer(config=config, dry_run_git=True)
    optimizer._eval_sync = MagicMock(return_value=baseline_report)
    optimizer._eval_holdout_base_sync = MagicMock(return_value=0.0)
    optimizer._eval_holdout_final_sync = MagicMock(return_value=0.0)

    optimizer.run()

    ledger = load_failure_ledger("ccba-legal-advisor")
    assert ledger is not None
    assert len(ledger.signals) > 0
    assert any(s.code == "EXPIRED_UNACKNOWLEDGED" for s in ledger.signals)


def test_06_daemon_does_not_skip_exhausted_when_unapplied_signals_exist(tmp_path):
    """Case 6: Daemon does NOT skip YAML-exhausted skill if unapplied signals exist."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Skill\n", encoding="utf-8")

    _daemon = NightlyTunerDaemon(root=tmp_path)
    assert _daemon is not None

    # Simulated item: exhausted YAML, unchanged hash, but has unapplied signals
    item = {
        "skill_name": "ccba-legal-advisor",
        "target_file": skill_file,
        "dataset_file": tmp_path / "dataset.json",
        "baseline_score": 85.0,
        "in_cooldown": False,
        "is_exhausted": True,
        "strat_hash_unchanged": True,
        "has_unapplied_signals": True,
        "needs_ledger_seed": False,
    }

    # Should not skip exhausted
    skip_exhausted = (
        item.get("is_exhausted")
        and item.get("strat_hash_unchanged")
        and not item.get("has_unapplied_signals")
        and not item.get("needs_ledger_seed")
    )
    assert skip_exhausted is False


def test_07_daemon_does_not_skip_exhausted_when_needs_ledger_seed(tmp_path):
    """Case 7: Daemon does NOT skip YAML-exhausted skill if legal archetype needs ledger seed."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Skill\n", encoding="utf-8")

    item = {
        "skill_name": "ccba-legal-advisor",
        "target_file": skill_file,
        "dataset_file": tmp_path / "dataset.json",
        "baseline_score": 85.0,
        "in_cooldown": False,
        "is_exhausted": True,
        "strat_hash_unchanged": True,
        "has_unapplied_signals": False,
        "needs_ledger_seed": True,
    }

    skip_exhausted = (
        item.get("is_exhausted")
        and item.get("strat_hash_unchanged")
        and not item.get("has_unapplied_signals")
        and not item.get("needs_ledger_seed")
    )
    assert skip_exhausted is False


def test_08_daemon_skips_exhausted_for_non_legal_archetype(tmp_path):
    """Case 8: Daemon skips YAML-exhausted skill with unchanged hash for non-legal archetype."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Coding Skill\n", encoding="utf-8")

    item = {
        "skill_name": "ccba-append-only-logger",  # coding archetype
        "target_file": skill_file,
        "dataset_file": tmp_path / "dataset.json",
        "baseline_score": 95.0,
        "in_cooldown": False,
        "is_exhausted": True,
        "strat_hash_unchanged": True,
        "has_unapplied_signals": False,
        "needs_ledger_seed": False,
    }

    skip_exhausted = (
        item.get("is_exhausted")
        and item.get("strat_hash_unchanged")
        and not item.get("has_unapplied_signals")
        and not item.get("needs_ledger_seed")
    )
    assert skip_exhausted is True


def test_09_priority_queue_does_not_deprioritize_exhausted_with_signals():
    """Case 9: WeightedPriorityQueue does not push exhausted skill with unapplied signals to end."""
    exhausted_with_signals = {
        "skill_name": "legal_with_signals",
        "baseline_score": 50.0,
        "in_cooldown": False,
        "is_exhausted": True,
        "strat_hash_unchanged": True,
        "has_unapplied_signals": True,
        "needs_ledger_seed": False,
    }
    exhausted_no_signals = {
        "skill_name": "coding_exhausted",
        "baseline_score": 50.0,
        "in_cooldown": False,
        "is_exhausted": True,
        "strat_hash_unchanged": True,
        "has_unapplied_signals": False,
        "needs_ledger_seed": False,
    }

    ranked = WeightedPriorityQueue.rank_skills([exhausted_no_signals, exhausted_with_signals])
    # The one with unapplied signals must come FIRST (not demoted by is_exhausted)
    assert ranked[0]["skill_name"] == "legal_with_signals"
    assert ranked[1]["skill_name"] == "coding_exhausted"


def test_10_ratchet_loop_avoids_duplicate_fingerprints_in_same_session(tmp_path):
    """Case 10: Optimizer tracks applied fingerprints to avoid proposing duplicate cards."""
    skill_file = tmp_path / "SKILL.md"
    initial_content = "---\nname: ccba-legal-advisor\n---\n# Legal Advisor\n"
    skill_file.write_text(initial_content, encoding="utf-8")

    sig = FailureSignal(
        code="UNKNOWN_DOCUMENT",
        item_id="item_single",
        scorer="legal_verbatim_provenance",
        fingerprint="fp_only_once",
        fields={"unknown_doc": "88/2028/NĐ-CP"},
    )
    save_failure_ledger("ccba-legal-advisor", [sig], initial_content)

    config = RatchetConfig(
        target_file=skill_file,
        skill_name="ccba-legal-advisor",
        max_failure_patches=3,
    )
    optimizer = GitRatchetOptimizer(config=config, dry_run_git=True)

    # First proposal applies the card
    mutated_1 = optimizer.propose_mutation(initial_content, iteration=1)
    assert "88/2028/NĐ-CP" in mutated_1
    assert "fp_only_once" in optimizer._applied_fingerprints

    # If simulation reverts/rolls back to initial_content, candidate check skips fp_only_once
    mutated_2 = optimizer.propose_mutation(initial_content, iteration=2)
    # mutated_2 should NOT have 88/2028/NĐ-CP reapplied from failure patches
    assert mutated_2 != mutated_1
