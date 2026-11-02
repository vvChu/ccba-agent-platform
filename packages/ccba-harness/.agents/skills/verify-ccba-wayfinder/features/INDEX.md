# Application Features Map & Verification Matrix (`ccba-wayfinder`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-WF-001` | Frontmatter, Slash Command & GPI Threshold ($14.5 \ge 12.0$) | `.agents/skills/ccba-wayfinder/SKILL.md` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-002` | Boundary (`/ccba-grilling` vs `/ccba-wayfinder`), Leading Words & Planning Rules | `.agents/skills/ccba-wayfinder/SKILL.md` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-003` | 5-Section Map Contract & `Fog vs. Ticket Test` Classifier | `run_verify_wayfinder.validate_wayfinder_map_sections` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-004` | 4 Ticket Types (`Research`/`Prototype`/`Grilling`/`Task`), Parallel Dispatch & Claiming Lock | `run_verify_wayfinder.validate_ticket_execution_transition` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-005` | Spoke Sync Legacy Alias, Archetype Catalog & Simulator Registration | `scripts.spoke.sync.coordinator.SKILL_DEPRECATION_ALIASES` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `.agents/skills/ccba-wayfinder/harness/run_verify_wayfinder.py` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
| `FEAT-WF-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `.agents/skills/ccba-wayfinder/harness/test_wayfinder_suite.py` | `stable` | 2026-11-02 |
