import base64
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from ccba_harness._guard import HarnessGuard


def test_bypass_list_comp_shift(tmp_path: Path) -> None:
    """Bypass 1: Test list comprehension of chr with arithmetic shift in subprocess.

    The character codes are shifted by +1 so that they don't contain any sensitive literal strings or
    constants that are easily evaluated by AST parsing. The child python process reconstructs the path.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content-1")

    # Shifted character codes of "secret_credential" by +1:
    # "secret_credential": [115, 101, 99, 114, 101, 116, 95, 99, 114, 101, 100, 101, 110, 116, 105, 97, 108]
    # Shifted (+1):       [116, 102, 100, 115, 102, 117, 96, 100, 115, 102, 101, 102, 111, 117, 106, 98, 109]
    shifted = [116, 102, 100, 115, 102, 117, 96, 100, 115, 102, 101, 102, 111, 117, 106, 98, 109]

    py_code = f"import os; codes = {shifted}; fn = ''.join([chr(x - 1) for x in codes]); print(open(fn + '.txt').read())"

    with HarnessGuard():
        cmd = [sys.executable, "-c", py_code]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)


def test_bypass_string_format(tmp_path: Path) -> None:
    """Bypass 2: Test string formatting/modulo operator in subprocess.

    Using '%s' string formatting to dynamically construct the open statement. The AST check
    doesn't evaluate modulo (%) operators.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content-2")

    py_code = (
        "import os; exec(\"print(op%s('sec%s_cred%s.txt').read())\" % ('en', 'ret', 'ential'))"
    )

    with HarnessGuard():
        cmd = [sys.executable, "-c", py_code]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, cwd=tmp_path)


def test_bypass_bytes_shift_eval(tmp_path: Path) -> None:
    """Bypass 3: Test bytes shift eval in subprocess.

    Using shifted character codes for the entire python code string, then reconstructing and
    evaluating it in the child process.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content-3")

    sensitive_file_str = str(sensitive_file).replace("\\", "/")
    target_code = f"print(open('{sensitive_file_str}').read())"

    # Shift character codes by +1
    shifted_bytes = [ord(c) + 1 for c in target_code]

    py_code = f"exec(bytes([x - 1 for x in {shifted_bytes}]).decode())"

    with HarnessGuard():
        cmd = [sys.executable, "-c", py_code]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True)


def test_bypass_sqlite_attach_expression(tmp_path: Path) -> None:
    """Bypass 4: SQLite ATTACH DATABASE using a parenthesized expression.

    HarnessGuard's SQL query parsing only extracts standard ATTACH string literals. It fails to
    detect paths inside parenthesized expressions or string concatenations.
    """
    sensitive_db = tmp_path / "secret_credential.db"

    # Create the sensitive DB
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content-4')")
    conn.commit()
    conn.close()

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        # We attach using string concatenation inside parentheses
        with pytest.raises(PermissionError):
            conn.execute(f"ATTACH ('{tmp_path}/secret_' || 'credential.db') AS subdb")
        conn.close()


def test_bypass_base32(tmp_path: Path) -> None:
    """Bypass 5: Base32 obfuscation of subprocess arguments.

    HarnessGuard only checks base64, zlib, and hex encoding. It does not check base32, base85,
    or other encoders.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content-5")

    sensitive_path_str = str(sensitive_file).replace("\\", "/")
    b32_path = base64.b32encode(sensitive_path_str.encode("utf-8")).decode("utf-8")

    py_code = f"import base64; print(open(base64.b32decode('{b32_path}').decode()).read())"

    with HarnessGuard():
        cmd = [sys.executable, "-c", py_code]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True)
