# 26. Isolated Test Execution and Timeout Policy for Agent Stability

Date: 2026-08-11
Status: Approved (Revised 2026-08-12)

## Context
During test execution across large package suites (such as `ccba-legal-intel` with 22 test files), running unscoped or monolithic test commands (`pytest`) frequently led to sub-process hangs, CPU locks, or inter-test state leakage. This caused external timeout cancellations (`User Cancelled Agent Execution`), disrupting agent sessions and requiring manual task restarts.

## Decisions

1. **Isolated Sub-process Execution**:
   - Test suites MUST be executed via the centralized runner: `python scripts/run_isolated_tests.py -p <package-name>` (located at `scripts/eval/run_isolated_tests.py`).
   - Monolithic unscoped pytest invocations across multi-package repos are strictly prohibited in automated workflows.

2. **Process Safety via Centralized Utilities**:
   - All test runner scripts MUST use utilities from `scripts.eval.process_safety` (`ensure_single_instance`, `kill_process_tree`, `get_venv_python`) as mandated by `scripts/README.md`.
   - Process cleanup routines MUST explicitly preserve both current process (`os.getpid()`) and parent host process (`os.getppid()`).
   - Scripts MUST NOT re-implement singleton locks via file-based mechanisms; use the `psutil`-based `ensure_single_instance()` which verifies process liveness.

3. **Dual-Layer Timeout Policy**:
   - **Layer 1 (subprocess):** The runner enforces a configurable subprocess timeout (default `--timeout 60`) that kills the entire pytest sub-process if it exceeds the deadline.
   - **Layer 2 (pytest-timeout):** Individual test functions are governed by `pytest-timeout` configured in each package's `pyproject.toml` (e.g., `timeout = 30` for `ccba-legal-intel`).
   - Layer 1 timeout MUST always be greater than Layer 2 to avoid conflicts. Layer 2 handles individual slow tests gracefully; Layer 1 is the hard backstop against full process hangs.

## Consequences
- Completely eliminates Agent session freezes caused by deadlocked or slow test execution.
- Centralizes test infrastructure in `scripts/eval/` following the 2-tier architecture, avoiding duplicate scripts in `.md/scripts/`.
- Protects Agent Server host stability and resource utilization.
