"""test_run_safe_eval_wrapper.py - Unit test suite cho Safe Execution Sandbox Wrapper."""

import json
import sys
from pathlib import Path

# Thêm thư mục gốc vào sys.path để import scripts
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.eval.run_safe_eval_wrapper import run_safe_wrapper


def test_wrapper_successful_execution(tmp_path: Path) -> None:
    """Kiểm tra kịch bản lệnh chạy thành công: exit code 0, status = PASS."""
    python_exe = sys.executable
    cmd = f'"{python_exe}" -c "print(\'Hello World Success\')"'

    result = run_safe_wrapper(cmd=cmd, timeout_seconds=10, output_dir=tmp_path, cwd=PROJECT_ROOT)

    assert result["status"] == "PASS"
    assert result["error_type"] == "NONE"
    assert result["returncode"] == 0
    assert Path(result["log_file"]).exists()

    # Kiểm tra file diagnostics.json được tạo ra
    diag_file = tmp_path / "diagnostics.json"
    assert diag_file.exists()
    with open(diag_file, encoding="utf-8") as f:
        diag_data = json.load(f)
    assert diag_data["status"] == "PASS"


def test_wrapper_timeout_expired(tmp_path: Path) -> None:
    """Kiểm tra kịch bản lệnh chạy vượt quá thời gian timeout (sleep 5s, timeout 1s): status = TIMEOUT."""
    python_exe = sys.executable
    cmd = f'"{python_exe}" -c "import time; time.sleep(5)"'

    result = run_safe_wrapper(cmd=cmd, timeout_seconds=1, output_dir=tmp_path, cwd=PROJECT_ROOT)

    assert result["status"] == "TIMEOUT"
    assert result["error_type"] == "TIMEOUT"
    assert "vượt quá thời gian" in result["summary_traceback"][0]

    diag_file = tmp_path / "diagnostics.json"
    assert diag_file.exists()
    with open(diag_file, encoding="utf-8") as f:
        diag_data = json.load(f)
    assert diag_data["status"] == "TIMEOUT"


def test_wrapper_failed_command_traceback(tmp_path: Path) -> None:
    """Kiểm tra kịch bản lệnh chạy bị lỗi: exit code != 0, status = FAILED, trích xuất traceback."""
    python_exe = sys.executable
    cmd = f'"{python_exe}" -c "raise ValueError(\'Simulated Failure Error\')"'

    result = run_safe_wrapper(cmd=cmd, timeout_seconds=10, output_dir=tmp_path, cwd=PROJECT_ROOT)

    assert result["status"] == "FAILED"
    assert result["error_type"] == "EXECUTION_ERROR"
    assert result["returncode"] != 0
    assert any(
        "ValueError: Simulated Failure Error" in line for line in result["summary_traceback"]
    )

    diag_file = tmp_path / "diagnostics.json"
    assert diag_file.exists()
    with open(diag_file, encoding="utf-8") as f:
        diag_data = json.load(f)
    assert diag_data["status"] == "FAILED"
    assert len(diag_data["summary_traceback"]) > 0
