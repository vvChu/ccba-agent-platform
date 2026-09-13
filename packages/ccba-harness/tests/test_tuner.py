"""test_tuner.py - Comprehensive Unit Tests for Git-Ratchet Prompt Auto-Tuner (AH-1, ADR-0023).

Tests:
1. RatchetConfig parsing from markdown program.md and CLI parameters.
2. YAML frontmatter preservation (byte-for-byte protection, edge cases, horizontal rules).
3. Domain scorer factory (legal, pccc, academic, bim, fallback).
4. GitRatchetOptimizer evaluation, mutation proposing, and Karpathy decision loop.
5. Safe git checkpointing and rollback (dry-run, git commands, exception safety).
6. Integration with run_eval_pipeline and CCBA Harness CLI.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from ccba_harness.evals.runner import run_eval_pipeline
from ccba_harness.evals.scorers import RegexScorer
from ccba_harness.evals.tuner import (
    GitRatchetOptimizer,
    GitRatchetTuner,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    get_default_domain_scorers,
    preserve_yaml_frontmatter,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


# =========================================================================
# 1. RatchetConfig Tests
# =========================================================================


def test_ratchet_config_defaults(tmp_path: Path):
    """Test default values and explicit initialization of RatchetConfig."""
    target = tmp_path / "SKILL.md"
    cfg = RatchetConfig(target_file=target)

    assert cfg.target_file == target
    assert cfg.eval_dataset_file is None
    assert cfg.target_score == 90.0
    assert cfg.max_iterations == 10
    assert cfg.skill_name == ""
    assert not cfg.full_sweep


def test_ratchet_config_from_markdown_program(tmp_path: Path):
    """Test parsing a program.md file into RatchetConfig."""
    prog_file = tmp_path / "program.md"
    content = """# AutoResearch Tuning Program
- **Target File**: `skills/ccba-legal/SKILL.md`
- **Target Score**: 92.5%
- **Max Iterations**: 7
- **Dataset File**: `tests/legal_cases.json`
"""
    prog_file.write_text(content, encoding="utf-8")

    cfg = RatchetConfig.from_markdown_program(prog_file, root=tmp_path)
    assert cfg.target_file == (tmp_path / "skills/ccba-legal/SKILL.md").resolve()
    assert cfg.target_score == 92.5
    assert cfg.max_iterations == 7
    assert cfg.eval_dataset_file == (tmp_path / "tests/legal_cases.json").resolve()
    assert cfg.skill_name == "ccba-legal"


def test_ratchet_config_nonexistent_file_raises_error(tmp_path: Path):
    """Test that nonexistent program file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="Program spec file not found"):
        RatchetConfig.from_markdown_program(tmp_path / "nonexistent.md")


def test_ratchet_config_missing_target_raises_error(tmp_path: Path):
    """Test that omitting target file in program.md raises ValueError."""
    prog_file = tmp_path / "program.md"
    prog_file.write_text("# Program\n- **Target Score**: 85.0%\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required 'Target File'"):
        RatchetConfig.from_markdown_program(prog_file, root=tmp_path)


# =========================================================================
# 2. YAML Frontmatter Preservation Tests
# =========================================================================


def test_preserve_yaml_frontmatter_basic():
    """Test frontmatter is strictly preserved when body is mutated."""
    orig = """---
name: test-skill
description: A test skill
version: 1.0.0
---

# Instruction Heading
Initial prompt instructions.
"""
    edited = "# New Heading\nMutated instructions without frontmatter."
    merged = preserve_yaml_frontmatter(orig, edited)

    assert merged.startswith("---")
    assert "name: test-skill" in merged
    assert "version: 1.0.0" in merged
    assert "# New Heading" in merged
    assert "Mutated instructions without frontmatter." in merged


def test_preserve_yaml_frontmatter_when_edited_has_frontmatter():
    """Test that if edited content inadvertently contains frontmatter, only original is kept."""
    orig = """---
name: original-name
secret: original-secret
---

# Original Body
"""
    edited = """---
name: hijacked-name
secret: leaked
---

# Mutated Body
Only this body should survive.
"""
    merged = preserve_yaml_frontmatter(orig, edited)

    assert "name: original-name" in merged
    assert "secret: original-secret" in merged
    assert "hijacked-name" not in merged
    assert "leaked" not in merged
    assert "Only this body should survive." in merged


