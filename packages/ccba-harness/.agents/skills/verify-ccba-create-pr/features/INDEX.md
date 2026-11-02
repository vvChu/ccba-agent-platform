# Application Features Map & Verification Matrix (`ccba-create-pr`)

| Mã Tính Năng | Tên Tính Năng | Endpoint / CLI / Module | Verification Script | Trạng Thái | Last Verified |
| :--- | :--- | :--- | :--- | :---: | :---: |
| `FEAT-PR-001` | Frontmatter, Slash Command & GPI Threshold ($14.0 \ge 12.0$) | `.agents/skills/ccba-create-pr/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-002` | Bước 0 Main Branch Guard & Bước 1 Local Shift-Left Gate (`verify-patch` Exit 0) | `.agents/skills/ccba-create-pr/SKILL.md` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-003` | Bước 3 Show-Me Visual & Merge Danger (`## Summary`, `## Evidence`, `## Merge Danger` — `v1.3.0 #1120`) | `.github/pull_request_template.md` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-004` | Bước 4–5 Dual-Gate CI & Copilot Review (`audit_pr_comments.py`, Zero-Polling `RULE-4.8`, `.md/knowledge/reports/walkthrough.md`) | `run_verify_create_pr.validate_pr_creation_flow` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-005` | Spoke Sync Alias (`create-pr` $\to$ `ccba-contribute-to-hub`) & `PlatformToolingDomainSimulator` Registration | `scripts.spoke.sync.coordinator.SKILL_DEPRECATION_ALIASES` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-006` | 5-Block Lifecycle, Statechart Bug-Path Replay & Drift Modes | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/run_verify_create_pr.py` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
| `FEAT-PR-007` | Surface Diff Parity, Git Provenance & Domain Eval Ratchet Optimizer ($100.0\%$) | `ccba_harness.evals.tuner.GitRatchetOptimizer` | `packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py` | `stable` | 2026-11-03 |
