# 31. Capability-First Instructions and Stale Path Mitigation

Date: 2026-08-15
Status: Approved

## Context
Previous iterations of `.agents/AGENTS.md` and rule sets contained hardcoded file paths to internal utility scripts (e.g. `scripts/safe_pytest.py`, `scripts/hooks/test_speed_guard.py`, `run_harness_evals.py`). When scripts are refactored into deep modules or unified CLIs, hardcoded references in static instructions quickly become stale, leading to **Context Poisoning** where AI Agents hallucinate non-existent files and execute broken workflows.

Following the principles in Matt Pocock's "A Complete Guide To AGENTS.md", the platform establishes a capability-first doctrine for instruction authoring.

## Decisions

1. **Capability-First Instruction Standard**:
   - Instructions and rules MUST describe intended behaviors, objectives, and standard interfaces (e.g. "Run scoped unit tests in isolation with timeout and exclusion of `@pytest.mark.slow`") rather than hardcoding internal helper script file paths.
   - Standard CLI interfaces (`pytest`, `ruff`, `pip`, standard package seams) are preferred over ad-hoc script paths.

2. **Just-In-Time (JIT) Discovery**:
   - Agents are empowered to discover project scripts dynamically during the Recon/Planning phase via semantic search or catalog lookups rather than relying on brittle hardcoded paths.

3. **Exemption for Root Invariants**:
   - Only fundamental platform invariants (e.g., `.md/workspace_context.yaml`, `catalog.yaml`, `docs/adr/`, `CONTEXT.md`) are permitted to be explicitly path-referenced.

## Consequences
- Eliminates context poisoning caused by codebase refactoring and file reorganization.
- Reduces brittle coupling between documentation rules and internal helper script implementations.
- Enhances Agent autonomy in locating appropriate tooling dynamically.