def test_preserve_yaml_frontmatter_no_frontmatter():
    """Test when original has no frontmatter, edited content is returned as-is."""
    orig = "# Simple Markdown Document\nNo frontmatter here."
    edited = "# Updated Document\nNew body content."
    merged = preserve_yaml_frontmatter(orig, edited)

    assert merged == edited


def test_preserve_yaml_frontmatter_with_markdown_rules():
    """Test frontmatter preservation when body contains markdown horizontal rules (---)."""
    orig = """---
name: skill-with-rules
---

# Section 1
Content 1
---
# Section 2
Content 2
"""
    edited = "# Section 1\nNew Content\n---\n# Section 2\nUpdated Content"
    merged = preserve_yaml_frontmatter(orig, edited)

    assert merged.startswith("---\nname: skill-with-rules\n---")
    assert "New Content" in merged
    assert "---" in merged
    assert "Updated Content" in merged


def test_preserve_yaml_frontmatter_with_comments_and_blank_lines():
    """Test frontmatter preserves exact formatting, indentation, and comments."""
    orig = """---
# Important Skill Metadata
name: ccba-pccc
description: >
  Multi-line description
  with indentation
version: 2.1.0
---

# PCCC Audit
Original text
"""
    edited = "# PCCC Audit\nMutated text"
    merged = preserve_yaml_frontmatter(orig, edited)

    assert "# Important Skill Metadata" in merged
    assert "Multi-line description" in merged
    assert "with indentation" in merged
    assert "Mutated text" in merged


# =========================================================================
# 3. Domain Scorers Tests
# =========================================================================


def test_get_default_domain_scorers_legal():
    """Test domain scorers for legal skill."""
    scorers = get_default_domain_scorers("ccba-legal-advisor")
    names = [s.name for s in scorers]
    assert "legal_grounding" in names
    assert "anti_trap_hard_floor" in names
    assert any(s.is_critical for s in scorers)


def test_get_default_domain_scorers_pccc():
    """Test domain scorers for pccc/qc skill."""
    scorers = get_default_domain_scorers("ccba-ai-qc-pccc-audit")
    names = [s.name for s in scorers]
    assert "technical_qc" in names
    assert "pccc_anti_trap_hard_floor" in names


def test_get_default_domain_scorers_academic():
    """Test domain scorers for academic writing skill."""
    scorers = get_default_domain_scorers("ccba-academic-writing")
    names = [s.name for s in scorers]
    assert "academic_structure" in names
    assert "academic_rigor_hard_floor" in names


def test_get_default_domain_scorers_bim():
    """Test domain scorers for bim classification skill."""
    scorers = get_default_domain_scorers("bigbim-classification")
    names = [s.name for s in scorers]
    assert "bim_classification_rules" in names
    assert "bim_anti_trap_hard_floor" in names


def test_get_default_domain_scorers_fallback():
    """Test fallback scorers for generic skill."""
    scorers = get_default_domain_scorers("generic-skill")
    assert len(scorers) == 1
    assert isinstance(scorers[0], RegexScorer)


# =========================================================================
# 4. GitRatchetOptimizer Core Engine Tests
# =========================================================================


def test_optimizer_alias():
    """Verify GitRatchetTuner is an alias of GitRatchetOptimizer."""
    assert GitRatchetTuner is GitRatchetOptimizer


def test_propose_mutation_preserves_frontmatter(tmp_path: Path):
    """Test propose_mutation preserves frontmatter across iterations."""
    target = tmp_path / "SKILL.md"
    initial_text = """---
name: ccba-copywriting
version: 1.0.0
---

# CCBA Copywriting
Original instruction text.
"""
    target.write_text(initial_text, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, skill_name="ccba-copywriting")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    mutated = tuner.propose_mutation(initial_text, 1)
    assert mutated.startswith("---")
    assert "name: ccba-copywriting" in mutated
    assert "version: 1.0.0" in mutated
    assert len(mutated) > len(initial_text)


