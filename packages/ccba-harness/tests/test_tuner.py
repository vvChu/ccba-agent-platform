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
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness.evals.models import EvalItem, EvalItemResult, EvalReport, ScoreResult
from ccba_harness.evals.runner import run_eval_pipeline
from ccba_harness.evals.scorers import LegalVerbatimProvenanceScorer, RegexScorer, get_legal_scorers
from ccba_harness.evals.tuner import (
    AdaptiveRateLimiter,
    CircuitBreakerOpenError,
    GitRatchetOptimizer,
    GitRatchetTuner,
    LLMTaskAdapter,
    RatchetConfig,
    RatchetReport,
    RatchetTrialResult,
    TokenBudgetExceededError,
    TokenUsageTracker,
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
    """Test domain scorers for legal skill routes to get_legal_scorers() (ADR-0059)."""
    scorers = get_default_domain_scorers("ccba-legal-advisor")
    names = [s.name for s in scorers]
    assert "legal_verbatim_provenance" in names
    assert any(s.is_critical for s in scorers)
    assert pytest.approx(sum(s.weight for s in scorers)) == 1.0


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_valid_citation():
    """Verify valid citation with existing article passes with SHA-256 provenance."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_valid", input_prompt="Quy định thẩm duyệt PCCC mới nhất")
    text = (
        "Căn cứ theo Nghị định số 105/2025/NĐ-CP tại Điều 15, việc thẩm định thiết kế PCCC "
        "được phân định thẩm quyền rõ ràng cho Cơ quan chuyên môn về xây dựng."
    )
    result = await scorer.score(text, item)
    assert result.score == 1.0
    assert result.is_critical_fail is False
    assert "Xác thực căn cứ pháp lý thành công" in result.reasoning
    assert "provenance" in result.metadata
    prov = result.metadata["provenance"]
    assert len(prov) >= 1
    assert prov[0]["document_number"] == "105/2025/NĐ-CP"
    assert len(prov[0]["pdf_sha256"]) == 64


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_expired_trap_fails_critically():
    """Verify citing expired statute without replacement notice fails critically (score 0.0)."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_trap", input_prompt="Thẩm duyệt PCCC theo NĐ 136")
    text = (
        "Căn cứ theo Nghị định 136/2020/NĐ-CP Điều 13, hồ sơ thẩm duyệt thiết kế PCCC "
        "bao gồm đơn đề nghị và bản vẽ thiết kế cơ sở."
    )
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Anti-Trap Hard Floor" in result.reasoning
    assert "136/2020" in result.reasoning
    assert "105/2025" in result.reasoning


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_expired_trap_with_replacement_passes():
    """Verify citing expired statute WITH replacement acknowledgement passes."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_trap_resolved", input_prompt="Thẩm duyệt PCCC theo NĐ 136")
    text = (
        "Lưu ý: Nghị định 136/2020/NĐ-CP đã hết hiệu lực và được thay thế bởi Nghị định 105/2025/NĐ-CP. "
        "Căn cứ theo Nghị định số 105/2025/NĐ-CP tại Điều 15, thẩm quyền thẩm duyệt được thực hiện..."
    )
    result = await scorer.score(text, item)
    assert result.score == 1.0
    assert result.is_critical_fail is False


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_hallucinated_statute_fails_critically():
    """Verify citing non-existent statutory document fails critically (score 0.0)."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_hallucinated_doc", input_prompt="Hỏi luật")
    text = (
        "Căn cứ theo Nghị định số 999/2026/NĐ-CP quy định chi tiết về quản lý quy hoạch xây dựng..."
    )
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Zero-Hallucination Hard Floor" in result.reasoning
    assert "999/2026/NĐ-CP" in result.reasoning


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_hallucinated_clause_fails_critically():
    """Verify citing non-existent clause in valid document fails critically (score 0.0)."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_hallucinated_clause", input_prompt="Hỏi luật")
    text = "Căn cứ theo Nghị định số 105/2025/NĐ-CP tại Điều 999 quy định về chế tài xử phạt..."
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Zero-Hallucination Hard Floor" in result.reasoning
    assert "Điều 999" in result.reasoning


@pytest.mark.asyncio
async def test_legal_verbatim_provenance_scorer_no_citation_fails_critically():
    """Verify legal skill output without any statutory citation fails critically."""
    scorer = LegalVerbatimProvenanceScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legal_no_cite", input_prompt="Hỏi luật")
    text = (
        "Để thực hiện thủ tục này, chủ đầu tư cần liên hệ cơ quan có thẩm quyền để được giải quyết."
    )
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Không phát hiện trích dẫn" in result.reasoning


def test_get_legal_scorers_composition():
    """Verify composition and weights of get_legal_scorers()."""
    scorers = get_legal_scorers()
    names = [s.name for s in scorers]
    assert "legal_verbatim_provenance" in names
    assert "progressive_disclosure_links" in names
    assert "anti_debris" in names
    assert "depth" in names
    assert any(s.is_critical for s in scorers)
    assert pytest.approx(sum(s.weight for s in scorers)) == 1.0


def test_get_default_domain_scorers_pccc():
    """Test domain scorers for pccc/qc skill."""
    scorers = get_default_domain_scorers("ccba-ai-qc-pccc-audit")
    names = [s.name for s in scorers]
    assert "pccc_parametric" in names
    assert "anti_debris" in names
    assert "depth" in names
    assert any(s.is_critical for s in scorers)
    assert pytest.approx(sum(s.weight for s in scorers)) == 1.0


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
    assert "bim_classification" in names
    assert any(s.is_critical for s in scorers)


def test_get_default_domain_scorers_fallback():
    """Test fallback scorers for generic skill uses safe LeanStructuralScorer suite."""
    scorers = get_default_domain_scorers("generic-skill")
    names = [s.name for s in scorers]
    assert "progressive_disclosure_links" in names
    assert "depth" in names
    assert "anti_debris" in names
    assert not any(
        s.is_critical for s in scorers
    )  # ADR-0058 Hard Completion Lock is NOT forced on fallback
    assert pytest.approx(sum(s.weight for s in scorers)) == 1.0


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
        json.dumps(
            [{"id": "c1", "input_prompt": "Soạn thảo văn bản hành chính theo Nghị định 30"}]
        ),
        encoding="utf-8",
    )

    async def mock_task(item: EvalItem) -> str:
        return (
            "Căn cứ Nghị định 30/2020/NĐ-CP Điều 8 và Điều 10 quy định thể thức văn bản hành chính."
        )

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
    """Test that propose_mutation produces distinct changes across iterations and halts cleanly without HTML comment junk."""
    target = tmp_path / "SKILL.md"
    initial_text = "---\nname: ccba-codebase-design\n---\n# Baseline\nInitial text."
    target.write_text(initial_text, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, skill_name="ccba-codebase-design")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    # Iteration 1 adds Strategy 1 (Hard Completion Lock)
    mut1 = tuner.propose_mutation(initial_text, 1)
    assert "Bất Biến Vận Hành & Khóa Cứng Hoàn Tất" in mut1
    assert "python -m ccba_harness verify-patch" in mut1

    # Iteration 2 adds Strategy 2 (Double-Pass Review)
    mut2 = tuner.propose_mutation(mut1, 2)
    assert mut2 != mut1
    assert "Double-Pass Adversarial Review" in mut2

    # Iteration 3 adds Strategy 3 (KISS & Error Handling)
    mut3 = tuner.propose_mutation(mut2, 3)
    assert mut3 != mut2
    assert "KISS, Idempotency & Error Handling" in mut3

    # Iteration 4: All strategies applied -> returns unchanged (HALT_NO_FURTHER_STRATEGIES)
    mut4 = tuner.propose_mutation(mut3, 4)
    assert mut4 == mut3
    assert "<!-- Ratchet Optimization Refinement" not in mut4


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

    with (
        patch("ccba_harness.evals.tuner.GitRatchetOptimizer.run") as mock_tuner_run,
        patch("ccba_harness.evals.tuner.GitRatchetOptimizer.evaluate_content") as mock_eval,
    ):
        mock_tuner_run.return_value = RatchetReport(
            target_file=str(skill_file),
            initial_score=100.0,
            final_score=100.0,
            total_iterations=2,
            kept_commits=0,
            reverted_trials=2,
        )
        mock_eval.return_value = EvalReport(
            total_items=1,
            passed_items=1,
            failed_items=0,
            overall_score=100.0,
            pass_rate=1.0,
            item_results=[],
            summary_by_scorer={},
            metadata={},
        )
        rep = run_eval_pipeline(
            skill="copywriting",
            trials=2,
            auto_tune=True,
            full_sweep=True,
            dataset=dataset_file,
            project_root=tmp_path,
            task=lambda item: "OK",
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


# =========================================================================
# 7. Real LLM Adapter, Token Budget Ceiling & Circuit Breaker Tests (Ticket 03)
# =========================================================================


def test_token_usage_tracker_accumulation_and_thresholds():
    """Verify TokenUsageTracker correctly accumulates usage and sets warning / halt flags."""
    tracker = TokenUsageTracker(budget_ceiling=1000)

    # 1. Initial state
    assert tracker.total_tokens == 0
    assert tracker.is_exhausted is False
    assert tracker.warning_triggered is False
    assert tracker.halt_triggered is False

    # 2. Record below 90%
    tracker.record_usage(prompt_tokens=400, completion_tokens=400, latency_s=1.0)
    assert tracker.total_tokens == 800
    assert tracker.warning_triggered is False
    assert tracker.is_exhausted is False

    # 3. Reach 90% (900 tokens) -> Warning triggered
    tracker.record_usage(prompt_tokens=50, completion_tokens=50, latency_s=0.5)
    assert tracker.total_tokens == 900
    assert tracker.warning_triggered is True
    assert tracker.halt_triggered is False
    assert tracker.is_exhausted is False

    # 4. Reach 100% (1000 tokens) -> Hard ceiling halt triggered
    tracker.record_usage(prompt_tokens=60, completion_tokens=50, latency_s=0.5)
    assert tracker.total_tokens == 1010
    assert tracker.halt_triggered is True
    assert tracker.is_exhausted is True
    assert tracker.total_calls == 3
    assert tracker.avg_latency_s == (1.0 + 0.5 + 0.5) / 3


def test_llm_task_adapter_call_and_token_recording():
    """Verify LLMTaskAdapter executes inference, records tokens, and returns response content."""
    from types import SimpleNamespace

    mock_client = MagicMock()
    mock_res = SimpleNamespace(
        content="Quy định PCCC Bậc I...",
        usage=SimpleNamespace(prompt_tokens=30, completion_tokens=70, total_tokens=100),
    )
    mock_client.chat_with_metadata.return_value = mock_res

    tracker = TokenUsageTracker(budget_ceiling=10000)
    adapter = LLMTaskAdapter(
        model="gemini-3.7-flash-high",
        client=mock_client,
        token_tracker=tracker,
    )

    eval_task = adapter.create_eval_task(skill_content="# Skill Content")
    item = EvalItem(id="case_1", input_prompt="Kiểm tra bậc chịu lửa")

    output = eval_task(item)
    assert output == "Quy định PCCC Bậc I..."
    assert tracker.prompt_tokens == 30
    assert tracker.completion_tokens == 70
    assert tracker.total_tokens == 100
    assert tracker.total_calls == 1

    # Verify call parameters
    mock_client.chat_with_metadata.assert_called_once_with(
        message="Kiểm tra bậc chịu lửa",
        system="# Skill Content",
        model="gemini-3.7-flash-high",
        temperature=0.0,
    )


def test_llm_task_adapter_budget_exhaustion_raises_error():
    """Verify LLMTaskAdapter raises TokenBudgetExceededError when tracker is exhausted."""
    tracker = TokenUsageTracker(budget_ceiling=500)
    tracker.record_usage(300, 300)  # Total 600 > 500 ceiling
    assert tracker.is_exhausted is True

    mock_client = MagicMock()
    adapter = LLMTaskAdapter(client=mock_client, token_tracker=tracker)
    eval_task = adapter.create_eval_task(skill_content="# Skill")
    item = EvalItem(id="case_1", input_prompt="Prompt")

    with pytest.raises(TokenBudgetExceededError, match="Token budget ceiling"):
        eval_task(item)
    mock_client.chat_with_metadata.assert_not_called()


def test_tuner_with_real_llm_adapter_telemetry(tmp_path: Path):
    """Verify GitRatchetOptimizer in real LLM mode records tokens in report and history."""
    from types import SimpleNamespace

    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-llm-skill\n---\n# Test Skill\nCăn cứ Luật Xây dựng...",
        encoding="utf-8",
    )

    mock_client = MagicMock()
    mock_res = SimpleNamespace(
        content="Nghị định 105/2025/NĐ-CP và Luật Xây dựng quy định...",
        usage=SimpleNamespace(prompt_tokens=40, completion_tokens=60, total_tokens=100),
    )
    mock_client.chat_with_metadata.return_value = mock_res

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        llm_model="gemini-3.7-flash-high",
        max_iterations=2,
        token_budget=10000,
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        client=mock_client,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.total_tokens > 0
    assert report.prompt_tokens > 0
    assert report.completion_tokens > 0
    assert report.avg_latency_s >= 0.0
    assert len(report.history) > 0
    assert report.history[0].total_tokens > 0


def test_tuner_circuit_breaker_halt(tmp_path: Path):
    """Verify GitRatchetOptimizer halts gracefully without crashing when CircuitBreaker is open."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-cb-skill\n---\n# Skill Content",
        encoding="utf-8",
    )

    mock_client = MagicMock()
    # Baseline succeeds
    from types import SimpleNamespace

    mock_res_ok = SimpleNamespace(
        content="Valid content",
        usage=SimpleNamespace(prompt_tokens=10, completion_tokens=10, total_tokens=20),
    )
    # Iteration fails with CircuitBreakerOpenError
    mock_client.chat_with_metadata.side_effect = [
        mock_res_ok,
        mock_res_ok,
        CircuitBreakerOpenError("Circuit is OPEN"),
    ]

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_iterations=5,
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        client=mock_client,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.halt_reason == "CIRCUIT_BREAKER_OPEN"
    assert len(report.history) > 0
    last_trial = report.history[-1]
    assert last_trial.decision == "REVERT"
    assert "Circuit Breaker" in last_trial.summary


