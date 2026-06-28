import builtins
import os
import subprocess
import sys
import threading
import time

import pytest
from ccba_legal.harness import HarnessGuard


def test_subthread_leak(tmp_path):
    """Verify if a subthread spawned within HarnessGuard context is blocked by the guard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")

    leak_succeeded = False
    exception_raised = None

    def worker():
        nonlocal leak_succeeded, exception_raised
        try:
            # Attempt to read the sensitive file
            with open(sensitive_file) as f:
                content = f.read()
            if content == "super-secret":
                leak_succeeded = True
        except Exception as e:
            exception_raised = e

    with HarnessGuard():
        t = threading.Thread(target=worker)
        t.start()
        t.join()

    # The subthread should have been blocked because guard context propagates
    assert leak_succeeded is False
    assert isinstance(exception_raised, PermissionError)


def test_global_hook_deactivation_race(tmp_path):
    """Verify if Thread B is still blocked by the HarnessGuard while Thread A is running a subprocess."""
    sensitive_file = tmp_path / "secret_api_key.txt"
    sensitive_file.write_text("sensitive-api-key")

    stop_event = threading.Event()
    bypass_count = 0
    total_attempts = 0

    def thread_a_subprocess_runner():
        # Continually run a dummy subprocess to trigger _wrapped_popen
        while not stop_event.is_set():
            try:
                # We use a lightweight subprocess command
                subprocess.run([sys.executable, "-c", "pass"], capture_output=True)
            except Exception:
                pass
            time.sleep(0.001)

    def thread_b_file_accessor():
        nonlocal bypass_count, total_attempts
        with HarnessGuard():
            while not stop_event.is_set():
                total_attempts += 1
                try:
                    with open(sensitive_file) as f:
                        f.read()
                    bypass_count += 1
                except PermissionError:
                    pass
                time.sleep(0.001)

    t_a = threading.Thread(target=thread_a_subprocess_runner)
    t_b = threading.Thread(target=thread_b_file_accessor)

    t_a.start()
    t_b.start()

    time.sleep(2.0)  # Run for 2 seconds
    stop_event.set()

    t_a.join()
    t_b.join()

    print(f"Total attempts: {total_attempts}, Bypass count: {bypass_count}")
    # Bypasses must be 0 because Thread A's popen does not globally deactivate hooks
    assert bypass_count == 0, (
        f"Vulnerability detected: Thread B bypassed the guard: {bypass_count}/{total_attempts}"
    )


def test_bypass_via_os_open(tmp_path):
    """Verify if low-level os.open is blocked by HarnessGuard file protection."""
    sensitive_file = tmp_path / "secret_password.txt"
    sensitive_file.write_text("password123")

    with HarnessGuard():
        # Attempting open() should fail
        with pytest.raises(PermissionError):
            open(sensitive_file)

        # Attempting os.open should also fail
        with pytest.raises(PermissionError):
            os.open(sensitive_file, os.O_RDONLY)


def test_bypass_via_pre_imported_open(tmp_path):
    """Verify if importing open before entering HarnessGuard is blocked."""
    sensitive_file = tmp_path / "secret_private_key.txt"
    sensitive_file.write_text("private-key-data")

    # Simulate pre-importing open
    pre_imported_open = builtins.open

    with HarnessGuard():
        # Attempting normal open() should fail
        with pytest.raises(PermissionError):
            open(sensitive_file)

        # Attempting pre_imported_open() should also fail
        with pytest.raises(PermissionError):
            with pre_imported_open(sensitive_file, "r") as f:
                f.read()


def test_subprocess_execution_bypass(tmp_path):
    """Verify if running a subprocess that attempts to read/use sensitive files is blocked."""
    sensitive_file = tmp_path / "secret_token.txt"
    sensitive_file.write_text("token-value")

    with HarnessGuard():
        # Python open should fail
        with pytest.raises(PermissionError):
            open(sensitive_file)

        # Subprocess run should fail due to argument inspection raising PermissionError
        with pytest.raises(PermissionError) as exc_info:
            subprocess.run(
                [sys.executable, "-c", f"print(open({repr(str(sensitive_file))}).read().strip())"],
                capture_output=True,
                text=True,
            )
        assert "Access to sensitive" in str(exc_info.value)


def test_deep_nesting_performance():
    """Verify performance and behaviour with deeply nested guards."""
    start_time = time.time()
    guards = [HarnessGuard() for _ in range(50)]

    # Enter all guards
    for g in guards:
        g.__enter__()

    try:
        # Perform some operations
        for _ in range(100):
            with open(os.devnull, "w") as f:
                f.write("")
    finally:
        # Exit all guards in reverse order
        for g in reversed(guards):
            g.__exit__(None, None, None)

    duration = time.time() - start_time
    print(f"Deep nesting duration: {duration:.4f}s")
    assert duration < 1.0  # Should be fast


def test_bypass_via_io_fileio(tmp_path):
    """Verify if opening a sensitive file using io.FileIO is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    with HarnessGuard():
        with pytest.raises(PermissionError):
            import io

            io.FileIO(sensitive_file)


