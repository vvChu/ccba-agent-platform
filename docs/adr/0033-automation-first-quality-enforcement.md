# 33. Automation-First Code Quality Enforcement and Instruction Pruning

Date: 2026-08-15
Status: Approved

## Context
Prior versions of `.agents/AGENTS.md` and global rules contained explicit textual instructions for standard programming practices (such as using f-strings, prohibiting bare excepts, enforcing snake_case naming, requiring Python type hints, and mandating docstrings). As verified in `pyproject.toml`, automated linters (Ruff `E,W,F,I,B,C4,UP` rulesets) and static type checkers (Mypy in strict mode) already enforce these constraints deterministically. Re-stating these obvious adages in prompt instructions consumed significant Instruction Budget (~150-200 instructions cap) without adding defensive value.

Following Matt Pocock's "A Complete Guide To AGENTS.md" (Step 5: Flag for deletion of redundant and automated instructions), the platform adopts an automation-first quality gate.

## Decisions

1. **Prune Redundant Textual Rules**:
   - Explicit ad-hoc rules regarding formatting, basic typing, bare exceptions, and naming conventions are pruned from the root `.agents/AGENTS.md`.
   - Detailed stylistic conventions are preserved in `docs/rules/code_quality.md` under progressive disclosure.

2. **Automated Linter Delegation**:
   - The root constitution specifies a single unified quality constraint: All code changes MUST pass automated validation via `ruff check` and `mypy` prior to completion.

3. **Pre-commit and CI Gate Authority**:
   - Tooling (pre-commit hooks, `pytest -m "not slow"`, Ruff, Mypy) is established as the sole authoritative enforcement mechanism for mechanical code standards.

## Consequences
- Saves ~500 prompt tokens and eliminates redundant cognitive load from every request.
- Focuses the Agent's reasoning budget on high-leverage architectural designs, Deep Seams, and business domain logic.