def test_tuner_token_budget_exceeded_halt(tmp_path: Path):
    """Verify GitRatchetOptimizer halts when token budget is exceeded."""
    from types import SimpleNamespace

    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-budget-skill\n---\n# Skill Content",
        encoding="utf-8",
    )

    mock_client = MagicMock()
    # Returns 100 tokens per call, while budget ceiling is only 50
    mock_res = SimpleNamespace(
        content="Content...",
        usage=SimpleNamespace(prompt_tokens=50, completion_tokens=50, total_tokens=100),
    )
    mock_client.chat_with_metadata.return_value = mock_res

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_iterations=5,
        token_budget=250,  # Allows baseline (200 tokens) but exhausts on iteration 1
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        client=mock_client,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.halt_reason == "TOKEN_BUDGET_EXCEEDED"
    assert len(report.history) > 0
    assert report.history[-1].decision == "REVERT"
    assert "token budget" in report.history[-1].summary.lower()


def test_tuner_token_budget_exceeded_during_baseline(tmp_path: Path):
    """Verify GitRatchetOptimizer halts gracefully if budget is exceeded during baseline."""
    from types import SimpleNamespace

    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-budget-baseline-skill\n---\n# Skill Content",
        encoding="utf-8",
    )

    mock_client = MagicMock()
    mock_res = SimpleNamespace(
        content="Content...",
        usage=SimpleNamespace(prompt_tokens=50, completion_tokens=50, total_tokens=100),
    )
    mock_client.chat_with_metadata.return_value = mock_res

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_iterations=5,
        token_budget=50,  # Smaller than 1 call (100 tokens)
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        client=mock_client,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.halt_reason == "TOKEN_BUDGET_EXCEEDED"
    assert report.total_iterations == 0
    assert len(report.history) == 0


