import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness import DetachedExecutionEngine

pytestmark = [pytest.mark.fast, pytest.mark.unit]


def test_resolve_scratch_dir_explicit_root(tmp_path):
    scratch = DetachedExecutionEngine.resolve_scratch_dir(root=tmp_path)
    assert scratch == tmp_path / ".md" / "scratch"
    assert scratch.exists()


def test_resolve_scratch_dir_cwd_with_git(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    sub_dir = tmp_path / "sub" / "package"
    sub_dir.mkdir(parents=True)

    with patch.object(Path, "cwd", return_value=sub_dir):
        scratch = DetachedExecutionEngine.resolve_scratch_dir()
        assert scratch == tmp_path / ".md" / "scratch"
        assert scratch.exists()


def test_resolve_scratch_dir_cwd_with_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("[project]\nname='test'\n", encoding="utf-8")
    sub_dir = tmp_path / "deep" / "nested"
    sub_dir.mkdir(parents=True)

    with patch.object(Path, "cwd", return_value=sub_dir):
        scratch = DetachedExecutionEngine.resolve_scratch_dir()
        assert scratch == tmp_path / ".md" / "scratch"
        assert scratch.exists()


def test_resolve_scratch_dir_fallback(tmp_path):
    isolated = tmp_path / "isolated"
    isolated.mkdir()

    # Mock cwd to isolated directory where no parent has .git or pyproject.toml
    with patch.object(Path, "cwd", return_value=isolated):
        scratch = DetachedExecutionEngine.resolve_scratch_dir()
        assert scratch.name == "scratch"
        assert scratch.parent.name == ".md"
        assert scratch.exists()


def test_cleanup_old_logs(tmp_path):
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)

    old_log = scratch_dir / "exec_log_old1234.txt"
    old_log.write_text("old log", encoding="utf-8")
    # Set mtime to 30 hours ago
    thirty_hours_ago = time.time() - 30 * 3600
    os.utime(old_log, (thirty_hours_ago, thirty_hours_ago))

    fresh_log = scratch_dir / "exec_log_fresh56.txt"
    fresh_log.write_text("fresh log", encoding="utf-8")

    DetachedExecutionEngine.cleanup_old_logs(scratch_dir=scratch_dir, max_age_hours=24)

    assert not old_log.exists()
    assert fresh_log.exists()


@patch("subprocess.Popen")
def test_run_detached_success(mock_popen, tmp_path):
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)

    mock_process = MagicMock()
    mock_process.pid = 9999
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    result = DetachedExecutionEngine.run_detached("python -c 'print(1)'", scratch_dir=scratch_dir)

    assert result["status"] == "completed"
    assert result["return_code"] == 0
    assert result["pid"] == 9999
    assert (scratch_dir / f"exec_log_{result['id']}.txt").exists()
    assert (scratch_dir / f"exec_status_{result['id']}.json").exists()


@patch("subprocess.Popen")
def test_run_detached_failure_exit_code(mock_popen, tmp_path):
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)

    mock_process = MagicMock()
    mock_process.pid = 8888
    mock_process.wait.return_value = 2
    mock_popen.return_value = mock_process

    result = DetachedExecutionEngine.run_detached("false", scratch_dir=scratch_dir)

    assert result["status"] == "failed"
    assert result["return_code"] == 2


@patch("subprocess.Popen", side_effect=FileNotFoundError("Executable not found"))
def test_run_detached_exception(mock_popen, tmp_path):
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)

    result = DetachedExecutionEngine.run_detached("nonexistent_binary", scratch_dir=scratch_dir)

    assert result["status"] == "failed"
    assert "Executable not found" in result["error"]


def test_check_status_completed(tmp_path, capsys):
    scratch_dir = tmp_path / ".md" / "scratch"
    scratch_dir.mkdir(parents=True)

    status_file = scratch_dir / "exec_status_abc12345.json"
    status_data = {
        "id": "abc12345",
        "command": "echo test",
        "status": "completed",
        "pid": 111,
        "return_code": 0,
    }
    status_file.write_text(json.dumps(status_data), encoding="utf-8")

    DetachedExecutionEngine.check_status(status_id="abc12345", scratch_dir=scratch_dir)
    captured = capsys.readouterr()

    assert "abc12345" in captured.out
    assert "completed" in captured.out


