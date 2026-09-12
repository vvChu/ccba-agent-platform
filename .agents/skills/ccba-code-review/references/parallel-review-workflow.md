# Parallel Review Workflow

Deeply analyze the review scope to list potential edge cases, then coordinate parallel review subagents to verify across two orthogonal axes: **Standards** (Coding style, smells, reliability) and **Spec** (Requirements, functional coverage, edge cases).

**IMPORTANT:** Activate needed skills. Ensure token efficiency. Maximize concision.

## Single-Writer Protocol & Sandbox Constraints

- **Single-Writer Protocol:** Only the coordinating agent writes to permanent project files, logs, and user reports. Subagents operate in strictly read-only mode and may only output draft reports to `.system_generated/scratch/` or return them via message.
- **Max Parallel Subagents:** Exactly 2 subagents (Standards Worker & Spec Worker) running simultaneously.
- **Two-Layer Sub-Agent Guardrail:** Subagent prompts must strictly prohibit spawning child sub-agents, modifying files, or proposing arbitrary command execution.

## Workflow

### 1. Edge Case & Scope Analysis

The coordinating agent analyzes the scope to identify critical risk areas:
- Inspect git diff and modified files across package seams.
- Brainstorm and list potential failure modes:
  - Null/undefined/empty scenarios
  - Boundary conditions (off-by-one, empty collections, maximum values)
  - Error handling gaps and uncaught exceptions
  - Concurrency, race conditions, async edge cases
  - Input validation holes and security boundaries
  - Resource leaks and unclosed file handles
  - Untested code paths

**Draft Output:**
Coordinator records potential edge cases into `.system_generated/scratch/edge_cases_scout.md`.

### 2. Spawn 2 Parallel Workers

Launch 2 dedicated review subagents simultaneously:

1. **Standards Worker (`research` / read-only subagent):**
   - **Scope:** Coding standards, Fowler smells, linting rules, type safety, error handling, KISS guidelines.
   - **Sandbox Output:** Writes draft findings to `.system_generated/scratch/standards_report.md`.
   - **Constraint:** Read-only inspection tools only.

2. **Spec Worker (`research` / read-only subagent):**
   - **Scope:** Spec compliance, functional requirements, missing features, scope creep, unhandled edge cases from Step 1.
   - **Sandbox Output:** Writes draft findings to `.system_generated/scratch/spec_report.md`.
   - **Constraint:** Read-only inspection tools only.

### 3. Aggregate Results

Coordinator reads `.system_generated/scratch/standards_report.md` and `.system_generated/scratch/spec_report.md` and compiles the unified verification report:

```markdown
## Edge Case Verification & Review Report

### Summary
- Total edge cases evaluated: X
- Handled: Y
- Unhandled (need fix): Z
- Partial: W

### Unhandled Edge Cases (Blocking)
| # | Category | Edge Case / Violation | File:Line | Status |
|---|----------|------------------------|-----------|--------|
```

### 4. Verification Review

After aggregation, verify accepted findings against the full scope:
- Re-check aggregated findings and unhandled edge cases.
- Confirm each blocking issue has a concrete file/line and reproduction path.
- Classify findings as Accept / Reject / Defer.

### 5. Deterministic Gate Check

Run deterministic verification before concluding:
```bash
python -m ccba_harness verify-patch --preset code --target <target_path>
```
If multi-package diff, fallback to `--preset ci`.

### 6. Final Report & User Decision

- Present summary of findings and deterministic verification status to user.
- If unhandled issues exist, ask user: "Found N unhandled edge cases / issues. Proceed with fixes? [Y/n]".
- If all checks pass, ask user: "Verification passed. Proceed to commit? [Y/n]".
