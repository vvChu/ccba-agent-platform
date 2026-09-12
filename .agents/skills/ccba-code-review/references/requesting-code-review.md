---
name: requesting-code-review
description: Use when completing tasks, implementing major features, or before merging to verify work meets requirements - dispatches review subagents to review implementation against plan or requirements before proceeding
---

# Requesting Code Review

Dispatch review subagents (Standards Worker & Spec Worker) to catch issues before they cascade.

**Core principle:** Scout first, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**0. Scout edge cases first:**
```
Before dispatching review subagents, scout edge cases to find:
- Files affected by changes (not just modified files)
- Data flow paths that could break
- Edge cases and boundary conditions
- Potential side effects

See: edge-case-scouting.md
```

**1. Get git SHAs:**
```powershell
$BASE_SHA = git rev-parse HEAD~1  # or origin/main
$HEAD_SHA = git rev-parse HEAD
```

**2. Dispatch review subagents:**

Dispatch review subagents (Standards Worker & Spec Worker) with read-only tools and Two-Layer Sub-Agent Guardrail.

**Placeholders:**
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary

**PR Review & Copilot Gating:**
When reviewing a Pull Request before merge:
```bash
# Audit Copilot review comments and unaddressed suggestions
python scripts/validation/audit_pr_comments.py --pr <pr_number>
```
If Copilot has pending feedback, address each finding before proceeding.

**Simplify Gate & Diff Complexity Threshold (RULE-2.10):**
Inspect diff size against complexity thresholds (`scripts/hooks/simplify.py`):
- Thresholds: Max 400 LOC total / Max 8 files / Max 200 LOC per file.
- If diff exceeds thresholds without approval, break into smaller commits or provide explicit rationale: `# APPROVED: <reason>`.

**3. Act on feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.
```powershell
$BASE_SHA = git log --grep="Task 1" -n 1 --format="%H"
$HEAD_SHA = git rev-parse HEAD
```

[Dispatch review subagents]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[Subagents return]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development:**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans:**
- Review after each batch (3 tasks)
- Get feedback, apply, continue

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification