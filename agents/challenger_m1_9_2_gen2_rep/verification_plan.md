# Verification and Stress Test Plan

This document outlines the step-by-step plan for verifying the security bypass fixes and finding new gaps in `packages/ccba-legal-intel/ccba_legal/harness.py`.

## Verification Steps

### Step 1: Base Test Execution
- Run the full pytest suite for `packages/ccba-legal-intel`.
- **Verification Condition:** All existing unit tests pass, except for verified failures of active bypasses.

### Step 2: Investigation of Known Failures (Gen 3)
- Investigate the failures in `test_harness_adversarial_challenger_gen3.py` (specifically `test_sys_argv_bypass` and `test_py_launcher_bypass`).
- Confirm if these tests demonstrate successful bypasses (vulnerabilities).
- **Verification Condition:** If these tests fail because they "DID NOT RAISE PermissionError", it confirms the presence of these bypasses (vulnerabilities).

### Step 3: Edge Case & Obfuscation Design (Gen 4)
- Formulate new obfuscation bypasses:
  1. JSON unicode escapes (`\u` notation) dynamically decoded in python child process.
  2. SQLite custom functions called inside SQL to dynamically resolve sensitive paths.
  3. PowerShell command-line string concatenation.
  4. Fully obfuscated getattr-replace call (no sensitive substrings in any literal).
- **Verification Condition:** Add these to `test_harness_adversarial_challenger_gen4.py` and run them.

### Step 4: Empirical Run & Diagnosis
- Execute pytest to verify which bypasses successfully execute and which are blocked.
- Document the results.
- **Verification Condition:** Any test that fails because it "DID NOT RAISE PermissionError" is a confirmed bypass. Any test that passes (raises `PermissionError`) is blocked by `HarnessGuard`.
