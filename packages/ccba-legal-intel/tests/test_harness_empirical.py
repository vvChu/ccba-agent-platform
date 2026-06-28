import ctypes
import sqlite3
import subprocess
import sys

import pytest
from ccba_legal.harness import HarnessGuard


def get_short_path_name(long_name):
    buffer = ctypes.create_unicode_buffer(260)
    ctypes.windll.kernel32.GetShortPathNameW(str(long_name), buffer, 260)
    return buffer.value


def test_bypass_reversed_string_obfuscation(tmp_path):
    """Verify that a subprocess using reversed string reconstruction bypasses the guard and reads a sensitive file."""
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("super-secret-content")

    path_str = str(sensitive_file)
    reversed_path = path_str[::-1]

    with HarnessGuard():
        cmd = [
            sys.executable,
            "-c",
            f"import sys; path = {repr(reversed_path)}[::-1]; print(open(path).read())",
        ]
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True)


def test_bypass_8dot3_short_names(tmp_path):
    """Verify that using Windows 8.3 short names bypasses the guard's keyword checking."""
    if sys.platform != "win32":
        pytest.skip("8.3 short name behavior is Windows specific.")

    sensitive_file = tmp_path / "my_token_store.txt"
    sensitive_file.write_text("secret-token-value")

    short_path = get_short_path_name(sensitive_file)
    print(f"Long path: {sensitive_file}")
    print(f"Short path: {short_path}")

    if short_path.lower() == str(sensitive_file).lower():
        pytest.skip("8.3 short names are not enabled or generated on this volume.")

    keywords = ["credential", "secret", "private_key", "password", "api_key", "token"]
    for kw in keywords:
        assert kw not in short_path.lower(), f"Keyword '{kw}' still in short path '{short_path}'"

    with HarnessGuard():
        # Opening via long name is blocked
        with pytest.raises(PermissionError):
            open(sensitive_file)

        # Opening via short name: if bypassed, it will succeed and read the file
        with pytest.raises(PermissionError):
            with open(short_path) as f:
                f.read()


def test_bypass_sqlite_attach_expression(tmp_path):
    """Verify that using string concatenation in SQLite ATTACH DATABASE bypasses the guard."""
    sensitive_db = tmp_path / "my_secret_db.db"

    # Create the db and write some content
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('db-secret-content')")
    conn.commit()
    conn.close()

    # The path to the db
    db_path_str = str(sensitive_db)

    # Split the path right in the middle of 'secret': 'se' and 'cret_db.db'
    idx = db_path_str.lower().find("secret")
    assert idx != -1, f"Path '{db_path_str}' must contain 'secret'"
    split_idx = idx + 2  # split right after 'se'

    part1 = db_path_str[:split_idx]
    part2 = db_path_str[split_idx:]

    # Ensure neither part has the full keywords
    keywords = ["credential", "secret", "private_key", "password", "api_key", "token"]
    for kw in keywords:
        assert kw not in part1.lower()
        assert kw not in part2.lower()

    with HarnessGuard():
        # Connecting directly is blocked
        with pytest.raises(PermissionError):
            sqlite3.connect(sensitive_db)

        # Attaching via expression concatenation is also blocked
        conn = sqlite3.connect(":memory:")
        sql_attach = f"ATTACH DATABASE '{part1}' || '{part2}' AS subdb"

        with pytest.raises(PermissionError):
            conn.execute(sql_attach)
        conn.close()
