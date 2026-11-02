# Application Features Map & Verification Matrix (`ccba-harness`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-001` | CLI Dispatcher & Static Command Registry | `ccba_harness.cli.core.main` | `.agents/skills/verify-ccba-harness/harness/test_harness_suite.py` | `stable` | 2026-11-01 |
| `FEAT-002` | Two-Stage Decision Framework & GPI Engine | `ccba_harness.gpi.evaluate_two_stage_decision` | `.agents/skills/verify-ccba-harness/harness/test_harness_suite.py` | `stable` | 2026-11-01 |
| `FEAT-003` | Deterministic Patch & Document Verifier | `ccba_harness.verifier.verify_patch_execution` | `.agents/skills/verify-ccba-harness/harness/test_harness_suite.py` | `stable` | 2026-11-01 |
| `FEAT-004` | 3-Tier One-Way Door Classification | `ccba_harness.door_policy.classify_pr_door` | `.agents/skills/verify-ccba-harness/harness/test_harness_suite.py` | `stable` | 2026-11-01 |
| `FEAT-005` | 5-Block Verification Lifecycle Runner | `run_verify_harness.py` | `.agents/skills/verify-ccba-harness/harness/run_verify_harness.py` | `stable` | 2026-11-01 |
| `FEAT-006` | Statechart Bug-Path Replay & Drift Provenance | `run_verify_harness.classify_drift_status` | `.agents/skills/verify-ccba-harness/harness/test_harness_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-001` | Xia Frontmatter, Slash Command & GPI Threshold ($16.5 \ge 12.0$) | `.agents/skills/ccba-xia/SKILL.md` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-002` | Xia Pha 1 Recon, Shallow Clone & License Classification Gate | `scripts.spoke.upstream_evaluator.check_repo_license` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-003` | Xia Pha 2 Hub Catalog Duplicate Check & Gate 0 Determinism | `scripts.spoke.upstream_evaluator.check_is_duplicate` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-004` | Xia Pha 4 Challenge Hard Gate & ADR-0022 Mode Restrictions | `.agents/skills/ccba-xia/references/modes.md` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-005` | Xia Pha 5 & 6 Plan, 1-Click Command, `[XIA-COPY-RAW]` & Cleanup | `scripts.spoke.upstream_evaluator.generate_xia_command` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-006` | Xia 5-Block Lifecycle, Evals Optimizer, Statechart & Drift Modes | `.agents/skills/ccba-xia/harness/run_verify_xia.py` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-007` | Xia Surface Diff Parity & Domain Eval Ratchet Optimizer | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
| `FEAT-XIA-008` | Xia Upstream `mattpocock/skills` v1.3.2 Hybrid Adopt & Tier 2A References (`COND-01`..`COND-04`) | `.agents/skills/ccba-*/references/*.md` | `.agents/skills/verify-ccba-xia/harness/test_xia_suite.py` | `stable` | 2026-11-01 |
