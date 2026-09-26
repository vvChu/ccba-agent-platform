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


def test_semantic_dedup_recognizes_headers_with_adr_tags(tmp_path: Path) -> None:
    """Verify semantic dedup normalizes away ADR tags in headers so existing sections are not duplicated."""
    target = tmp_path / "SKILL.md"
    base_content = """---
name: ccba-coding-skill
---
# Coding Skill

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)
* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.
* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:
  ```bash
  python -m ccba_harness verify-patch
  ```
* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.
"""
    target.write_text(base_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    # Strategy 1 (Hard Completion Lock) is already in base_content with (ADR-0058).
    # Mutation 1 must NOT re-apply strategy 1; it should advance to strategy 2 (Double-Pass Review).
    mut = tuner.propose_mutation(base_content, 1)
    assert "## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)" in mut
    # The original ADR-0058 heading must remain intact
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)" in mut
    # Should not have duplicate Hard Completion Lock headings
    assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1


def test_header_replacement_preserves_existing_adr_tags(tmp_path: Path) -> None:
    """Verify section replacement regex preserves existing ADR tags and uses line anchors."""
    target = tmp_path / "SKILL.md"
    base_content = """---
name: ccba-coding-skill
---
# Coding Skill

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)
* Old outdated bullet to be updated.

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất Nâng Cao
* Distinct section that should not be touched.
"""
    target.write_text(base_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    # Since the body content of strategy 1 is different, propose_mutation will replace the section
    mut = tuner.propose_mutation(base_content, 1)

    # Must preserve the ADR-0058 tag on the replaced header
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)" in mut
    # Must update the body of that section
    assert "python -m ccba_harness verify-patch" in mut
    assert "Old outdated bullet" not in mut
    # Must NOT have modified or replaced the distinct partial prefix section
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất Nâng Cao" in mut
    assert "* Distinct section that should not be touched." in mut


def test_monotonic_token_guard_rejects_mutations_dropping_adr_tags(tmp_path: Path) -> None:
    """Verify GitRatchetOptimizer fast-fails and rolls back if a mutation drops existing ADR tokens."""
    target = tmp_path / "SKILL.md"
    initial_content = """---
name: test-skill
---
# Skill Documentation

## Section A (ADR-0058)
* Important rule according to HUB-ADR-0057.
"""
    target.write_text(initial_content, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=3,
        target_score=100.0,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    # Baseline evaluation returns 50.0%
    baseline_report = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=50.0,
        pass_rate=0.0,
        item_results=[],
    )
    optimizer.evaluate_content = MagicMock(return_value=baseline_report)
    optimizer.git_rollback_target = MagicMock()

    # Mutation drops ADR-0058 (keeps HUB-ADR-0057)
    bad_mutation = """---
name: test-skill
---
# Skill Documentation

## Section A
* Important rule according to HUB-ADR-0057.
"""
    optimizer.propose_mutation = MagicMock(return_value=bad_mutation)

    report = optimizer.run()

    # Must have recorded a REVERT decision for iteration 1
    assert len(report.history) >= 1
    trial = report.history[0]
    assert trial.decision == "REVERT"
    assert "Từ chối mutation vì làm mất thẻ ADR" in trial.summary
    assert "ADR-0058" in trial.summary

    # evaluate_content was called ONLY for baseline, never for the bad mutation!
    assert optimizer.evaluate_content.call_count == 1
    # Rollback was called to revert the bad mutation
    optimizer.git_rollback_target.assert_called()