def test_get_default_domain_scorers_risk_and_orchestration():
    """Verify get_default_domain_scorers provides specialized scorers for risk and orchestration."""
    from ccba_harness.evals.tuner import get_default_domain_scorers

    # 1. bigbim-risk
    risk_scorers = get_default_domain_scorers("bigbim-risk")
    risk_names = [s.name for s in risk_scorers]
    assert "risk_conflict_audit" in risk_names
    assert "risk_anti_trap_hard_floor" in risk_names
    assert "risk_mitigation_guard" in risk_names

    # 2. orchestration
    orch_scorers = get_default_domain_scorers("ccba-teamwork")
    orch_names = [s.name for s in orch_scorers]
    assert "single_writer_invariant" in orch_names
    assert "progressive_disclosure_links" in orch_names
    assert "handoff_protocol" in orch_names

    # 3. platform-loader / ccba-handoff / ccba-issue-tree
    for name in ["platform-loader", "ccba-handoff", "ccba-issue-tree"]:
        scs = get_default_domain_scorers(name)
        assert any(s.name == "single_writer_invariant" for s in scs)

    # 4. bigbim-governance
    gov_scorers = get_default_domain_scorers("bigbim-governance")
    gov_names = [s.name for s in gov_scorers]
    assert "governance_thread_audit" in gov_names
    assert "governance_anti_trap_hard_floor" in gov_names
    assert "governance_risk_matrix_guard" in gov_names

    # 5. bigbim-rase
    rase_scorers = get_default_domain_scorers("bigbim-rase")
    rase_names = [s.name for s in rase_scorers]
    assert "rase_decomposition_audit" in rase_names
    assert "rase_ifc4x3_pmapping_hard_floor" in rase_names
    assert "rase_qto_mapping_guard" in rase_names


def test_bigbim_risk_eval_dataset_and_scorer(tmp_path: Path):
    """Verify bigbim-risk skill evaluates against eval_bigbim_risk.json with high fidelity score >= 85%."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: bigbim-risk
triggers:
- mâu thuẫn thông tin
- information conflict
- V2 - Coordination
---
# BIGBIM Risk & Information Conflict Audit Skill
Mâu thuẫn thông tin (Information Conflict) tại bước phối hợp V2 - Coordination:
- Phân biệt Va chạm vật lý Level 1 và Khoảng hở thao tác Level 2 (Level 2 Space Gap).
- Khoảng cách an toàn tối thiểu mặt trước tủ điện >= 900mm và ống trần đến dầm/sàn >= 150mm.
- Bảo vệ thuộc tính BBP và Sợi Chỉ Đỏ, giữ nguyên cấu trúc Unique ID gán từ BBP-A0.
- Leo thang /ccba-issue-tree (Why-Tree và How-Tree) dưới quyền phê duyệt của Chủ trì Bộ môn.
""",
        encoding="utf-8",
    )

    dataset_file = (
        Path(__file__).resolve().parent.parent.parent.parent
        / ".agents"
        / "skills"
        / "ccba-eval-gate"
        / "test_cases"
        / "eval_bigbim_risk.json"
    )
    assert dataset_file.exists(), f"Dataset file must exist at {dataset_file}"

    cfg = RatchetConfig(
        target_file=skill_file,
        eval_dataset_file=dataset_file,
        skill_name="bigbim-risk",
        max_iterations=1,
    )

    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=tmp_path)
    report = opt.run()

    # Score must achieve >= 85.0% without critical failures
    assert report.initial_score >= 85.0
    assert report.final_score >= 85.0


def test_bigbim_governance_eval_dataset_and_scorer(tmp_path: Path):
    """Verify bigbim-governance skill evaluates against eval_bigbim_governance.json with score >= 85%."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: bigbim-governance
triggers:
- sợi chỉ vàng
- sợi chỉ đỏ
- unique id
- governance
- golden thread
- red thread
- ST2
- ISO 19650-5
---
# BIGBIM Governance Core Guardrails Skill
Kiểm duyệt Sợi Chỉ Vàng & Rào chắn Sợi Chỉ Đỏ (BIGBIM Governance Core):
- Trụ cột Sợi Chỉ Vàng (Golden Thread): Quản trị thông tin dài hạn 75 năm (PM_80), cấp an ninh ST2 theo chuẩn ISO 19650-5, kiểm soát Đoạn Đò-3 chống LMS vendor lock-in.
- Trụ cột Sợi Chỉ Đỏ (Red Thread Risk Matrix): Quét 4 mã rủi ro RK_50_40_35 (No-Risk), RK_10_70_04 (Time-Risk), RK_50_40_45 (Do-Risk), RK_50_60_28 (Use-Risk En_25_70_47).
- Cưỡng chế Unique ID Bất biến & Đối soát 3 Chiều: Khóa mã Unique ID từ pha BBP-A0, đối soát bản vẽ thiết kế, AIM và biển hiệu thực tế.
""",
        encoding="utf-8",
    )

    dataset_file = (
        Path(__file__).resolve().parent.parent.parent.parent
        / ".agents"
        / "skills"
        / "ccba-eval-gate"
        / "test_cases"
        / "eval_bigbim_governance.json"
    )
    assert dataset_file.exists(), f"Dataset file must exist at {dataset_file}"

    cfg = RatchetConfig(
        target_file=skill_file,
        eval_dataset_file=dataset_file,
        skill_name="bigbim-governance",
        max_iterations=1,
    )

    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=tmp_path)
    report = opt.run()

    # Score must achieve >= 85.0% without critical failures
    assert report.initial_score >= 85.0
    assert report.final_score >= 85.0
    assert not any(trial.critical_fails > 0 for trial in report.history)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert not any(item_res.critical_failed for item_res in eval_rep.item_results)


def test_bigbim_rase_eval_dataset_and_scorer(tmp_path: Path):
    """Verify bigbim-rase skill evaluates against eval_bigbim_rase.json with score >= 85%."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        """---
