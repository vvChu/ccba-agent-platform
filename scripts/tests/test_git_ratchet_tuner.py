"""test_git_ratchet_tuner.py - Scoped Fast Unit Tests for GitRatchetTuner.

Tests program.md parsing, frontmatter preservation, ratchet KEEP/REVERT decisions,
and end-to-end dry-run optimization loop.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccba_harness.evals.models import EvalItemResult, EvalReport, ScoreResult
from scripts.eval.git_ratchet_tuner import GitRatchetTuner, RatchetConfig

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_ratchet_config_from_markdown_program(tmp_path: Path):
    """Test parsing program.md into RatchetConfig."""
    prog_file = tmp_path / "program.md"
    content = """
# AutoResearch Program
- **Target File**: `my_skill/SKILL.md`
- **Target Score**: 95.0%
- **Max Iterations**: 5
- **Dataset File**: `tests/eval_my_skill.json`
"""
    prog_file.write_text(content, encoding="utf-8")

    config = RatchetConfig.from_markdown_program(prog_file, root=tmp_path)
    assert config.target_file == (tmp_path / "my_skill/SKILL.md").resolve()
    assert config.target_score == 95.0
    assert config.max_iterations == 5
    assert config.eval_dataset_file == (tmp_path / "tests/eval_my_skill.json").resolve()


def test_ratchet_frontmatter_preservation():
    """Test preserving YAML frontmatter during prompt mutations."""
    orig = "---\nname: my-skill\nversion: 1.0.0\n---\n\n# Body content"
    edited = "# Mutated body content"

    tuner = GitRatchetTuner(
        RatchetConfig(target_file=Path("dummy")),
        dry_run_git=True,
    )
    result = tuner.preserve_yaml_frontmatter(orig, edited)

    assert "---" in result
    assert "name: my-skill" in result
    assert "# Mutated body content" in result


def test_ratchet_full_run_dry_run(tmp_path: Path):
    """Test full execution of GitRatchetTuner in dry-run mode."""
    target_skill = tmp_path / "SKILL.md"
    target_skill.write_text(
        "---\nname: test-skill\n---\n# Original skill prompt instructions\n",
        encoding="utf-8",
    )

    dataset_file = tmp_path / "dataset.json"
    dataset_file.write_text(
        '[{"id": "t1", "input_prompt": "Kiểm tra theo Nghị định 30", "rubric": "Phải đúng"}]',
        encoding="utf-8",
    )

    config = RatchetConfig(
        target_file=target_skill,
        eval_dataset_file=dataset_file,
        target_score=90.0,
        max_iterations=3,
    )

    tuner = GitRatchetTuner(config, dry_run_git=True)
    report = tuner.run()

    assert report.total_iterations >= 1
    assert report.final_score >= report.initial_score
    assert len(report.history) >= 1


def test_ratchet_critical_failure_triggers_revert(tmp_path: Path):
    """Test that any critical failure strictly forces a REVERT even if overall score is high."""
    target_skill = tmp_path / "SKILL.md"
    target_skill.write_text("# Target Content", encoding="utf-8")

    config = RatchetConfig(
        target_file=target_skill,
        target_score=90.0,
        max_iterations=1,
    )
    tuner = GitRatchetTuner(config, dry_run_git=True)

    # Mock evaluate_content returning 95% score but with 1 critical failure
    def mock_eval_with_crit_fail(content: str) -> EvalReport:
        item_res = EvalItemResult(
            item_id="t1",
            task_output="Bad output",
            scores=[ScoreResult(scorer_name="Regex", score=0.0, is_critical_fail=True)],
            composite_score=0.0,
            passed=False,
            critical_failed=True,
        )
        return EvalReport(
            total_items=1,
            passed_items=0,
            failed_items=1,
            overall_score=95.0,  # high score but critical failure
            pass_rate=0.0,
            item_results=[item_res],
        )

    tuner.evaluate_content = mock_eval_with_crit_fail
    report = tuner.run()

    assert report.reverted_trials == 1
    assert report.kept_commits == 0
    assert report.history[0].decision == "REVERT"
