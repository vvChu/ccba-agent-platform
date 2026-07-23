import codecs
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.stress, pytest.mark.adversarial]


from ccba_harness._guard import HarnessGuard


def test_generator_expression_shift_bypass(tmp_path: Path) -> None:
    """Verify that using functools.reduce instead of a loop/join bypasses the guard's AST and loop checkers.

    Since we use functools.reduce instead of loops (for/while), comprehensions, or .join(), we bypass
    all string and regex pattern blockers.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("generator-secret-content")

    # Shifted path by +1
    path_str = str(sensitive_file).replace("\\", "/")
    shifted_codes = [ord(c) + 1 for c in path_str]

    # Reconstruct inside subprocess using functools.reduce
    py_code = (
        f"import functools; "
        f"fn = functools.reduce(lambda a, b: a + chr(b - 1), {shifted_codes}, ''); "
        f"print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_rot13_obfuscation_bypass(tmp_path: Path) -> None:
    """Verify that ROT13 encoding bypasses all keyword and AST checkers.

    ROT13-encoded path does not trigger any keyword match, nor does it look like base64/hex/base32/base85.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("rot13-secret-content")

    path_str = str(sensitive_file).replace("\\", "/")
    rot13_path = codecs.encode(path_str, "rot_13")

    py_code = f"import codecs; fn = codecs.decode('{rot13_path}', 'rot_13'); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_lambda_unsupported_op_bypass(tmp_path: Path) -> None:
    """Verify that using an unsupported operator in a map lambda body bypasses AST evaluation.

    The AST evaluator handles BitXor but not FloorDiv (//). This causes the AST evaluator
    to fail and return None, while the child process can successfully reconstruct the path.
    Also, using // does not trigger the shell redirection check (which > or >> would trigger).
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("lambda-secret-content")

    path_str = str(sensitive_file).replace("\\", "/")
    # Obfuscate using floor division: we store values as (char_code * 2)
    shifted_codes = [ord(c) * 2 for c in path_str]

    py_code = f"fn = bytes(map(lambda x: x // 2, {shifted_codes})).decode(); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_child_process_file_copy_bypass(tmp_path: Path) -> None:
    """Verify that copying a sensitive file to a benign name inside a subprocess bypasses the guard.

    The subprocess performs the copy, which is not hooked because HarnessGuard is not active
    in the child process. The parent process can then read the benign file.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("copy-secret-content")

    benign_file = tmp_path / "benign_copied_file.txt"

    path_str = str(sensitive_file).replace("\\", "/")
    benign_str = str(benign_file).replace("\\", "/")
    shifted_codes = [ord(c) * 2 for c in path_str]

    py_code = (
        f"import shutil; "
        f"src = bytes(map(lambda x: x // 2, {shifted_codes})).decode(); "
        f"shutil.copy(src, '{benign_str}')"
    )

    with HarnessGuard():
        # Copy is performed inside the child process using obfuscated name to bypass argument scan
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )
