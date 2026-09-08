"""test_cli.py - Unit and Integration Tests for ccba-harness CLI.

Tests:
1. Main CLI dispatching: help, validate-skill, evaluate-gpi, eval.
2. Subcommand `eval`:
   - Argument parsing (--skill, --trials, --auto-tune, --dataset, --json, --threshold).
   - Dataset loading from default .agents/skills/ccba-eval-gate/test_cases/.
   - Custom dataset execution with pass and fail cases.
   - Error handling on non-existent dataset paths.
   - Trials aggregation and auto-tune metadata recording.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ccba_harness.cli import main, run_eval_cli
from ccba_harness.evals.models import EvalItem
from ccba_harness.evals.runner import (
    load_eval_dataset,
)

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_main_eval_help_returns_zero(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that `ccba-harness eval --help` displays usage and exits with 0."""
    with pytest.raises(SystemExit) as exc_info:
        main(["eval", "--help"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "usage: ccba-harness eval" in captured.out
    assert "--skill" in captured.out
    assert "--trials" in captured.out
    assert "--auto-tune" in captured.out
    assert "--dataset" in captured.out


def test_eval_cli_nonexistent_dataset(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that pointing to a non-existent dataset returns exit code 1."""
    code = run_eval_cli(["--dataset", "non_existent_dataset_path_12345.json"])
    assert code == 1
    captured = capsys.readouterr()
    assert "ERROR: Dataset path does not exist" in captured.err


def test_eval_cli_custom_dataset_passing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify eval CLI passes when all test cases match golden answer."""
    dataset_file = tmp_path / "test_eval_cases.json"
    dataset_data = [
        {"id": "case_1", "input_prompt": "Prompt 1", "golden_answer": "Expected 1"},
        {"id": "case_2", "input_prompt": "Prompt 2", "golden_answer": "Expected 2"},
    ]
    dataset_file.write_text(json.dumps(dataset_data), encoding="utf-8")

    async def mock_task(item: EvalItem) -> str:
        return str(item.golden_answer)

    with patch("ccba_harness.evals.runner._create_default_eval_task", return_value=mock_task):
        code = run_eval_cli(
            ["--dataset", str(dataset_file), "--trials", "2", "--threshold", "80.0", "--json"]
        )
        assert code == 0
        captured = capsys.readouterr()
        res = json.loads(captured.out)
        assert res["total_items"] == 2
        assert res["passed_items"] == 2
        assert res["failed_items"] == 0
        assert res["overall_score"] == 100.0
        assert res["pass_rate"] == 100.0
        assert res["passed"] is True
        assert res["trials"] == 2


def test_eval_cli_custom_dataset_failing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify eval CLI fails (returns 1) when score is below threshold."""
    dataset_file = tmp_path / "test_eval_cases.json"
    dataset_data = [
        {"id": "case_fail_1", "input_prompt": "Prompt 1", "golden_answer": "Expected 1"},
    ]
    dataset_file.write_text(json.dumps(dataset_data), encoding="utf-8")

    async def mock_failing_task(item: EvalItem) -> str:
        return "Wrong output"

    with patch(
        "ccba_harness.evals.runner._create_default_eval_task", return_value=mock_failing_task
    ):
        code = run_eval_cli(
            ["--dataset", str(dataset_file), "--trials", "1", "--threshold", "85.0"]
        )
        assert code == 1
        captured = capsys.readouterr()
        assert "CCBA SKILL EVALUATION REPORT" in captured.out
        assert "Status           : FAIL" in captured.out
        assert "Failed Cases     : 1" in captured.out


def test_eval_cli_auto_tune_flag_recording(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify --auto-tune flag is recorded in report metadata."""
    dataset_file = tmp_path / "test_eval_cases.json"
    dataset_data = [
        {"id": "case_1", "input_prompt": "Prompt", "golden_answer": "Answer"},
    ]
    dataset_file.write_text(json.dumps(dataset_data), encoding="utf-8")

    async def mock_task(item: EvalItem) -> str:
        return "Answer"

    with patch("ccba_harness.evals.runner._create_default_eval_task", return_value=mock_task):
        code = run_eval_cli(["--dataset", str(dataset_file), "--auto-tune", "--json"])
        assert code == 0
        captured = capsys.readouterr()
        res = json.loads(captured.out)
        assert res["auto_tune"] is True
        assert res["metadata"]["auto_tune"] is True


def test_load_eval_dataset_discovery_from_eval_gate(tmp_path: Path) -> None:
    """Verify load_eval_dataset can locate cases by skill name in ccba-eval-gate/test_cases."""
    # Create fake project root structure
    test_cases_dir = tmp_path / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    test_cases_dir.mkdir(parents=True)
    sample_cases = [
        {
            "id": "copywriting_01",
            "input_prompt": "Draft headline",
            "golden_answer": "Headline A",
            "metadata": {"target_skill": "copywriting"},
        }
    ]
    (test_cases_dir / "eval_copywriting.json").write_text(
        json.dumps(sample_cases), encoding="utf-8"
    )

    items = load_eval_dataset(skill_name="copywriting", project_root=tmp_path)
    assert len(items) == 1
    assert items[0].id == "copywriting_01"
    assert items[0].golden_answer == "Headline A"

    # Also check with ccba- prefix
    items_prefix = load_eval_dataset(skill_name="ccba-copywriting", project_root=tmp_path)
    assert len(items_prefix) == 1
    assert items_prefix[0].id == "copywriting_01"


def test_main_dispatch_eval(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify main() directly routes first argument 'eval' to run_eval_cli."""
    dataset_file = tmp_path / "test_cases.json"
    dataset_file.write_text(
        json.dumps([{"id": "t1", "input_prompt": "A", "golden_answer": "A"}]),
        encoding="utf-8",
    )

    async def mock_task(item: EvalItem) -> str:
        return "A"

    with patch("ccba_harness.evals.runner._create_default_eval_task", return_value=mock_task):
        code = main(["eval", "--dataset", str(dataset_file), "--json"])
        assert code == 0
        captured = capsys.readouterr()
        res = json.loads(captured.out)
        assert res["total_items"] == 1
        assert res["passed"] is True


def test_eval_cli_nonexistent_skill_returns_failure(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that evaluating a nonexistent skill returns 1 and does not pass."""
    code = run_eval_cli(["--skill", "non_existent_skill_xyz", "--json"])
    assert code == 1
    captured = capsys.readouterr()
    res = json.loads(captured.out)
    assert res["passed"] is False
    assert res["total_items"] == 0
    assert "No evaluation test cases found" in captured.err


def test_eval_cli_skill_path_resolution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that passing skill as a directory path or SKILL.md path properly discovers dataset."""
    test_cases_dir = tmp_path / ".agents" / "skills" / "ccba-eval-gate" / "test_cases"
    test_cases_dir.mkdir(parents=True)
    sample_cases = [
        {
            "id": "c1",
            "input_prompt": "Prompt 1",
            "golden_answer": "Answer 1",
            "metadata": {"target_skill": "copywriting"},
        }
    ]
    (test_cases_dir / "eval_copywriting.json").write_text(
        json.dumps(sample_cases), encoding="utf-8"
    )

    skill_dir = tmp_path / ".agents" / "skills" / "ccba-copywriting"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: ccba-copywriting\n---\n# Copywriting", encoding="utf-8"
    )

    async def mock_task(item: EvalItem) -> str:
        return "Answer 1"

    with patch("ccba_harness.evals.runner._create_default_eval_task", return_value=mock_task):
        # 1. Test using directory path
        code_dir = run_eval_cli(["--skill", str(skill_dir), "--root", str(tmp_path), "--json"])
        assert code_dir == 0
        cap_dir = capsys.readouterr()
        res_dir = json.loads(cap_dir.out)
        assert res_dir["total_items"] == 1
        assert res_dir["passed"] is True

        # 2. Test using SKILL.md file path
        code_file = run_eval_cli(
            ["--skill", str(skill_dir / "SKILL.md"), "--root", str(tmp_path), "--json"]
        )
        assert code_file == 0
        cap_file = capsys.readouterr()
        res_file = json.loads(cap_file.out)
        assert res_file["total_items"] == 1
        assert res_file["passed"] is True


def test_eval_cli_empty_dataset_returns_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify that an empty dataset file returns exit code 1."""
    empty_file = tmp_path / "empty_cases.json"
    empty_file.write_text("[]", encoding="utf-8")

    code = run_eval_cli(["--dataset", str(empty_file)])
    assert code == 1
    captured = capsys.readouterr()
    assert "No evaluation test cases found" in captured.err
