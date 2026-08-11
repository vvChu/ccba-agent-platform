# 26. Isolated Test Execution and Timeout Policy for Agent Stability

Date: 2026-08-11
Status: Approved

## Context
During test execution across large package suites (such as `ccba-legal-intel`), running unscoped or monolithic test commands (`pytest`) frequently led to sub-process hangs, CPU locks, or inter-test state leakage. This caused external timeout cancellations (`User Cancelled Agent Execution`), disrupting agent sessions and requiring manual task restarts.

## Decisions

1. **Isolated Sub-process Execution**:
   - Test suites MUST be executed per test file in isolated Python sub-processes (`python .md/scripts/run_isolated_tests.py`).
   - Monolithic unscoped pytest invocations across multi-package repos are strictly prohibited in automated workflows.

2. **Singleton Process Lock (`ensure_single_instance()`)**:
   - The isolated test runner MUST enforce a singleton process lock to prevent concurrent runner invocations.
   - Process cleanup routines MUST explicitly preserve both current process (`os.getpid()`) and parent host process (`os.getppid()`).

3. **Per-File Timeout & Suite Non-Blocking Policy**:
   - Each test file receives a strict 5-second execution deadline (`timeout=5`).
   - If a test file times out, the runner kills the isolated sub-process, logs `TIMEOUT` for that specific file, and continues scanning all remaining test files to provide a complete benchmark report (`.md/wayfinder/test_benchmark_report.md`).

## Consequences
- Completely eliminates Agent session freezes caused by deadlocked or slow test execution.
- Enables clear, actionable benchmark reports pinpointing exact failing or timing out test files.
- Protects Agent Server host stability and resource utilization.
