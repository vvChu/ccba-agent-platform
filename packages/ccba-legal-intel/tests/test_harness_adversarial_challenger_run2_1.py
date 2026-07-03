import codecs
import sqlite3
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import pytest
from ccba_legal.harness._guard import HarnessGuard


def test_in_hook_flag_tampering_bypass(tmp_path):
    """Bypass 1: Tampering with the _local.in_hook flag.

    By importing the internal thread-local object from ccba_legal.harness and
    setting _local.in_hook = True, we trick all check functions and hooks into
    thinking they are executing inside a hook call, which bypasses all security checks.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("in-hook-bypass-content")

    import os

    import ccba_legal.harness

    with HarnessGuard():
        # Set the hook flag to True
        ccba_legal.harness._local.in_hook = True
        with pytest.raises(PermissionError):
            fd = os.open(sensitive_file, os.O_RDONLY)
            os.close(fd)


def test_thread_pool_executor_pre_existing_bypass(tmp_path):
    """Bypass 2: Thread pool concurrency bypass.

    Worker threads in a ThreadPoolExecutor created before entering the HarnessGuard
    do not have the active guard in their thread-local storage, allowing them to
    completely bypass the guard's checks.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("thread-pool-bypass-content")

    # Create the thread pool executor before the guard is entered
    executor = ThreadPoolExecutor(max_workers=1)

    # Warm up the thread pool to ensure the worker thread is spawned
    executor.submit(lambda: None).result()

    def task():
        with open(sensitive_file) as f:
            return f.read()

    with HarnessGuard():
        with pytest.raises(PermissionError):
            executor.submit(task).result()

    executor.shutdown()


def test_sqlite_connection_base_class_method_override_blocked(tmp_path):
    """Bypass 3: SQLite ATTACH bypass via base class method override.

    HarnessGuard wraps connections using _Wrappedsqlite3Connection, but we can
    bypass the custom overridden methods (like execute) by calling the base class
    sqlite3.Connection.execute directly.
    However, the C-level audit hook in sys.addaudithook catches sqlite3.connect or ATTACH
    if it matches sensitive databases. Wait, actually, _audit_hook does NOT check
    sql queries unless they are attached via ATTACH in execute.
    Actually, let's verify if sqlite3.Connection.execute is caught.
    The test log shows:
      sqlite3.Connection.execute(conn, f"ATTACH DATABASE '{sensitive_db}' AS subdb")
      In packages/ccba-legal-intel/ccba_legal/harness.py:276: in execute: _check_sql_query(sql)
    This means the connection is still an instance of _Wrappedsqlite3Connection which inherits
    from sqlite3.Connection. The wrapper overrides execute, so calling sqlite3.Connection.execute
    still resolves to the C-level execute or wrapped execute?
    Wait, in Python, calling `sqlite3.Connection.execute(conn, sql)` on a subclass instance
    conn of `_Wrappedsqlite3Connection` where `_Wrappedsqlite3Connection` inherits from
    `_Originals.sqlite3_Connection` (which is `sqlite3.Connection` originally) will call
    `_Originals.sqlite3_Connection.execute`.
    Wait, the error traceback says:
      packages/ccba-legal-intel/tests/test_harness_adversarial_challenger_run2_1.py:88:
      _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
      packages/ccba-legal-intel/ccba_legal/harness.py:276: in execute
          _check_sql_query(sql)
    Aha! Since `sqlite3.connect` is wrapped and returns `_Wrappedsqlite3Connection`
    and `sqlite3.Connection` is set globally to `_Wrappedsqlite3Connection` (on line 1960),
    `sqlite3.Connection` IS `_Wrappedsqlite3Connection`!
    So `sqlite3.Connection.execute(conn, ...)` calls `_Wrappedsqlite3Connection.execute`!
    This is why it is blocked. This is a SUCCESSFUL block by the guard!
    Let's change our test expectation to assert that this is indeed blocked.
    """
    sensitive_db = tmp_path / "secret_credential.db"

    # Initialize the sensitive database
    conn = sqlite3.connect(sensitive_db)
    conn.execute("CREATE TABLE secrets (val TEXT)")
    conn.execute("INSERT INTO secrets VALUES ('sqlite-base-bypass')")
    conn.commit()
    conn.close()

    with HarnessGuard():
        conn = sqlite3.connect(":memory:")
        with pytest.raises(PermissionError):
            sqlite3.Connection.execute(conn, f"ATTACH DATABASE '{sensitive_db}' AS subdb")
        conn.close()