def test_evaluate_content_domain_simulation():
    """Test evaluate_content runs domain simulation correctly on legal traps."""
    target = Path("dummy/SKILL.md")
    cfg = RatchetConfig(target_file=target, skill_name="ccba-legal-advisor")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    # Content without guardrails: fails on trap 136/2020
    bad_content = "# Legal Skill\nBasic instructions without 105/2025"
    report_bad = tuner.evaluate_content(bad_content)
    assert report_bad.overall_score < 90.0

    # Content with 105/2025 guardrail: passes
    good_content = "# Legal Skill\nNghị định 105/2025 thay thế 136/2020. Luật số 135/2025."
    report_good = tuner.evaluate_content(good_content)
    assert report_good.overall_score >= report_bad.overall_score


def test_ratchet_keep_on_improvement(tmp_path: Path):
    """Test that improved score with 0 critical failures results in KEEP decision."""
    target = tmp_path / "SKILL.md"
    target.write_text("---\nname: my-skill\n---\n# Baseline\n", encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=2)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    eval_calls = 0

    def mock_eval(content: str) -> EvalReport:
        nonlocal eval_calls
        eval_calls += 1
        score = 60.0 if eval_calls == 1 else 95.0
        return EvalReport(
            total_items=1,
            passed_items=1 if score >= 90.0 else 0,
            failed_items=0 if score >= 90.0 else 1,
            overall_score=score,
            pass_rate=100.0 if score >= 90.0 else 0.0,
            item_results=[
                EvalItemResult(
                    item_id="c1",
                    task_output="OK",
                    scores=[ScoreResult(scorer_name="Test", score=score / 100.0)],
                    composite_score=score,
                    passed=(score >= 90.0),
                    critical_failed=False,
                )
            ],
        )

    tuner.evaluate_content = mock_eval
    report = tuner.run()

    assert report.kept_commits == 1
    assert report.reverted_trials == 0
    assert report.final_score == 95.0
    assert report.history[0].decision == "KEEP"