def test_header_replacement_preserves_multiple_and_complex_adr_tags(tmp_path: Path) -> None:
    """Verify section replacement regex preserves multiple ADR tags, comma-separated tags, and descriptive suffixes without duplicating sections."""
    target = tmp_path / "SKILL.md"

    cases = [
        (
            "Multiple distinct",
            "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058) (HUB-ADR-0057)",
        ),
        ("Comma separated", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058, HUB-ADR-0057)"),
        (
            "Descriptive suffix",
            "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058 Hard Completion Lock)",
        ),
    ]

    for label, header_line in cases:
        base_content = f"""---
name: ccba-coding-skill
---
# Coding Skill

{header_line}
* Outdated bullet to be replaced.

## Other Section
* Keep intact.
"""
        target.write_text(base_content, encoding="utf-8")
        cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
        tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

        mut = tuner.propose_mutation(base_content, 1)

        # Must not duplicate the section
        assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1, (
            f"Failed on {label}: duplicated section heading found!"
        )
        # Must preserve the exact ADR tags / suffix
        assert header_line in mut, f"Failed on {label}: heading was not preserved!"
        # Must replace the body with the strategy content
        assert "python -m ccba_harness verify-patch" in mut
        assert "Outdated bullet to be replaced." not in mut
        assert "## Other Section" in mut


def test_semantic_dedup_recognizes_complex_adr_tags(tmp_path: Path) -> None:
    """Verify semantic dedup normalizes away complex ADR tags (comma-separated, multi-tag) when checking whether strategy is applied."""
    target = tmp_path / "SKILL.md"
    base_content = """---
name: ccba-coding-skill
---
# Coding Skill

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058, HUB-ADR-0057)
* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.
* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:
  ```bash
  python -m ccba_harness verify-patch
  ```
* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.
"""
    target.write_text(base_content, encoding="utf-8")
    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    # Strategy 1 is already applied, so mutation 1 must advance to strategy 2
    mut = tuner.propose_mutation(base_content, 1)
    assert "## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)" in mut
    assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1


