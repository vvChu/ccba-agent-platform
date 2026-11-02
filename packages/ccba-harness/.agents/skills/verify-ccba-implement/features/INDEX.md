# Application Features Map & Verification Matrix (`ccba-implement`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-IMP-001` | Frontmatter, Orchestrator Tier & Slash Command Contract | `.agents/skills/ccba-implement/SKILL.md` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-002` | Context Budget Escalation (Cycle 3 Brief, Cycle 5 `/boost`) & 5-Step SDLC Flow | `run_verify_implement.evaluate_loop_budget_action` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-003` | Tier 2A `implement-spec.md`: Task Graph Frontier, First-Unit Canary & Single-Writer (`COND-01`) | `.agents/skills/ccba-implement/references/implement-spec.md` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-004` | Tier 2A `prototype_logic.md` & `prototyping_patterns.md`: Shareable HTML, Guided Walkthroughs & `prototype/<slug>` | `.agents/skills/ccba-implement/references/prototype_logic.md` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-005` | Spoke Sync Legacy Aliases (`implement`, `discard-feature`) & Archetype Catalog Registration | `scripts.spoke.sync.coordinator.SKILL_DEPRECATION_ALIASES` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `.agents/skills/ccba-implement/harness/run_verify_implement.py` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
| `FEAT-IMP-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `.agents/skills/ccba-implement/harness/test_implement_suite.py` | `stable` | 2026-11-03 |
