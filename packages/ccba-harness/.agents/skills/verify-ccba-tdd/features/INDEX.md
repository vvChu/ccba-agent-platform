# Application Features Map & Verification Matrix (`ccba-tdd`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-TDD-001` | Frontmatter, Slash Command & GPI Threshold ($12.0 \ge 12.0$) | `.agents/skills/ccba-tdd/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-002` | Red $\to$ Green $\to$ Refactor Phases & ADR-0058 `verify-patch --preset code` Hard Lock | `.agents/skills/ccba-tdd/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-003` | Public Seam Tradeoffs (`what it catches` / `what it misses`), Anti-Patterns & 5-Cycle Loop Budget (`safe_pytest.py`) | `run_verify_tdd.validate_tdd_cycle_transition` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-004` | Level 3 Progressive References `references/tests.md` & `references/mocking.md` | `.agents/skills/ccba-tdd/references/tests.md` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-005` | Spoke Sync Legacy Alias (`tdd` $\to$ `ccba-tdd`) & Archetype Catalog Registration | `scripts.spoke.sync.coordinator.SKILL_DEPRECATION_ALIASES` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/run_verify_tdd.py` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
| `FEAT-TDD-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `packages/ccba-harness/.agents/skills/verify-ccba-tdd/harness/test_tdd_suite.py` | `stable` | 2026-11-03 |
