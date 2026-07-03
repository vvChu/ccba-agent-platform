import sqlite3
import subprocess
import sys

import pytest

from ccba_harness._guard import HarnessGuard


def test_json_unicode_escape_bypass(tmp_path):
    """Bypass using JSON unicode escape sequences.

    The string containing the sensitive filename is escaped using unicode escapes (e.g. \\u0073 for s).
    The parent's AST and string decode checks do not recursively decode double-escaped strings,
    but json.loads() in the child process does.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("json-unicode-secret")

    # Encode "secret_credential.txt" into json unicode escapes
    path_str = str(sensitive_file).replace("\\", "/")
    escaped_path = "".join(f"\\u{ord(c):04x}" for c in path_str)

    py_code = f"import json; fn = json.loads('\"{escaped_path}\"'); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_sqlite_custom_function_bypass(tmp_path):
    """Bypass using sqlite3 custom SQL function.

    We connect to an in-memory database and register a custom function that returns
    the sensitive database path. Then we run ATTACH DATABASE using the function call.
    This bypasses both the static SQL query scanner and audit hooks.
    """
    sensitive_db = tmp_path / "secret_credential.db"
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('sqlite-func-secret')")
    conn.commit()
    conn.close()

    def get_sensitive_path():
        return str(sensitive_db)

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        conn.create_function("get_path", 0, get_sensitive_path)
        with pytest.raises(PermissionError):
            conn.execute("ATTACH DATABASE get_path() AS subdb")
        conn.close()


def test_powershell_concatenation_bypass(tmp_path):
    """Bypass using PowerShell string concatenation in subprocess.

    Powershell is used to run a command where the sensitive path is constructed
    dynamically by concatenating string literals. The static checkers do not parse
    PowerShell syntax, bypassing the block.
    """
    if sys.platform != "win32":
        pytest.skip("Windows PowerShell specific bypass")

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("powershell-secret")

    path_str = str(sensitive_file)
    # Split path_str into two halves
    half = len(path_str) // 2
    part1 = path_str[:half]
    part2 = path_str[half:]

    # Powershell command
    cmd = ["powershell", "-Command", f"Get-Content ('{part1}' + '{part2}')"]

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_getattr_replace_fully_obfuscated_bypass(tmp_path):
    """Bypass using getattr with fully obfuscated strings.

    We obfuscate the path by replacing characters so that neither "secret" nor "credential"
    appears as a substring in any literal in the python snippet.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("getattr-obfuscated-secret")

    path_str = str(sensitive_file).replace("\\", "/")
    # Obfuscate 'secret' to 'seXcret' and 'credential' to 'creXdential'
    obfuscated_path = path_str.replace("secret", "seXcret").replace("credential", "creXdential")

    py_code = f"fn = getattr('{obfuscated_path}', 'replace')('X', ''); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )
