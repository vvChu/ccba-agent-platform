import builtins
import os
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from ccba_harness import HarnessGuard
from ccba_harness._state import _Originals


def test_pre_action_hook_blocking_sensitive_files() -> None:
    """Verify that sensitive file paths are blocked when not approved."""
    # .env blocking
    with pytest.raises(PermissionError) as exc_info:
        with HarnessGuard():
            open(".env")
    assert "Access to sensitive file blocked" in str(exc_info.value)

    # Keyword matching
    sensitive_names = [
        "my_secret_file.txt",
        "credentials.json",
        "id_rsa.private_key",
        "passwords.yaml",
        "api_key.txt",
        "token.json",
    ]
    for name in sensitive_names:
        with pytest.raises(PermissionError) as exc_info:
            with HarnessGuard():
                open(name)
        assert "Access to sensitive file blocked" in str(exc_info.value)


def test_pre_action_hook_allowing_approved_files(tmp_path: Path) -> None:
    """Verify that sensitive files are allowed if explicitly approved."""
    secret_file = tmp_path / "my_secret.txt"
    # Write initial data to test file using normal open
    secret_file.write_text("my-secret-content")

    # 1. Exact match
    with HarnessGuard(approved_paths=[str(secret_file)]):
        with open(secret_file) as f:
            content = f.read()
        assert content == "my-secret-content"

    # 2. Parent directory match
    secret_dir = tmp_path / "secrets"
    secret_dir.mkdir(exist_ok=True)
    sub_secret = secret_dir / "db_password.txt"
    sub_secret.write_text("db-pass")

    with HarnessGuard(approved_paths=[str(secret_dir)]):
        with open(sub_secret) as f:
            content = f.read()
        assert content == "db-pass"

    # 3. Wildcard / Glob match
    another_secret = tmp_path / "api_key.json"
    another_secret.write_text("{}")
    with HarnessGuard(approved_paths=["*api_key.json"]):
        with open(another_secret) as f:
            content = f.read()
        assert content == "{}"


@patch("ccba_harness.subprocess.run")
def test_post_action_hook_success(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify post-action quality check hook runs ruff and pytest on success."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    test_py = tmp_path / "test_script.py"

    with HarnessGuard():
        with open(test_py, "w") as f:
            f.write("# some python code")

    # Verify that subprocess.run was called for both ruff and pytest
    assert mock_run.call_count == 2
    calls = [call[0][0] for call in mock_run.call_args_list]
    assert any("ruff" in cmd and "check" in cmd for cmd in calls)
    assert any("pytest" in cmd for cmd in calls)


@patch("ccba_harness.subprocess.run")
def test_post_action_hook_ruff_failure(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify that a ruff check failure raises a RuntimeError."""
    mock_res_fail = MagicMock()
    mock_res_fail.returncode = 1
    mock_res_fail.stdout = "Style violation found"
    mock_res_fail.stderr = ""
    mock_run.return_value = mock_res_fail

    test_py = tmp_path / "test_script.py"

    with pytest.raises(RuntimeError) as exc_info:
        with HarnessGuard():
            with open(test_py, "w") as f:
                f.write("invalid code")

    assert "ruff check failed" in str(exc_info.value)
    assert "Style violation found" in str(exc_info.value)


@patch("ccba_harness.subprocess.run")
def test_post_action_hook_pytest_failure(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify that a pytest failure raises a RuntimeError."""
    mock_res_ok = MagicMock()
    mock_res_ok.returncode = 0

    mock_res_fail = MagicMock()
    mock_res_fail.returncode = 1
    mock_res_fail.stdout = "1 test failed"
    mock_res_fail.stderr = ""

    # Mock success for ruff (first call) and failure for pytest (second call)
    mock_run.side_effect = [mock_res_ok, mock_res_fail]

    test_py = tmp_path / "test_script.py"

    with pytest.raises(RuntimeError) as exc_info:
        with HarnessGuard():
            with open(test_py, "w") as f:
                f.write("valid code")

    assert "pytest failed" in str(exc_info.value)
    assert "1 test failed" in str(exc_info.value)


@patch("ccba_harness.subprocess.run")
def test_post_action_hook_no_py_written(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify that non-python writes or only python reads do not trigger checks."""
    test_txt = tmp_path / "test.txt"
    with HarnessGuard():
        with open(test_txt, "w") as f:
            f.write("hello")

    test_py = tmp_path / "test.py"
    test_py.write_text("print(1)")
    with HarnessGuard():
        with open(test_py) as f:
            f.read()

    mock_run.assert_not_called()


@patch("ccba_harness.subprocess.run")
def test_decorator_usage(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify that HarnessGuard works when used as a decorator."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    test_py = tmp_path / "test_script.py"

    @HarnessGuard()
    def my_func() -> None:
        with open(test_py, "w") as f:
            f.write("# decorator code")

    my_func()
    assert mock_run.call_count == 2


def test_original_hooks_restored_in_subprocess() -> None:
    """Verify that the open hooks remain global and only use thread-local in_hook bypass during subprocess creation."""
    with HarnessGuard():
        assert builtins.open != _Originals.builtins_open

        builtins_open_during_popen = None
        in_hook_during_popen = None

        def mock_popen_check(*args: Any, **kwargs: Any) -> MagicMock:
            nonlocal builtins_open_during_popen, in_hook_during_popen
            builtins_open_during_popen = builtins.open
            from ccba_harness._engine import _local  # type: ignore[attr-defined]

            in_hook_during_popen = getattr(_local, "in_hook", False)
            # Return a mock process that supports context manager and communicate
            mock_proc = MagicMock()
            mock_proc.__enter__.return_value = mock_proc
            mock_proc.__exit__.return_value = False
            mock_proc.communicate.return_value = (b"", b"")
            mock_proc.returncode = 0
            return mock_proc

        with patch("ccba_harness._process_monitor._Originals.popen", side_effect=mock_popen_check):
            subprocess.run(["dummy_command"])

        # Check that during subprocess call, builtins.open remained wrapped (global hook intact)
        assert builtins_open_during_popen != _Originals.builtins_open
        # Check that in_hook was active to bypass the hook locally
        from ccba_harness._engine import _HOOK_TOKEN  # type: ignore[attr-defined]

        assert in_hook_during_popen is _HOOK_TOKEN
        # Check that after subprocess call, the hook is still wrapped
        assert builtins.open != _Originals.builtins_open


def test_os_rename_and_replace_intercept(tmp_path: Path) -> None:
    """Verify that os.rename and os.replace to sensitive destination paths are blocked."""
    src_file = tmp_path / "normal.txt"
    src_file.write_text("content")

    sensitive_dst = tmp_path / "secret_credential.txt"

    with HarnessGuard():
        # os.rename should fail when renaming to sensitive destination
        with pytest.raises(PermissionError):
            os.rename(src_file, sensitive_dst)

        # os.replace should fail when replacing to sensitive destination
        with pytest.raises(PermissionError):
            os.replace(src_file, sensitive_dst)


@patch("ccba_harness.subprocess.run")
def test_nested_guard_py_tracking(mock_run: MagicMock, tmp_path: Path) -> None:
    """Verify that writing a .py file tracks it in ALL active nested guards."""
    mock_res = MagicMock()
    mock_res.returncode = 0
    mock_run.return_value = mock_res

    test_py = tmp_path / "my_script.py"

    with HarnessGuard() as g1:
        with HarnessGuard() as g2:
            with open(test_py, "w") as f:
                f.write("# some python code")

            # Check that BOTH guards tracked the file
            assert os.path.abspath(test_py) in g2._written_py_files
            assert os.path.abspath(test_py) in g1._written_py_files
