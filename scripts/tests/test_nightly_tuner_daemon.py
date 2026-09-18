"""test_nightly_tuner_daemon.py - Unit and Integration tests for Nightly Auto-Tuner Daemon."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.eval.nightly_tuner_daemon import (
    NightlyDaemonReport,
    NightlyTunerDaemon,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_weighted_priority_queue_ordering() -> None:
    """Verify WeightedPriorityQueue prioritizes lower scores first."""
    skills = [
        {"skill_name": "perfect_skill", "baseline_score": 100.0},
        {"skill_name": "failing_skill", "baseline_score": 60.0},
        {"skill_name": "mediocre_skill", "baseline_score": 85.0},
        {"skill_name": "near_perfect", "baseline_score": 95.0},
    ]

    ranked = WeightedPriorityQueue.rank_skills(skills)
    ranked_names = [s["skill_name"] for s in ranked]

    # Failing (<90%) should be first, then mediocre (<90%), then near perfect (<100%), then 100%
    assert ranked_names[0] == "failing_skill"
    assert ranked_names[1] == "mediocre_skill"
    assert ranked_names[2] == "near_perfect"
    assert ranked_names[3] == "perfect_skill"


def test_discover_skills_and_datasets() -> None:
    """Verify daemon discovers local skills and maps them to test datasets."""
    daemon = NightlyTunerDaemon(root=project_root)
    discovered = daemon.discover_skills_and_datasets()

    assert len(discovered) > 0
    skill_names = [d["skill_name"] for d in discovered]
    assert "ccba-academic-writing" in skill_names
    assert "ccba-legal-intel" in skill_names


def test_generate_evolution_report_markdown() -> None:
    """Verify Markdown report generation contains all required metrics and safety badges."""
    report = NightlyDaemonReport(
        timestamp="20260816_020000",
        branch_name="auto-tune/nightly-20260816",
        total_skills_scanned=3,
        skills_optimized=2,
        total_commits=3,
        results=[
            SkillEvolutionSummary(
                skill_name="bigbim-classification",
                target_file=Path("dummy"),
                baseline_score=70.0,
                final_score=95.0,
                commits_kept=2,
                rollbacks=3,
                status="IMPROVED",
            ),
            SkillEvolutionSummary(
                skill_name="academic_writing",
                target_file=Path("dummy"),
                baseline_score=100.0,
                final_score=100.0,
                commits_kept=0,
                rollbacks=1,
                status="PERFECT_VERIFIED",
            ),
        ],
    )

    daemon = NightlyTunerDaemon(root=project_root)
    md_output = daemon.generate_evolution_report_markdown(report)

    assert "# 🌙 CCBA Nightly Auto-Tuner Evolution Report" in md_output
    assert "bigbim-classification" in md_output
    assert "+25.0%" in md_output
    assert "Zero-Regression" in md_output
    assert "Hard Floor Compliance" in md_output


def test_send_telegram_notification_mock() -> None:
    """Verify send_telegram_notification functions without API keys in mock mode."""
    report = NightlyDaemonReport(
        timestamp="20260816_020000",
        branch_name="auto-tune/nightly-20260816",
        total_skills_scanned=2,
        skills_optimized=1,
        total_commits=1,
        results=[
            SkillEvolutionSummary(
                skill_name="test_skill",
                target_file=Path("dummy"),
                baseline_score=80.0,
                final_score=90.0,
                commits_kept=1,
                rollbacks=2,
                status="IMPROVED",
            )
        ],
    )
    daemon = NightlyTunerDaemon(root=project_root)
    # When TELEGRAM_BOT_TOKEN is unset, it should return True in mock mode
    result = daemon.send_telegram_notification(report)
    assert result is True


def test_daemon_dry_run_execution() -> None:
    """Verify daemon executes dry run across discovered catalog without exceptions."""
    daemon = NightlyTunerDaemon(root=project_root, max_iterations_low=1)
    # Dry run should execute cleanly without git branch switching
    report = daemon.run_nightly_batch(dry_run=True)

    assert isinstance(report, NightlyDaemonReport)
    assert report.total_skills_scanned > 0
    assert len(report.results) == report.total_skills_scanned


def test_discover_skills_and_datasets_routing() -> None:
    """Verify specific skills are routed to their proper domain datasets."""
    daemon = NightlyTunerDaemon(root=project_root)
    discovered = daemon.discover_skills_and_datasets()
    mapping = {d["skill_name"]: d["eval_dataset_file"].name for d in discovered}

    if "ccba-copywriting" in mapping:
        assert mapping["ccba-copywriting"] == "eval_copywriting.json"
    if "ccba-ai-qc" in mapping:
        assert mapping["ccba-ai-qc"] == "eval_pccc_audit_redteam.json"
    if "bigbim-classification" in mapping:
        assert mapping["bigbim-classification"] == "eval_bigbim_classification.json"
    if "bigbim-risk" in mapping:
        assert mapping["bigbim-risk"] == "eval_bigbim_risk.json"
    if "ccba-legal-advisor" in mapping:
        assert mapping["ccba-legal-advisor"] == "eval_legal_intel.json"


def test_cleanup_old_empty_branches_logic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify _cleanup_old_empty_branches deletes only branches > 7 days without unique commits."""
    daemon = NightlyTunerDaemon(root=project_root)

    # Mock git branch output
    fake_branches = (
        "  auto-tune/nightly-20200101_000000\n"  # Very old, empty
        "  auto-tune/nightly-20200102_000000\n"  # Very old, has unique commits
        "  docs/auto-refactor-20200101_120000\n"  # Very old doc refactor, empty
        "  auto-tune/nightly-20990101_000000\n"  # Future/recent
    )

    deleted_branches: list[str] = []
    remote_deleted_branches: list[str] = []

    def mock_run(cmd, *args, **kwargs):
        class MockRes:
            def __init__(self, stdout: str = "", returncode: int = 0):
                self.stdout = stdout
                self.returncode = returncode

        if cmd[:3] == ["git", "branch", "--list"]:
            return MockRes(stdout=fake_branches)
        elif cmd[:2] == ["git", "cherry"]:
            branch = cmd[3]
            # Simulate branches with 20200101 have no unique commits, 20200102 has unique commit
            if "20200101" in branch:
                return MockRes(stdout="")
            else:
                return MockRes(stdout="+ 1234567 commit msg\n")
        elif cmd[:3] == ["git", "branch", "-D"]:
            deleted_branches.append(cmd[3])
            return MockRes()
        elif cmd[:4] == ["git", "push", "origin", "--delete"]:
            remote_deleted_branches.append(cmd[4])
            return MockRes()
        return MockRes()

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_run)

    count = daemon._cleanup_old_empty_branches(days=7)
    assert count == 2
    assert deleted_branches == [
        "auto-tune/nightly-20200101_000000",
        "docs/auto-refactor-20200101_120000",
    ]
    assert remote_deleted_branches == [
        "auto-tune/nightly-20200101_000000",
        "docs/auto-refactor-20200101_120000",
    ]


