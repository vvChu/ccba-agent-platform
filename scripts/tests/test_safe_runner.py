import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to sys.path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

import safe_runner
from eval.process_safety import DetachedExecutionEngine


@pytest.fixture
def mock_scratch_dir(tmp_path):
    with patch.object(DetachedExecutionEngine, "resolve_scratch_dir", return_value=tmp_path):
        yield tmp_path


def test_resolve_scratch_dir(tmp_path):
    # Test that it creates and returns a Path
    with patch("scripts.safe_runner.Path.cwd", return_value=tmp_path):
        scratch = safe_runner.resolve_scratch_dir()
        assert isinstance(scratch, Path)
        assert scratch.name == "scratch"
        assert scratch.parent.name == ".md"
        assert scratch.exists()


@patch("subprocess.Popen")
def test_run_detached_creates_status_file(mock_popen, mock_scratch_dir):
    mock_process = MagicMock()
    mock_process.pid = 12345
    mock_process.wait.return_value = 0
    mock_popen.return_value = mock_process

    command = "echo hello"
    safe_runner.run_detached(command)

    status_files = list(mock_scratch_dir.glob("exec_status_*.json"))
    assert len(status_files) == 1

    with open(status_files[0], encoding="utf-8") as f:
        status = json.load(f)

    assert status["command"] == command
    assert status["pid"] == 12345
    assert status["status"] in ("running", "completed")

    log_files = list(mock_scratch_dir.glob("exec_log_*.txt"))
    assert len(log_files) == 1
    content = log_files[0].read_text(encoding="utf-8")
    assert "=== Starting Detached Execution ===" in content


@patch("subprocess.Popen")
def test_run_detached_returns_immediately(mock_popen, mock_scratch_dir):
    mock_process = MagicMock()
    mock_process.pid = 54321
    mock_popen.return_value = mock_process

    start_time = time.time()
    safe_runner.run_detached("sleep 10")
    duration = time.time() - start_time

    assert duration < 1.0  # Should be nearly instantaneous
    mock_popen.assert_called_once()
    mock_process.wait.assert_called_once()


@patch("os.kill", side_effect=OSError)
def test_check_status_latest(mock_os_kill, mock_scratch_dir, capsys):
    with patch("sys.platform", "linux"):
        # Create two status files
        file1 = mock_scratch_dir / "exec_status_11111111.json"
        with open(file1, "w", encoding="utf-8") as f:
            json.dump({"id": "11111111", "status": "completed", "pid": 111}, f)

        time.sleep(0.1)  # ensure mtime is different

        file2 = mock_scratch_dir / "exec_status_22222222.json"
        with open(file2, "w", encoding="utf-8") as f:
            json.dump({"id": "22222222", "status": "running", "pid": 222}, f)

        safe_runner.check_status()
        captured = capsys.readouterr()

        assert "22222222" in captured.out
        assert "11111111" not in captured.out


@patch("subprocess.Popen", side_effect=FileNotFoundError("Executable not found"))
def test_run_detached_bad_command(mock_popen, mock_scratch_dir):
    safe_runner.run_detached("nonexistent_command")

    status_files = list(mock_scratch_dir.glob("exec_status_*.json"))
    assert len(status_files) == 1

    with open(status_files[0], encoding="utf-8") as f:
        status = json.load(f)

    assert status["status"] == "failed"
    assert "Executable not found" in status["error"]


def test_run_detached_bad_quotes(mock_scratch_dir):
    # This will raise ValueError from shlex.split
    safe_runner.run_detached('echo "unclosed quote')

    status_files = list(mock_scratch_dir.glob("exec_status_*.json"))
    assert len(status_files) == 1

    with open(status_files[0], encoding="utf-8") as f:
        status = json.load(f)

    assert (
        "Command parsing failed" in status["error"]
        or "No closing quotation" in status["error"]
        or "quotation" in status["error"]
    )


def test_cleanup_old_logs(mock_scratch_dir):
    old_file = mock_scratch_dir / "exec_status_old.json"
    old_file.write_text("{}")

    new_file = mock_scratch_dir / "exec_status_new.json"
    new_file.write_text("{}")

    # modify mtime of old_file to be 25 hours ago
    past_time = time.time() - (25 * 3600)
    os.utime(old_file, (past_time, past_time))

    safe_runner._cleanup_old_logs(mock_scratch_dir, max_age_hours=24)

    assert not old_file.exists()
    assert new_file.exists()