name: bigbim-rase
triggers:
- rase
- phân tích rase
- pset map
- IFC4X3
- IfcPropertySet
- IfcRelDefinesByProperties
---
# BIGBIM RASE Analyzer Skill
Bóc tách RASE và Ánh xạ thuộc tính IFC4X3 (ISO 16739):
- Phân rã ma trận R-A-S-E 4 tầng logic: Requirement (Chỉ số kỹ thuật), Applicability (Thực thể IFC), Selection (Thuộc tính IFC), Exception (Ngoại lệ).
- Quy chuẩn gán thuộc tính IFC4X3: Cấm gán trực tiếp vào IfcObject; bắt buộc đóng gói trong IfcPropertySet (Pset_) và liên kết gián tiếp qua quan hệ IfcRelDefinesByProperties.
- Tích hợp dữ liệu khối lượng Quantity Take-Off (Qto) BaseQuantities: Qto_SpaceBaseQuantities (GrossVolume), Qto_WallBaseQuantities, Qto_SlabBaseQuantities.
""",
        encoding="utf-8",
    )

    dataset_file = (
        Path(__file__).resolve().parent.parent.parent.parent
        / ".agents"
        / "skills"
        / "ccba-eval-gate"
        / "test_cases"
        / "eval_bigbim_rase.json"
    )
    assert dataset_file.exists(), f"Dataset file must exist at {dataset_file}"

    cfg = RatchetConfig(
        target_file=skill_file,
        eval_dataset_file=dataset_file,
        skill_name="bigbim-rase",
        max_iterations=1,
    )

    opt = GitRatchetOptimizer(config=cfg, dry_run_git=True, project_root=tmp_path)
    report = opt.run()

    # Score must achieve >= 85.0% without critical failures
    assert report.initial_score >= 85.0
    assert report.final_score >= 85.0
    assert not any(trial.critical_fails > 0 for trial in report.history)
    eval_rep = opt.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert not any(item_res.critical_failed for item_res in eval_rep.item_results)


def test_adaptive_rate_limiter_timing_and_backoff():
    """Verify AdaptiveRateLimiter enforces intervals and increases backoff on high latency."""
    from ccba_harness.evals.tuner import AdaptiveRateLimiter

    simulated_time = 100.0
    sleeps: list[float] = []

    def mock_time():
        nonlocal simulated_time
        return simulated_time

    def mock_sleep(d: float):
        nonlocal simulated_time
        sleeps.append(d)
        simulated_time += d

    # 60 RPM = 1.0s interval
    limiter = AdaptiveRateLimiter(
        requests_per_minute=60.0,
        latency_threshold_s=4.0,
        backoff_multiplier=1.5,
        sleeper=mock_sleep,
        time_fn=mock_time,
    )

    # First call: no previous call, base interval is satisfied
    d1 = limiter.wait(last_latency_s=1.0)
    assert d1 == 0.0

    # Second call immediately (0 elapsed): should delay ~1.0s
    d2 = limiter.wait(last_latency_s=1.0)
    assert d2 == 1.0
    assert len(sleeps) == 1

    # Third call with high latency (6.0s > 4.0s threshold): excess 2.0s * 0.5 = 1.0s backoff
    # If 0s elapsed, delay = 1.0 (base) + 1.0 (backoff) = 2.0s
    d3 = limiter.wait(last_latency_s=6.0)
    assert d3 == 2.0
    assert len(sleeps) == 2


def test_llm_task_adapter_with_rate_limiter():
    """Verify LLMTaskAdapter invokes rate_limiter.wait() on each eval call."""
    from unittest.mock import MagicMock

    from ccba_harness.evals.models import EvalItem
    from ccba_harness.evals.tuner import LLMTaskAdapter

    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.content = "Answer"
    mock_res.usage.prompt_tokens = 10
    mock_res.usage.completion_tokens = 10
    mock_client.chat_with_metadata.return_value = mock_res

    wait_calls: list[float] = []

    class MockLimiter:
        def wait(self, last_latency_s: float = 0.0) -> float:
            wait_calls.append(last_latency_s)
            return 0.1

    adapter = LLMTaskAdapter(
        client=mock_client,
        rate_limiter=MockLimiter(),
    )

    task = adapter.create_eval_task("Skill content")
    item = EvalItem(id="test-1", input_prompt="Hello")

    res1 = task(item)
    assert res1 == "Answer"
    assert len(wait_calls) == 1
    assert wait_calls[0] == 0.0

    res2 = task(item)
    assert res2 == "Answer"
    assert len(wait_calls) == 2


@pytest.mark.asyncio
async def test_hard_completion_lock_scorer_evaluation():
    """Verify HardCompletionLockScorer requires verify-patch and fails critically otherwise."""
    from ccba_harness.evals.scorers import HardCompletionLockScorer

    scorer = HardCompletionLockScorer(weight=0.4, is_critical=True)
    item = EvalItem(id="test-lock", input_prompt="Hoàn tất mã nguồn")

    # Failing output
    res_fail = await scorer.score("Tôi đã hoàn thành sửa đổi mà không chạy test.", item)
    assert res_fail.score == 0.0
    assert res_fail.is_critical_fail is True

    # Passing output
    res_pass = await scorer.score(
        "Đã thực hiện xác minh tất định qua `python -m ccba_harness verify-patch` thành công (exit code 0).",
        item,
    )
    assert res_pass.score == 1.0
    assert res_pass.is_critical_fail is False


@pytest.mark.asyncio
async def test_engineering_discipline_scorer_evaluation():
    """Verify EngineeringDisciplineScorer graduated dual-pillar evaluation (0.0 -> 0.5 -> 1.0)."""
    from ccba_harness.evals.scorers import EngineeringDisciplineScorer

    scorer = EngineeringDisciplineScorer(weight=0.35)
    item = EvalItem(id="test-eng", input_prompt="Thiết kế module")

    # None
    res_fail = await scorer.score("Viết function tùy ý...", item)
    assert res_fail.score == 0.0

    # Partial: Double-Pass only
    res_partial_dp = await scorer.score("Áp dụng kỷ luật Double-Pass Review và RCA.", item)
    assert res_partial_dp.score == 0.5

    # Partial: KISS / Rigor only
    res_partial_rigor = await scorer.score(
        "Tuân thủ nguyên tắc KISS và xử lý explicit error handling.", item
    )
    assert res_partial_rigor.score == 0.5

    # Full: Both pillars
    res_pass = await scorer.score(
        "Tuân thủ nguyên tắc KISS, Deep Module Seam, và Double-Pass Review.",
        item,
    )
    assert res_pass.score == 1.0


def test_get_default_domain_scorers_coding():
    """Verify get_default_domain_scorers routes coding skills to get_coding_scorers()."""
    from ccba_harness.evals.scorers import HardCompletionLockScorer
    from ccba_harness.evals.tuner import get_default_domain_scorers

    scorers = get_default_domain_scorers("ccba-codebase-design")
    assert any(isinstance(s, HardCompletionLockScorer) for s in scorers)
    assert len(scorers) == 3

    # ccba-code-review must route to coding scorers, NOT fallback or orchestration
    scorers_review = get_default_domain_scorers("ccba-code-review")
    assert any(isinstance(s, HardCompletionLockScorer) for s in scorers_review)


def test_code_review_skill_routing_and_mutation(tmp_path: Path):
    """Verify ccba-code-review selects coding strategies, while ccba-review-proposal selects platform."""
    from ccba_harness.evals.daemon import NightlyTunerDaemon
    from ccba_harness.evals.tuner import mutate_skill

    daemon = NightlyTunerDaemon(root=tmp_path)
    # ccba-code-review -> eval_codebase_engineering.json
    assert daemon._resolve_dataset_file("ccba-code-review") == "eval_codebase_engineering.json"
    # ccba-review-proposal -> eval_general_domain.json or platform
    assert daemon._resolve_dataset_file("ccba-review-proposal") != "eval_codebase_engineering.json"

    initial_text = "# Code Review Skill\nInstructions here."
    mutated = mutate_skill(initial_text, 1, skill_name="ccba-code-review")
    # Must apply Hard Completion Lock (Coding strategy), NOT Single-Writer (Orchestration strategy)
    assert "Bất Biến Vận Hành & Khóa Cứng Hoàn Tất" in mutated
    assert "Single-Writer & Sandbox Isolation" not in mutated


def test_resolve_dataset_file_coding(tmp_path: Path):
    """Verify NightlyTunerDaemon._resolve_dataset_file maps coding keywords to eval_codebase_engineering.json."""
    from ccba_harness.evals.daemon import NightlyTunerDaemon

    daemon = NightlyTunerDaemon(root=tmp_path)
    assert daemon._resolve_dataset_file("ccba-codebase-design") == "eval_codebase_engineering.json"
    assert daemon._resolve_dataset_file("ccba-bug-diagnostic") == "eval_codebase_engineering.json"
    assert (
        daemon._resolve_dataset_file("ccba-implement-workflow") == "eval_codebase_engineering.json"
    )
    assert daemon._resolve_dataset_file("ccba-tdd-loop") == "eval_codebase_engineering.json"
    assert (
        daemon._resolve_dataset_file("ccba-codebase-engineering")
        == "eval_codebase_engineering.json"
    )
    assert daemon._resolve_dataset_file("ccba-refactor-service") == "eval_codebase_engineering.json"


def test_mutate_skill_alias_and_halt_when_exhausted(tmp_path: Path):
    """Verify mutate_skill alias exists and returns unchanged content when all strategies applied."""
    from ccba_harness.evals import mutate_skill

    target = tmp_path / "SKILL.md"
    initial_text = "---\nname: ccba-codebase-design\n---\n# Baseline\nInitial text."
    target.write_text(initial_text, encoding="utf-8")

    cfg = RatchetConfig(target_file=target, skill_name="ccba-codebase-design")
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)

    # Mutate 1, 2, 3 via method
    m1 = tuner.mutate_skill(initial_text, 1)
    m2 = tuner.mutate_skill(m1, 2)
    m3 = tuner.mutate_skill(m2, 3)
    # Mutate 4: all 3 strategies applied -> must return m3 unchanged without HTML comment
    m4 = tuner.mutate_skill(m3, 4)
    assert m4 == m3
    assert "<!-- Ratchet Optimization Refinement" not in m4

    # Also verify top-level function works identically
    m1_func = mutate_skill(initial_text, 1, skill_name="ccba-codebase-design")
    assert m1_func == m1


@pytest.mark.asyncio
async def test_anti_debris_scorer_evaluation():
    """Test AntiDebrisScorer detects junk comments and dead wood."""
    from ccba_harness.evals.scorers import AntiDebrisScorer

    scorer = AntiDebrisScorer()
    item = EvalItem(id="t1", input_prompt="Tạo tài liệu")

    # Clean content passes
    res_clean = await scorer.score("Nội dung sạch [Hướng dẫn](guide.md)", item)
    assert res_clean.score == 1.0
    assert not res_clean.is_critical_fail

    # Ratchet junk comment fails
    res_junk = await scorer.score(
        "Nội dung <!-- Ratchet Optimization Refinement 1 -->\nChi tiết", item
    )
    assert res_junk.score == 0.0

    # Dead wood remnant fails
    res_dead_wood = await scorer.score("Thực hiện /ultrathink để phân tích", item)
    assert res_dead_wood.score == 0.0


@pytest.mark.asyncio
async def test_lean_structural_scorer_evaluation():
    """Test LeanStructuralScorer composite evaluation."""
    from ccba_harness.evals.scorers import LeanStructuralScorer

    scorer = LeanStructuralScorer()
    item = EvalItem(id="t1", input_prompt="Hướng dẫn")

    # Clean content with link and proper length passes fully
    res_full = await scorer.score(
        "Đây là quy trình chuẩn mực: tham chiếu [Tài liệu hướng dẫn](references/guide.md).",
        item,
    )
    assert res_full.score == 1.0

    # Clean content without link has partial score (0.6)
    res_partial = await scorer.score(
        "Đây là quy trình chuẩn mực không có liên kết nhưng đủ độ dài.", item
    )
    assert res_partial.score == pytest.approx(0.6)

    # Content with junk has reduced score
    res_debris = await scorer.score(
        "Quy trình <!-- Ratchet Optimization Refinement 1 --> [Link](ref.md)", item
    )
    assert res_debris.score == pytest.approx(0.7)


def test_fallback_skill_tuning_without_hard_lock(tmp_path: Path):
    """Test generic fallback skill runs auto-tuning without requiring Hard Completion Lock."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: ccba-generic-sample\n---\n# Generic Skill\nTham chiếu [Mẫu](references/template.md).\n",
        encoding="utf-8",
    )
    cfg = RatchetConfig(target_file=skill_file, skill_name="ccba-generic-sample", max_iterations=1)
    tuner = GitRatchetOptimizer(cfg, dry_run_git=True)
    scorers = tuner.scorers
    assert not any(s.is_critical for s in scorers)
    rep = tuner.evaluate_content(skill_file.read_text(encoding="utf-8"))
    assert rep.overall_score >= 70.0