def test_sys_argv_bypass(tmp_path):
    """Bypass 4: Sys.argv concatenation bypass.

    By passing the path components of a sensitive path as separate command line
    arguments to a child python process, no single argument contains the sensitive keywords,
    bypassing the subprocess argument checks. The child process then concatenates them and reads the file.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("sys-argv-bypass-content")

    # None of these strings match the sensitive keywords
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


def test_py_launcher_bypass(tmp_path):
    """Bypass 5: Non-python cmd wrapper bypass using py launcher.

    Using the 'py' launcher on Windows instead of 'python' or 'sys.executable' causes
    is_python_cmd to be False, disabling Python-specific linter and AST checks in subprocesses.
    This allows us to use rot13/codecs obfuscation inside the subprocess script.
    """
    if sys.platform != "win32":
        pytest.skip("py launcher is a Windows-specific python tool")

    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("py-launcher-bypass-content")

    path_str = str(sensitive_file).replace("\\", "/")
    rot13_path = codecs.encode(path_str, "rot_13")

    py_code = f"import codecs; fn = codecs.decode('{rot13_path}', 'rot_13'); print(open(fn).read())"

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(["py", "-c", py_code], capture_output=True, text=True, check=True)


def test_ast_concatenation_with_junk_blocked(tmp_path):
    """Bypass 6: Interrupt AST constant concatenation using junk strings.

    Our attempt to use a junk variable in a python command (e.g. part1 = 'path'; junk = 'junk'; part2 = 'path')
    to evade AST scanning is blocked because the whole script text (the python command string) is
    checked by `_check_value_for_sensitive` as a raw string!
    Since `part2` contains `secret_credential.txt`, it contains the sensitive keyword `secret_credential`
    as a raw substring. Thus, `_is_text_sensitive` triggers on the raw argument text itself,
    and it raises a PermissionError before even evaluating AST!
    Let's change our test expectation to assert that this is blocked.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("ast-junk-bypass-content")

    path_str = str(sensitive_file).replace("\\", "/")
    half = len(path_str) // 2
    part1 = path_str[:half]
    part2 = path_str[half:]

    py_code = (
        f"part1 = {repr(part1)}; "
        f"junk = 'totally_innocent_junk_string_to_break_ast_dfs_concatenation'; "
        f"part2 = {repr(part2)}; "
        f"print(open(part1 + part2).read())"
    )

    with HarnessGuard():
        with pytest.raises(PermissionError):
            subprocess.run(
                [sys.executable, "-c", py_code], capture_output=True, text=True, check=True
            )


def test_builtins_open_flag_tampering_bypass_vulnerability(tmp_path):
    """Bypass Vector 1: builtins.open/io.open remains bypassable by setting _local.in_hook = True.

    Since _wrapped_builtins_open checks `getattr(_local, "in_hook", False)` instead of `_check_in_hook()`,
    any truthy value in `_local.in_hook` causes it to return the original open without running the guard checks.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("vulnerable-builtins-open-content")

    import ccba_legal.harness

    with HarnessGuard():
        # Set the hook flag to True
        ccba_legal.harness._local.in_hook = True
        try:
            # Now, with the bypass blocked, this must raise PermissionError
            with pytest.raises(PermissionError):
                with open(sensitive_file) as f:
                    f.read()
        finally:
            ccba_legal.harness._local.in_hook = None


def test_compiled_frame_tampering_bypass(tmp_path):
    """Bypass Vector 2: os.open/sqlite3/FileIO bypassable by executing compiled code under 'harness.py'.

    _check_in_hook checks if any stack frame filename matches 'harness.py' and checks if
    _local.in_hook is exactly _HOOK_TOKEN. We can get _HOOK_TOKEN from the module namespace, and compile
    our payload with filename 'harness.py' so that _check_in_hook returns True and lets us bypass all guards.
    """
    sensitive_file = tmp_path / "secret_credential.txt"
    sensitive_file.write_text("vulnerable-compiled-code-content")

    import ccba_legal.harness

    with HarnessGuard():
        # Set the hook flag to the exact internal _HOOK_TOKEN object
        ccba_legal.harness._local.in_hook = ccba_legal.harness._HOOK_TOKEN
        try:
            # Compile a payload with filename 'harness.py'
            py_code = f"import os; fd = os.open(r'{sensitive_file}', os.O_RDONLY); data = os.read(fd, 100); os.close(fd); print(data.decode('utf-8'))"
            compiled = compile(py_code, "harness.py", "exec")

            import io
            import sys

            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                # With the bypass blocked, executing this must raise PermissionError
                with pytest.raises(PermissionError):
                    exec(compiled, {})
            finally:
                sys.stdout = old_stdout
        finally:
            ccba_legal.harness._local.in_hook = None