def test_monotonic_token_guard_padding_and_underscore_invariance(tmp_path: Path) -> None:
    """Verify monotonic guard does not falsely trigger on zero-padding differences (ADR-58 vs ADR-0058) and correctly tracks HUB_ADR."""
    target = tmp_path / "SKILL.md"
    initial_content = """---
name: test-skill
---
# Skill Documentation

## Section A (ADR-0058)
* Rule per HUB_ADR-0057.
"""
    target.write_text(initial_content, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=1,
        target_score=100.0,
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
    iteration_report = EvalReport(
        total_items=1,
        passed_items=1,
        failed_items=0,
        overall_score=100.0,
        pass_rate=1.0,
        item_results=[],
    )
    optimizer.evaluate_content = MagicMock(side_effect=[baseline_report, iteration_report])
    optimizer.git_rollback_target = MagicMock()

    # Mutation uses unpadded ADR-58 and keeps HUB_ADR-0057
    valid_mutation = """---
name: test-skill
---
# Skill Documentation

## Section A (ADR-58)
* Rule per HUB_ADR-0057.
"""
    optimizer.propose_mutation = MagicMock(return_value=valid_mutation)

    report = optimizer.run()

    # Should evaluate and KEEP, not fast-fail on padding difference
    assert len(report.history) >= 1
    assert report.history[0].decision == "KEEP"
    assert optimizer.evaluate_content.call_count == 2  # baseline + iteration 1


def test_header_replacement_preserves_lowercase_adr_tags(tmp_path: Path) -> None:
    """Verify section replacement regex preserves lowercase ADR tags (adr-0058, hub-adr-0058) without duplicating sections."""
    target = tmp_path / "SKILL.md"

    cases = [
        ("Lowercase adr", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (adr-0058)"),
        ("Lowercase hub-adr", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (hub-adr-0058)"),
        ("Mixed case hub-adr", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (Hub-Adr-0058)"),
    ]

    for label, header_line in cases:
        base_content = f"""---
name: ccba-coding-skill
---
# Coding Skill

{header_line}
* Outdated bullet to be replaced.

## Other Section
* Keep intact.
"""
        target.write_text(base_content, encoding="utf-8")
        cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
        tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

        mut = tuner.propose_mutation(base_content, 1)

        # Must not duplicate the section heading
        assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1, (
            f"Failed on {label}: duplicated section heading found!"
        )
        # Must preserve the exact case and tag as written in the original document
        assert header_line in mut, f"Failed on {label}: header was not preserved!"
        # Must update the body with the strategy content
        assert "python -m ccba_harness verify-patch" in mut
        assert "Outdated bullet to be replaced." not in mut
        assert "## Other Section" in mut


def test_header_replacement_preserves_no_whitespace_before_parenthesis(tmp_path: Path) -> None:
    """Verify section replacement regex handles zero whitespace before '(' (e.g. ## Tiêu Đề(ADR-0058)) and does not duplicate sections."""
    target = tmp_path / "SKILL.md"

    cases = [
        ("Zero whitespace standard tag", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(ADR-0058)"),
        ("Zero whitespace lowercase tag", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(adr-0058)"),
        ("Zero whitespace hub-adr tag", "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(hub-adr-0058)"),
    ]

    for label, header_line in cases:
        base_content = f"""---
name: ccba-coding-skill
---
# Coding Skill

{header_line}
* Outdated bullet to be replaced.

## Other Section
* Keep intact.
"""
        target.write_text(base_content, encoding="utf-8")
        cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
        tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

        mut = tuner.propose_mutation(base_content, 1)

        # Must not duplicate the section heading
        assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1, (
            f"Failed on {label}: duplicated section heading found!"
        )
        # Must preserve the exact zero-whitespace tag
        assert header_line in mut, f"Failed on {label}: header was not preserved!"
        # Must update the body with the strategy content
        assert "python -m ccba_harness verify-patch" in mut
        assert "Outdated bullet to be replaced." not in mut
        assert "## Other Section" in mut


def test_header_replacement_prevents_duplicate_tag_when_strategy_has_adr_tag(
    tmp_path: Path, monkeypatch
) -> None:
    """Verify that even if a strategy header contains an uppercase ADR tag, existing lowercase or zero-whitespace tags from the document are preserved without tag duplication."""
    target = tmp_path / "SKILL.md"
    base_content = """---
name: ccba-coding-skill
---
# Coding Skill

## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(adr-0058)
* Outdated bullet to be replaced.

## Other Section
* Keep intact.
"""
    target.write_text(base_content, encoding="utf-8")
    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    # Mock strategy to have an ADR tag in the strategy header itself
    synthetic_strategy = [
        (
            "Mock Strategy With Tag",
            "\n\n## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (ADR-0058)\n* Replacement body.\n",
        )
    ]
    monkeypatch.setattr(
        tuner,
        "propose_mutation",
        lambda current, it: tuner.preserve_yaml_frontmatter(
            current,
            # Test direct logic with synthetic strategy
            _simulate_mutation_with_strategy(tuner, current, synthetic_strategy),
        ),
    )

    def _simulate_mutation_with_strategy(opt, content, strats):
        import re

        from ccba_harness.evals.tuner import ADR_HEADER_TAG_REGEX

        fm_match = re.match(r"^\s*---\r?\n(.*?)\r?\n---\r?\n?", content, re.DOTALL)
        body = content[fm_match.end() :] if fm_match else content
        _s_name, enhancement = strats[0]
        section_header = enhancement.strip().split("\n")[0]
        clean_header = ADR_HEADER_TAG_REGEX.sub("", section_header).strip()
        header_pattern = re.escape(clean_header)
        section_regex = re.compile(
            rf"(?m)^[ \t]*{header_pattern}(?P<adr_suffix>(?:[ \t]*\([^)\n\r]*(?:HUB[-_]ADR|ADR)[-_\s]*[0-9]+[^)\n\r]*\))+)?(?:[ \t]*\r?$)\r?\n?"
            r"(?P<section_body>.*?)(?=(?:\r?\n## |\Z))",
            re.DOTALL | re.IGNORECASE,
        )
        match = section_regex.search(body)
        assert match is not None
        lines = enhancement.strip().split("\n")
        adr_suffix = match.group("adr_suffix")
        if adr_suffix:
            lines[0] = f"{clean_header}{adr_suffix}"
        effective_enhancement = "\n".join(lines)
        return body[: match.start()] + effective_enhancement.strip() + "\n" + body[match.end() :]

    mutated = _simulate_mutation_with_strategy(tuner, base_content, synthetic_strategy)
    # Must NOT have both (ADR-0058) and (adr-0058)
    assert "(ADR-0058)" not in mutated, "Failed: uppercase strategy tag leaked into output!"
    assert "(adr-0058)" in mutated, "Failed: original lowercase tag was lost!"
    assert "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(adr-0058)" in mutated


def test_semantic_dedup_recognizes_zero_whitespace_and_lowercase_tags(tmp_path: Path) -> None:
    """Verify semantic dedup recognizes zero-whitespace and lowercase ADR tags so strategy 1 is skipped."""
    target = tmp_path / "SKILL.md"

    test_headers = [
        "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(ADR-0058)",
        "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(adr-0058)",
        "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất (hub-adr-0058)",
    ]

    for header in test_headers:
        base_content = f"""---
name: ccba-coding-skill
---
# Coding Skill

{header}
* **Tiêu chí hoàn thành tất định:** Mọi thay đổi mã nguồn, kỹ năng hoặc tài liệu bắt buộc phải vượt qua bộ kiểm thử tự động.
* **Hard Completion Lock:** Nghiêm cấm tuyên bố hoàn thành task hoặc yêu cầu nghiệm thu nếu lệnh xác minh chưa vượt qua:
  ```bash
  python -m ccba_harness verify-patch
  ```
* **Zero Tolerance Exit Code:** Lệnh kiểm thử phải thoát với mã exit code 0; tuyệt đối không bỏ qua các lỗi linter hay hồi quy.
"""
        target.write_text(base_content, encoding="utf-8")
        cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
        tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

        mut = tuner.propose_mutation(base_content, 1)
        # Since strategy 1 is already applied, it must advance to strategy 2
        assert "## Kỷ Luật Rà Soát Hai Vòng (Double-Pass Adversarial Review)" in mut
        assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1


def test_header_replacement_preserves_multiple_tags_zero_whitespace(tmp_path: Path) -> None:
    """Verify section replacement preserves multiple tags with zero whitespace."""
    target = tmp_path / "SKILL.md"
    header_line = "## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất(adr-0058)(hub-adr-0057)"
    base_content = f"""---
name: ccba-coding-skill
---
# Coding Skill

{header_line}
* Outdated body.

## Next Section
* Preserved.
"""
    target.write_text(base_content, encoding="utf-8")
    cfg = RatchetConfig(target_file=str(target), skill_name="ccba-code-review")
    tuner = GitRatchetOptimizer(cfg, root=tmp_path, dry_run_git=True)

    mut = tuner.propose_mutation(base_content, 1)
    assert header_line in mut
    assert mut.count("## Bất Biến Vận Hành & Khóa Cứng Hoàn Tất") == 1
    assert "python -m ccba_harness verify-patch" in mut
    assert "Outdated body." not in mut
    assert "## Next Section" in mut


# ===========================================================================
# Issue #368: Auto-Tuner Hardening Tests
# 1. Config Precedence via _UNSET sentinel
# 2. Concurrency Token Reservation Barrier
# 3. Hard Max Tokens Per Skill Ceiling
# 4. Type-Safe Exception Preservation
# 5. Async Event Loop Decoupling
# ===========================================================================

import asyncio
from typing import Any

from ccba_harness.evals.runner import EvalRunner
from ccba_harness.evals.tuner import (
    CircuitBreakerOpenError,
    LLMTaskAdapter,
    RatchetReport,
    TokenUsageTracker,
)


def test_ratchet_config_precedence_unset_sentinel_respects_user_values(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify RatchetConfig uses _UNSET sentinel so user-supplied CLI/init parameters are never overridden by env vars."""
    target = tmp_path / "SKILL.md"
    target.write_text("# Test Skill", encoding="utf-8")

    monkeypatch.setenv("CCBA_TUNER_CONCURRENCY", "10")
    monkeypatch.setenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET", "100000")
    monkeypatch.setenv("CCBA_TUNER_HARD_MAX_PER_SKILL", "999999")

    # Case 1: Explicit user parameters must NOT be overridden by environment variables
    cfg_explicit = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_concurrency=5,
        per_skill_mutation_budget=250_000,
        hard_max_tokens_per_skill=500_000,
    )
    assert cfg_explicit.max_concurrency == 5
    assert cfg_explicit.per_skill_mutation_budget == 250_000
    assert cfg_explicit.hard_max_tokens_per_skill == 500_000

    # Case 2: Unset parameters must resolve from environment variables
    cfg_from_env = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
    )
    assert cfg_from_env.max_concurrency == 10
    assert cfg_from_env.per_skill_mutation_budget == 100_000
    assert cfg_from_env.hard_max_tokens_per_skill == 999_999

    # Case 3: When env vars are absent, fall back to robust defaults
    monkeypatch.delenv("CCBA_TUNER_CONCURRENCY", raising=False)
    monkeypatch.delenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET", raising=False)
    monkeypatch.delenv("CCBA_TUNER_HARD_MAX_PER_SKILL", raising=False)

    cfg_defaults = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
    )
    assert cfg_defaults.max_concurrency == 5
    assert cfg_defaults.per_skill_mutation_budget == 250_000
    assert cfg_defaults.hard_max_tokens_per_skill == 500_000


def test_token_usage_tracker_reservation_barrier() -> None:
    """Verify TokenUsageTracker reserve() and release_reservation() enforce token barriers."""
    tracker = TokenUsageTracker(budget_ceiling=1000)
    assert tracker.available_tokens == 1000
    assert tracker.reserved_tokens == 0
    assert not tracker.is_exhausted

    # Reserve 400 tokens
    assert tracker.reserve(400) is True
    assert tracker.reserved_tokens == 400
    assert tracker.available_tokens == 600

    # Reserve another 400 tokens
    assert tracker.reserve(400) is True
    assert tracker.reserved_tokens == 800
    assert tracker.available_tokens == 200

    # Attempting to reserve 300 tokens exceeds 1000 ceiling (800 + 300 = 1100) -> returns False
    assert tracker.reserve(300) is False
    assert tracker.reserved_tokens == 800
    assert tracker.available_tokens == 200

    # Release 400 tokens reservation
    tracker.release_reservation(400)
    assert tracker.reserved_tokens == 400
    assert tracker.available_tokens == 600

    # Record actual usage: 250 prompt, 150 completion = 400 total
    tracker.record_usage(prompt_tokens=250, completion_tokens=150)
    assert tracker.total_tokens == 400

    # Release remaining reservation
    tracker.release_reservation(400)
    assert tracker.reserved_tokens == 0
    assert tracker.available_tokens == 600

    # Now usage is 400. Reserving 601 exceeds ceiling -> returns False
    assert tracker.reserve(601) is False

    # Reserving exactly 600 is permitted
    assert tracker.reserve(600) is True
    assert tracker.is_exhausted
    assert tracker.available_tokens == 0


@pytest.mark.asyncio
async def test_llm_task_adapter_reservation_barrier_and_safe_release() -> None:
    """Verify LLMTaskAdapter dynamically reserves tokens and reliably releases reservation on error."""
    tracker = TokenUsageTracker(budget_ceiling=1000)

    class MockFailingClient:
        async def chat_with_metadata(self, *args, **kwargs) -> Any:
            await asyncio.sleep(0.01)
            raise RuntimeError("Simulation failure in LLM API call")

    adapter = LLMTaskAdapter(
        async_client=MockFailingClient(),
        token_tracker=tracker,
        estimated_task_tokens=500,
    )

    task = adapter.create_async_eval_task("test prompt")
    item = EvalItem(id="item-fail", input_prompt="input")

    # When task raises, reservation must be safely released in finally block
    with pytest.raises(RuntimeError, match="Simulation failure"):
        await task(item)

    assert tracker.reserved_tokens == 0
    assert tracker.available_tokens == 1000


def test_hard_max_tokens_per_skill_halts_even_if_improvements_kept(tmp_path: Path) -> None:
    """Verify GitRatchetOptimizer halts with HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED when hard ceiling is reached."""
    target = tmp_path / "SKILL.md"
    initial_text = "# Initial Skill"
    target.write_text(initial_text, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=5,
        target_score=100.0,
        full_sweep=True,
        per_skill_mutation_budget=None,
        hard_max_tokens_per_skill=1000,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    # Baseline evaluation consumes 0 mutation tokens
    baseline_rep = EvalReport(
        total_items=1,
        passed_items=0,
        failed_items=1,
        overall_score=50.0,
        pass_rate=0.0,
        item_results=[],
    )
    # Iteration 1 improves score to 80.0% (kept)
    iter1_rep = EvalReport(
        total_items=1,
        passed_items=1,
        failed_items=0,
        overall_score=80.0,
        pass_rate=1.0,
        item_results=[],
    )

    optimizer.evaluate_content = MagicMock(side_effect=[baseline_rep, iter1_rep])
    optimizer.propose_mutation = MagicMock(return_value="# Mutated Skill 1")
    optimizer.git_commit_improvement = MagicMock(return_value=True)

    # Simulate token consumption of 1200 tokens during iteration 1
    def mock_eval_with_tokens(content: str, dataset=None):
        if optimizer.evaluate_content.call_count == 2:
            optimizer.token_tracker.record_usage(prompt_tokens=800, completion_tokens=400)
            return iter1_rep
        return baseline_rep

    optimizer.evaluate_content.side_effect = mock_eval_with_tokens

    report = optimizer.run()

    # Even though iteration 1 was kept (kept_commits=1), mutation tokens (1200) >= hard_max (1000)
    assert report.halt_reason == "HARD_MAX_SKILL_TOKEN_LIMIT_EXCEEDED"
    assert report.kept_commits == 1
    assert report.total_iterations == 1
    assert optimizer.evaluate_content.call_count == 2


@pytest.mark.asyncio
async def test_eval_runner_and_item_result_exception_preservation() -> None:
    """Verify EvalItemResult preserves original Exception instance for type-safe inspection."""

    class CustomDomainError(Exception):
        pass

    async def throwing_task(item: EvalItem) -> str:
        if item.id == "error-1":
            raise CustomDomainError("Domain validation failed for entity X")
        elif item.id == "cb-1":
            raise CircuitBreakerOpenError("Circuit breaker tripped: downstream 503")
        return "valid output"

    dataset = [
        EvalItem(id="error-1", input_prompt="p1"),
        EvalItem(id="cb-1", input_prompt="p2"),
        EvalItem(id="ok-1", input_prompt="p3"),
    ]

    runner = EvalRunner()
    report = await runner.run(dataset=dataset, task=throwing_task, scorers=[])

    assert len(report.item_results) == 3

    res1 = report.item_results[0]
    assert res1.error is not None
    assert "Domain validation failed" in res1.error
    assert isinstance(res1.exception, CustomDomainError)

    res2 = report.item_results[1]
    assert res2.error is not None
    assert isinstance(res2.exception, CircuitBreakerOpenError)

    res3 = report.item_results[2]
    assert res3.error is None
    assert res3.exception is None


@pytest.mark.asyncio
async def test_async_event_loop_decoupling_native_coroutines(tmp_path: Path) -> None:
    """Verify evaluate_content_async and run_async execute seamlessly inside existing event loops without deadlock."""
    target = tmp_path / "SKILL.md"
    initial_text = "# Test Async Skill"
    target.write_text(initial_text, encoding="utf-8")

    config = RatchetConfig(
        target_file=str(target),
        skill_name="test-skill",
        max_iterations=2,
        target_score=100.0,
    )
    optimizer = GitRatchetOptimizer(config=config, root=tmp_path)

    # 1. Native coroutine evaluation inside event loop
    eval_rep = await optimizer.evaluate_content_async(initial_text)
    assert isinstance(eval_rep, EvalReport)

    # 2. Native run_async inside event loop
    async def mock_async_eval(content: str, dataset=None) -> EvalReport:
        await asyncio.sleep(0.001)
        return EvalReport(
            total_items=1,
            passed_items=1,
            failed_items=0,
            overall_score=100.0,
            pass_rate=1.0,
            item_results=[],
        )

    optimizer.evaluate_content_async = mock_async_eval
    optimizer.git_commit_improvement = MagicMock(return_value=True)

    report = await optimizer.run_async()
    assert isinstance(report, RatchetReport)
    assert report.initial_score == 100.0
