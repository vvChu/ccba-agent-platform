import sqlite3
import subprocess
import sys

import pytest
from ccba_harness._guard import HarnessGuard


def test_fstring_bypass(tmp_path):
    """Bypass 1: Use f-strings and character variables to reconstruct the path.

    This avoids list comprehensions, join, replace, format, and is not evaluated
    by the AST parser (since it doesn't handle ast.JoinedStr).
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("fstring-secret-content")

    # Construct python code: a = 's'; b = 'e'; ...; fn = f'{a}{b}...'; print(open(fn).read())
    path_str = str(sensitive_file).replace("\\", "/")
    chars_setup = "; ".join(f"c{i} = '{c}'" for i, c in enumerate(path_str))
    fstring_expr = "".join(f"{{c{i}}}" for i in range(len(path_str)))

    py_code = f"{chars_setup}; fn = f'{fstring_expr}'; print(open(fn).read())"

    with HarnessGuard():
        # This is expected to raise PermissionError if protected, but it bypasses the guard.
        # Thus, it will run successfully, causing pytest.raises(PermissionError) to fail (asserting vulnerability).
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_getattr_replace_bypass(tmp_path):
    """Bypass 2: Use getattr to call replace dynamically.

    This bypasses the AST parser (which doesn't evaluate getattr) and the regex check
    (since there's no literal '.replace(' in the code).
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("getattr-replace-secret")

    path_str = str(sensitive_file).replace("\\", "/")
    # Insert a dummy char 'X' to be replaced
    obfuscated_path = path_str.replace("secret", "seXcret")

    py_code = f"fn = getattr('{obfuscated_path}', 'replace')('X', ''); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_sys_argv_bypass(tmp_path):
    """Bypass 3: Pass path components as separate command arguments.

    Splitting the sensitive path into non-sensitive parts and passing them as arguments
    to the subprocess, which then concatenates them. Since no individual argument is
    sensitive, the command argument check passes.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("sys-argv-secret")

    # None of these substrings contain "secret" or "credential"
    parts = ["secre", "t_", "crede", "ntial.txt"]

    py_code = (
        "import sys; "
        "fn = sys.argv[1] + sys.argv[2] + sys.argv[3] + sys.argv[4]; "
        "print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code] + parts,
                capture_output=True,
                text=True,
                check=True,
                cwd=tmp_path,
            )


def test_bytearray_bypass(tmp_path):
    """Bypass 4: Use bytearray to reconstruct path.

    This is not evaluated by the AST parser (since it doesn't handle bytearray)
    and is not blocked by regex or keyword checks.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("bytearray-secret")

    path_str = str(sensitive_file).replace("\\", "/")
    char_codes = [ord(c) for c in path_str]

    py_code = f"fn = bytearray({char_codes}).decode(); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_sqlite_str_subclass_upper_bypass(tmp_path):
    """Bypass 5: Subclass str and override upper() to bypass SQL checks.

    Overriding upper() to return a benign query avoids the ATTACH check in _check_sql_query,
    but sqlite3's C library still executes the original ATTACH statement.
    """
    sensitive_db = tmp_path / "secret_credential.db"
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('subclass-db-secret')")
    conn.commit()
    conn.close()

    class QueryStr(str):
        def upper(self):
            return "SELECT 1"

    sql_query = QueryStr(f"ATTACH DATABASE '{sensitive_db}' AS subdb")

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(sql_query)
        conn.close()


def test_py_launcher_bypass(tmp_path):
    """Bypass 6: Use the py launcher instead of sys.executable.

    Running Python via 'py' disables all Python-specific checks (like blocked libraries,
    list comprehensions, join/replace checks) because is_python_cmd becomes False.
    This allows ROT13 or codecs obfuscation to pass.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("py-launcher-secret")

    path_str = str(sensitive_file).replace("\\", "/")
    rot13_path = path_str.translate(
        str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "NOPQRSTUVWXYZABCDEFGHIJKLMnopqrstuvwxyzabcdefghijklm",
        )
    )

    py_code = f"import codecs; fn = codecs.decode('{rot13_path}', 'rot_13'); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(["py", "-c", py_code], capture_output=True, text=True, check=True)