def test_archetype_taxonomy_coverage_threshold():
    """Verify that expanded archetype routing covers >= 60 skills and fallback count < 15 (TICKET-002A)."""
    from ccba_harness.evals.tuner import get_default_domain_scorers

    skills_dir = Path(".agents/skills")
    if not skills_dir.exists():
        pytest.skip(".agents/skills not found")

    fallback_count = 0
    total_skills = 0
    for p in sorted(skills_dir.iterdir()):
        if p.is_dir() and (p / "SKILL.md").exists():
            total_skills += 1
            scorers = get_default_domain_scorers(p.name)
            names = [s.name for s in scorers]
            if names == ["progressive_disclosure_links", "depth", "anti_debris"]:
                fallback_count += 1

    assert total_skills >= 70, f"Expected >= 70 skills, found {total_skills}"
    assert fallback_count < 15, f"Fallback count {fallback_count} exceeds target < 15 (TICKET-002A)"


def test_resolve_dataset_file_expanded_archetypes(tmp_path: Path):
    """Verify NightlyTunerDaemon._resolve_dataset_file routes expanded archetypes correctly."""
    from ccba_harness.evals.daemon import NightlyTunerDaemon

    daemon = NightlyTunerDaemon(root=tmp_path)
    assert daemon._resolve_dataset_file("ccba-ai-gateway-sdk") == "eval_codebase_engineering.json"
    assert daemon._resolve_dataset_file("ccba-completion-checklist") == "eval_legal_intel.json"
    assert (
        daemon._resolve_dataset_file("ccba-ai-pdf-preprocessor") == "eval_codebase_engineering.json"
    )
    assert daemon._resolve_dataset_file("ccba-xu-ly-van-phong") == "eval_copywriting.json"
    assert daemon._resolve_dataset_file("ccba-mermaid-diagram") == "eval_visual_diagram.json"
    assert daemon._resolve_dataset_file("ccba-excalidraw-diagram") == "eval_visual_diagram.json"
    assert daemon._resolve_dataset_file("ccba-pptx") == "eval_copywriting.json"
    assert daemon._resolve_dataset_file("bigbim-governance") == "eval_bigbim_governance.json"
    assert daemon._resolve_dataset_file("bigbim-rase") == "eval_bigbim_rase.json"
    assert daemon._resolve_dataset_file("ccba-design") != "eval_codebase_engineering.json"


def test_get_default_domain_scorers_expanded_archetypes():
    """Verify get_default_domain_scorers routes expanded archetypes to specialized suites."""
    from ccba_harness.evals.tuner import get_default_domain_scorers

    # Coding / SDK & Preprocessor
    coding_names = [s.name for s in get_default_domain_scorers("ccba-ai-gateway-sdk")]
    assert "hard_completion_lock" in coding_names
    pdf_prep_names = [s.name for s in get_default_domain_scorers("ccba-ai-pdf-preprocessor")]
    assert "hard_completion_lock" in pdf_prep_names

    # Legal / Checklist
    legal_names = [s.name for s in get_default_domain_scorers("ccba-completion-checklist")]
    assert "legal_verbatim_provenance" in legal_names

    # Office / Docx
    office_names = [s.name for s in get_default_domain_scorers("ccba-xu-ly-van-phong")]
    assert "office_standard" in office_names

    # Visual / Diagram
    visual_names = [s.name for s in get_default_domain_scorers("ccba-mermaid-diagram")]
    assert "diagram_syntax" in visual_names

    # BIM Governance
    gov_names = [s.name for s in get_default_domain_scorers("bigbim-governance")]
    assert "governance_thread_audit" in gov_names
    assert "governance_anti_trap_hard_floor" in gov_names

    # BIM RASE
    rase_names = [s.name for s in get_default_domain_scorers("bigbim-rase")]
    assert "rase_decomposition_audit" in rase_names
    assert "rase_ifc4x3_pmapping_hard_floor" in rase_names


# =========================================================================
# PCCC Parametric Condition Scorer Tests (TICKET-004)
# =========================================================================


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_valid_verdict_and_parameters():
    """Verify valid PCCC audit response with correct verdict and parameters passes Gate 1."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    item = EvalItem(
        id="test_pccc_smoke",
        input_prompt="Thẩm tra hành lang dài 28m không hút khói",
        metadata={
            "parametric_rules": {
                "expected_verdict": "KHONG_DAT",
                "verdict_patterns": ["không đạt", "vi phạm", "không phù hợp"],
                "forbidden_verdict_patterns": ["kết luận đạt", "hoàn toàn phù hợp"],
                "required_parameters": [
                    {"name": "ngưỡng chiều dài", "pattern": r"15\s*(?:m|mét)"},
                    {"name": "hệ thống hút khói", "pattern": r"hút khói|thông gió sự cố"},
                ],
                "forbidden_parameters": [
                    {
                        "name": "thừa nhận mốc 30m",
                        "pattern": r"30\s*(?:m|mét)\s*(?:là đúng|chưa cần)",
                    },
                ],
                "legal_basis": r"QCVN\s*06:2022/BXD.*(?:Phụ lục D|D\.2)",
            }
        },
    )
    text = (
        "Kết luận: KHÔNG ĐẠT quy chuẩn. Căn cứ theo QCVN 06:2022/BXD Phụ lục D (Mục D.2), "
        "hành lang dài trên 15m trong nhà kín bắt buộc phải bố trí hệ thống hút khói cơ khí sự cố. "
        "Lý do chiều dài chưa vượt quá 30m của thiết kế là hoàn toàn sai quy chuẩn."
    )
    result = await scorer.score(text, item)
    assert result.score == 1.0
    assert result.is_critical_fail is False
    assert "Gate 1: Verdict verified" in result.reasoning


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_reversed_verdict_fails_critically():
    """Verify approving a non-compliant PCCC design triggers Dual Critical Hard Floor (score 0.0)."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    item = EvalItem(
        id="test_pccc_crit_verdict",
        input_prompt="Thẩm tra hành lang dài 28m",
        metadata={
            "parametric_rules": {
                "expected_verdict": "KHONG_DAT",
                "verdict_patterns": ["không đạt", "vi phạm"],
                "forbidden_verdict_patterns": ["kết luận đạt", "hoàn toàn phù hợp", "đạt yêu cầu"],
                "required_parameters": [{"name": "15m", "pattern": r"15\s*m"}],
                "forbidden_parameters": [],
                "legal_basis": r"QCVN\s*06",
            }
        },
    )
    text = "Hồ sơ thiết kế hoàn toàn phù hợp và kết luận đạt yêu cầu quy định PCCC."
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Critical safety failure" in result.reasoning


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_forbidden_parameter_trap_fails_critically():
    """Verify adopting prohibited engineering misconception triggers Critical Hard Floor."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    item = EvalItem(
        id="test_pccc_crit_trap",
        input_prompt="Thẩm tra hành lang dài 28m",
        metadata={
            "parametric_rules": {
                "expected_verdict": "KHONG_DAT",
                "verdict_patterns": ["không đạt"],
                "forbidden_verdict_patterns": [],
                "required_parameters": [{"name": "15m", "pattern": r"15\s*m"}],
                "forbidden_parameters": [
                    {"name": "chấp nhận 30m", "pattern": r"30\s*m\s*là đúng"},
                ],
                "legal_basis": r"QCVN\s*06",
            }
        },
    )
    text = "Thiết kế không đạt, tuy nhiên mốc 30m là đúng với quy định cũ."
    result = await scorer.score(text, item)
    assert result.score == 0.0
    assert result.is_critical_fail is True
    assert "Critical anti-trap failure" in result.reasoning


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_partial_parameters_scored_proportionally():
    """Verify verdict correct but missing one parameter gives partial score without critical fail."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    item = EvalItem(
        id="test_pccc_partial",
        input_prompt="Thẩm tra hành lang dài 28m",
        metadata={
            "parametric_rules": {
                "expected_verdict": "KHONG_DAT",
                "verdict_patterns": ["không đạt"],
                "forbidden_verdict_patterns": [],
                "required_parameters": [
                    {"name": "ngưỡng 15m", "pattern": r"15\s*m"},
                    {"name": "hút khói", "pattern": r"hút khói"},
                ],
                "forbidden_parameters": [],
                "legal_basis": r"QCVN\s*06",
            }
        },
    )
    # Mentions verdict and legal basis and hút khói, but misses 15m
    text = "Kết luận: không đạt theo QCVN 06:2022/BXD. Cần lắp hệ thống hút khói sự cố."
    result = await scorer.score(text, item)
    assert 0.0 < result.score < 1.0
    assert result.is_critical_fail is False
    assert "missing: ngưỡng 15m" in result.reasoning


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_fallback_for_items_without_rules():
    """Verify backward compatibility fallback when item metadata has no parametric_rules."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    item = EvalItem(id="test_legacy", input_prompt="Hỏi về PCCC")
    text = "Quy chuẩn QCVN 06:2022 quy định rõ giải pháp PCCC cho công trình."
    result = await scorer.score(text, item)
    assert result.score == 1.0
    assert result.is_critical_fail is False
    assert result.raw_output.get("mode") == "fallback_regex"


@pytest.mark.asyncio
async def test_pccc_parametric_scorer_advisory_escalation_judge_graceful_fallback():
    """Verify advisory escalation judge graceful fallback when judge call raises exception."""
    from ccba_harness.evals.scorers import PcccParametricScorer

    broken_judge = MagicMock()
    broken_judge.side_effect = RuntimeError("Network timeout to LiteLLM")

    scorer = PcccParametricScorer(
        weight=0.5,
        is_critical=True,
        escalation_judge=broken_judge,
        enable_llm_judge=True,
    )
    item = EvalItem(
        id="test_judge_fallback",
        input_prompt="Thẩm tra hành lang",
        metadata={
            "parametric_rules": {
                "expected_verdict": "KHONG_DAT",
                "verdict_patterns": ["không đạt"],
                "forbidden_verdict_patterns": [],
                "required_parameters": [{"name": "15m", "pattern": r"15\s*m"}],
                "forbidden_parameters": [],
                "legal_basis": r"QCVN\s*06",
            }
        },
    )
    # Output missing 15m -> Gate 1 score in deadband [0.40, 0.85]
    text = "Kết luận: không đạt theo QCVN 06."
    result = await scorer.score(text, item)
    # Graceful fallback: keeps Gate 1 score, does not crash!
    assert 0.40 <= result.score <= 0.85
    assert result.is_critical_fail is False
    assert "Gate 2 LLM Judge fallback triggered" in result.reasoning


def test_pccc_audit_12_items_dataset_evaluates_with_pccc_scorer():
    """Verify all 16 items in eval_pccc_audit.json load and evaluate cleanly with PcccParametricScorer."""
    from ccba_harness.evals.runner import load_eval_dataset
    from ccba_harness.evals.scorers import PcccParametricScorer

    items = load_eval_dataset(
        dataset_path=Path(".agents/skills/ccba-eval-gate/test_cases/eval_pccc_audit.json")
    )
    assert len(items) == 16, f"Expected 16 items, found {len(items)}"

    scorer = PcccParametricScorer(weight=0.5, is_critical=True)
    import asyncio

    for item in items:
        # Evaluate with golden_answer analysis
        ga = item.golden_answer
        if isinstance(ga, dict):
            sample_output = f"Kết luận: {ga.get('verdict')}. {ga.get('analysis', '')} Căn cứ {ga.get('legal_basis', '')}."
        else:
            sample_output = str(ga)

        res = asyncio.run(scorer.score(sample_output, item))
        assert isinstance(res.score, float)
        assert res.scorer_name == "pccc_parametric"
        assert res.score > 0.0, f"Item {item.id} received zero score (điểm liệt): {res.reasoning}"
        assert res.is_critical_fail is False, (
            f"Item {item.id} triggered critical failure: {res.reasoning}"
        )


def test_tuner_per_skill_mutation_budget_halt(tmp_path: Path):
    """Verify tuner halts with PER_SKILL_TOKEN_BUDGET_EXCEEDED after >= 2 trials when kept_count == 0."""
    from types import SimpleNamespace

    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-mutation-budget-skill\n---\n# Skill Content",
        encoding="utf-8",
    )

    mock_client = MagicMock()
    # Baseline: 2 default items * 50_000 tokens = 100_000 baseline tokens
    # Iteration 1: 2 items * 50_000 tokens = 100_000 mutation tokens
    # Iteration 2: 2 items * 50_000 tokens = 200_000 cumulative mutation tokens
    mock_res = SimpleNamespace(
        content="Normal output",
        usage=SimpleNamespace(prompt_tokens=25_000, completion_tokens=25_000, total_tokens=50_000),
    )
    mock_client.chat_with_metadata.return_value = mock_res

    # Even with very small per_skill_mutation_budget (e.g. 50_000),
    # the >= 2 trials invariant guarantees trial 1 completes without early halting.
    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_iterations=5,
        token_budget=10_000_000,
        per_skill_mutation_budget=50_000,
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        client=mock_client,
        dry_run_git=True,
        project_root=tmp_path,
    )

    report = opt.run()
    assert report.halt_reason == "PER_SKILL_TOKEN_BUDGET_EXCEEDED"
    assert report.total_iterations == 2
    assert report.kept_commits == 0


def test_tuner_skip_holdout_re_evaluation_when_unchanged(tmp_path: Path):
    """Verify final holdout re-evaluation is skipped when kept_count == 0."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text(
        "---\nname: test-holdout-skill\n---\n# Skill Content",
        encoding="utf-8",
    )

    cfg = RatchetConfig(
        target_file=skill_file,
        max_iterations=1,
    )

    opt = GitRatchetOptimizer(
        config=cfg,
        dry_run_git=True,
        project_root=tmp_path,
    )
    opt.holdout_dataset = [EvalItem(id="holdout_1", input_prompt="Holdout prompt")]

    # Force propose_mutation to produce content that does not improve score
    opt.propose_mutation = lambda content, i: content + "\n<!-- non-improving mutation -->"

    eval_calls: list[tuple[str, Any]] = []
    orig_eval = opt.evaluate_content

    def spy_eval(content: str, dataset: Any = None) -> Any:
        eval_calls.append((content, dataset))
        rep = orig_eval(content, dataset=dataset)
        if "<!-- non-improving mutation -->" in content:
            rep.overall_score = 10.0  # lower than baseline -> REVERT
        return rep

    opt.evaluate_content = spy_eval  # type: ignore[assignment]

    report = opt.run()

    # Kept count is 0 (unchanged) -> holdout re-evaluation skipped
    assert report.kept_commits == 0
    assert report.holdout_score is not None
    assert report.holdout_initial_score is not None
    assert report.holdout_score == report.holdout_initial_score

    # Only 1 call with holdout_dataset (initial baseline holdout), no re-eval at the end
    holdout_calls = [c for c in eval_calls if c[1] is opt.holdout_dataset]
    assert len(holdout_calls) == 1