def test_tuner_tiered_budget_and_early_stopping(tmp_path: Path) -> None:
    """Verify GitRatchetOptimizer sets correct effective budget and early stops."""
    from ccba_harness.evals import EvalItem, ExactMatchScorer, GitRatchetOptimizer, RatchetConfig

    dataset = [EvalItem(id="item1", input_prompt="Hello", golden_answer="Pass")]
    scorers = [ExactMatchScorer()]

    # 1. Test 100% baseline budget clamping to 1 iteration
    perfect_skill = tmp_path / "perfect_skill.md"
    perfect_skill.write_text("# Perfect Skill\n", encoding="utf-8")
    cfg_perfect = RatchetConfig(
        target_file=perfect_skill,
        max_iterations=10,
        patience=3,
        target_score=100.0,
    )
    opt_perfect = GitRatchetOptimizer(
        cfg_perfect,
        root=tmp_path,
        dry_run_git=True,
        dataset=dataset,
        scorers=scorers,
        task=lambda item: "Pass",
    )
    report_perfect = opt_perfect.run()
    assert report_perfect.initial_score == 100.0
    assert report_perfect.total_iterations == 1

    # 2. Test early stopping when mutations are stagnant (patience=2)
    stagnant_skill = tmp_path / "stagnant_skill.md"
    stagnant_skill.write_text("# Stagnant Skill\n", encoding="utf-8")
    cfg_stagnant = RatchetConfig(
        target_file=stagnant_skill,
        max_iterations=10,
        patience=2,
        target_score=100.0,
    )
    opt_stagnant = GitRatchetOptimizer(
        cfg_stagnant,
        root=tmp_path,
        dry_run_git=True,
        dataset=dataset,
        scorers=scorers,
        task=lambda item: "Fail",
    )
    report_stagnant = opt_stagnant.run()
    # Should halt after effective_patience (2) iterations instead of running all 10
    assert report_stagnant.total_iterations == 2


def test_daemon_real_llm_and_token_budget(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify daemon initializes real LLM configuration, engine flag, and token budget."""
    from ccba_harness.evals.tuner import RatchetReport

    daemon = NightlyTunerDaemon(
        root=project_root,
        max_iterations_low=1,
        use_real_llm=True,
        token_budget=200_000,
        model="qwen-local-primary",
    )
    assert daemon.use_real_llm is True
    assert daemon.token_budget == 200_000
    assert daemon.model == "qwen-local-primary"

    # Mock discover to 1 skill for ultra-fast unit test execution
    monkeypatch.setattr(
        daemon,
        "discover_skills_and_datasets",
        lambda: [
            {
                "skill_name": "ccba-test-skill",
                "target_file": project_root
                / ".agents"
                / "skills"
                / "ccba-copywriting"
                / "SKILL.md",
                "dataset_file": project_root
                / "packages"
                / "ccba-harness"
                / "evals"
                / "datasets"
                / "eval_copywriting.json",
                "baseline_score": 85.0,
            }
        ],
    )

    def mock_run(self):
        return RatchetReport(
            target_file=str(self.config.target_file),
            initial_score=100.0,
            final_score=100.0,
            total_iterations=1,
            kept_commits=0,
            reverted_trials=0,
            history=[],
            total_tokens=1500,
            prompt_tokens=1000,
            completion_tokens=500,
        )

    monkeypatch.setattr("ccba_harness.evals.tuner.GitRatchetOptimizer.run", mock_run)

    # Dry run should reflect REAL_LLM engine flag and aggregate tokens
    report = daemon.run_nightly_batch(dry_run=True)
    assert report.engine == "REAL_LLM"
    assert report.total_skills_scanned == 1
    assert report.total_tokens == 1500
    assert report.prompt_tokens == 1000
    assert report.completion_tokens == 500
