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
