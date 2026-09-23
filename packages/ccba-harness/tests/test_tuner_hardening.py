"""test_tuner_hardening.py - Unit tests for Tuner Hardening & Queue Breakthrough (ADR-0058).

Tests:
1. seen_hashes Fast-Halt mechanism stops immediately on duplicate mutations.
2. ccba-issue-tree and orchestration archetype skills receive the orchestration mutation template.
3. Orchestration mutation template achieves 100% score and zero LinkAuditor link errors.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from scripts.governance.link_auditor import LinkAuditor

from ccba_harness.evals.archetypes import (
    get_orchestration_scorers,
)
from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from ccba_harness.evals.scorers import HardCompletionLockScorer
from ccba_harness.evals.tuner import GitRatchetOptimizer, RatchetConfig


def test_tuner_fast_halt_on_duplicate_mutation_hash(tmp_path: Path) -> None:
    """Verify seen_hashes fast-halt stops execution immediately when a duplicate mutation is proposed."""
    target = tmp_path / "SKILL.md"
    initial_text = "# Initial Skill Content\nSome body text."
    target.write_text(initial_text, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=5,
        target_score=100.0,
        patience=5,
        full_sweep=True,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    # Mock evaluate_content so baseline is 50.0%, iteration 1 evaluates to 40.0% (reverted)
    optimizer.evaluate_content = MagicMock()
    baseline_report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=50.0,
        pass_rate=0.0,
        item_results=[],
    )
    reverted_report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=40.0,
        pass_rate=0.0,
        item_results=[
            EvalItemResult(
                item_id="1",
                task_output="test output",
                scores=[ScoreResult(scorer_name="test", score=0.4, raw_output=None)],
                composite_score=40.0,
                passed=False,
                critical_failed=False,
            )
        ],
    )
    optimizer.evaluate_content.side_effect = [baseline_report, reverted_report]

    # Propose mutation returns the EXACT same mutated text on both iteration 1 and iteration 2
    duplicate_mutation = "# Initial Skill Content\nSome body text.\n\n## Mutation Attempt"
    optimizer.propose_mutation = MagicMock(return_value=duplicate_mutation)

    # Mock git operations
    optimizer.git_commit_improvement = MagicMock(return_value=False)
    optimizer.git_rollback_target = MagicMock()

    report = optimizer.run()

    # Iteration 1 ran and was reverted. Iteration 2 detected duplicate hash and halted immediately!
    assert report.halt_reason == "HALT_NO_FURTHER_STRATEGIES"
    assert report.total_iterations == 1
    assert len(report.history) == 1
    assert report.history[0].decision == "REVERT"
    # propose_mutation was called twice (iteration 1, then iteration 2 which halted)
    assert optimizer.propose_mutation.call_count == 2
    # evaluate_content was called only twice (baseline + iteration 1), NEVER for iteration 2!
    assert optimizer.evaluate_content.call_count == 2


def test_tuner_fast_halt_when_propose_mutation_returns_unchanged(tmp_path: Path) -> None:
    """Verify optimizer halts with HALT_NO_FURTHER_STRATEGIES when propose_mutation returns unchanged content."""
    target = tmp_path / "SKILL.md"
    initial_text = "# Existing Skill"
    target.write_text(initial_text, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=5,
        target_score=100.0,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)
    optimizer.evaluate_content = MagicMock(
        return_value=EvalReport(
            total_items=1,
            passed_items=1,
            failed_items=0,
            overall_score=80.0,
            pass_rate=100.0,
            item_results=[],
        )
    )
    # Returns best_content unchanged
    optimizer.propose_mutation = MagicMock(side_effect=lambda content, i: content)

    report = optimizer.run()
    assert report.halt_reason == "HALT_NO_FURTHER_STRATEGIES"
    assert report.total_iterations == 0
    assert len(report.history) == 0


def test_tuner_fast_halt_when_mutation_matches_baseline_after_kept_iteration(
    tmp_path: Path,
) -> None:
    """Verify optimizer halts when mutation matches initial baseline content after a kept iteration."""
    target = tmp_path / "SKILL.md"
    initial_text = "# Baseline Content"
    target.write_text(initial_text, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=5,
        target_score=100.0,
        full_sweep=True,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    baseline_report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=50.0,
        pass_rate=0.0,
        item_results=[],
    )
    kept_report = EvalReport(
        total_items=1,
        passed_items=1,
        failed_items=0,
        overall_score=75.0,
        pass_rate=100.0,
        item_results=[
            EvalItemResult(
                item_id="1",
                task_output="test output",
                scores=[ScoreResult(scorer_name="test", score=0.75, raw_output=None)],
                composite_score=75.0,
                passed=True,
                critical_failed=False,
            )
        ],
    )
    optimizer.evaluate_content = MagicMock(side_effect=[baseline_report, kept_report])
    optimizer.git_commit_improvement = MagicMock(return_value=True)
    optimizer.git_rollback_target = MagicMock()

    # Iteration 1 proposes "# Baseline Content\nMutation 1" (kept)
    # Iteration 2 proposes "# Baseline Content" (exact match to initial baseline)
    mutation_1 = "# Baseline Content\nMutation 1"
    optimizer.propose_mutation = MagicMock(side_effect=[mutation_1, initial_text])

    report = optimizer.run()
    assert report.halt_reason == "HALT_NO_FURTHER_STRATEGIES"
    assert report.total_iterations == 1
    assert report.kept_commits == 1
    # evaluate_content called only for baseline + iteration 1, not iteration 2
    assert optimizer.evaluate_content.call_count == 2


def test_propose_mutation_orchestration_archetype_keywords(tmp_path: Path) -> None:
    """Verify ccba-issue-tree and orchestration archetype skills receive the orchestration template."""
    target = tmp_path / "SKILL.md"
    base_content = "---\nname: ccba-issue-tree\ndescription: Test\n---\n# Issue Tree Workflow\n"
    target.write_text(base_content, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="ccba-issue-tree",
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    mutated = optimizer.propose_mutation(base_content, 1)

    # Must contain orchestration section & key invariants
    assert "## Bất Biến Ranh Giới Điều Phối, Single-Writer & Handoff Protocol" in mutated
    assert "* **Single-Writer & Isolated Sandbox:**" in mutated
    assert "* **Handoff Protocol & Autonomous Notification:**" in mutated
    assert (
        "* **Bộc Lộ Dần (Progressive Disclosure):** Tổ chức tài liệu và chỉ dẫn theo [Hiến pháp AGENTS.md](../../AGENTS.md)"
        in mutated
    )
    assert (
        "* **Hard Completion Lock:** Bắt buộc vượt qua xác minh tất định `python -m ccba_harness verify-patch` trước khi hoàn tất."
        in mutated
    )

    # Verify other orchestration keywords also receive orchestration template
    for keyword in ["teamwork", "orchestrat", "platform", "handoff", "wayfinder"]:
        cfg = RatchetConfig(
            target_file=str(target),
            skill_name=f"test-{keyword}-skill",
        )
        opt = GitRatchetOptimizer(config=cfg, root=tmp_path)
        res = opt.propose_mutation(base_content, 1)
        assert "## Bất Biến Ranh Giới Điều Phối, Single-Writer & Handoff Protocol" in res


@pytest.mark.asyncio
async def test_orchestration_template_scores_100_percent() -> None:
    """Verify orchestration mutation template scores 100.0% against all orchestration scorers."""
    orchestration_template = """# Sample Skill
