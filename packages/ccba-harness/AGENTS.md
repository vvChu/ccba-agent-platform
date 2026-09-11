# ccba-harness Package Guidance

Deterministic evaluation framework for benchmarking AI Agent skills and workflows.

- **Public Deep Seams**: `from ccba_harness import HarnessEngine, HarnessGuard, FileMutexLock, HarnessLocal, HarnessState, DetachedExecutionEngine, EvalRunner, EvalItem, EvalReport, ExactMatchScorer, RegexScorer, JsonSchemaScorer, LengthBoundsScorer, LLMRubricScorer, SkillValidator, SkillAuditIssue, ArchitectureTier, GPIMetrics, DecisionRequest, DecisionResult, calculate_gpi, evaluate_two_stage_decision, GPI_STANDALONE_THRESHOLD`.
- **CLI Commands**: `ccba-harness validate-skill [paths...] [--file FILE] [--root ROOT] [--strict] [--enforce-gpi]` and `ccba-harness evaluate-gpi [--file FILE] [--name NAME] [--s S] [--k K] [--a A] [--p P] [--deterministic] [--orchestrated] [--parent PARENT] [--json]`.
- **Contracts**: Evaluations must be deterministic and isolated with explicit timeout guards. Two-Stage Granularity Decision Framework and GPI calculation enforce RES-2026-ARCH-001 v1.2 architecture rules. Fast unit tests must maintain SLA < 2.0s.
- **Scoped Tests**: `pytest packages/ccba-harness/tests`
