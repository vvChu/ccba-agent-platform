import os
import sqlite3
import subprocess
import sys
import threading

import pytest

from ccba_legal.harness import HarnessGuard


def test_unicode_normalization_bypass(tmp_path, monkeypatch):
    """Unicode/Normalization trick:
    Use unicodedata.normalize inside python subprocess to construct the sensitive path.
    The AST scanner and regex look for ASCII keywords like 'secret'.
    By using 'secr\u212ft' (where \u212f is the script small e), we bypass keyword matching,
    but unicodedata.normalize('NFKC', ...) converts it to 'secret' at runtime in the subprocess.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("unicode-secret")

    # Character U+212F is script small e. Normalized to NFKC, it becomes 'e'.
    # File name will normalize to 'secret.txt'
    obfuscated_name = "secr\u212ft.txt"

    py_code = (
        f"import unicodedata; "
        f"fn = unicodedata.normalize('NFKC', '{obfuscated_name}'); "
        f"print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_env_var_split_bypass(tmp_path, monkeypatch):
    """Environment variable manipulation:
    Split the sensitive path into multiple environment variables, none of which contain
    sensitive keywords individually. Reconstruct them in the subprocess.
    This bypasses both the command string checks and environment variable checks.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("env-secret")

    # Split 'secret.txt' so no individual part matches sensitive keywords
    env = {"PART1": "secre", "PART2": "t.txt"}

    py_code = "import os; fn = os.environ['PART1'] + os.environ['PART2']; print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code],
                env={**os.environ, **env},
                capture_output=True,
                text=True,
                check=True,
            )


def test_sqlite_attach_concat_expression_bypass(tmp_path, monkeypatch):
    """SQLite ATTACH complex expression/concatenation bypass:
    Combine subclassing string (to bypass '||' checks in the 'if "ATTACH" in sql.upper()' block)
    with string concatenation (to hide the sensitive 'secret_db.db' keyword from the
    regex-based path extractor).
    """
    monkeypatch.chdir(tmp_path)
    sensitive_db = "secret_db.db"

    # Create the database and table
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('attach-concat-secret')")
    conn.commit()
    conn.close()

    class QueryStr(str):
        def upper(self):
            return "SELECT 1"

    # SQLite evaluates 'sec' || 'ret_db.db' to 'secret_db.db'.
    sql_query = QueryStr("ATTACH DATABASE 'sec' || 'ret_db.db' AS subdb")

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            conn.execute(sql_query)
        conn.close()


def test_base64_whitespace_bypass(tmp_path, monkeypatch):
    """Base64 obfuscation:
    Insert whitespace inside the Base64 string.
    Python's base64.b64decode ignores whitespace, but the regex scanner in the guard
    splits it into separate non-sensitive candidates.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("base64-secret")

    # Base64 for "secret.txt" is: "c2VjcmV0LnR4dA=="
    # Split with spaces: "c2Vj cmV0 LnR4 dE=="
    obfuscated_b64 = "c2Vj cmV0 LnR4 dE=="

    py_code = (
        f"import base64; fn = base64.b64decode('{obfuscated_b64}').decode(); print(open(fn).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_fs_hardlink_bypass(tmp_path, monkeypatch):
    """File system hardlink bypass:
    Create a hard link of a sensitive file to a benign name BEFORE entering the guard.
    Since hard links do not resolve back to their alternative paths, the guard's
    path-based checks see only the benign name and permit opening the file.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("hardlink-secret")

    benign_link = "benign_hardlink.txt"
    os.link(sensitive_file, benign_link)

    with HarnessGuard():
        with pytest.raises(PermissionError):
            with open(benign_link) as f:
                f.read()


