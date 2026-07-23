import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import pytest

pytestmark = [pytest.mark.stress, pytest.mark.slow]


from ccba_harness._guard import HarnessGuard
from ccba_harness._state import _original_builtins_open


def test_concurrent_guard_bypass_via_subprocess(tmp_path: Path) -> None:
    """Test if a subprocess run in one thread globally disables open hooks for other threads using a loop to catch the race condition."""
    sensitive_file = tmp_path / "secret_credential_file.txt"
    sensitive_file.write_text("super-secret-key")

    bypass_detected = []
    stop_event = threading.Event()

    def thread_subprocess_runner() -> None:
        with HarnessGuard():
            while not stop_event.is_set():
                # We spawn sub-processes repeatedly to maximize the window where hooks are restored
                p = subprocess.Popen(["python", "-c", "pass"])
                p.wait()
                time.sleep(0.001)

    def thread_file_accessor() -> None:
        with HarnessGuard():
            # Try to read the sensitive file repeatedly
            for _ in range(200):
                try:
                    with open(sensitive_file) as f:
                        content = f.read()
                    bypass_detected.append(content)
                except PermissionError:
                    pass
                time.sleep(0.001)

    t1 = threading.Thread(target=thread_subprocess_runner)
    t2 = threading.Thread(target=thread_file_accessor)

    t1.start()
    t2.start()

    # Wait for accessor to finish
    t2.join()
    stop_event.set()
    t1.join()

    # If the bypass occurred, bypass_detected will have the content of the secret file
    assert len(bypass_detected) == 0, (
        f"Vulnerability confirmed: accessed sensitive data: {bypass_detected}"
    )


def test_security_bypass_via_os_open(tmp_path: Path) -> None:
    """Verify that os.open is blocked by HarnessGuard security controls."""
    sensitive_file = tmp_path / "secret_private_key.pem"
    sensitive_file.write_text("private-key-data")

    # Accessing via normal open() is blocked
    with pytest.raises(PermissionError):
        with HarnessGuard():
            open(sensitive_file)

    # Accessing via os.open is also blocked
    with HarnessGuard():
        with pytest.raises(PermissionError):
            os.open(sensitive_file, os.O_RDONLY)


def test_nested_guard_correctness(tmp_path: Path) -> None:
    """Test behavior of nested HarnessGuard instances on the same thread."""
    secret1 = tmp_path / "credential_one.txt"
    secret2 = tmp_path / "password_two.txt"
    secret1.write_text("creds1")
    secret2.write_text("pass2")

    # Nested guards with different approved paths
    with HarnessGuard(approved_paths=[str(secret1)]):
        # Inside outer guard, secret1 is approved, secret2 is blocked
        with open(secret1) as f:
            assert f.read() == "creds1"
        with pytest.raises(PermissionError):
            open(secret2)

        with HarnessGuard(approved_paths=[str(secret2)]):
            # Inside inner guard, both active. If ANY active guard blocks, raise PermissionError.
            # Both secret2 (blocked by outer g1) and secret1 (blocked by inner g2) are blocked.
            with pytest.raises(PermissionError):
                open(secret2)

            with pytest.raises(PermissionError):
                open(secret1)

        # After inner guard exits, outer guard is active again, so secret1 should be allowed, secret2 blocked
        with open(secret1) as f:
            assert f.read() == "creds1"
        with pytest.raises(PermissionError):
            open(secret2)


def test_deep_recursion_handling(tmp_path: Path) -> None:
    """Verify that deep nested calls or recursion do not crash the guard."""
    # Test nesting up to 100 levels
    guards = []
    try:
        for _ in range(100):
            g = HarnessGuard()
            g.__enter__()
            guards.append(g)

        # Test open still works
        temp_file = tmp_path / "temp.txt"
        temp_file.write_text("test")
        with open(temp_file) as f:
            assert f.read() == "test"
    finally:
        for g in reversed(guards):
            g.__exit__(None, None, None)


def test_performance_overhead(tmp_path: Path) -> None:
    """Measure file opening performance overhead introduced by HarnessGuard."""
    temp_file = tmp_path / "bench.txt"
    temp_file.write_text("data")

    # Warm up
    for _ in range(100):
        with _original_builtins_open(temp_file, "r") as f:
            f.read()

    # Benchmark original open
    t0 = time.perf_counter()
    for _ in range(1000):
        with _original_builtins_open(temp_file, "r") as f:
            f.read()
    t_orig = time.perf_counter() - t0

    # Benchmark guarded open (with empty approved_paths)
    t1 = time.perf_counter()
    with HarnessGuard():
        for _ in range(1000):
            with open(temp_file) as f:
                f.read()
    t_guard = time.perf_counter() - t1

    print(f"\nBenchmark: original open={t_orig:.4f}s, guarded open={t_guard:.4f}s")
    # Verify it doesn't blow up completely (e.g. >100x slower)
    assert t_guard < t_orig * 150, (
        f"Performance bottleneck detected: guard is {t_guard / t_orig:.1f}x slower"
    )


def test_path_types(tmp_path: Path) -> None:
    """Test support for various path type arguments in open()."""
    sensitive_file = tmp_path / "api_key.txt"
    sensitive_file.write_text("my-key")

    with HarnessGuard():
        # Test bytes path
        with pytest.raises(PermissionError):
            open(bytes(sensitive_file), "rb")

        # Test pathlib.Path path
        with pytest.raises(PermissionError):
            open(sensitive_file)

        # Test string path
        with pytest.raises(PermissionError):
            open(str(sensitive_file))


def test_false_positive_path_matching(tmp_path: Path) -> None:
    """Verify that any file under a directory containing a sensitive keyword in its name is blocked."""
    sensitive_dir = tmp_path / "my_secrets_folder"
    sensitive_dir.mkdir()
    benign_file = sensitive_dir / "benign_file.txt"
    benign_file.write_text("not-secret")

    # Even though filename is benign_file.txt, because it's under my_secrets_folder,
    # the absolute path contains 'secret', causing HarnessGuard to block it.
    with pytest.raises(PermissionError):
        with HarnessGuard():
            open(benign_file)


def test_bypasses_blocked_stress(tmp_path: Path) -> None:
    """Verify all new bypasses are blocked by HarnessGuard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret")
    benign_link = tmp_path / "benign_link.txt"
    benign_symlink = tmp_path / "benign_symlink.txt"
    sensitive_db = tmp_path / "secret_credential.db"

    with HarnessGuard():
        # 1. io.FileIO
        with pytest.raises(PermissionError):
            import io

            io.FileIO(sensitive_file)

        # 2. os.link
        with pytest.raises(PermissionError):
            os.link(sensitive_file, benign_link)

        # 3. os.symlink
        try:
            os.symlink(sensitive_file, benign_symlink)
            with pytest.raises(PermissionError):
                with open(benign_symlink) as f:
                    f.read()
        except OSError:
            # Handle Windows/insufficient privilege gracefully
            pass

        # 4. sqlite3
        with pytest.raises(PermissionError):
            import sqlite3

            conn = sqlite3.connect(sensitive_db)
            conn.close()

        # 5. Shell obfuscation
        with pytest.raises(PermissionError):
            subprocess.Popen([sys.executable, "-c", f"print(open('{str(sensitive_file)}').read())"])

        # 6. Environment variable bypass
        with pytest.raises(PermissionError):
            subprocess.Popen(
                [sys.executable, "-c", "pass"], env={"MY_SECRET_ENV": str(sensitive_file)}
            )

        # 7. _io.open and _io.FileIO
        with pytest.raises(PermissionError):
            import _io

            _io.open(sensitive_file)
        with pytest.raises(PermissionError):
            import _io

            _io.FileIO(sensitive_file)

        # 8. sqlite3.Connection directly
        with pytest.raises(PermissionError):
            import sqlite3

            sqlite3.Connection(sensitive_db)

        # 9. os.system
        with pytest.raises(PermissionError):
            os.system(f"echo {sensitive_file}")

        # 10. os.spawnv
        if hasattr(os, "spawnv"):
            with pytest.raises(PermissionError):
                os.spawnv(
                    os.P_WAIT,
                    sys.executable,
                    [sys.executable, "-c", f"print(open('{sensitive_file}').read())"],
                )

        # 11. os.execv
        if hasattr(os, "execv"):
            with pytest.raises(PermissionError):
                os.execv(
                    sys.executable,
                    [sys.executable, "-c", f"print(open('{sensitive_file}').read())"],
                )

        # 12. base64 obfuscation in subprocess args
        with pytest.raises(PermissionError):
            subprocess.Popen([sys.executable, "-c", "pass", "c2VjcmV0X2NyZWRlbnRpYWw="])