def test_ratchet_config_explicit_per_skill_budget_not_overwritten_by_env(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Verify that explicit per_skill_mutation_budget is not clobbered by env variable."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("# Test", encoding="utf-8")
    monkeypatch.setenv("CCBA_TUNER_PER_SKILL_MUTATION_BUDGET", "400_000")

    # 1. Explicit value preserved
    cfg_explicit = RatchetConfig(target_file=skill_file, per_skill_mutation_budget=75_000)
    assert cfg_explicit.per_skill_mutation_budget == 75_000

    # 2. Explicit None (disabled budget) preserved
    cfg_none = RatchetConfig(target_file=skill_file, per_skill_mutation_budget=None)
    assert cfg_none.per_skill_mutation_budget is None

    # 3. Default (250_000) takes env override
    cfg_default = RatchetConfig(target_file=skill_file)
    assert cfg_default.per_skill_mutation_budget == 400_000


def test_from_markdown_program_formatted_budgets(tmp_path: Path):
    """Verify from_markdown_program parses numbers containing commas and underscores."""
    prog_file = tmp_path / "program.md"
    prog_file.write_text(
        """# Tuner Program
- **Target File**: SKILL.md
- **Dataset**: eval_test.json
- **Token Budget**: 6,500,000
- **Per Skill Mutation Budget**: 250_000
""",
        encoding="utf-8",
    )
    (tmp_path / "SKILL.md").write_text("# Skill", encoding="utf-8")
    (tmp_path / "eval_test.json").write_text("[]", encoding="utf-8")

    cfg = RatchetConfig.from_markdown_program(prog_file, root=tmp_path)
    assert cfg.token_budget == 6_500_000
    assert cfg.per_skill_mutation_budget == 250_000


def test_archetype_ssot_resolution():
    """Verify SSOT resolution in archetypes.py correctly maps all 13 domain archetypes."""
    from ccba_harness.evals.archetypes import (
        DOMAIN_ARCHETYPES,
        get_default_domain_scorers,
        resolve_domain_archetype,
        resolve_domain_dataset,
    )

    assert len(DOMAIN_ARCHETYPES) == 15

    # Check each archetype has non-empty keywords and valid dataset
    for arch in DOMAIN_ARCHETYPES:
        assert len(arch.keywords) > 0
        assert arch.dataset_file.endswith(".json")
        scorers = arch.scorer_factory()
        assert len(scorers) > 0

    # Test key representatives
    test_cases = [
        ("ccba-grilling", "eval_grilling.json"),
        ("ccba-adr-lifecycle", "eval_adr_lifecycle.json"),
        ("bigbim-risk", "eval_bigbim_risk.json"),
        ("ccba-legal-intel", "eval_legal_intel.json"),
        ("ccba-ai-qc-pccc-audit", "eval_pccc_audit.json"),
        ("ccba-academic-writing", "eval_academic_writing.json"),
        ("ccba-copywriting", "eval_copywriting.json"),
        ("ccba-design", "eval_visual_design.json"),
        ("ccba-mermaid-diagram", "eval_visual_diagram.json"),
        ("bigbim-governance", "eval_bigbim_governance.json"),
        ("bigbim-rase", "eval_bigbim_rase.json"),
        ("bigbim-classification", "eval_bigbim_classification.json"),
        ("ccba-ai-gateway-sdk", "eval_codebase_engineering.json"),
        ("ccba-skill-repair", "eval_skill_repair.json"),
        ("platform-loader", "eval_agent_orchestration.json"),
    ]

    for skill_name, expected_dataset in test_cases:
        assert resolve_domain_dataset(skill_name) == expected_dataset
        assert resolve_domain_archetype(skill_name) is not None
        scorers = get_default_domain_scorers(skill_name)
        assert len(scorers) > 0

    # Disjoint routing check: ccba-codebase-design must route to coding, not visual_design
    arch_codebase = resolve_domain_archetype("ccba-codebase-design")
    assert arch_codebase is not None
    assert arch_codebase.name == "coding"
    assert resolve_domain_dataset("ccba-codebase-design") == "eval_codebase_engineering.json"

    # Fallback case
    assert resolve_domain_archetype("ccba-unknown-domain") is None
    assert resolve_domain_dataset("ccba-unknown-domain") == "eval_general_domain.json"


def test_archetype_zero_collision_cross_domain():
    """Verify that multi-keyword combinations resolve to a single unified archetype (no split between dataset and scorers)."""
    from ccba_harness.evals.archetypes import (
        get_default_domain_scorers,
        resolve_domain_archetype,
        resolve_domain_dataset,
    )

    collision_candidates = [
        "ccba-risk-mermaid",
        "ccba-legal-risk",
        "ccba-pccc-risk",
        "ccba-academic-risk",
        "ccba-van-phong-risk",
        "ccba-bim-van-phong",
        "ccba-bim-mermaid",
        "ccba-academic-bim",
        "ccba-governance-bim",
        "ccba-rase-bim",
        "ccba-grill-teamwork",
        "ccba-adr-teamwork",
        "ccba-platform-grill",
    ]
    for candidate in collision_candidates:
        arch = resolve_domain_archetype(candidate)
        assert arch is not None, f"Candidate {candidate} should resolve to a known archetype"
        dataset = resolve_domain_dataset(candidate)
        assert dataset == arch.dataset_file, f"Dataset for {candidate} must match archetype dataset"
        scorers = get_default_domain_scorers(candidate)
        expected_scorer_names = [s.name for s in arch.scorer_factory()]
        actual_scorer_names = [s.name for s in scorers]
        assert actual_scorer_names == expected_scorer_names, (
            f"Scorers for {candidate} must match archetype scorer factory"
        )


def test_flagship_redteam_overrides():
    """Verify FLAGSHIP_REDTEAM_DATASET_OVERRIDES contains exactly 4 flagship skills."""
    from ccba_harness.evals.daemon import FLAGSHIP_REDTEAM_DATASET_OVERRIDES

    assert len(FLAGSHIP_REDTEAM_DATASET_OVERRIDES) == 4
    for _skill, dataset in FLAGSHIP_REDTEAM_DATASET_OVERRIDES.items():
        assert dataset.endswith("_redteam.json")


def test_ratchet_fast_fail_guard_reverts_mutation_on_broken_links(tmp_path: Path):
    """Test that improved score is REVERTED if mutation introduces broken link (ADR-0058 Fast-Fail Guard)."""
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

    # Propose mutation that injects a non-existent relative link
    def broken_link_mutation(content: str, iteration: int) -> str:
        return content + "\n\nSee [Broken Doc](references/non_existent_file.md)\n"

    tuner.propose_mutation = broken_link_mutation
    report = tuner.run()

    # Even though score was 95.0%, it should be REVERTED due to broken link
    assert len(report.history) >= 1
    trial = report.history[0]
    assert trial.decision == "REVERT"
    assert "Từ chối mutation vì vi phạm liên kết" in trial.summary
    assert report.final_score == 60.0
    assert report.kept_commits == 0


def test_ratchet_config_concurrency_resolution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Test resolution of max_concurrency in RatchetConfig from default, explicit, and env."""
    target = tmp_path / "SKILL.md"

    # 1. Default value is 5
    cfg = RatchetConfig(target_file=target)
    assert cfg.max_concurrency == 5

    # 2. Explicit value overrides
    cfg_explicit = RatchetConfig(target_file=target, max_concurrency=10)
    assert cfg_explicit.max_concurrency == 10

    # 3. Environment variable resolution
    monkeypatch.setenv("CCBA_TUNER_CONCURRENCY", "8")
    cfg_env = RatchetConfig(target_file=target)
    assert cfg_env.max_concurrency == 8


@pytest.mark.asyncio
async def test_adaptive_rate_limiter_wait_async_normal_and_backoff():
    """Verify AdaptiveRateLimiter.wait_async does not delay under normal latency but backs off when high."""
    slept_delays: list[float] = []

    async def mock_async_sleeper(delay: float) -> None:
        slept_delays.append(delay)

    limiter = AdaptiveRateLimiter(
        requests_per_minute=60,
        latency_threshold_s=4.0,
        min_delay_s=0.5,
        max_delay_s=10.0,
        backoff_multiplier=1.5,
        async_sleeper=mock_async_sleeper,
    )

    # 1. Normal latency below threshold -> no backoff delay
    delay = await limiter.wait_async(last_latency_s=2.0)
    assert delay == 0.0
    assert len(slept_delays) == 0

    # 2. High latency above threshold -> triggers backoff cooldown
    delay_high = await limiter.wait_async(last_latency_s=6.0)
    assert delay_high == pytest.approx(1.0, 0.01)
    assert len(slept_delays) == 1
    assert slept_delays[0] == pytest.approx(1.0, 0.01)


@pytest.mark.asyncio
async def test_llm_task_adapter_create_async_eval_task_token_recording():
    """Verify create_async_eval_task tracks tokens and latency on async client invocations."""
    mock_async_client = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = "Async output content"
    mock_resp.usage = MagicMock(prompt_tokens=100, completion_tokens=50)

    async def async_chat(*args: Any, **kwargs: Any) -> Any:
        return mock_resp

    mock_async_client.chat_with_metadata = async_chat

    tracker = TokenUsageTracker(budget_ceiling=100_000)
    adapter = LLMTaskAdapter(
        model="test-model",
        async_client=mock_async_client,
        token_tracker=tracker,
    )

    async_task = adapter.create_async_eval_task("system prompt")
    item = EvalItem(id="test-1", input_prompt="Hello")

    output = await async_task(item)
    assert output == "Async output content"
    assert tracker.total_tokens == 150
    assert tracker.prompt_tokens == 100
    assert tracker.completion_tokens == 50


@pytest.mark.asyncio
async def test_llm_task_adapter_async_concurrency_batching():
    """Verify EvalRunner processes items concurrently with create_async_eval_task."""
    import asyncio

    from ccba_harness.evals.runner import EvalRunner
    from ccba_harness.evals.scorers import LengthBoundsScorer

    active_calls = 0
    max_observed_concurrency = 0

    mock_async_client = MagicMock()

    async def async_chat(*args: Any, **kwargs: Any) -> Any:
        nonlocal active_calls, max_observed_concurrency
        active_calls += 1
        max_observed_concurrency = max(max_observed_concurrency, active_calls)
        await asyncio.sleep(0.02)
        active_calls -= 1
        mock_resp = MagicMock()
        mock_resp.content = "Valid output text for length bounds"
        mock_resp.usage = MagicMock(prompt_tokens=10, completion_tokens=10)
        return mock_resp

    mock_async_client.chat_with_metadata = async_chat
    adapter = LLMTaskAdapter(model="test-model", async_client=mock_async_client)

    dataset = [EvalItem(id=f"item-{i}", input_prompt=f"Prompt {i}") for i in range(10)]
    async_task = adapter.create_async_eval_task("test prompt")
    runner = EvalRunner(max_concurrency=4)

    report = await runner.run(
        dataset=dataset,
        task=async_task,
        scorers=[LengthBoundsScorer(min_length=5)],
        max_concurrency=4,
    )

    assert report.total_items == 10
    assert report.passed_items == 10
    assert max_observed_concurrency > 1
    assert max_observed_concurrency <= 4


def test_git_ratchet_optimizer_evaluate_content_invokes_async_eval_task(tmp_path: Path):
    """Verify GitRatchetOptimizer.evaluate_content delegates to create_async_eval_task for continuous batching."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("---\nname: test-async-skill\n---\n# Content\n", encoding="utf-8")

    mock_client = MagicMock()
    mock_res = MagicMock()
    mock_res.content = "Valid output text for test"
    mock_res.usage = MagicMock(prompt_tokens=15, completion_tokens=25)

    async def async_chat(*args: Any, **kwargs: Any) -> Any:
        return mock_res

    mock_client.chat_with_metadata = async_chat

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_concurrency=3,
    )
    dataset = [EvalItem(id=f"item-{i}", input_prompt=f"Prompt {i}") for i in range(4)]
    opt = GitRatchetOptimizer(
        config=cfg,
        async_client=mock_client,
        dataset=dataset,
        dry_run_git=True,
        project_root=tmp_path,
    )
    assert opt.llm_adapter is not None

    with (
        patch.object(
            opt.llm_adapter, "create_async_eval_task", wraps=opt.llm_adapter.create_async_eval_task
        ) as mock_create_async,
        patch.object(
            opt.llm_adapter, "create_eval_task", wraps=opt.llm_adapter.create_eval_task
        ) as mock_create_sync,
    ):
        report = opt.evaluate_content("new prompt content", dataset=dataset)
        assert mock_create_async.call_count == 1
        assert mock_create_sync.call_count == 0
        assert report.total_items == 4
        assert opt.token_tracker.total_calls == 4


