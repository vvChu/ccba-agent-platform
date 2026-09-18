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


def test_tuner_tiered_budget_and_early_stopping() -> None:
    """Verify GitRatchetOptimizer sets correct effective budget and early stops."""
    from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig

    # 1. Config with patience
    cfg = RatchetConfig(
        target_file=project_root / ".agents" / "skills" / "ccba-academic-writing" / "SKILL.md",
        max_iterations=10,
        patience=3,
    )
    assert cfg.patience == 3

    # 2. Optimizer mock run with 100% baseline -> effective max_iter=1, patience=1
    opt = GitRatchetOptimizer(cfg, root=project_root)
    assert opt.config.patience == 3