def test_ratchet_revert_on_degraded_score(tmp_path: Path):
    """Test that degraded score triggers a REVERT and restores file content."""
    target = tmp_path / "SKILL.md"
    initial_content = "---\nname: my-skill\n---\n# Baseline High Quality\n"
    target.write_text(initial_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    eval_calls = 0

    def mock_eval(content: str) -> EvalReport:
        nonlocal eval_calls
        eval_calls += 1
        # Baseline is 80.0%, candidate is 50.0% (degradation)
        score = 80.0 if eval_calls == 1 else 50.0
        return EvalReport(
            total_items=1,
            passed_items=0,
            failed_items=1,
            overall_score=score,
            pass_rate=0.0,
            item_results=[
                EvalItemResult(
                    item_id="c1",
                    task_output="OK",
                    scores=[ScoreResult(scorer_name="Test", score=score / 100.0)],
                    composite_score=score,
                    passed=False,
                    critical_failed=False,
                )
            ],
        )

    tuner.evaluate_content = mock_eval
    report = tuner.run()

    assert report.reverted_trials == 1
    assert report.kept_commits == 0
    assert report.history[0].decision == "REVERT"
    # Target file must be restored to initial baseline
    assert target.read_text(encoding="utf-8") == initial_content


def test_ratchet_revert_on_critical_failure_even_with_high_score(tmp_path: Path):
    """Test that a critical failure strictly causes REVERT even if overall score is high."""
    target = tmp_path / "SKILL.md"
    initial_content = "# Initial Baseline"
    target.write_text(initial_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    eval_calls = 0

    def mock_eval(content: str) -> EvalReport:
        nonlocal eval_calls
        eval_calls += 1
        if eval_calls == 1:
            return EvalReport(
                total_items=1,
                passed_items=0,
                failed_items=1,
                overall_score=70.0,
                pass_rate=0.0,
                item_results=[
                    EvalItemResult(
                        item_id="c1",
                        task_output="OK",
                        scores=[ScoreResult(scorer_name="Test", score=0.7)],
                        composite_score=70.0,
                        passed=False,
                        critical_failed=False,
                    )
                ],
            )
        # Candidate has 99.0% score but 1 critical failure
        return EvalReport(
            total_items=1,
            passed_items=0,
            failed_items=1,
            overall_score=99.0,
            pass_rate=0.0,
            item_results=[
                EvalItemResult(
                    item_id="c1",
                    task_output="Violates rule",
                    scores=[
                        ScoreResult(scorer_name="R1", score=1.0),
                        ScoreResult(scorer_name="Crit", score=0.0, is_critical_fail=True),
                    ],
                    composite_score=99.0,
                    passed=False,
                    critical_failed=True,
                )
            ],
        )

    tuner.evaluate_content = mock_eval
    report = tuner.run()

    assert report.reverted_trials == 1
    assert report.kept_commits == 0
    assert report.history[0].critical_fails == 1
    assert report.history[0].decision == "REVERT"
    assert target.read_text(encoding="utf-8") == initial_content


def test_ratchet_exception_during_iteration_recovers_safely(tmp_path: Path):
    """Test that an exception during mutation/evaluation cleanly rolls back target file."""
    target = tmp_path / "SKILL.md"
    initial_content = "---\nname: safe\n---\n# Unbroken State\n"
    target.write_text(initial_content, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    eval_calls = 0

    def mock_eval_raising(content: str) -> EvalReport:
        nonlocal eval_calls
        eval_calls += 1
        if eval_calls == 1:
            return EvalReport(
                total_items=1,
                passed_items=0,
                failed_items=1,
                overall_score=50.0,
                pass_rate=0.0,
                item_results=[],
            )
        raise RuntimeError("Simulated transient evaluation crash!")

    tuner.evaluate_content = mock_eval_raising
    report = tuner.run()

    assert report.reverted_trials == 1
    assert "Lỗi thực thi" in report.history[0].summary
    # Disk content must be restored
    assert target.read_text(encoding="utf-8") == initial_content


def test_ratchet_git_checkpoint_invocations(tmp_path: Path):
    """Verify git add, commit, and checkout subprocess calls when dry_run_git=False."""
    target = tmp_path / "SKILL.md"
    target.write_text("# Initial", encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=2)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=False, project_root=tmp_path)

    # Mock subprocess.run
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # 1. Test commit improvement
        committed = tuner.git_commit_improvement("50.0% -> 95.0%")
        assert committed is True
        assert mock_run.call_count == 2  # git add, git commit

        # Verify git commit message format
        commit_cmd = mock_run.call_args_list[1][0][0]
        assert "git" in commit_cmd
        assert "commit" in commit_cmd
        assert "ratchet(opt):" in commit_cmd[3]

        # 2. Test rollback after commit
        tuner.git_rollback_target("# Restored", has_committed=True)
        assert mock_run.call_count == 3  # git checkout called
        checkout_cmd = mock_run.call_args_list[2][0][0]
        assert "checkout" in checkout_cmd


def test_ratchet_report_to_dict():
    """Test RatchetReport serialization to dictionary."""
    trial = RatchetTrialResult(
        iteration=1,
        score=95.0,
        passed=True,
        critical_fails=0,
        decision="KEEP",
        summary="Improved",
    )
    rep = RatchetReport(
        target_file="test/SKILL.md",
        initial_score=70.0,
        final_score=95.0,
        total_iterations=1,
        kept_commits=1,
        reverted_trials=0,
        history=[trial],
    )
    d = rep.to_dict()
    assert d["target_file"] == "test/SKILL.md"
    assert d["initial_score"] == 70.0
    assert d["final_score"] == 95.0
    assert len(d["history"]) == 1
    assert d["history"][0]["decision"] == "KEEP"


def test_custom_task_callable(tmp_path: Path):
    """Test that custom task callable passed to GitRatchetOptimizer is used."""
    target = tmp_path / "SKILL.md"
    target.write_text("# Target", encoding="utf-8")

    dataset = [EvalItem(id="item1", input_prompt="Hello", golden_answer="World")]
    called_task = False

    def my_task(item: EvalItem) -> str:
        nonlocal called_task
        called_task = True
        return "World"

    scorers = [RegexScorer(pattern="World")]
    cfg = RatchetConfig(target_file=target, max_iterations=1)
    tuner = GitRatchetOptimizer(
        cfg,
        scorers=scorers,
        dry_run_git=True,
        task=my_task,
        dataset=dataset,
    )
    report = tuner.evaluate_content("any content")

    assert called_task is True
    assert report.overall_score == 100.0


# =========================================================================
# 5. Integration with run_eval_pipeline & CLI Tests
# =========================================================================


def test_run_eval_pipeline_auto_tune_integration(tmp_path: Path):
    """Test run_eval_pipeline with auto_tune=True activates GitRatchetOptimizer."""
    skills_dir = tmp_path / ".agents" / "skills" / "ccba-copywriting"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: ccba-copywriting\n---\n# Copywriting Guidelines\nInitial content\n",
        encoding="utf-8",
    )

    dataset_file = tmp_path / "cases.json"
    dataset_file.write_text(
        json.dumps([{"id": "c1", "input_prompt": "Soạn thảo văn bản hành chính theo Nghị định 30"}]),
        encoding="utf-8",
    )

    async def mock_task(item: EvalItem) -> str:
        return "Căn cứ Nghị định 30/2020/NĐ-CP Điều 8 và Điều 10 quy định thể thức văn bản hành chính."

    rep = run_eval_pipeline(
        skill="copywriting",
        trials=2,
        auto_tune=True,
        dataset=dataset_file,
        project_root=tmp_path,
        task=mock_task,
        dry_run_git=True,
    )

    assert rep.metadata["auto_tune"] is True
    assert "ratchet_report" in rep.metadata
    assert rep.metadata["ratchet_report"]["total_iterations"] >= 1


def test_run_eval_cli_auto_tune_flag(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    """Test CLI ccba-harness eval with --auto-tune and --dry-run-git."""
    from ccba_harness.cli import run_eval_cli

    skills_dir = tmp_path / ".agents" / "skills" / "ccba-copywriting"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text(
        "---\nname: ccba-copywriting\n---\n# Instructions\n",
        encoding="utf-8",
    )

    dataset_file = tmp_path / "cases.json"
    dataset_file.write_text(
        json.dumps([{"id": "c1", "input_prompt": "Kiểm tra Nghị định 30", "golden_answer": "OK"}]),
        encoding="utf-8",
    )

    async def mock_task(item: EvalItem) -> str:
        return "OK"

    with patch("ccba_harness.evals.runner._create_default_eval_task", return_value=mock_task):
        code = run_eval_cli(
            [
                "--skill",
                "copywriting",
                "--dataset",
                str(dataset_file),
                "--auto-tune",
                "--dry-run-git",
                "--root",
                str(tmp_path),
                "--json",
            ]
        )
        assert code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["auto_tune"] is True
        assert "ratchet_report" in data["metadata"]
        assert data["metadata"]["ratchet_report"]["target_file"] == str(skill_file.resolve())


def test_ratchet_config_auto_infers_skill_name(tmp_path: Path):
    """Test RatchetConfig automatically infers skill_name from directory path."""
    skill_file = tmp_path / ".agents" / "skills" / "ccba-legal-advisor" / "SKILL.md"
    cfg = RatchetConfig(target_file=skill_file)
    assert cfg.skill_name == "ccba-legal-advisor"


def test_propose_mutation_distinct_enhancements_across_iterations(tmp_path: Path):
    """Test that propose_mutation produces distinct changes on subsequent iterations."""
    target = tmp_path / "SKILL.md"
    initial_text = "---\nname: ccba-test\n---\n# Baseline\nInitial text."
    target.write_text(initial_text, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, skill_name="generic")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    # Iteration 1 adds enhancement
    mut1 = tuner.propose_mutation(initial_text, 1)
    assert "## 5. Bất Biến Vận Hành & Khóa Cứng Hoàn Tất" in mut1

    # Iteration 2 with same strategy must add refinement, NOT produce identical text
    mut2 = tuner.propose_mutation(mut1, 2)
    assert mut2 != mut1
    assert "<!-- Ratchet Optimization Refinement 2 -->" in mut2


def test_propose_mutation_pccc_domain(tmp_path: Path):
    """Test propose_mutation provides PCCC-specific strategies for PCCC skills."""
    target = tmp_path / "SKILL.md"
    initial_text = "---\nname: ccba-ai-qc-pccc-audit\n---\n# PCCC Audit\n"
    target.write_text(initial_text, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, skill_name="ccba-ai-qc-pccc-audit")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    mut = tuner.propose_mutation(initial_text, 1)
    assert "QCVN 06" in mut or "PCCC" in mut


def test_git_commit_scopes_to_target_file_only(tmp_path: Path):
    """Verify git commit scopes commit to target file pathspec only."""
    target = tmp_path / "SKILL.md"
    target.write_text("# Target", encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=False, project_root=tmp_path)

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        committed = tuner.git_commit_improvement("70% -> 90%")
        assert committed is True

        commit_cmd = mock_run.call_args_list[1][0][0]
        assert "--" in commit_cmd
        # Pathspec after '--' must match target file relative path
        dash_dash_idx = commit_cmd.index("--")
        assert commit_cmd[dash_dash_idx + 1] == "SKILL.md"


def test_git_commit_failure_cleans_staging_index(tmp_path: Path):
    """Verify that if git commit fails, git restore --staged is invoked to clean index."""
    target = tmp_path / "SKILL.md"
    target.write_text("# Target", encoding="utf-8")

    cfg = RatchetConfig(target_file=target, target_score=90.0, max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=False, project_root=tmp_path)

    def side_effect(cmd, **kwargs):
        if "commit" in cmd:
            raise RuntimeError("Simulated git commit failure!")
        return MagicMock(returncode=0)

    with patch("subprocess.run", side_effect=side_effect) as mock_run:
        committed = tuner.git_commit_improvement("70% -> 90%")
        assert committed is False

        # Must have attempted git restore --staged
        commands_run = [call[0][0] for call in mock_run.call_args_list]
        restore_calls = [c for c in commands_run if "restore" in c and "--staged" in c]
        assert len(restore_calls) == 1


def test_run_eval_pipeline_nonexistent_skill_raises_error(tmp_path: Path):
    """Test run_eval_pipeline with auto_tune=True raises FileNotFoundError if skill cannot be resolved."""
    dataset_file = tmp_path / "cases.json"
    dataset_file.write_text(
        json.dumps([{"id": "c1", "input_prompt": "Test"}]),
        encoding="utf-8",
    )

    with pytest.raises(FileNotFoundError, match="Target skill file could not be resolved"):
        run_eval_pipeline(
            skill="definitely_nonexistent_skill_xyz",
            auto_tune=True,
            dataset=dataset_file,
            project_root=tmp_path,
        )


def test_run_eval_pipeline_full_sweep_forwarding(tmp_path: Path):
    """Test full_sweep parameter is passed to RatchetConfig in run_eval_pipeline."""
    skills_dir = tmp_path / ".agents" / "skills" / "ccba-copywriting"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("---\nname: ccba-copywriting\n---\n# Body\n", encoding="utf-8")

    dataset_file = tmp_path / "cases.json"
    dataset_file.write_text(
        json.dumps([{"id": "c1", "input_prompt": "Prompt", "golden_answer": "OK"}]),
        encoding="utf-8",
    )

    with patch("ccba_harness.evals.tuner.GitRatchetOptimizer.run") as mock_tuner_run:
        mock_tuner_run.return_value = RatchetReport(
            target_file=str(skill_file),
            initial_score=100.0,
            final_score=100.0,
            total_iterations=2,
            kept_commits=0,
            reverted_trials=2,
        )
        rep = run_eval_pipeline(
            skill="copywriting",
            trials=2,
            auto_tune=True,
            full_sweep=True,
            dataset=dataset_file,
            project_root=tmp_path,
            dry_run_git=True,
        )
        assert rep.metadata["full_sweep"] is True


def test_resolve_target_skill_file_bigbim(tmp_path: Path):
    """Test resolve_target_skill_file resolves bigbim-* prefix properly."""
    from ccba_harness.evals.runner import resolve_target_skill_file

    skills_dir = tmp_path / ".agents" / "skills" / "bigbim-classification"
    skills_dir.mkdir(parents=True, exist_ok=True)
    skill_file = skills_dir / "SKILL.md"
    skill_file.write_text("---\nname: bigbim-classification\n---\n", encoding="utf-8")

    # Resolve with 'classification'
    res1 = resolve_target_skill_file("classification", tmp_path)
    assert res1 == skill_file.resolve()

    # Resolve with full 'bigbim-classification'
    res2 = resolve_target_skill_file("bigbim-classification", tmp_path)
    assert res2 == skill_file.resolve()


def test_preserve_yaml_frontmatter_crlf():
    """Test frontmatter preservation maintains CRLF line endings when present in original."""
    orig = "---\r\nname: crlf-skill\r\n---\r\n\r\n# Body\r\nText"
    edited = "# New Body\r\nNew text"
    merged = preserve_yaml_frontmatter(orig, edited)
    assert "\r\n" in merged
    assert merged.startswith("---\r\nname: crlf-skill\r\n---")

