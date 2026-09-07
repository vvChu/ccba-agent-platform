# ccba-harness Package Guidance

Deterministic evaluation framework for benchmarking AI Agent skills and workflows.

- **Public Deep Seams**: `from ccba_harness import HarnessEngine, HarnessGuard, FileMutexLock, HarnessLocal, HarnessState, EvalRunner, EvalItem, EvalReport, ExactMatchScorer, RegexScorer, JsonSchemaScorer, LengthBoundsScorer, LLMRubricScorer, SkillValidator, SkillAuditIssue`.
- **CLI Commands**: `ccba-harness validate-skill [paths...] [--file FILE] [--root ROOT] [--strict]`.
- **Contracts**: Evaluations must be deterministic and isolated with explicit timeout guards. Fast unit tests must maintain SLA < 2.0s.
- **Scoped Tests**: `pytest packages/ccba-harness/tests`
