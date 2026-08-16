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
    assert "academic_writing" in skill_names
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
