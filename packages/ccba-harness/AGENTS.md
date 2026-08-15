# ccba-harness Package Guidance

Deterministic evaluation framework for benchmarking AI Agent skills and workflows.

- **Public Deep Seams**: `from ccba_harness import HarnessEngine, HarnessGuard, FileMutexLock, HarnessLocal`.
- **Contracts**: Evaluations must be deterministic and isolated with explicit timeout guards.
- **Scoped Tests**: `pytest packages/ccba-harness/tests`