def test_bypass_via_hardlink(tmp_path):
    """Verify if creating a hardlink to a sensitive file allows reading it under a benign name."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    benign_link = tmp_path / "benign_link.txt"
    with HarnessGuard():
        with pytest.raises(PermissionError):
            os.link(sensitive_file, benign_link)
            with open(benign_link) as f:
                f.read()


def test_bypass_via_symlink(tmp_path):
    """Verify if creating a symlink to a sensitive file allows reading it under a benign name."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    benign_symlink = tmp_path / "benign_symlink.txt"
    with HarnessGuard():
        try:
            os.symlink(sensitive_file, benign_symlink)
        except OSError:
            pytest.skip("Symlinks not supported or requires admin privileges")

        with pytest.raises(PermissionError):
            with open(benign_symlink) as f:
                f.read()


def test_bypass_via_sqlite3(tmp_path):
    """Verify if opening a sensitive database file via sqlite3 is blocked."""
    sensitive_db = tmp_path / "secret_credential.db"
    with HarnessGuard():
        with pytest.raises(PermissionError):
            import sqlite3

            conn = sqlite3.connect(sensitive_db)
            conn.close()


def test_bypass_via_shell_obfuscation(tmp_path):
    """Verify that command-line obfuscation (quotes/wildcards) is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    with HarnessGuard():
        # Quotes obfuscation in subprocess
        with pytest.raises(PermissionError):
            subprocess.Popen([sys.executable, "-c", f"print(open('{str(sensitive_file)}').read())"])

        # Wildcard obfuscation in subprocess
        wildcard_path = str(tmp_path / "secret_cred*")
        with pytest.raises(PermissionError):
            subprocess.Popen(
                [sys.executable, "-c", f"import glob; print(glob.glob('{wildcard_path}'))"]
            )


def test_bypass_via_env_variable(tmp_path):
    """Verify that passing sensitive paths in subprocess env is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    with HarnessGuard():
        # Single sensitive env var
        with pytest.raises(PermissionError):
            subprocess.Popen(
                [sys.executable, "-c", "pass"], env={"MY_SECRET_PATH": str(sensitive_file)}
            )

        # Sensitive path in a path-like env list
        with pytest.raises(PermissionError):
            subprocess.Popen(
                [sys.executable, "-c", "pass"],
                env={"PATH": f"C:\\some_folder{os.pathsep}{str(sensitive_file)}"},
            )


def test_bypass_via_os_system_blocked(tmp_path):
    """Verify os.system with sensitive command arguments is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    with HarnessGuard():
        with pytest.raises(PermissionError):
            os.system(f"cat {sensitive_file}")


def test_bypass_via_os_spawn_blocked(tmp_path):
    """Verify os.spawn* functions are blocked when accessing sensitive paths."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")

    if hasattr(os, "spawnv"):
        with HarnessGuard():
            with pytest.raises(PermissionError):
                os.spawnv(
                    os.P_WAIT,
                    sys.executable,
                    [sys.executable, "-c", f"print(open('{sensitive_file}').read())"],
                )


def test_bypass_via_os_exec_blocked(tmp_path):
    """Verify os.exec* functions are blocked when accessing sensitive paths."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")

    if hasattr(os, "execv"):
        with HarnessGuard():
            with pytest.raises(PermissionError):
                os.execv(
                    sys.executable,
                    [sys.executable, "-c", f"print(open('{sensitive_file}').read())"],
                )


def test_bypass_via_io_open_and_fileio(tmp_path):
    """Verify that _io.open and _io.FileIO are blocked for sensitive paths."""
    import _io

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")

    with HarnessGuard():
        with pytest.raises(PermissionError):
            _io.open(sensitive_file, "r")
        with pytest.raises(PermissionError):
            _io.FileIO(sensitive_file, "r")


def test_bypass_via_sqlite3_connection(tmp_path):
    """Verify that sqlite3.Connection directly blocks sensitive paths."""
    sensitive_db = tmp_path / "secret_credential.db"
    with HarnessGuard():
        with pytest.raises(PermissionError):
            import sqlite3

            sqlite3.Connection(sensitive_db)


def test_bypass_via_base64_obfuscation(tmp_path):
    """Verify that command-line base64 obfuscation is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")

    # "secret_credential" base64 encoded is "c2VjcmV0X2NyZWRlbnRpYWw="
    obfuscated_arg = "c2VjcmV0X2NyZWRlbnRpYWw="

    with HarnessGuard():
        # Plain base64 string looking argument
        with pytest.raises(PermissionError):
            subprocess.Popen([sys.executable, "-c", "pass", obfuscated_arg])

        # Argument containing base64/b64decode/decode('base64') and base64 text
        with pytest.raises(PermissionError):
            subprocess.Popen([sys.executable, "-c", "import base64; base64.b64decode('c2VjcmV0')"])
