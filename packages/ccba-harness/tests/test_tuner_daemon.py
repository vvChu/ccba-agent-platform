"""test_tuner_daemon.py - Unit tests for ccba_harness.evals.daemon Deep Seam."""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals.daemon import (
    NightlyDaemonReport,
    NightlyTunerDaemon,
    SkillEvolutionSummary,
    WeightedPriorityQueue,
    find_project_root,
    send_telegram_alert,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_find_project_root() -> None:
    """Verify find_project_root resolves repo root with .git or .agents."""
    root = find_project_root()
    assert (root / ".agents").exists() or (root / ".git").exists()


def test_daemon_exports_and_priority_queue() -> None:
    """Verify priority queue ordering preserves failing and mediocre skills first."""
    skills = [
        {"skill_name": "s_100", "baseline_score": 100.0},
        {"skill_name": "s_70", "baseline_score": 70.0},
        {"skill_name": "s_92", "baseline_score": 92.0},
    ]
    ranked = WeightedPriorityQueue.rank_skills(skills)
    names = [s["skill_name"] for s in ranked]
    assert names == ["s_70", "s_92", "s_100"]


def test_daemon_custom_alert_emitter() -> None:
    """Verify NightlyTunerDaemon respects custom injected alert_emitter."""
    captured: list[str] = []

    def mock_emitter(msg: str) -> bool:
        captured.append(msg)
        return True

    daemon = NightlyTunerDaemon(alert_emitter=mock_emitter)
    report = NightlyDaemonReport(
        timestamp="20260919_120000",
        branch_name="auto-tune/test",
        total_skills_scanned=1,
        skills_optimized=1,
        total_commits=1,
        results=[
            SkillEvolutionSummary(
                skill_name="test-skill",
                target_file=Path("SKILL.md"),
                baseline_score=80.0,
                final_score=95.0,
                commits_kept=1,
                rollbacks=0,
                status="IMPROVED",
            )
        ],
    )
    result = daemon.send_telegram_notification(report)
    assert result is True
    assert len(captured) == 1
    assert "test-skill" in captured[0]


def test_daemon_send_telegram_alert_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify send_telegram_alert with mock fallback."""
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    res = send_telegram_alert("Hello test", mock_fallback=True)
    assert res is True
