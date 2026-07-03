import os
import shutil
import subprocess
import sys

import pytest
from ccba_legal.harness._guard import HarnessGuard


def test_env_var_concat_bypass(tmp_path):
    """Bypass: Environment variable concatenation.

    Split the sensitive path into non-sensitive parts and pass them as separate env vars.
    In the child process, reconstruct the path by concatenating the env vars.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("env-var-secret")

    # None of these substrings contain "secret" or "credential"
    env_parts = {"PART_A": "secre", "PART_B": "t_", "PART_C": "crede", "PART_D": "ntial.txt"}

    py_code = (
        "import os; "
        "fn = os.environ['PART_A'] + os.environ['PART_B'] + os.environ['PART_C'] + os.environ['PART_D']; "
        "print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ, **env_parts},
                cwd=tmp_path,
            )


def test_python_copied_exec_bypass(tmp_path):
    """Bypass: Copy the python executable to a non-python name.

    This disables the is_python_cmd check in the parent, bypassing all python-specific filters
    like blocked libraries and string reconstruction checks.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("copied-exec-secret")

    # Copy python executable to a temporary file with a name not containing "python"
    exec_dir = os.path.dirname(sys.executable)
    copied_exec = os.path.join(exec_dir, "benign_runner.exe")

    try:
        shutil.copy2(sys.executable, copied_exec)
    except Exception:
        # Fallback to temp path if write permissions to virtualenv are restricted
        copied_exec = os.path.join(tmp_path, "benign_runner.exe")
        try:
            shutil.copy2(sys.executable, copied_exec)
        except Exception as e:
            pytest.skip(f"Failed to copy python executable for test: {e}")

    # Use ROT13 obfuscation which is blocked under python subprocess but not benign subprocess
    path_str = str(sensitive_file).replace("\\", "/")
    rot13_path = path_str.translate(
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
    )

    py_code = f"import codecs; fn = codecs.decode('{rot13_path}', 'rot_13'); print(open(fn).read())"

    try:
        with HarnessGuard():
            with pytest.raises(PermissionError):
                subprocess.run(
                    [copied_exec, "-c", py_code], capture_output=True, text=True, check=True
                )
    finally:
        if os.path.exists(copied_exec):
            try:
                os.remove(copied_exec)
            except Exception:
                pass


def test_base64_split_bypass(tmp_path):
    """Bypass: Pass base64 encoded path split into short command arguments.

    Split the base64 string into chunks shorter than 4 characters or parts that do not
    decode to a sensitive keyword individually, then concatenate them in the subprocess.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("split-b64-secret")

    # base64 of "secret_credential.txt" is "c2VjcmV0X2NyZWRlbnRpYWwudHh0"
    # We split it into elements of length 4, which individually don't decode to any sensitive word
    chunks = ["c2Vj", "cmV0", "X2Ny", "ZWRl", "bnRp", "YWwudHh0"]

    py_code = (
        "import base64; "
        "import sys; "
        "b64_str = sys.argv[1] + sys.argv[2] + sys.argv[3] + sys.argv[4] + sys.argv[5] + sys.argv[6]; "
        "fn = base64.b64decode(b64_str).decode(); "
        "print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code] + chunks,
                capture_output=True,
                text=True,
                check=True,
                cwd=tmp_path,
            )
