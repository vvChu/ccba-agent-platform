import ctypes
import os
import subprocess
import sys
import zlib
from pathlib import Path

import pytest

from ccba_harness import HarnessGuard


def test_bypass_hex_obfuscation_in_subprocess(tmp_path: Path) -> None:
    """Verify that a subprocess using hex obfuscation is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    hex_path = str(sensitive_file).encode("utf-8").hex()

    with HarnessGuard():
        cmd = [
            sys.executable,
            "-c",
            f"print(open(bytes.fromhex('{hex_path}').decode('utf-8')).read())",
        ]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_bypass_stdin_obfuscation(tmp_path: Path) -> None:
    """Verify that a subprocess reading Python code from stdin is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    with HarnessGuard():
        with pytest.raises(PermissionError):
            p = subprocess.Popen(
                [sys.executable, "-c", "import sys; exec(sys.stdin.read())"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            p.communicate(input=f"print(open(r'{sensitive_file}').read())")


def test_bypass_ctypes_libc(tmp_path: Path) -> None:
    """Verify that ctypes dlopen loading is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    if sys.platform != "win32":
        pytest.skip("This test is configured for Windows ctypes libc bypass.")

    with HarnessGuard():
        with pytest.raises(PermissionError):
            _ = ctypes.cdll.msvcrt


def test_bypass_zlib_compression(tmp_path: Path) -> None:
    """Verify that zlib compressed argument is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    compressed_path = zlib.compress(str(sensitive_file).encode("utf-8"))
    compressed_repr = repr(compressed_path)

    with HarnessGuard():
        cmd = [
            sys.executable,
            "-c",
            f"import zlib; print(open(zlib.decompress({compressed_repr}).decode()).read())",
        ]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_bypass_pre_imported_os_system(tmp_path: Path) -> None:
    """Verify that pre-importing os.system before HarnessGuard is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")
    out_file = tmp_path / "out.txt"

    from os import system as pre_imported_system

    with HarnessGuard():
        # Calling normal os.system is blocked
        with pytest.raises(PermissionError):
            os.system(f"echo {sensitive_file}")

        # Calling pre_imported_system is also blocked by audit hooks!
        cmd_str = (
            f"type {sensitive_file} > {out_file}"
            if sys.platform == "win32"
            else f"cat {sensitive_file} > {out_file}"
        )
        with pytest.raises(PermissionError):
            pre_imported_system(cmd_str)


def test_bypass_base64_obfuscation_no_keywords(tmp_path: Path) -> None:
    """Placeholder for base64 obfuscation without keywords."""
    pass


def test_bypass_split_base64_no_keywords(tmp_path: Path) -> None:
    """Verify that splitting base64 string into pieces of length < 8 is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    import base64

    path_str = str(sensitive_file)
    chunks = [path_str[i : i + 3] for i in range(0, len(path_str), 3)]
    b64_chunks = [base64.b64encode(c.encode("utf-8")).decode("utf-8") for c in chunks]

    for bc in b64_chunks:
        assert len(bc) < 8

    b64_chunks_repr = repr(b64_chunks)

    with HarnessGuard():
        cmd = [
            sys.executable,
            "-c",
            f"import binascii; f = getattr(binascii, bytes([97, 50, 98, 95, 98, 97, 115, 101, 54, 52]).decode()); path = ''.join(f(x).decode() for x in {b64_chunks_repr}); print(open(path).read())",
        ]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_bypass_sqlite_attach(tmp_path: Path) -> None:
    """Verify that SQLite ATTACH DATABASE is blocked."""
    sensitive_db = tmp_path / "secret_credential.db"
    import sqlite3

    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content')")
    conn.commit()
    conn.close()

    with HarnessGuard():
        with pytest.raises(PermissionError):
            sqlite3.connect(sensitive_db)

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(f"ATTACH DATABASE '{sensitive_db}' AS subdb")
        conn.close()


def test_bypass_windows_cmd_env_concat(tmp_path: Path) -> None:
    """Verify that Windows CMD environment variable concatenation is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    if sys.platform != "win32":
        pytest.skip("This test is for Windows platforms.")

    path_str = str(sensitive_file)
    parts = [path_str[i : i + 3] for i in range(0, len(path_str), 3)]

    keywords = ["credential", "secret", "private_key", "password", "api_key", "token", ".env"]
    for p in parts:
        for kw in keywords:
            assert kw not in p.lower()

    cmd_parts = "&& ".join(f"set P{i}={part}" for i, part in enumerate(parts))
    var_expansion = "".join(f"%P{i}%" for i in range(len(parts)))
    cmd_str = f'cmd.exe /c "{cmd_parts}&& call type \\"{var_expansion}\\""'

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(cmd_str, shell=True, capture_output=True, text=True, check=True)


def test_bypass_unix_shell_env_concat(tmp_path: Path) -> None:
    """Verify that Unix shell environment variable concatenation is blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    if sys.platform == "win32":
        pytest.skip("This test is for Unix platforms.")

    path_str = str(sensitive_file)
    parts = [path_str[i : i + 3] for i in range(0, len(path_str), 3)]

    keywords = ["credential", "secret", "private_key", "password", "api_key", "token", ".env"]
    for p in parts:
        for kw in keywords:
            assert kw not in p.lower()

    cmd_parts = "; ".join(f"P{i}='{part}'" for i, part in enumerate(parts))
    var_expansion = "".join(f"$P{i}" for i in range(len(parts)))
    cmd_str = f'{cmd_parts}; cat "{var_expansion}"'

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(cmd_str, shell=True, capture_output=True, text=True, check=True)


def test_bypass_raw_thread_spawning(tmp_path: Path) -> None:
    """Verify that raw thread spawning (_thread.start_new_thread) passes the guards to the subthread."""
    import _thread
    import time

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    thread_exceptions = []

    def thread_target() -> None:
        try:
            with open(sensitive_file) as f:
                f.read()
        except Exception as e:
            thread_exceptions.append(e)

    with HarnessGuard():
        _thread.start_new_thread(thread_target, ())
        time.sleep(0.2)

    assert len(thread_exceptions) == 1
    assert isinstance(thread_exceptions[0], PermissionError)


def test_bypass_sqlite_comment_attach(tmp_path: Path) -> None:
    """Verify that comment-based sqlite ATTACH bypasses are blocked."""
    sensitive_db = tmp_path / "secret_credential.db"
    import sqlite3

    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content')")
    conn.commit()
    conn.close()

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        # Block comments spacing
        with pytest.raises(PermissionError):
            conn.execute(f"ATTACH/**/DATABASE/**/'{sensitive_db}'/**/AS/**/subdb")
        # Line comments spacing
        with pytest.raises(PermissionError):
            conn.execute(f"ATTACH -- comment\nDATABASE '{sensitive_db}' AS subdb2")
        conn.close()


def test_bypass_ast_arithmetic_operators(tmp_path: Path) -> None:
    """Verify that addition operations on constant string and integer segments in AST scan are blocked."""
    with HarnessGuard():
        # Addition of strings
        cmd_str_add = [sys.executable, "-c", "import sys; print('sec' + 'ret')"]
        with pytest.raises(PermissionError):
            subprocess.run(cmd_str_add, capture_output=True, text=True, check=True)

        # Addition of character codes chr(115) + chr(101) + chr(99) + chr(114) + chr(101) + chr(116)
        cmd_chr_add = [
            sys.executable,
            "-c",
            "import sys; print(chr(115) + chr(101) + chr(99) + chr(114) + chr(101) + chr(116))",
        ]
        with pytest.raises(PermissionError):
            subprocess.run(cmd_chr_add, capture_output=True, text=True, check=True)


def test_bypass_codecs_invalid_escape_sequence(tmp_path: Path) -> None:
    """Verify that invalid escape sequences like \\G do not bypass sensitive keyword checks."""
    with HarnessGuard():
        # String containing '\Gsecret'
        cmd = [sys.executable, "-c", "print('\\Gsecret')"]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_bypass_env_variable_encoding(tmp_path: Path) -> None:
    """Verify that obfuscated sensitive keywords in environment variables are blocked."""
    import base64

    # Base64 encoded 'secret'
    b64_secret = base64.b64encode(b"secret").decode("utf-8")

    with HarnessGuard():
        # Check base64 obfuscation in environment variable
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", "import os; print(os.environ.get('MY_ENV'))"],
                env={"MY_ENV": b64_secret},
            )


def test_no_false_positive_on_os_environ() -> None:
    """Verify that accessing os.environ or having 'environ' keyword doesn't raise PermissionError."""
    with HarnessGuard():
        # Accessing os.environ should not raise PermissionError
        env = os.environ
        assert env is not None
        # Subprocess running script referencing os.environ should not raise PermissionError
        subprocess.run(
            [sys.executable, "-c", "import os; print(os.environ.get('PATH'))"],
            capture_output=True,
            text=True,
            check=True,
        )


def test_bypass_pre_loaded_ctypes(tmp_path: Path) -> None:
    """Verify that pre-loading ctypes before HarnessGuard allows file writing and execution bypass."""
    import sys

    if sys.platform != "win32":
        pytest.skip("ctypes kernel32 bypass is configured for Windows.")

    import ctypes

    # Load kernel32 before entering the guard
    kernel32 = ctypes.windll.kernel32

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-ctypes")

    # We will write to a temp file
    temp_file = tmp_path / "temp_bypass_exec.py"

    GENERIC_WRITE = 0x40000000
    CREATE_ALWAYS = 2
    FILE_ATTRIBUTE_NORMAL = 0x80

    with HarnessGuard():
        # Open via pre-loaded ctypes (blocked by ctypes audit hook)
        with pytest.raises(PermissionError):
            kernel32.CreateFileW(
                str(temp_file), GENERIC_WRITE, 0, None, CREATE_ALWAYS, FILE_ATTRIBUTE_NORMAL, None
            )


def test_bypass_floor_div_map(tmp_path: Path) -> None:
    """Verify that reconstructing sensitive keyword using FloorDiv and map in subprocess bypasses the guard."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-floordiv")

    # Path to sensitive file: we can pass it using char codes
    path_str = str(sensitive_file)
    char_codes = [ord(c) for c in path_str]
    # Represent each code as `c * 2 // 2`
    expr_list = [f"{c * 2} // 2" for c in char_codes]
    expr_str = ", ".join(expr_list)

    py_code = f"import os; print(open(bytes(list(map(int, [{expr_str}]))).decode()).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_bypass_sqlite_char_attach(tmp_path: Path) -> None:
    """Verify that SQLite ATTACH DATABASE can be bypassed using char() concatenation."""
    import sqlite3

    sensitive_db = tmp_path / "secret_credential.db"

    # Create the db
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content-char')")
    conn.commit()
    conn.close()

    db_path_str = str(sensitive_db).replace("\\", "/")
    char_expr = " || ".join(f"char({ord(c)})" for c in db_path_str)
    sql_attach = f"ATTACH DATABASE ({char_expr}) AS subdb"

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(sql_attach)
        conn.close()


def test_bypass_windows_cmd_quoted_env_concat(tmp_path: Path) -> None:
    """Verify that quoted environment variable concatenation (e.g. set "P0=val") is correctly blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("quoted-env-concat-secret")

    if sys.platform != "win32":
        pytest.skip("Windows CMD specific test")

    path_str = str(sensitive_file)
    parts = [path_str[i : i + 3] for i in range(0, len(path_str), 3)]

    cmd_parts = "&& ".join(f'set "P{i}={part}"' for i, part in enumerate(parts))
    var_expansion = "".join(f"%P{i}%" for i in range(len(parts)))
    cmd_str = f'cmd.exe /c "{cmd_parts}&& call type \\"{var_expansion}\\""'

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(cmd_str, shell=True, capture_output=True, text=True, check=True)


def test_bypass_windows_cmd_caret_escape(tmp_path: Path) -> None:
    r"""Verify that environment variables set with caret escapes (e.g. set P0=C:\My ^& Path) are correctly parsed/cleaned and blocked."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("caret-escape-env-secret")

    if sys.platform != "win32":
        pytest.skip("Windows CMD specific test")

    path_str = str(sensitive_file)
    # Caret-escape some characters in parts
    parts = []
    for i in range(0, len(path_str), 3):
        chunk = path_str[i : i + 3]
        # Insert a caret escape before a character to obfuscate
        if len(chunk) > 1:
            chunk = chunk[0] + "^" + chunk[1:]
        parts.append(chunk)

    cmd_parts = "&& ".join(f"set P{i}={part}" for i, part in enumerate(parts))
    var_expansion = "".join(f"%P{i}%" for i in range(len(parts)))
    cmd_str = f'cmd.exe /c "{cmd_parts}&& call type \\"{var_expansion}\\""'

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(cmd_str, shell=True, capture_output=True, text=True, check=True)