---
name: test-orchestration
---
## Bất Biến Ranh Giới Điều Phối, Single-Writer & Handoff Protocol
* **Single-Writer & Isolated Sandbox:** Duy nhất Lead Orchestrator ghi nhận dữ liệu chính thức; subagents chỉ xuất kết quả trung gian vào sandbox `.agents/<agent_name>/scratch/`.
* **Handoff Protocol & Autonomous Notification:** Chuyển giao ngữ cảnh qua `send_message` gửi parent agent kèm báo cáo bàn giao (handoff report) và kết luận hoàn tất (`verdict`).
* **Bộc Lộ Dần (Progressive Disclosure):** Tổ chức tài liệu và chỉ dẫn theo [Hiến pháp AGENTS.md](../../AGENTS.md) tuân thủ mô hình bộc lộ dần theo cấp độ.
* **Hard Completion Lock:** Bắt buộc vượt qua xác minh tất định `python -m ccba_harness verify-patch` trước khi hoàn tất.
"""

    eval_item = EvalItem(
        id="orch-1",
        input_prompt="Explain orchestration protocol",
        golden_answer="Single-Writer, handoff, progressive disclosure",
    )

    scorers = get_orchestration_scorers()
    assert len(scorers) == 3

    total_weight = sum(s.weight for s in scorers)
    weighted_score = 0.0

    for scorer in scorers:
        result = await scorer.score(orchestration_template, eval_item)
        assert result.score == 1.0, f"Scorer {scorer.name} did not score 1.0"
        assert not result.is_critical_fail, f"Scorer {scorer.name} critically failed"
        weighted_score += scorer.weight * result.score

    final_score = (weighted_score / total_weight) * 100.0
    assert final_score == 100.0

    # Also verify HardCompletionLockScorer passes
    hcl_scorer = HardCompletionLockScorer()
    hcl_result = await hcl_scorer.score(orchestration_template, eval_item)
    assert hcl_result.score == 1.0
    assert not hcl_result.is_critical_fail


def test_orchestration_template_link_auditor_clean(tmp_path: Path) -> None:
    """Verify orchestration mutation template passes LinkAuditor with zero link issues."""
    # Setup a mock repo structure where .agents/AGENTS.md exists
    # and the skill file is located at .agents/skills/test-orchestration-skill/SKILL.md
    project_root = tmp_path
    agents_dir = project_root / ".agents"
    agents_dir.mkdir(parents=True)
    agents_md = agents_dir / "AGENTS.md"
    agents_md.write_text("# CCBA Platform Constitution\n", encoding="utf-8")

    skills_dir = agents_dir / "skills" / "test-orchestration-skill"
    skills_dir.mkdir(parents=True)
    skill_file = skills_dir / "SKILL.md"

    skill_content = """---
name: test-orchestration-skill
description: Skill to test LinkAuditor validity
---
# Test Orchestration Skill

## Bất Biến Ranh Giới Điều Phối, Single-Writer & Handoff Protocol
* **Single-Writer & Isolated Sandbox:** Duy nhất Lead Orchestrator ghi nhận dữ liệu chính thức; subagents chỉ xuất kết quả trung gian vào sandbox `.agents/<agent_name>/scratch/`.
* **Handoff Protocol & Autonomous Notification:** Chuyển giao ngữ cảnh qua `send_message` gửi parent agent kèm báo cáo bàn giao (handoff report) và kết luận hoàn tất (`verdict`).
* **Bộc Lộ Dần (Progressive Disclosure):** Tổ chức tài liệu và chỉ dẫn theo [Hiến pháp AGENTS.md](../../AGENTS.md) tuân thủ mô hình bộc lộ dần theo cấp độ.
* **Hard Completion Lock:** Bắt buộc vượt qua xác minh tất định `python -m ccba_harness verify-patch` trước khi hoàn tất.
"""
    skill_file.write_text(skill_content, encoding="utf-8")

    auditor = LinkAuditor(project_root)
    issues = [
        issue
        for issue in auditor.audit(skill_file)
        if issue.category in ("links", "okf_links", "okf_conflicts")
    ]

    assert len(issues) == 0, f"LinkAuditor found issues: {issues}"
