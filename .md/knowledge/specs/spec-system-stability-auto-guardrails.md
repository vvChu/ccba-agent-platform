# Spec: System Stability & Auto-Guardrails for Async Tasks (Hệ Thống Tự Động Ổn Định & Chống Nghẽn Tiến Trình Ngầm)

## Problem Statement

When AI Agents execute complex workflows (such as `/ccba-eval-gate`, `/ccba-implement`, or `/ccba-create-pr`), heavy test runners (`run_harness_evals.py`) may be launched multiple times concurrently in background tasks. Running multiple full-suite evaluation processes in parallel exhausts system CPU and RAM, causing the IDE Extension Host to freeze or drop heartbeat connections. This results in execution timeouts, forced agent cancellations (`User cancelled agent execution`), and unexpected restarts of the Antigravity Agent extension.

## Solution

Implement an automated, two-layer defense architecture to ensure system stability and zero process crashes:
1. **Source Code Level (Process Lock & Auto-Cleanup)**:
   - Add a Singleton Process Lock (`ensure_single_instance()`) in `run_harness_evals.py` using process iteration (`psutil` / `wmic`) to automatically detect and terminate duplicate or stale instances before running new evaluations.
   - Upgrade `session_cleanup.py` with `clean_zombies()` to automatically prune orphan `pytest` and `safe_runner` processes older than 15 minutes.
   - Enforce smart scoped diff checking (checking modified files only) as the default behavior in `run_harness_evals.py`.
2. **Policy & Guardrail Level**:
   - Update `AGENTS.md` and workflow specifications to mandate Bounded Async Task execution, preventing agents from spawning duplicate background tasks for identical test runners.

## User Stories

1. As a platform developer, I want `run_harness_evals.py` to automatically terminate duplicate evaluation processes before execution, so that my CPU and RAM are never exhausted by redundant test suites.
2. As a DevOps engineer, I want `session_cleanup.py` to automatically clean up orphan zombie processes left behind by crashed sessions, so that background tasks do not linger indefinitely.
3. As a developer running CI gates, I want `run_harness_evals.py` to default to checking git diffs rather than the full codebase, so that feedback is fast and resource consumption is minimized.
4. As an AI Agent, I want explicit Execution Guardrails in `AGENTS.md`, so that I never invoke duplicate async background tasks that could crash the extension host.
5. As a system administrator, I want workspace health checks (disk space, RAM) to run prior to heavy background jobs, so that low-resource conditions are caught early.

## Implementation Decisions

- **Singleton Process Lock**:
  - Module: `scripts/run_harness_evals.py`
  - Logic: Iterates over system process tables (`psutil` primary, `wmic`/`taskkill` fallback on Windows) at entry point to match `run_harness_evals.py` command lines. If another PID is found, it sends a termination signal.
- **Orphan Zombie Cleanup**:
  - Module: `scripts/session_cleanup.py`
  - Logic: Scans active process creation timestamps using `time.time()`. Any process running `pytest` or `safe_runner` older than 15 minutes is automatically terminated.
- **Scoped Diff Default**:
  - Module: `scripts/run_harness_evals.py`
  - Logic: Resolves `get_git_modified_files()` via `git status` and `git diff`. Performs linter, formatter, typecheck, and unit test suites only on modified Python/Markdown files unless `--all` is explicitly set.
- **Execution Policy Integration**:
  - Module: `.agents/AGENTS.md`
  - Logic: Added explicit Bounded Async Task Policy and invalid args circuit breaker rules in Section 4.

## Testing Decisions

- **Behavioral Testing Seams**:
  - `scripts/run_harness_evals.py`: Tested via `--no-test` execution to verify singleton lock detection and graceful gate reporting.
  - `scripts/session_cleanup.py`: Tested via `--execute` flag to verify disk space health check, branch/worktree pruning, and zombie process cleanup.
- **External Behavior Verification**:
  - Execute `run_harness_evals.py` while another background process is simulated to confirm auto-termination without throwing unhandled exceptions.
  - Verify that normal execution exits with code 0 on success and non-zero on failure without leaking background child processes.

## Out of Scope

- Modifying core VS Code Extension Host process scheduling or IPC communication mechanisms.
- Replacing `pytest` or `ruff` with alternative testing/linting engines.

## Further Notes

- All changes maintain full backward compatibility with existing CI/CD pipelines.
- The `ensure_single_instance()` function has cross-platform fallback support for environments where `psutil` is not pre-installed.
