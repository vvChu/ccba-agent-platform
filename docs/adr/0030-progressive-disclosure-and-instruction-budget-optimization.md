# 30. Progressive Disclosure and Instruction Budget Optimization for AGENTS.md

Date: 2026-08-15
Status: Approved

## Context
As the CCBA Agent Services Platform expanded, `.agents/AGENTS.md` (Layer 1 Constitution) grew to nearly 10 KB (~2,500 tokens), containing full operational specifications for Git conventions, Ruff linting rules, and 8 detailed execution guardrails. Under Frontier LLM constraints (where instruction budget is strictly limited to ~150-200 instructions), loading the monolithic constitution on every single user turn consumed excessive context budget and created instruction interference during non-coding tasks.

Following Matt Pocock's "A Complete Guide To AGENTS.md" (aihero.dev), the platform architecture was stress-tested to transition from a monolithic constitution to a progressive disclosure model.

## Decisions

1. **Root AGENTS.md Minimal Anchor**:
   - The root `.agents/AGENTS.md` retains only foundational invariants: Platform role, Hub vs Spoke demarcation, Reuse-First Gate, Core Standards summary, and Session Learnings bootstrap.
   - Target size: Under 35 lines (< 1 KB / ~300 tokens).

2. **Progressive Disclosure Document Structure**:
   - Detailed operational rules and guardrails are decoupled into modular documentation under `docs/rules/`:
     - `docs/rules/git_conventions.md`: Branch naming, commit types, and atomic unit rules.
     - `docs/rules/execution_guardrails.md`: Async task polling circuit breakers, TDD retry cap, process safety, and 2-tier test speed guards.
     - `docs/rules/code_quality.md`: Python type hints, docstrings, and Ruff scoping.
   - The root `AGENTS.md` provides breadcrumb links to these domain documents.

3. **Dynamic Rule Injection Integration**:
   - Heavy execution rules and domain-specific checklists are dynamically loaded on-demand via `catalog.yaml` (`dynamic_rules`) only when specific SDLC workflows or coding modes are active.

## Consequences
- Reduces base context token consumption by ~80% per prompt round-trip.
- Preserves the ~150-200 instruction budget for task-specific reasoning and user constraints.
- Eliminates context poisoning from static brittle file paths in root rules.
