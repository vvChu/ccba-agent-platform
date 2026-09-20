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


def test_discover_skills_with_scoped_target_skills() -> None:
    """Verify daemon correctly filters discovered skills when target_skills is specified."""
    daemon = NightlyTunerDaemon(root=project_root, target_skills=["bigbim-risk", "ccba-grilling"])
    discovered = daemon.discover_skills_and_datasets()

    skill_names = [d["skill_name"] for d in discovered]
    assert len(discovered) == 2
    assert "bigbim-risk" in skill_names
    assert "ccba-grilling" in skill_names
    assert "ccba-academic-writing" not in skill_names


def test_load_recent_baseline_scores(tmp_path: Path) -> None:
    """Verify daemon extracts recent baseline scores from reports directory."""
    reports_dir = tmp_path / ".md" / "knowledge" / "reports"
    reports_dir.mkdir(parents=True)
    report_file = reports_dir / "nightly_tuner_report_20260919_120000.md"
    report_file.write_text(
        "| Kỹ Năng (Skill Name) | Điểm Ban Đầu | Điểm Sau Tối Ưu |\n"
        "| :--- | :---: | :---: |\n"
        "| `ccba-grilling` | 71.7% | **85.5%** |\n"
        "| `bigbim-risk` | 96.7% | **100.0%** |\n",
        encoding="utf-8",
    )

    daemon = NightlyTunerDaemon(root=tmp_path)
    scores = daemon._load_recent_baseline_scores()
    assert scores.get("ccba-grilling") == 85.5
    assert scores.get("bigbim-risk") == 100.0


def test_save_plateau_brief(tmp_path: Path) -> None:
    """Verify plateau escalation brief is exported properly under ADR-0052."""
    from scripts.eval.git_ratchet_tuner import RatchetReport

    daemon = NightlyTunerDaemon(root=tmp_path)
    mock_report = RatchetReport(
        target_file=str(tmp_path / "SKILL.md"),
        initial_score=75.0,
        final_score=75.0,
        total_iterations=3,
        kept_commits=0,
        reverted_trials=3,
        history=[],
    )

    brief_path = daemon._save_plateau_brief("ccba-test-skill", tmp_path / "SKILL.md", mock_report)
    assert brief_path.exists()
    assert brief_path.name == "ccba-test-skill_plateau.md"
    content = brief_path.read_text(encoding="utf-8")
    assert "# ⚠️ CCBA Plateau Escalation Brief (ADR-0052)" in content
    assert "75.0%" in content
    assert "gemini-3.8-flash-high" in content


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
    if "ccba-grilling" in mapping:
        assert mapping["ccba-grilling"] == "eval_grilling.json"
    if "ccba-adr-lifecycle" in mapping:
        assert mapping["ccba-adr-lifecycle"] == "eval_adr_lifecycle.json"


def test_adr_lifecycle_and_risk_redteam_integration() -> None:
    """Verify adr lifecycle has dedicated scorers and risk redteam dataset is valid."""
    from ccba_harness.evals.runner import load_eval_dataset
    from ccba_harness.evals.tuner import get_default_domain_scorers

    # 1. ADR Lifecycle
    adr_scorers = get_default_domain_scorers("ccba-adr-lifecycle")
    adr_scorer_names = [s.name for s in adr_scorers]
    assert "adr_scaffolding_and_lifecycle" in adr_scorer_names
    assert "adr_anti_trap_hard_floor" in adr_scorer_names
    assert "adr_governance_guard" in adr_scorer_names

    adr_items = load_eval_dataset(skill_name="ccba-adr-lifecycle")
    assert len(adr_items) == 5
    adr_item_ids = [it.id for it in adr_items]
    assert "test_adr_lifecycle_scaffold_new_adr" in adr_item_ids
    assert "test_adr_lifecycle_status_cascading_supersede" in adr_item_ids

    # 2. BigBIM Risk Red-Team
    rt_items = load_eval_dataset(skill_name="bigbim-risk-redteam")
    assert len(rt_items) >= 17
    rt_item_ids = [it.id for it in rt_items]
    assert "test_bigbim_risk_redteam_01_compound_chain_conflict" in rt_item_ids
    assert "test_bigbim_risk_redteam_02_spatial_zone_smoke_compartment" in rt_item_ids


def test_grilling_scorers_and_dataset_integration() -> None:
    """Verify grilling skills have dedicated scorers and valid dataset items."""
    from ccba_harness.evals.runner import load_eval_dataset
    from ccba_harness.evals.tuner import get_default_domain_scorers

    scorers = get_default_domain_scorers("ccba-grilling")
    scorer_names = [s.name for s in scorers]
    assert "grilling_one_by_one_and_recommendation" in scorer_names
    assert "grilling_anti_trap_hard_floor" in scorer_names
    assert "grilling_escalation_guard" in scorer_names

    items = load_eval_dataset(skill_name="ccba-grilling")
    assert len(items) == 5
    item_ids = [it.id for it in items]
    assert "test_grilling_standard_stress_test_single_question" in item_ids
    assert "test_grilling_escalation_issue_tree" in item_ids


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


def test_create_pull_request_logs_error_and_retries_without_bad_label(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify _create_pull_request logs gh CLI errors and retries without invalid labels."""
    import logging

    daemon = NightlyTunerDaemon(root=project_root)

    def mock_subprocess_run(cmd, *args, **kwargs):
        class MockResult:
            def __init__(self, returncode: int, stdout: str, stderr: str):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "verify-patch" in cmd_str:
            return MockResult(0, "PASSED", "")
        if "git" in cmd_str and "diff" in cmd_str:
            return MockResult(1, "diff --git a/test b/test", "")
        if "git" in cmd_str and "push" in cmd_str:
            return MockResult(0, "", "")
        if "gh" in cmd_str and "pr" in cmd_str and "create" in cmd_str:
            if "--label" in cmd_str:
                return MockResult(1, "", "could not add label: 'triage:auto-tuned' not found")
            return MockResult(0, "https://github.com/vvChu/ccba-agent-platform/pull/293\n", "")
        return MockResult(0, "", "")

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    with caplog.at_level(logging.WARNING):
        pr_url = daemon._create_pull_request("auto-tune/nightly-test", "Report body")

    assert pr_url == "https://github.com/vvChu/ccba-agent-platform/pull/293"
    assert "could not add label: 'triage:auto-tuned' not found" in caplog.text


def test_create_pull_request_cancels_on_whitespace_or_empty_diff(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """Verify _create_pull_request cancels PR creation when git diff reveals no semantic changes."""
    import logging

    daemon = NightlyTunerDaemon(root=project_root)

    def mock_subprocess_run(cmd, *args, **kwargs):
        class MockResult:
            def __init__(self, returncode: int, stdout: str, stderr: str):
                self.returncode = returncode
                self.stdout = stdout
                self.stderr = stderr

        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
        if "verify-patch" in cmd_str:
            return MockResult(0, "PASSED", "")
        if "git" in cmd_str and "diff" in cmd_str:
            return MockResult(0, "", "")  # returncode 0 = no diff
        return MockResult(0, "", "")

    monkeypatch.setattr("subprocess.run", mock_subprocess_run)

    with caplog.at_level(logging.WARNING):
        pr_url = daemon._create_pull_request("auto-tune/nightly-test", "Report body")

    assert pr_url is None
    assert "Nhánh không có thay đổi ngữ nghĩa nào ngoài khoảng trắng. Hủy tạo PR." in caplog.text