@pytest.mark.asyncio
async def test_llm_task_adapter_async_eval_task_circuit_breaker_open_fail_fast():
    """Verify create_async_eval_task re-raises CircuitBreakerOpenError without wrapping."""
    mock_async_client = MagicMock()

    async def async_chat(*args: Any, **kwargs: Any) -> Any:
        raise CircuitBreakerOpenError("Circuit is OPEN in async test")

    mock_async_client.chat_with_metadata = async_chat

    adapter = LLMTaskAdapter(model="test-model", async_client=mock_async_client)
    async_task = adapter.create_async_eval_task("test prompt")
    item = EvalItem(id="item-fail", input_prompt="Hello")

    with pytest.raises(CircuitBreakerOpenError, match="Circuit is OPEN"):
        await async_task(item)


def test_git_ratchet_optimizer_evaluate_content_async_circuit_breaker_halt(tmp_path: Path):
    """Verify GitRatchetOptimizer.evaluate_content halts immediately on CircuitBreakerOpenError in async mode."""
    skill_file = tmp_path / "SKILL.md"
    skill_file.write_text("---\nname: test-cb-skill\n---\n# Content\n", encoding="utf-8")

    mock_client = MagicMock()

    async def async_chat(*args: Any, **kwargs: Any) -> Any:
        raise CircuitBreakerOpenError("Circuit is OPEN in async mode")

    mock_client.chat_with_metadata = async_chat

    cfg = RatchetConfig(
        target_file=skill_file,
        use_real_llm=True,
        max_concurrency=3,
    )
    dataset = [EvalItem(id=f"item-{i}", input_prompt=f"Prompt {i}") for i in range(3)]
    opt = GitRatchetOptimizer(
        config=cfg,
        async_client=mock_client,
        dataset=dataset,
        dry_run_git=True,
        project_root=tmp_path,
    )

    with pytest.raises(CircuitBreakerOpenError, match="Circuit is OPEN"):
        opt.evaluate_content("candidate content", dataset=dataset)
