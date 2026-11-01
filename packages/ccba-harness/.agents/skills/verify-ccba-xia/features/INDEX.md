# Application Features Map & Verification Matrix (`ccba-xia`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-XIA-001` | Frontmatter, Slash Command & GPI Threshold ($16.5 \ge 12.0$) | `.agents/skills/ccba-xia/SKILL.md` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-002` | Pha 1 Recon, Shallow Clone & License Classification Gate | `scripts.spoke.upstream_evaluator.check_repo_license` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-003` | Pha 2 Hub Catalog Duplicate Check & Gate 0 Determinism | `scripts.spoke.upstream_evaluator.check_is_duplicate` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-004` | Pha 4 Challenge Hard Gate & ADR-0022 Mode Restrictions | `.agents/skills/ccba-xia/references/modes.md` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-005` | Pha 5 & 6 Plan, 1-Click Command, `[XIA-COPY-RAW]` & Cleanup | `scripts.spoke.upstream_evaluator.generate_xia_command` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `.agents/skills/ccba-xia/harness/run_verify_xia.py` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-007` | Surface Diff Parity & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-008` | Upstream `mattpocock/skills` v1.3.2 Hybrid Adopt & Tier 2A References (`COND-01`..`COND-04`) | `.agents/skills/ccba-*/references/*.md` | `.agents/skills/ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