@patch("subprocess.run")
def test_find_modified_test_files(mock_run, tmp_path):
    test_file_1 = tmp_path / "tests" / "test_a.py"
    test_file_1.parent.mkdir(parents=True)
    test_file_1.write_text("# test", encoding="utf-8")

    test_file_2 = tmp_path / "packages" / "foo" / "tests" / "test_b.py"
    test_file_2.parent.mkdir(parents=True)
    test_file_2.write_text("# test", encoding="utf-8")

    conftest_file = tmp_path / "conftest.py"
    conftest_file.write_text("# conftest", encoding="utf-8")

    git_output = f" M {test_file_1}\n?? {test_file_2}\n M {conftest_file}\n M docs/README.md\n"
    mock_run.return_value = MagicMock(stdout=git_output)

    results = DetachedExecutionEngine.find_modified_test_files()

    assert str(test_file_1) in results
    assert str(test_file_2) in results
    assert str(conftest_file) not in results


def test_run_safe_pytest_dry_run(capsys):
    ret = DetachedExecutionEngine.run_safe_pytest(
        target_file="tests/test_sample.py",
        fast=True,
        dry_run=True,
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert "[SafePytest DRY-RUN]" in captured.out
    assert "tests/test_sample.py" in captured.out
    assert "-m" in captured.out


def test_run_safe_pytest_package_not_found(capsys):
    ret = DetachedExecutionEngine.run_safe_pytest(
        package="nonexistent_pkg_xyz",
    )
    captured = capsys.readouterr()

    assert ret == 1
    assert "Package tests directory not found" in captured.out


@patch.object(DetachedExecutionEngine, "run_detached", return_value={"return_code": 0})
def test_run_safe_pytest_execution(mock_run_detached):
    ret = DetachedExecutionEngine.run_safe_pytest(
        target_file="tests/test_sample.py",
        extra_args=["-v", "--capture=no"],
    )

    assert ret == 0
    mock_run_detached.assert_called_once()
    called_cmd = mock_run_detached.call_args[0][0]
    assert "tests/test_sample.py" in called_cmd
    assert "-v" in called_cmd
    assert "--capture=no" in called_cmd


@patch("subprocess.run")
def test_find_modified_test_files_with_rename(mock_run, tmp_path):
    renamed_test = tmp_path / "tests" / "test_renamed.py"
    renamed_test.parent.mkdir(parents=True, exist_ok=True)
    renamed_test.write_text("# test renamed", encoding="utf-8")

    git_output = f"R  tests/old_test.py -> {renamed_test}\n"
    mock_run.return_value = MagicMock(stdout=git_output)

    results = DetachedExecutionEngine.find_modified_test_files()
    assert str(renamed_test) in results


def test_run_safe_pytest_multiple_target_files(capsys):
    ret = DetachedExecutionEngine.run_safe_pytest(
        target_file=["tests/test_1.py", "tests/test_2.py"],
        dry_run=True,
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert "[SafePytest DRY-RUN]" in captured.out
    assert "tests/test_1.py" in captured.out
    assert "tests/test_2.py" in captured.out


@patch.object(DetachedExecutionEngine, "find_modified_test_files", return_value=[])
def test_run_safe_pytest_clean_tree_exits_zero(mock_find, capsys):
    ret = DetachedExecutionEngine.run_safe_pytest(
        dry_run=True,
        allow_unscoped=False,
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert "Không phát hiện file test nào bị sửa đổi" in captured.out
    assert "Planned execution" not in captured.out


@patch.object(DetachedExecutionEngine, "find_modified_test_files", return_value=[])
def test_run_safe_pytest_extra_args_with_options_not_treated_as_targets(mock_find, capsys):
    ret = DetachedExecutionEngine.run_safe_pytest(
        extra_args=["--tb", "short", "-k", "sample_test_name"],
        dry_run=True,
        allow_unscoped=False,
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert "Không phát hiện file test nào bị sửa đổi" in captured.out
    assert "Planned execution" not in captured.out
