# Hard Handoff Report - explorer_m1_10_1

## 1. Observation
We observed the following regarding the HarnessGuard implementation and adversarial tests:
- **Test execution result**: Running `python -m pytest tests/test_harness_adversarial_challenger_gen3.py tests/test_harness_adversarial_challenger_run2_2.py tests/test_harness_adversarial_challenger_gen5.py` fails with:
  ```
  FAILED tests/test_harness_adversarial_challenger_run2_2.py::test_unicode_normalization_bypass
  FAILED tests/test_harness_adversarial_challenger_run2_2.py::test_env_var_split_bypass
  FAILED tests/test_harness_adversarial_challenger_run2_2.py::test_sqlite_attach_concat_expression_bypass
  FAILED tests/test_harness_adversarial_challenger_run2_2.py::test_base64_whitespace_bypass
  FAILED tests/test_harness_adversarial_challenger_gen5.py::test_python_copied_exec_bypass
  ======================== 5 failed, 10 passed in 5.44s =========================
  ```
- **Windows Path corruption**: Running `shlex.split` on a Windows path with backslashes (verbatim command: `python -c "import shlex; path = 'C:\\Users\\chuvu\\AppData\\Local\\Temp\\pytest-of-chuvu\\pytest-315\\test_python_copied_exec_bypass0\\benign_runner.exe'; print(shlex.split(path))"`) results in the backslashes being stripped:
  ```
  ['C:UserschuvuAppDataLocalTemppytest-of-chuvupytest-315test_python_copied_exec_bypass0benign_runner.exe']
  ```
  This causes `os.path.isfile(path)` inside `_is_copied_python_executable` to return `False`.
- **Inherited Env Var pollution**: In `test_env_var_split_bypass`, when gộp environment variables via `combined_candidates.append("".join(sorted_values))`, it concatenates system environment variables (including `AI_GATEWAY_KEY` value `sk-spark-secure-key-2026`). Since the result contains both `secret.txt` (from the test) and `sk-spark-secure-key-2026`, it raises `PermissionError` on the entire combined string.
- **Missing Inode-based validation**: The function `_check_file_access` (packages/ccba-legal-intel/ccba_legal/harness.py:2356) and `_wrapped_os_open` (line 1920) only check `self._is_sensitive(file_str)` (path-based check). They never check `_sensitive_inodes`.
- **Single URL decode pass**: `_clean_and_decode_db_path` (line 231) uses a single `urllib.parse.unquote(path)` pass, failing to resolve double-escaped paths like `%2565`.

## 2. Logic Chain
1. **Windows path corruption in shlex**: Because `shlex.split` on Windows defaults to POSIX mode, it strips backslashes. This corrupts the executable path passed to `_is_copied_python_executable`, causing it to return `False` and bypass python subprocess analysis (Bypass 7).
2. **Strict executable size comparison**: Because `_is_copied_python_executable` requires the file size to be exactly `os.path.getsize(sys.executable)`, adding any dummy bytes to the copied python executable will bypass the size matching check.
3. **Blanket env var concatenation**: Because `_check_subprocess_call_internal` concatenates all environment variable values regardless of whether they were inherited or custom-passed, it causes false positives by scanning system secrets/keys. Only custom-passed environments (`env is not None`) should be combined.
4. **Lack of Inode-based verification**: Because hardlinks point to the same inode on disk but have different, benign filenames, path-based checks alone let hardlinks bypass the guard. Since we scan and collect sensitive inodes in `_sensitive_inodes`, we must verify the opened file's inode `(st_dev, st_ino)` against `_sensitive_inodes` (Bypass 6).
5. **Single-pass URI unquoting**: Because SQLite's URI filename parser can decode URI-escaped paths multiple times, a single-pass unquote check fails to detect double URL-encoded paths like `%2565` (Bypass 4).

## 3. Caveats
- The investigation was conducted on a Windows 10 host. The recommended fixes include standard cross-platform checks (e.g. `posix=(sys.platform != "win32")`).
- The directory walk in `_scan_for_sensitive_inodes()` is capped at 2000 files to maintain performance. If a sensitive file is deeper than the scan limit, its inode will not be collected, but path-based validation remains active as a fallback.

## 4. Conclusion
We recommend applying the following concrete fix strategies:
1. **Command argument splitting**: Update `_split_command_to_words` to use `posix=(sys.platform != "win32")` to preserve backslashes.
2. **Alternative launcher**: Support common launcher names (`poetry`, `uv`, etc.) in name checks.
3. **Environment variable split**: Only perform combined env var concatenation checks if `env is not None`.
4. **Double URL-encoding in SQLite**: Recursively decode database paths using a loop in `_clean_and_decode_db_path`.
5. **Whitespace Base64 obfuscation**: Clean the command arguments by stripping non-base64 chars before regex scanning.
6. **File system hardlink bypass**: Implement `(st_dev, st_ino) in _sensitive_inodes` verification in all file access interceptors.
7. **Alternative executable copy bypass**: In `_is_copied_python_executable`, check size within a 1MB tolerance and read the first 64KB of the binary to scan for `b"python"`.

Additionally, the adversarial tests `test_unicode_normalization_bypass`, `test_env_var_split_bypass`, `test_sqlite_attach_concat_expression_bypass`, and `test_base64_whitespace_bypass` must be wrapped with `pytest.raises(PermissionError)` to expect the security blocks.

## 5. Verification Method
- **Command to run**:
  `python -m pytest tests/test_harness_adversarial_challenger_gen3.py tests/test_harness_adversarial_challenger_run2_2.py tests/test_harness_adversarial_challenger_gen5.py`
- **Files to inspect**: `packages/ccba-legal-intel/ccba_legal/harness.py`
- **Invalidation conditions**: Any test failures (meaning a bypass is not blocked or a false positive is triggered).
