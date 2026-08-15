# 35. Polyglot Deep Modules Enforcement and Sub-Agent Review Guardrails

Date: 2026-08-15
Status: Approved

## Context
Following real-world findings from Matt Pocock's AI Hero and skills ecosystem, several critical architectural risks were identified:
1. **Sub-agent Infinite Recursion in Code Review**: Review sub-agents exploring the workspace without strict prompt constraints can re-invoke `/code-review` recursively, triggering unbounded agent cascades (>50 agents).
2. **Unbounded Token Burning in Standalone Reference Skills**: `codebase-design` is a reference/vocabulary skill rather than a driver workflow. When invoked standalone without a specific target, models could wander across the codebase executing exploratory rewrites (`DESIGN-IT-TWICE.md`).
3. **Monorepo Polyglot Deep Modules Alignment**: Upstream tooling (`setup-ts-deep-modules` via `dependency-cruiser`) focuses exclusively on TypeScript. CCBA Platform is a polyglot monorepo anchored in Python packages (`packages/ccba-ai`, `packages/ccba-legal-intel`, `packages/ccba-pdf-prep`, etc.) with Web/TypeScript frontends, necessitating a unified deep-module boundary enforcement strategy across both ecosystems.

## Decisions

1. **Two-Layer Sub-Agent Guardrail for `/code-review`**:
   - **Prompt Constraint**: Inject mandatory anti-delegation headers into both Standards and Spec sub-agents forbidding child sub-agent spawning, self-invocation, and shell mutation.
   - **Tool Scoping**: Restrict sub-agents to read-only tools (`view_file`, `grep_search`, `read_resource`) and set `disable-model-invocation: true` on review commands where applicable.

2. **Reference Skill Contract & Stopping Rules for `/codebase-design`**:
   - Mark `codebase-design` with `disable-model-invocation: true`.
   - When invoked standalone without arguments, enforce an immediate hard stop: display the core 7-term vocabulary and route the engineer to an appropriate driver skill (`/improve-codebase-architecture`, `/ccba-implement`, or `/ccba-grill-with-docs`).

3. **Polyglot Monorepo Deep Seams Enforcement**:
   - **Python Packages (`packages/*/`)**:
     - Export only 2–3 public Deep Seams via `__all__` in `__init__.py`.
     - Maintain internal implementations with leading underscores (`_service.py`, `_analyzer.py`) or under `internal/`.
     - Enforce non-leaky imports via `ruff check` (rule `SLF001` / private access) and automated CI validation.
     - Maintain local `packages/{pkg}/AGENTS.md` specifying public entry points.
   - **TypeScript Packages**:
     - Enforce `dependency-cruiser` boundary rules forbidding imports into package subfolders (`lib/`, `tests/`) from outside.
   - **Skill Unification**:
     - Generalize `setup-deep-modules` to support both Python and TypeScript monorepo conventions.

## Consequences
- Eliminates risk of runaway agent loops and context poisoning during code review.
- Prevents token wastage by anchoring reference skills to explicit targets and driver workflows.
- Establishes uniform, automated architectural boundaries across all Python and TypeScript monorepo packages.
