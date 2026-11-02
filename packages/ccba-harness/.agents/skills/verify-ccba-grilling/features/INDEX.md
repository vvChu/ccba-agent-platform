# Application Features Map & Verification Matrix (`ccba-grilling`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-GRILL-001` | Frontmatter, Slash Command & GPI Threshold ($14.5 \ge 12.0$) | `.agents/skills/ccba-grilling/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-002` | Bước 0 Pre-Flight (`in-your-own-words`, `sharpen`, `outside check`) & Nhánh A/B/C | `.agents/skills/ccba-grilling/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-003` | Design Tree, Frontier Questions, `Facts vs. Decisions` & `/ccba-issue-tree` Escalation | `run_verify_grilling.validate_grilling_question_turn` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-004` | Tier 2A Progressive Reference `to-questionnaire.md` (*Grill the send, not the subject*) & `workflow_looping.md` | `.agents/skills/ccba-grilling/references/to-questionnaire.md` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-005` | Spoke Sync Legacy Alias (`grilling` $\to$ `ccba-grilling`) & Archetype Catalog Registration | `scripts.spoke.sync.coordinator.SKILL_DEPRECATION_ALIASES` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/run_verify_grilling.py` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
| `FEAT-GRILL-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `packages/ccba-harness/.agents/skills/verify-ccba-grilling/harness/test_grilling_suite.py` | `stable` | 2026-11-03 |