def test_pre_existing_thread_bypass(tmp_path, monkeypatch):
    """Thread concurrency bypass:
    Start a thread BEFORE entering the HarnessGuard context.
    Since HarnessGuard's security hooks and audit hooks are controlled by thread-local
    active guards list, a pre-existing thread that does not copy any active guards list
    can open any sensitive file completely unrestricted, even while HarnessGuard is active
    on another thread.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("pre-thread-secret")

    opened_content = None
    exception_raised = None
    thread_ready = threading.Event()
    guard_entered = threading.Event()

    def worker():
        thread_ready.set()
        # Wait until parent enters HarnessGuard
        guard_entered.wait()
        try:
            with open(sensitive_file) as f:
                nonlocal opened_content
                opened_content = f.read()
        except Exception as e:
            nonlocal exception_raised
            exception_raised = e

    # Start thread BEFORE entering HarnessGuard
    t = threading.Thread(target=worker)
    t.start()
    thread_ready.wait()

    # Enter HarnessGuard on parent thread
    with HarnessGuard():
        guard_entered.set()
        t.join()

    # The bypass fails if the pre-existing thread raised PermissionError
    assert opened_content is None
    assert isinstance(exception_raised, PermissionError)


def test_powershell_obfuscation_bypass(tmp_path, monkeypatch):
    """PowerShell interpreter obfuscation bypass:
    Use PowerShell string concatenation to reconstruct the sensitive path.
    Since PowerShell is a native shell interpreter, it doesn't load Python's sitecustomize.py,
    and we bypass the parent process's static command checks.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("powershell-secret")

    # In PowerShell, 'secre' + 't.txt' evaluates to 'secret.txt'.
    cmd = ["powershell", "-Command", "$s = 'secre' + 't.txt'; Get-Content $s"]

    with HarnessGuard():
        # This bypass is blocked by HarnessGuard checking joined command string for shell interpreter
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_cmd_obfuscation_bypass(tmp_path, monkeypatch):
    """CMD variable replacement obfuscation bypass:
    Use CMD's variable substring substitution syntax %A:a=e% which is not parsed by
    the parent process's _reconstruct_shell_variables regex.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("cmd-secret")

    # cmd replaces 'a' with 'e' in 'secrat.txt' to get 'secret.txt'
    cmd = ["cmd", "/c", "set A=secrat.txt&& call type %A:a=e%"]

    with HarnessGuard():
        # This bypass is blocked by HarnessGuard reconstructing shell variables
        with pytest.raises(PermissionError):
            subprocess.run(cmd, capture_output=True, text=True, check=True)


def test_sqlite_vacuum_into_bypass(tmp_path, monkeypatch):
    """SQLite VACUUM INTO bypass:
    Use SQLite's VACUUM INTO statement to write database content to a sensitive path.
    Since it is not an ATTACH query, and writes via SQLite's internal C I/O,
    it completely bypasses the Python open/connect hooks.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        # This bypass is blocked by SQLite VACUUM INTO checks
        with pytest.raises(PermissionError):
            conn.execute(f"VACUUM INTO '{sensitive_file}'")
        conn.close()


def test_thread_local_state_manipulation_bypass(tmp_path, monkeypatch):
    """Thread-local state manipulation bypass:
    Manipulate _local.active_guards by setting it to a custom object that evaluates
    to True but has an empty iterator. This bypasses all file checks on the thread.
    """
    monkeypatch.chdir(tmp_path)
    sensitive_file = "secret.txt"
    with open(sensitive_file, "w") as f:
        f.write("thread-local-secret")

    from ccba_legal.harness import _local

    class FakeList:
        def __bool__(self):
            return True

        def __iter__(self):
            return iter([])

        def __len__(self):
            return 0

        def append(self, x):
            pass

        def remove(self, x):
            pass

    orig_guards = getattr(_local, "active_guards", None)
    try:
        with HarnessGuard():
            # Set active_guards to our FakeList
            _local.active_guards = FakeList()
            # This bypass is blocked because FakeList is rejected and we fall back to global guards.
            with pytest.raises(PermissionError):
                with open(sensitive_file) as f:
                    f.read()
    finally:
        if orig_guards is not None:
            _local.active_guards = orig_guards
        else:
            if hasattr(_local, "active_guards"):
                delattr(_local, "active_guards")

