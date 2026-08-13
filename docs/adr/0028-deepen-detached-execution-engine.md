# 28. Deepen DetachedExecutionEngine in `scripts/eval/process_safety.py`

* Status: accepted
* Deciders: Antigravity AI, User
* Date: 2026-08-13

## Context and Problem Statement

`scripts/safe_runner.py` (208 LOC) and `scripts/safe_pytest.py` (118 LOC) were procedural CLI wrappers that managed detached subprocess execution, scratch log management, and git test file discovery independently. Furthermore, `safe_pytest.py` was invoking `safe_runner.py` via an extra Python subprocess invocation, adding unnecessary runtime overhead.

## Decision Drivers

* Need a unified, high-leverage process safety and execution module.
* Need to eliminate inter-script subprocess overhead when launching scoped tests.
* Maintain 100% backward CLI compatibility for all existing scripts and workflows.

## Considered Options

* Option A: Consolidate detached execution, log resolution, and scoped test discovery into `DetachedExecutionEngine` inside `scripts/eval/process_safety.py` and turn CLI scripts into thin delegates.
* Option B: Keep procedural functions across `safe_runner.py` and `safe_pytest.py`.

## Decision Outcome

Chosen Option: Option A.

### Positive Consequences

* Concentrates process safety, single-instance process locking, tree-killing, log cleanup, and detached execution into a single Deep Module `DetachedExecutionEngine`.
* Reduces `safe_runner.py` from 208 LOC to ~25 LOC and `safe_pytest.py` from 118 LOC to ~30 LOC.
* Eliminates inter-script Python subprocess overhead when triggering `safe_pytest`.
* All 5 CI Eval Gates pass 100%.
