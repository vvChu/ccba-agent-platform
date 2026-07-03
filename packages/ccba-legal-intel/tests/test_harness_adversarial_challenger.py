import sqlite3
import subprocess
import sys

import pytest
from ccba_legal.harness._guard import HarnessGuard


def test_iterator_bypass(tmp_path):
    """Bypass 1: Passing iterator/generator to subprocess.Popen bypasses the checks.

    Since the guard converts non-list/tuple/str arguments to str(cmd_args), it gets the
    iterator string representation, leaving the elements inside unscanned.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("my-secret-content")

    # The command uses python to read the sensitive file
    cmd = iter([sys.executable, "-c", f"print(open(r'{sensitive_file}').read())"])

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def test_sqlite_char_attach_bypass(tmp_path):
    """Bypass 2: SQLite ATTACH DATABASE using char() function.

    HarnessGuard's SQL check only scans single/double-quoted literals and unquoted words.
    Using char() dynamically reconstructs the string without quotes, bypassing AST and keyword scans.
    """
    sensitive_db = tmp_path / "secret_credential.db"
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('my-db-secret')")
    conn.commit()
    conn.close()

    # 'secret_credential.db' character codes
    codes = ",".join(str(ord(c)) for c in str(sensitive_db))
    sql = f"ATTACH DATABASE char({codes}) AS subdb"

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(sql)
        conn.close()


def test_sqlite_hex_cast_attach_bypass(tmp_path):
    """Bypass 3: SQLite ATTACH DATABASE using CAST and hex literal.

    Using CAST(x'hex_digits' AS TEXT) constructs the filename string dynamically,
    which does not use single/double quotes around the filename, bypassing the regex.
    """
    sensitive_db = tmp_path / "secret_credential.db"
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('my-hex-secret')")
    conn.commit()
    conn.close()

    hex_str = str(sensitive_db).encode("utf-8").hex()
    sql = f"ATTACH DATABASE CAST(x'{hex_str}' AS TEXT) AS subdb"

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(sql)
        conn.close()


def test_ast_subscript_bypass(tmp_path):
    """Bypass 4: AST Subscript Bypass.

    Instead of using a literal list of characters which the AST parser collects and joins,
    we use string subscripting on a benign alphabet string. The AST parser does not evaluate
    subscripting operations, letting the dynamic string reconstruction pass through.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("subscript-secret")

    # We construct "secret_credential.txt" using subscripting of a benign alphabet
    # index map for "secret_credential.txt" from alphabet "aebcdfgilnoprstux_."
    # s(13), e(1), c(3), r(12), e(1), t(14), _(17), c(3), r(12), e(1), d(4), e(1), n(9), t(14), i(7), a(0), l(8), .(18), t(14), x(16), t(14)
    py_code = (
        "b = 'aebcdfgilnoprstux_.'; "
        "fn = b[13]+b[1]+b[3]+b[12]+b[1]+b[14]+b[17]+b[3]+b[12]+b[1]+b[4]+b[1]+b[9]+b[14]+b[7]+b[0]+b[8]+b[18]+b[14]+b[16]+b[14]; "
        "print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.Popen(
                [sys.executable, "-c", py_code],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=tmp_path,
            )


def test_cmd_caret_bypass(tmp_path):
    """Bypass 5: Windows CMD Caret Escape.

    On Windows, the CMD shell strips carets (^). However, the guard's string matching
    sees "s^e^c^r^e^t_c^r^e^d^e^n^t^i^a^l.t^x^t" which doesn't trigger keyword matches,
    allowing the subprocess to execute and read the file successfully.
    """
    if sys.platform != "win32":
        pytest.skip("Windows CMD specific bypass")

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("cmd-caret-secret")

    # Caret-escape the whole filename
    cmd_str = "cmd.exe /c type s^e^c^r^e^t_c^r^e^d^e^n^t^i^a^l.t^x^t"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.Popen(
                cmd_str,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=tmp_path,
            )


def test_cmd_quoted_set_bypass(tmp_path):
    """Bypass 5: Windows CMD double-quoted SET variable concatenation.

    CMD supports setting variables like: set "X=sec"
    The regex in reconstruct_shell_variables looks for set <name>=<value> without quotes around the name,
    which fails to capture X, bypassing variable reconstruction.
    """
    if sys.platform != "win32":
        pytest.skip("Windows CMD specific bypass")

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("cmd-quoted-secret")

    # Split "secret_credential.txt" into benign parts: "sec", "ret_cred", "ential.txt"
    cmd_str = (
        'cmd.exe /c "set "X=sec"&& set "Y=ret_cred"&& set "Z=ential.txt"&& call type %X%%Y%%Z%"'
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.Popen(
                cmd_str,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=tmp_path,
            )


def test_bypass_bitwise_or_map(tmp_path):
    """Verify that reconstructing sensitive keyword using Bitwise OR in subprocess bypasses the guard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-bitwise-or")

    path_str = str(sensitive_file)
    char_codes = [ord(c) for c in path_str]
    expr_list = [f"int({c}).__or__(0)" for c in char_codes]
    expr_str = ", ".join(expr_list)

    py_code = f"import os; print(open(bytes([{expr_str}]).decode()).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_bypass_bitwise_and_map(tmp_path):
    """Verify that reconstructing sensitive keyword using Bitwise AND in subprocess bypasses the guard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-bitwise-and")

    path_str = str(sensitive_file)
    char_codes = [ord(c) for c in path_str]
    expr_list = [f"{c} & 127" for c in char_codes]
    expr_str = ", ".join(expr_list)

    py_code = f"import os; print(open(bytes([{expr_str}]).decode()).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_bypass_lshift_rshift_map(tmp_path):
    """Verify that reconstructing sensitive keyword using Left and Right Shift in subprocess bypasses the guard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-shift")

    path_str = str(sensitive_file)
    char_codes = [ord(c) for c in path_str]
    expr_list = [f"int({c}).__lshift__(1).__rshift__(1)" for c in char_codes]
    expr_str = ", ".join(expr_list)

    py_code = f"import os; print(open(bytes([{expr_str}]).decode()).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )
