# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #926` (`#918`)
## Docs(skills): Chuẩn Hóa Cổng Kiểm Chuẩn Software Spoke & Điều Hướng Hub-vs-Spoke

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#926](https://github.com/vvChu/ccba-agent-platform/pull/926) (`fb9e1939f96ebe7ac503774a6c3c9cde1f2bad6b`, hợp nhất `2026-11-26T23:26:24Z`) | **Branch:** `docs/issue-918-software-spoke-gates` (`d3af801a` + `ca5d36fd`, đã xóa local & remote) | **Base:** `a120c433` | **Issue Đã Đóng:** [#918](https://github.com/vvChu/ccba-agent-platform/issues/918) (`CLOSED`, gỡ `in-progress`, `#issuecomment-7205553726`)  
> **Trạng thái chung:** ✅ **PR #926 MERGED (`--merge`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `634 passed, 1 skipped, 10 deselected` in `31.30s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS (`audit_pr_comments.py` Exit `0`), `door-triage` PASS (`ONE_WAY_DOOR`, Tradeoff Card Valid), `sync_commit` `d3af801a` REACHABLE (`git cat-file -e` Exit `0`), `compile_catalog.py --check` `[OK]`, `sync_spoke.py --all --apply` (`3/6` SUCCESS, `3/6` dirty-tree guarded), ISSUE #918 CLOSED**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#926` (`#918`)

| Thành Phần | Tệp Thay Đổi Chính (`6` files, `+60/-24`) | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Software Spoke Shift-Left Gate** | [`ccba-create-pr/SKILL.md`](../../../.agents/skills/ccba-create-pr/SKILL.md) (`1.3.5` $\to$ `1.3.6`) | Tách Bước 1.2 thành **Legal / Knowledge Corpus Spokes** (`scripts/validate_legal_spoke.py`) và **Software / Enterprise Governance Spokes** (`.agents/skills/verify-<spoke>/harness/runner.py` hoặc scoped `pytest` + `scripts/_guardrails/check_spoke_cleanliness.py`); tinh gọn chú thích thừa để hạ dung lượng xuống `4331/4394` LF tokens (`-63` tokens). | Verified |
| **2. Software Spoke Release Gate & `CCBA_HUB_PATH` Guard** | [`ccba-release-feature/SKILL.md`](../../../.agents/skills/ccba-release-feature/SKILL.md) (`1.3.8` $\to$ `1.3.9`) | Tách Cổng 0.2 cho Legal vs Software/Enterprise Governance Spokes; bọc `ensure_single_instance('pytest')` ở Bước 3.1 theo Hub vs Spoke qua `CCBA_HUB_PATH` (0 bashism, tự bỏ qua an toàn khi không có `scripts/eval/*`); ghi rõ `(nếu tại Hub)` cho `compile_catalog.py` ở Bước 3.3 (`3335/4000` LF tokens). | Verified |
| **3. Phân Tách Vòng Đời Hub vs Spoke** | [`ccba-issue-to-hub/SKILL.md`](../../../.agents/skills/ccba-issue-to-hub/SKILL.md) (`1.1.0` $\to$ `1.1.1`) | Phân tách Bước 5 giữa **Triển khai trực tiếp tại Hub** (`/ccba-new-feature #[ISSUE_ID]` $\to$ `/ccba-create-pr` $\to$ `/ccba-release-feature`) và **Đóng góp mã nguồn từ Spoke lên Hub** (`/ccba-graduate-rd --issue #[ISSUE_ID]` $\to$ `/ccba-contribute-to-hub --issue #[ISSUE_ID]`) (`2521/4000` LF tokens). | Verified |
| **4. Provenance Lock & Contract Tests** | [`verify-ccba-create-pr/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-create-pr/SKILL.md) (`1.0.5` $\to$ `1.0.6`), [`test_create_pr_workflow.py`](../../../tests/test_create_pr_workflow.py), [`test_upstream_workflows.py`](../../../tests/test_upstream_workflows.py) | Re-anchor `sync_commit` sang `d3af801a6b732dc4452ae57587ba4ee89d2dfab9` và cập nhật LF SHA-256 `covered_sha256` của `ccba-create-pr/SKILL.md` (`69c93da3...`) ở Commit 2 (`ca5d36fd`); bổ sung contract tests cho cả 3 kỹ năng. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Shift-Left & Scoped Verification (`d3af801a` + `ca5d36fd`):**
  - `validate_skills.py --enforce-gpi`: PASS 3/3 skills; `compile_catalog.py --check`, `compile_skills_docs.py --check`, `scripts/sync_hub_adr_matrix.py --check`: PASS `0` drift.
  - Token ratchet (`test_real_codebase_skill_token_budget_ratchet`): PASS (`ccba-create-pr` `4331 <= 4394`); `verify-patch --preset skill`: **4/4 PASSED** (`4223.1ms`).
  - 5-Block `verify-ccba-create-pr/harness/run_verify_create_pr.py`: **7/7 passed** (`0.72s`); `sanitize_review_diff.py --check`: `[PASS]`; `sync_spoke.py --all --dry-run`: **6/6 Spokes SUCCESS**.
- **Giao thức TRIHT Pre-Release (Cổng 0.1–0.3):**
  - Cổng 0.1 (`check_release_cleanliness.py --phase pre`): stash tác vụ song song (`wip: concurrent work before release PR #926`) $\to$ `PASS` (`100%` sạch sẽ).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` `6.23s`, `ccba-diagram` `0.35s`, `ccba-harness` `12.45s`, `ccba-legal-intel` `51.00s`, `ccba-maskara` `0.30s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `6.78s`, `ccba-pdf-prep` `9.75s`, `ccba-qc-core` `1.15s`, `mdconverter` `3.06s`, `scripts` `16.77s`, `root-tests` **`634 passed, 1 skipped, 10 deselected` in `31.30s`**).
  - Cổng 0.3 (`check_release_cleanliness.py --phase post`): `PASS` (`100% Hermetic`).
- **CI, AI Review & Hậu Hợp Nhất (`fb9e1939`, `--merge` theo `RULE-2.21`):**
  - GitHub Actions CI: **8/8 PASS** (Python `3.10`/`3.11`/`3.12`, Deterministic Parity, Lint Markdown, PR Danger Triage & Verifier `7/7`, Security & Privacy Scan, Documentation Check); `audit_pr_comments.py --pr 926` Exit `0` (CodeRabbit auto-review skipped do repo `<10` sao).
  - Hậu hợp nhất: merge `--merge --delete-branch` tại `fb9e1939`, xóa nhánh `docs/issue-918-software-spoke-gates` local & remote, `git cat-file -e d3af801a6b732dc4452ae57587ba4ee89d2dfab9^{commit}` Exit `0`, Issue [#918](https://github.com/vvChu/ccba-agent-platform/issues/918) `CLOSED` & gỡ nhãn `in-progress`, `compile_catalog.py --check` `[OK]`.
  - Đồng bộ Spokes (`sync_spoke.py --all --apply`): `IDOP-CCBA-WAY`, `ccba-legal-knowledge`, `dgx-spark-toolkit` **SUCCESS**; 3 Spokes (`IBST_UNIFIED_ERP`, `ctymmt_ai_native_organization`, `vvc-second-brain`) được bộ khóa dirty-tree giữ nguyên do có thay đổi `.agents/` chưa commit.

---

## Lưu Trữ Phát Hành Trước Đó — Phát Hành `PR #921` (`#917`)
### Fix(harness): In `tradeoff_card_errors` Ra `sys.stderr` Trong Nhánh Non-JSON Của `door-triage`

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#921](https://github.com/vvChu/ccba-agent-platform/pull/921) (`b1df59f14c502651f5f35049e4a0d6b70ffe5c5c`, hợp nhất `2026-11-26T14:51:15Z`) | **Branch:** `fix/issue-917-door-triage-stderr` (`cacd81de`, đã xóa local & remote) | **Base:** `cdfd62e3` | **Issue Đã Đóng:** [#917](https://github.com/vvChu/ccba-agent-platform/issues/917) (`CLOSED`, `#issuecomment-7195435414`)  
> **Trạng thái chung:** ✅ **PR #921 MERGED (`--merge`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `ccba-harness` `11.79s`, `root-tests` `626 passed, 1 skipped, 10 deselected` in `29.29s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS (`audit_pr_comments.py` Exit `0`), `door-triage` PASS (`ONE_WAY_DOOR`, Tradeoff Card Valid), `sync_commit` `13bec7b4` REACHABLE (`git cat-file -e` Exit `0`), `compile_catalog.py --check` `[OK]`, ISSUE #917 CLOSED**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#921` (`#917`)

| Thành Phần | Tệp Thay Đổi Chính (`4` files, `+167/-3`) | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Non-JSON `stderr` Diagnostics (`_execute_door_triage`)** | [`architecture.py`](../../../packages/ccba-harness/src/ccba_harness/cli/commands/architecture.py) | Trong nhánh non-JSON của `_execute_door_triage`, khi `args.enforce_tradeoff_card` được bật và `card_errors` không rỗng, in tiêu đề lỗi, danh sách lỗi `card_errors` và gợi ý 3 trường bắt buộc (`Core Invariant`, `Invalidation Condition`, `Git Hunk Reference`) ra `sys.stderr`; giữ nguyên 100% `stdout`, schema `--json` và exit codes (`0\|1\|4`). | Verified |
| **2. Unit Tests Matrix & JSON Parity** | [`test_agent_envelope.py`](../../../packages/ccba-harness/tests/test_agent_envelope.py) | Bổ sung kiểm tra `stderr == ""` trên toàn bộ ma trận `--json`; thêm unit tests cho 5 kịch bản lỗi non-JSON (`none`, `missing`, `oserror`, `missing_card`, `invalid_fields`) và 4 kịch bản không phát `stderr` (`valid`, unenforced, `PAVED_ROAD`, `TWO_WAY_DOOR`). | Verified |
| **3. Provenance Lock & Harness Suite (`FEAT-007`)** | [`verify-ccba-harness/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-harness/SKILL.md), [`test_harness_suite.py`](../../../packages/ccba-harness/.agents/skills/verify-ccba-harness/harness/test_harness_suite.py) | Cập nhật LF SHA-256 `covered_sha256` cho `architecture.py` (`7fbf0de6...`, giữ nguyên `sync_commit` `13bec7b4...` trên `main`) và bổ sung kiểm tra non-JSON `stderr` trong `test_feat_007_agent_json_envelope_and_semantic_exit_codes`. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Shift-Left & Scoped Verification (`wt-issue-917`, `cacd81de`):**
  - `pytest packages/ccba-harness/tests -q`: **`782 passed, 6 skipped, 81 deselected`** in `11.56s`.
  - `pytest packages/ccba-harness/.agents/skills/verify-ccba-harness/harness/test_harness_suite.py -q`: **`8 passed`** in `0.36s`.
  - `python -m ccba_harness verify-patch --preset code`: **3/3 PASS** (`ruff check`, `ruff format --check`, `pytest tests/ -q` in `30.6s`).
  - `mypy packages/ccba-harness/src --follow-imports=silent`: **0 issues in 109 source files**; `compile_catalog.py --check` `[OK]`; `check_dependency_contracts.py` (`566` files, 0 vi phạm); `sanitize_review_diff.py --check` `[PASS]`.
- **Giao thức TRIHT Pre-Release (Cổng 0.1–0.3 trên `wt-issue-917`):**
  - Cổng 0.1 (`check_release_cleanliness.py --phase pre`): `PASS` (`100%` sạch sẽ).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` `4.97s`, `ccba-diagram` `0.35s`, `ccba-harness` `11.79s`, `ccba-legal-intel` `51.33s`, `ccba-maskara` `0.35s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `6.07s`, `ccba-pdf-prep` `9.68s`, `ccba-qc-core` `1.21s`, `mdconverter` `2.36s`, `scripts` `16.51s`, `root-tests` **`626 passed, 1 skipped, 10 deselected` in `29.29s`**).
  - Cổng 0.3 (`check_release_cleanliness.py --phase post`): `PASS` (`100% Hermetic`).
- **CI, AI Review & Hậu Hợp Nhất (`b1df59f1`, `--merge` theo `RULE-2.21`):**
  - GitHub Actions CI: **8/8 PASS** (Python `3.10`/`3.11`/`3.12`, Deterministic Parity & Schema Audit, Lint Markdown, PR Danger Triage & Verifier Gate `7/7`, Security & Privacy Scan, Documentation Check); `audit_pr_comments.py --pr 921` Exit `0` (CodeRabbit auto-review skipped do repo `<10` sao).
  - Hậu hợp nhất: tháo worktree `wt-issue-917`, merge `--merge` tại `b1df59f1`, xóa nhánh `fix/issue-917-door-triage-stderr` local & remote, fast-forward `main`, `git cat-file -e 13bec7b4720d6562e1d8ca56f391e767da706017^{commit}` Exit `0`, đóng Issue [#917](https://github.com/vvChu/ccba-agent-platform/issues/917) (gỡ nhãn `in-progress`), `compile_catalog.py --check` `[OK]`.

---

## Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #909` & `PR #911` (Nâng Cấp `/ccba-ask` v1.4.0, Khóa Hợp Đồng Slash Host & `ccba-knowledge-loop` v1.2.0)

> **PR `#909` Đã Hợp Nhất (`--squash --delete-branch`):** [#909](https://github.com/vvChu/ccba-agent-platform/pull/909) (`ce2a424ef113b0af68d6036ef5f2fd9eb70191be`, hợp nhất `2026-11-25T14:32:25Z`) | **Branch:** `feat/ccba-ask-v140` (đã xóa local & remote) | **Base:** `9096e22d`  
> **PR `#911` Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#911](https://github.com/vvChu/ccba-agent-platform/pull/911) (`d731dfbd9a39645ea2c8f2419d3943ffcf1fa116`, hợp nhất `2026-11-25T14:53:00Z`) | **Branch:** `feat/ccba-ask-contracts-and-knowledge-loop` (`76e698bb`, đã xóa local & remote) | **Base:** `ce2a424e` | **Backlog Issue:** [#910](https://github.com/vvChu/ccba-agent-platform/issues/910) (`OPEN`)  
> **Trạng thái chung:** ✅ **2/2 PRs MERGED, TRIHT CỔNG 0.1–0.3 PASS x2 (`12/12` TARGETS, `root-tests` `618` -> `623 passed, 1 skipped, 10 deselected` in `29.57s` / `29.75s`), `8/8` CI CHECKS PASS x2, `0` UNRESOLVED PR COMMENTS x2, `door-triage` PASS (`ONE_WAY_DOOR`, Tradeoff Card Valid), `verify-ccba-*` + `dogfood` + contracts `63 passed in 2.30s`, `compile_catalog.py --check` `[OK]`**

### Tổng Kết Thay Đổi Kỹ Thuật — PR `#909` & PR `#911`

| Thành Phần | Tệp Thay Đổi Chính (`12` + `8` files) | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Nâng Cấp `/ccba-ask` v1.4.0 & L3 Guides (PR `#909`)** | [`ccba-ask/SKILL.md`](../../../.agents/skills/ccba-ask/SKILL.md), [`delegation_matrix.md`](../../../.agents/skills/ccba-ask/references/delegation_matrix.md), [`builtin_vs_ccba.md`](../../../.agents/skills/ccba-ask/references/builtin_vs_ccba.md), [`brainstorm_templates.md`](../../../.agents/skills/ccba-ask/references/brainstorm_templates.md), [`brainstorm_techniques.md`](../../../.agents/skills/ccba-ask/references/brainstorm_techniques.md), [`clarification_patterns.md`](../../../.agents/skills/ccba-ask/references/clarification_patterns.md) | Áp dụng khóa chỉ đọc cứng (`Read-Only Lock`) ngăn chặn lỗi `write_file` khi nhắc `/plan`, điều phối trạng thái tự động (`State-Aware Routing`), tách 2 hướng dẫn L3 (`delegation_matrix.md`, `builtin_vs_ccba.md`), thêm kỹ thuật `Reframe` (`pstack@2a562168`), dọn sạch rò rỉ Spoke `vvc-notes`, thu gọn ngân sách `3,733/4,013` tokens (`+280` headroom, `GPI 14.00`); tái biên dịch [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml), [`docs/index.html`](../../../docs/index.html) và `docs/skills/*`. | Verified |
| **2. Cho Phép Host Slash & Khóa Hợp Đồng (PR `#911`)** | [`_skill_content_checks.py`](../../../packages/ccba-harness/src/ccba_harness/_skill_content_checks.py), [`builtin_vs_ccba.md`](../../../.agents/skills/ccba-ask/references/builtin_vs_ccba.md), [`test_ccba_ask_contracts.py`](../../../tests/governance/test_ccba_ask_contracts.py) | Mở rộng `ALLOWED_HOST_COMMANDS` với `/plan`, `/teamwork`, `/swarm` (LF SHA-256 `e3fd35f2...`); chuẩn hóa cú pháp slash trong `builtin_vs_ccba.md`; thêm 5 contract tests khóa bất biến của `ccba-ask` v1.4.0 & `ccba-knowledge-loop` v1.2.0. | Verified |
| **3. Tinh Chỉnh `ccba-knowledge-loop` v1.2.0, Upstream Ledger & Re-Anchor Harnesses (PR `#911`)** | [`ccba-knowledge-loop/SKILL.md`](../../../.agents/skills/ccba-knowledge-loop/SKILL.md), [`upstream_sources.yaml`](../upstream_sources.yaml), [`test_upstream_evaluator.py`](../../../tests/test_upstream_evaluator.py), [`verify-ccba-harness/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-harness/SKILL.md), [`verify-ccba-knowledge-loop/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-knowledge-loop/SKILL.md) | Phân định ranh giới với `/ccba-ask`, nới lỏng `input_documents/`, bổ sung After-Friction Hook (`chief-of-staff@6f7f7831`, LF SHA-256 `aa04be52...`); bảo toàn `61` mục gốc `pstack@74bcc61b` & `aliases.ketchup = "ccba-handoff"`, ghi nhận `pstack/reframe -> ccba-ask` (`ADOPTED`, `2a562168`) và cập nhật `chief-of-staff` (`6f7f7831`); neo lại `covered_sha256` trên 2 harness skills (`sync_commit` giữ nguyên). | Verified |

---

### Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất — PR `#909` & PR `#911`

- **Kiểm toán Thực nghiệm & Phản biện Ngang hàng (Grok Peer Audit):**
  - Kiểm toán `543` transcripts (`2026-10-07` -> `2026-11-25`, `3,093` lượt `USER_INPUT`, `/ccba-ask` Top `#4/77`, `62T/46C`, `85.5%` hiệu quả hành vi); chốt 4/4 Frontiers qua `/ccba-grilling` và tạo Issue backlog [#910](https://github.com/vvChu/ccba-agent-platform/issues/910) (`RED_QUARANTINE_LOCKED` 61/77 skills & `eval_ccba_ask.json`).
  - Grok Pass 1 (`ba5aee9b-b871-4409-87b0-76a6b0d925f2`, `REVISE_PLAN`) -> Pass 2 (`fd94ba26-e718-4806-b791-710714b7fd68`, **`APPROVE_PLAN`**, `risk_score: 2`, `0` blocking); Seam Audit Receipt `NO_MATCH` (`index_sha256: 29d4ee1a...`).
- **Giao thức TRIHT Pre-Release (Cổng 0.1–0.3 x2):**
  - **PR `#909`:** Cổng 0.1 sạch 100%; Cổng 0.2 **12/12 targets PASS** (`root-tests` `618 passed, 1 skipped, 10 deselected` in `29.57s`); Cổng 0.3 `100% Hermetic`.
  - **PR `#911`:** Cổng 0.1 sạch 100% (stash tác vụ song song `wip: concurrent work before release PR #911`); Cổng 0.2 **12/12 targets PASS** (`ccba-ai` `4.87s`, `ccba-diagram` `0.30s`, `ccba-harness` `11.85s`, `ccba-legal-intel` `49.66s`, `ccba-maskara` `0.30s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `5.92s`, `ccba-pdf-prep` `9.68s`, `ccba-qc-core` `1.15s`, `mdconverter` `2.31s`, `scripts` `16.41s`, `root-tests` **`623 passed, 1 skipped, 10 deselected` in `29.75s`** / `30.47s`); Cổng 0.3 `100% Hermetic`.
- **Shift-Left, CI & Post-Merge (`ce2a424e` & `d731dfbd`):**
  - `verify-patch --preset ci` (`7/7 PASS`), `--preset skill` (`4/4 PASS`), `test_telemetry_economy.py` (`10/10 PASS`), `compile_skills_docs.py --check` `[OK]`, `sanitize_review_diff.py --check` `[PASS]`.
  - GitHub Actions CI: **8/8 PASS** trên PR `#909` và **8/8 PASS** trên PR `#911`; `audit_pr_comments.py` exit `0` trên cả 2 PR; `door-triage --enforce-tradeoff-card` PASS (`ONE_WAY_DOOR`, `Streak: 7`).
  - Post-merge PR `#911`: `git cat-file -e` exit `0` trên `13bec7b4720d6562e1d8ca56f391e767da706017` (`verify-ccba-harness`) và `778c25d5e9d30f28c3ec1049b3d531bb5e12b9c2` (`verify-ccba-knowledge-loop`); `compile_catalog.py --check` `[OK]`; dogfood + contracts + upstream evaluator + 2 suites `verify-ccba-*`: **`63 passed in 2.30s`**; nhánh local & remote đã xóa sạch.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Định Tuyến Alias `create-pr` $\to$ `ccba-create-pr` & Hỗ Trợ `$CCBA_HUB_PATH` Trong Audit Global Skill (`PR #899`)

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#899](https://github.com/vvChu/ccba-agent-platform/pull/899) (`23bdaf90791154448b4386fcf8fb8eb2606637fb`, hợp nhất `2026-11-24T08:19:26Z`) | **Branch:** `fix/create-pr-sync-alias-and-global-skill` (`b3fb046f`, đã xóa local & remote) | **Base:** `10d6934a` | **Issue:** N/A

- **Thành phần chính (`13 files, +44/-20`):** Xóa `"ccba-create-pr": "ccba-contribute-to-hub"` và đổi `"create-pr"` $\to$ `"ccba-create-pr"` trong `SKILL_DEPRECATION_ALIASES` ([`coordinator.py`](../../../scripts/spoke/sync/coordinator.py), LF SHA-256 `23defb1a...`, [`test_spoke_synchronizer.py`](../../../tests/test_spoke_synchronizer.py)); cập nhật [`test_global_skills_integrity.py`](../../../tests/governance/test_global_skills_integrity.py) hỗ trợ `$CCBA_HUB_PATH/...` và đồng bộ global `ccba-platform/SKILL.md`; cập nhật `FEAT-PR-005` ([`test_create_pr_suite.py`](../../../packages/ccba-harness/.agents/skills/verify-ccba-create-pr/harness/test_create_pr_suite.py)) và re-anchor `7` harnesses [`verify-ccba-*`](../../../packages/ccba-harness/.agents/skills/verify-ccba-create-pr/SKILL.md).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `618 passed, 1 skipped, 10 deselected` in `29.47s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 899` exit `0`, `door-triage` `ONE_WAY_DOOR` (`Streak: 5`), `7/7` `verify-ccba-*` + `dogfood` `55 passed in 1.39s`, `compile_catalog.py --check` `[OK]`, walkthrough PR [#900](https://github.com/vvChu/ccba-agent-platform/pull/900) (`61ea1535`).

---

## 4. Lưu Trữ Phát Hành Trước Đó — Phân Tách `/ccba-create-pr` vs `/ccba-contribute-to-hub` Trên Các Kỹ Năng `universal` (`PR #897`)

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#897](https://github.com/vvChu/ccba-agent-platform/pull/897) (`c750eed21fb44fc9e715ec698f7189e1b60d232b`, hợp nhất `2026-11-24T05:55:36Z`) | **Branch:** `fix/universal-skills-pr-routing` (`b91fb4df`, đã xóa local & remote) | **Base:** `39273beb` | **Issue:** N/A

- **Thành phần chính (`11 files, +76/-22`):** Phân tách `/ccba-create-pr` (repo hiện tại: Hub hoặc nội bộ Spoke) vs `/ccba-contribute-to-hub` (chỉ Spoke $\to$ Hub) trên [`ccba-new-feature`](../../../.agents/skills/ccba-new-feature/SKILL.md) (`5810/5846`), [`ccba-ask`](../../../.agents/skills/ccba-ask/SKILL.md) (`4003/4013`), [`ccba-code-review`](../../../.agents/skills/ccba-code-review/SKILL.md) (`4746/4763`), [`ccba-platform`](../../../.agents/skills/ccba-platform/SKILL.md) (`4384/4393`) và [`ccba-contribute-to-hub`](../../../.agents/skills/ccba-contribute-to-hub/SKILL.md) (`4991/5002`, gỡ trigger `ccba-create-pr`/`create-pr`); cập nhật LF SHA-256 trong [`verify-ccba-code-review/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-code-review/SKILL.md) (`761cecad...`); thêm `test_universal_skills_pr_routing_contract()` trong [`test_upstream_workflows.py`](../../../tests/test_upstream_workflows.py) và tái biên dịch [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml) / [`docs/index.html`](../../../docs/index.html) (`77` skills).
- **Nghiệm thu:** Grok Pass 2 `APPROVE_PLAN` (`43315150-4933-451e-8150-eddaad5e5e38`, `0` blocking), `validate_skills.py --enforce-gpi` & `token_economy.py check-ratchet` (`77` skills PASS), `verify-patch --preset skill` (`4/4`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `617 passed, 1 skipped, 10 deselected` in `29.36s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 897` exit `0`, walkthrough PR [#898](https://github.com/vvChu/ccba-agent-platform/pull/898) (`10d6934a`).

---

## 5. Lưu Trữ Phát Hành Trước Đó — Khử Lỗi Bold-Glue `____`, Kiểm Định `MALFORMED_BOLD_GLUE`, NFC Gate 11 & Rào Chắn `ccba-legal-ingest` (`PR #895` / `#892`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#895](https://github.com/vvChu/ccba-agent-platform/pull/895) (`5d1a8af81c75110417928e3e7a8e0b01fe3a7de7`, hợp nhất `2026-11-24T04:37:05Z`) | **Branch:** `fix/issue-892-bold-glue-nfc-legal-ingest` (`bbdbf3e7` -> `b4d7b9ca`, đã xóa local & remote) | **Base:** `8154720a` | **Issue Đã Đóng:** [#892](https://github.com/vvChu/ccba-agent-platform/issues/892) (`CLOSED`)

- **Thành phần chính (`9 files, +219/-7`):** Gỡ xóa anchor trùng trong [`vbpl_admin.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/vbpl_admin.py) và bổ sung `_strip_mammoth_anchors_and_glue()` trong [`unit_normalizer.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/unit_normalizer.py); bổ sung `_MALFORMED_BOLD_GLUE_RE` & `_is_bold_glue_exempt()` trong [`visual_parity.py`](../../../packages/ccba-legal-intel/src/ccba_legal/visual_parity.py); chuẩn hóa `unicodedata.normalize("NFC", ...)` và bộ lọc preamble trong [`provenance.py`](../../../packages/ccba-legal-intel/src/ccba_legal/provenance.py); nâng [`SKILL.md`](../../../.agents/skills/ccba-legal-ingest/SKILL.md) `v1.4.0` (`GPI 24.50`), đăng ký `"scripts/hydrate_sources_from_vault.py"` trong [`test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) và bổ sung tests hồi quy.
- **Nghiệm thu:** `verify-patch --preset code` (`4/4 PASS`), `--preset skill` (`4/4 PASS`), `run_verify_legal_intel.py` (`6 passed`), `packages/ccba-legal-intel/tests` (`473 passed, 2 skipped, 20 deselected`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.51s` / `30.23s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 895` exit `0`, Issue `#892` `CLOSED`, walkthrough PR [#896](https://github.com/vvChu/ccba-agent-platform/pull/896) (`39273beb`).

---

## 6. Lưu Trữ Phát Hành Trước Đó — Cấu Hình `--verify-timeout` / `CCBA_VERIFY_TIMEOUT` & Chẩn Đoán Timeout (`PR #893` / `#889`)

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#893](https://github.com/vvChu/ccba-agent-platform/pull/893) (`2f135728943920041ad146bc7b4bcbc46cfe786a`, hợp nhất `2026-11-24T03:50:11Z`) | **Branch:** `feat/issue-889-configurable-verify-timeout` (`f686ff6b` -> `227175bc`, đã xóa local & remote) | **Base:** `a2f371d1` | **Issue Đã Đóng:** [#889](https://github.com/vvChu/ccba-agent-platform/issues/889) (`CLOSED`, `#issuecomment-7121478815`)

- **Thành phần chính (`14 files, +514/-47`):** Bổ sung `DEFAULT_VERIFY_TIMEOUT = 180.0`, `CCBA_VERIFY_TIMEOUT`, `parse_positive_verify_timeout()`, `resolve_verify_timeout()` và `format_verify_failure_lines()` ([`base.py`](../../../scripts/spoke/sync/base.py)); truyền timeout qua `verify_spoke()` và các hàm đồng bộ ([`coordinator.py`](../../../scripts/spoke/sync/coordinator.py)); thêm `--verify-timeout SECONDS` ([`cli.py`](../../../scripts/spoke/sync/cli.py)) & cập nhật [`ccba-update-spoke`](../../../.agents/skills/ccba-update-spoke/SKILL.md) (`4293 <= 4412` tokens, `GPI 14.00`); thêm `39` unit tests ([`test_spoke_verify_timeout.py`](../../../scripts/tests/test_spoke_verify_timeout.py)) và re-anchor `7` [`verify-ccba-*`](../../../packages/ccba-harness/.agents/skills/verify-ccba-code-review/SKILL.md).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.36s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 893` exit `0`, `git cat-file -e <sync_commit>^{commit}` exit `0` trên `7/7` suites, `test_verification_harness_dogfood.py` `5 passed`, `compile_catalog.py --check` `[OK]`, walkthrough PR [#894](https://github.com/vvChu/ccba-agent-platform/pull/894) (`8154720a`).

---

## 7. Lưu Trữ Phát Hành Trước Đó — Mở Rộng Bao Đóng Phụ Thuộc Nội Bộ Hub & Đưa `ccba-maskara` Vào `tier0` (`PR #890` / `#888`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#890](https://github.com/vvChu/ccba-agent-platform/pull/890) (`fc85177ed3a9ae014fa8d6d739397e5e278ad6aa`, hợp nhất `2026-11-24T01:31:12Z`) | **Branch:** `fix/issue-888-spoke-bootstrap-transitive-deps` (`02cd2d58`, đã xóa local & remote) | **Base:** `6a21510f` | **Issue Đã Đóng:** [#888](https://github.com/vvChu/ccba-agent-platform/issues/888) (`CLOSED`, `2026-11-24T01:31:14Z`)

- **Thành phần chính (`5 files, +562/-162`):** Tạo [`_bootstrap_deps.py`](../../../scripts/spoke/_bootstrap_deps.py) (`157` LOC, `<= 40` LOC/hàm) chuẩn hóa PEP 503/508, đọc `[project.dependencies]`, tính bao đóng chuyển tiếp chống chu trình và sắp xếp Kahn; thu gọn [`spoke_bootstrap.py`](../../../scripts/spoke/spoke_bootstrap.py) (`867` -> `741` LOC) cho cả `resolve_install_set()` và `_resolve_legacy_target_packages()`; thêm `ccba-maskara` vào `package_bindings.tier0` trong [`catalog_base.yaml`](../../../.agents/skills/platform-loader/catalog_base.yaml) & biên dịch [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml); bổ sung 9 unit tests trong [`test_declarative_package_bindings.py`](../../../scripts/tests/test_declarative_package_bindings.py).
- **Nghiệm thu:** Clean-venv E2E (`enterprise_governance` `6/6`, `project_delivery` `8/8`), `pytest scripts/tests/ -q` (`419 passed, 3 deselected`), `verify-patch --preset ci` (`7/7`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.43s` / `30.07s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 890` exit `0`, Issue `#888` `CLOSED`, walkthrough PR [#891](https://github.com/vvChu/ccba-agent-platform/pull/891) (`a2f371d1`).

---

## 8. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `actions/cache` Từ Version 4 Lên Version 6 (`PR #870`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#870](https://github.com/vvChu/ccba-agent-platform/pull/870) (`06d9132638e4279ccf5f86ef9dc8b41766d89ed5`, hợp nhất `2026-11-23T16:41:11Z`) | **Branch:** `dependabot/github_actions/actions/cache-6` (đã xóa remote) | **Base:** `4f5f658c` | **Issue:** N/A

- **Thành phần chính (`3 files, +4/-4`):** Nâng cấp `actions/cache@v4` -> `actions/cache@v6` trong [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml), [`.github/workflows/nightly-slow-tests.yml`](../../../.github/workflows/nightly-slow-tests.yml) và [`.github/workflows/pr-verifier.yml`](../../../.github/workflows/pr-verifier.yml).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `30.04s` / `30.73s`), `7/7` CI `SUCCESS`, `audit_pr_comments.py --pr 870` exit `0`, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid).

---

## 9. Lưu Trữ Phát Hành Trước Đó — Chuẩn Hóa Hướng Dẫn CLI/Seam Môi Trường Spoke Cho Maskara, Retrospective, Release Skills (`PR #880` / `#874`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#880](https://github.com/vvChu/ccba-agent-platform/pull/880) (`4f5f658cb977cad86917db68ef51733e7062a0d2`, hợp nhất `2026-11-23T16:36:01Z`) | **Branch:** `docs/issue-874-spoke-cli-skills` (đã xóa local & remote) | **Base:** `f2021607` | **Issue Đã Đóng:** [#874](https://github.com/vvChu/ccba-agent-platform/issues/874) (`CLOSED`, `2026-11-23T16:36:04Z`)  
> **Trạng thái chung:** ✅ **PR #880 MERGED (`--squash`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.75s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS, `door-triage` PASS, `compile_catalog.py --check` `[OK]`, SPOKE SYNC APPLIED (`ccba-legal-knowledge`)**

- **Thành phần chính (`3 files, +48/-26`):** Nâng [`ccba-maskara`](../../../.agents/skills/ccba-maskara/SKILL.md) lên `v1.0.1` chuẩn hóa CLI đa môi trường `maskara` / `python -m ccba_maskara.cli` và seam `maskara_scanner.v1`; nâng [`ccba-session-retrospective`](../../../.agents/skills/ccba-session-retrospective/SKILL.md) lên `v1.7.4` ưu tiên `scripts/sync_adr_matrix.py` trên Spoke có SSOT và siết chặt token ratchet budget; biên dịch lại `headings` cho `ccba-maskara` tại [`docs/index.html`](../../../docs/index.html).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 880` exit `0`, Issue `#874` `CLOSED`, Spoke sync applied `ccba-legal-knowledge`.

---

## 10. Lưu Trữ Phát Hành Trước Đó — Mặc Định `docProps/core.xml` `IBST - CCBA` & Khối Ký Tùy Chọn (`PR #884` / `#883`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#884](https://github.com/vvChu/ccba-agent-platform/pull/884) (`0fb9cf28c26f36008a923788fe11e288541f471b`, hợp nhất `2026-11-23T15:46:44Z`) | **Branch:** `feat/issue-883-ooxml-core-props-signoff` (`419c4b0f` -> rebased `e079c3c6`, đã xóa local & remote) | **Base:** `5e62429c` | **Issue Đã Đóng:** [#883](https://github.com/vvChu/ccba-agent-platform/issues/883) (`CLOSED`, `2026-11-23T15:46:47Z`)  
> **Trạng thái chung:** ✅ **PR #884 MERGED (`--squash`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.86s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid), `compile_catalog.py --check` `[OK]`**

- **Thành phần chính (`6 files, +144/-23`, `161` logic LOC):** Chuẩn hóa `IBST/CCBA` -> `IBST - CCBA` (`_report_chrome.py`); mở rộng `render_signoff_block(..., title=...)`; opt-in `header_include_revision`; gán `author`/`last_modified_by` và xóa `"generated by python-docx"` (`_tech_report.py`); bổ sung OpenXML DOM tests (`test_docx_tech_report.py`); đồng bộ schema và nâng `ccba-xu-ly-van-phong` `v2.3.2`.
- **Nghiệm thu:** `pytest packages/ccba-ooxml/tests` (`120 passed`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#883` `CLOSED`, walkthrough PR [#885](https://github.com/vvChu/ccba-agent-platform/pull/885) (`f2021607`).

---

## 11. Lưu Trữ Phát Hành Trước Đó — Gia Cố Rào Chắn Hậu Chỉnh Tay Word (`ccba-xu-ly-van-phong` v2.3.1) & Đường Dẫn Guardrails Spoke (`ccba-session-retrospective` v1.7.3) (`PR #876`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#876](https://github.com/vvChu/ccba-agent-platform/pull/876) (`843032defd57d1279e9c9e25b7a3c5d42ade2323`, hợp nhất `2026-11-23T15:12:58Z`) | **Branch:** `proposal/harden-docx-post-edit-and-spoke-retrospective-cli` (`99f10474` -> `f4b791af` -> `8f1ec7ab`) | **Base:** `65d91fc0` | **Refs:** [#874](https://github.com/vvChu/ccba-agent-platform/issues/874)

- **Thành phần chính (`4 files, +49/-21`):** Nâng [`ccba-xu-ly-van-phong`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) lên `v2.3.1` với Rào chắn #5 (`Post-Manual-Word-Edit Hygiene`) & tính tùy chọn dòng tiêu đề khối ký tại [`docx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/docx.md); nâng [`ccba-session-retrospective`](../../../.agents/skills/ccba-session-retrospective/SKILL.md) lên `v1.7.3` sửa đường dẫn `scripts/spoke/` qua `CCBA_HUB_PATH` và bổ sung hướng dẫn Spoke non-git; lưu hồ sơ đề xuất [`2026-11-23_harden-docx-post-edit-and-spoke-retrospective-cli.md`](../../../.agents/proposals/2026-11-23_harden-docx-post-edit-and-spoke-retrospective-cli.md) (`status: "merged"`, `843032de`).
- **Nghiệm thu:** Tier 2 Boost (`77 GREEN`, `verify-patch --preset skill` `4/4`, `79 passed in 2.94s`, `tests/governance/` `367 passed, 1 skipped, 9 deselected in 12.74s` trên `f4b791af`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, walkthrough PR [#881](https://github.com/vvChu/ccba-agent-platform/pull/881) (`21224846`).

---

## 12. Lưu Trữ Phát Hành Trước Đó — Gia Cố Nhận Diện `VBPL_ADMIN`, Cắt `Nơi nhận:`, `legal_basis` & Timeout Tải/Hydrate (`PR #877` / `#873`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#877](https://github.com/vvChu/ccba-agent-platform/pull/877) (`8d6ff9a1b47c84a32586001c3921b7944cb84dcb`, hợp nhất `2026-11-23T14:41:53Z`) | **Branch:** `fix/issue-873-harden-vbpl-ingest` (`58ac8f6c` -> `93a50e70` -> `386bcab9`, đã xóa local & remote) | **Base:** `ee9dbe71` | **Issue Đã Đóng:** [#873](https://github.com/vvChu/ccba-agent-platform/issues/873) (`CLOSED`, `2026-11-23T14:41:55Z`)

- **Thành phần chính (`10 files, +582/-149`, `+194` net logic LOC):** Bổ sung `_ADMIN_NUM_RE`, `_ADMIN_TYPES` và `_is_vbpl_admin_hint()` tại [`archetype_scanner.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/archetype_scanner.py) kèm sửa `\x08` -> `\b`; chia sẻ `_BODY_START_RE`, sửa `sig_pattern`, `_dump_yaml_no_aliases()` và `_infer_vbpl_doc_type()` tại [`vbpl_admin.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/vbpl_admin.py); nâng timeout tải Chrome/hydrator tại [`session.py`](../../../packages/ccba-legal-intel/src/ccba_legal/session.py), [`cdp.py`](../../../packages/ccba-legal-intel/src/ccba_legal/cdp.py), [`tier_downloader.py`](../../../packages/ccba-legal-intel/src/ccba_legal/crawler/tier_downloader.py), [`hydrator.py`](../../../packages/ccba-legal-intel/src/ccba_legal/hydrator.py); nâng [`SKILL.md`](../../../.agents/skills/ccba-legal-ingest/SKILL.md) `v1.3.1` (`GPI 24.50`) và bổ sung unit tests hồi quy.
- **Nghiệm thu:** `467 passed, 2 skipped, 20 deselected`, tái chuyển đổi `4` mẫu DOCX đạt `0 Errors, 0 Warnings`, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.62s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, walkthrough PR [#879](https://github.com/vvChu/ccba-agent-platform/pull/879) (`65d91fc0`).

---

## 13. Lưu Trữ Phát Hành Trước Đó — Chuẩn Hóa Phát Hiện `GENERIC` `ERROR` & Chống False Positive `SYSTEM_MESSAGE` Trong `evals.miner` (`PR #875`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#875](https://github.com/vvChu/ccba-agent-platform/pull/875) (`8a9f47c63fcbb274e7779ab449469d1d3e827831`, hợp nhất `2026-11-23T14:03:36Z`) | **Branch:** `fix/miner-generic-error-and-system-msg` (`a2e6aff4`, đã xóa local & remote) | **Base:** `badce709` | **Issue:** N/A

- **Thành phần chính (`2 files, +150/-35`):** Bổ sung `_TRACEBACK_MARKER` và `_classify_jsonl_step_response()` trong [`miner.py`](../../../packages/ccba-harness/src/ccba_harness/evals/miner.py) (`518` LOC, `max_fn_len <= 50`) để chỉ gắn lỗi khi `status == "ERROR"` hoặc chứa traceback thực sự, tách `active_user_prompt` khỏi `pending_planner_prompt`; bổ sung `4` unit tests trong [`test_miner.py`](../../../packages/ccba-harness/tests/test_miner.py) (`10/10` passed in `0.51s`).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `30.01s` / `30.64s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid), walkthrough PR [#878](https://github.com/vvChu/ccba-agent-platform/pull/878) (`ee9dbe71`).

---

## 14. Lưu Trữ Phát Hành Trước Đó — Kiểm Toán Song Song Hai Spoke (`ERP` Sóng 4 × `IDOP` Bridge Sóng 3) & Lộ Trình R&D Hub-Spoke CCBA WAY (`PR #871`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#871](https://github.com/vvChu/ccba-agent-platform/pull/871) (`67b6cb3ef97449aa4dadf47dee833741b9951f91`, hợp nhất `2026-11-23T04:43:20Z`) | **Branch:** `docs/hub-spoke-idop-ccba-way-research` (`585a106c` -> `bd4d8d75`) | **Base:** `e5dc4bf6` | **Issue:** N/A

- **Thành phần chính (`2 files, +172 insertions`):** Xuất bản [`research-hub-spoke-idop-ccba-way-next-steps.md`](../research_and_studies/research-hub-spoke-idop-ccba-way-next-steps.md) và đăng ký tại [`index.md`](../index.md) (kiểm toán `IBST_UNIFIED_ERP` Sóng 4 × `IDOP-CCBA-WAY` Issue `#177` Bridge Sóng 3, phát hiện va chạm chéo PG `:5433`, vạch lộ trình `H0.2 -> R1 -> R4`, nâng Node.js `v26.13.1` LTS).
- **Nghiệm thu:** `validate_docs.py .md/knowledge --changed` (`32/32`), `verify-patch --preset doc` (`1/1`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `32.55s` / `34.42s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 871` exit `0`, `compile_catalog.py --check` `[OK]`, walkthrough PR [#872](https://github.com/vvChu/ccba-agent-platform/pull/872) (`badce709`).

---

## 15. Lưu Trữ Phát Hành Trước Đó — Bổ Sung `frontend/src` Vào `DEFAULT_PRODUCTION_ROOTS` & SSOT Module Size Budget (`PR #866` / `#865`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#866](https://github.com/vvChu/ccba-agent-platform/pull/866) (`ac6f83dc9b5931426728ffa9d5e78ea1d908eb02`, hợp nhất `2026-11-22T14:41:33Z`) | **Branch:** `proposal/module-budget-frontend-src` (`97bae48e` -> `fb2fcd53`) | **Base:** `368cdbd1` | **Issue:** [#865](https://github.com/vvChu/ccba-agent-platform/issues/865) (`CLOSED`)

- **Thành phần chính (`4 files, +94/-5, 51 logic LOC`):** Bổ sung `"frontend/src"` vào `DEFAULT_PRODUCTION_ROOTS` tại [`_module_size_budget.py`](../../../packages/ccba-harness/src/ccba_harness/_module_size_budget.py); đồng bộ SSOT sang [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) (`930 <= 941` LOC); bổ sung `test_frontend_src_tsx_enforced_and_roots_parity` trong [`test_module_size_budget_seam.py`](../../../packages/ccba-harness/tests/test_module_size_budget_seam.py); cập nhật [`2026-11-22_module-budget-frontend-src.md`](../../../.agents/proposals/2026-11-22_module-budget-frontend-src.md) (`status: "merged"`, `merged_commit: ac6f83dc`, đính chính cờ `--ratchet-update`).
- **Nghiệm thu:** `809 passed, 6 skipped, 81 deselected` (`14.51s`), `ruff`/`mypy`/`check_spoke_leakage.py` (`0` violations), `validate_docs.py`/`compile_catalog.py`/`compile_skills_docs.py`/`sync_hub_adr_matrix.py` (`61` ADRs) PASS, `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#865` `CLOSED`, walkthrough PR [#869](https://github.com/vvChu/ccba-agent-platform/pull/869) (`e5dc4bf6`).

---

## 16. Lưu Trữ Phát Hành Trước Đó — Thay `gemini-3.7-flash-high` Trong `ccba-ai-qc-pccc-audit` & Living Doc SSoT Parity (`PR #867` / `#847`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#867](https://github.com/vvChu/ccba-agent-platform/pull/867) (`368cdbd13c80b16f976b1ebb2a6a033c4f83814b`, hợp nhất `2026-11-22T14:35:28Z`) | **Branch:** `fix/issue-847-pccc-audit-living-doc-drift` (`42aac9ae`) | **Base:** `ccf3ab44` | **Issue:** [#847](https://github.com/vvChu/ccba-agent-platform/issues/847) (`CLOSED`)

- **Thành phần chính (`3 files, +149/-117`):** Thay thế `ModelArchetype.REASONING` / `gemini-3.7-flash-high` bằng `ModelArchetype.TIER_REASONING` / `"tier-reasoning"` (khớp [`routing.py`](../../../packages/ccba-ai/src/ccba_ai/routing.py)) trong [`SKILL.md`](../../../.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md) (`v1.0.1`); nhập khẩu `LIVING_DOC_BANNED_TOKENS` từ [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) vào [`audit_skills_hygiene.py`](../../../scripts/governance/audit_skills_hygiene.py) (`_scan_living_doc_drift()`, thu gọn `819` -> `782` LOC); bổ sung 2 test parity trong [`test_audit_skills_hygiene.py`](../../../tests/governance/test_audit_skills_hygiene.py).
- **Nghiệm thu:** `verify-patch --preset skill` (`4/4`) & `--preset ci` (`7/7`), `audit_skills_hygiene.py --check` (`77 GREEN`), `79` governance tests + `406` script tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.28s` / `29.84s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 867` exit `0`, Issue `#847` `CLOSED`, và walkthrough PR [#868](https://github.com/vvChu/ccba-agent-platform/pull/868) (`5c23674f`).

---

## 17. Lưu Trữ Phát Hành Trước Đó — Bộ Chuẩn Bảng Màu, Template Tier 2A & YAML Schema Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 (`PR #863` / `Part 2 of #856`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#863](https://github.com/vvChu/ccba-agent-platform/pull/863) (`478991cc8c65d5fc0bb3fe97f2bcc3d6de8786d0`, hợp nhất `2026-11-22T13:59:41Z`) | **Branch:** `docs/issue-856-docx-tech-report-standards` (`91d1f8e3`) | **Base:** `357520a0` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED`)

- **Thành phần chính (`5 files, +258/-1`):** Chuẩn hóa [`docx-ccba-brand.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/docx-ccba-brand.md), [`docx-ky-thuat-bao-cao-danh-gia.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/docx-ky-thuat-bao-cao-danh-gia.md), [`tech_report_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/tech_report_template_schema.yaml), định tuyến `TechnicalReportBuilder` / `build_tech_report_from_yaml` trong [`docx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/docx.md) và nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) lên `v2.3.0`.
- **Nghiệm thu:** `ccba-ooxml tech-report` (`success: true`), 3-page PDF Visual QA PASS, `verify-patch --preset ci` (`7/7 PASS`), `116` governance tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 863` exit `0`, Issue `#856` `CLOSED`, walkthrough PR [#864](https://github.com/vvChu/ccba-agent-platform/pull/864) (`ccf3ab44`).

---

## 18. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 & CLI `tech-report` (`PR #861` / `Part 1 of #856`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#861](https://github.com/vvChu/ccba-agent-platform/pull/861) (`42e15a42eab82252cd4209189ff96f57f90e32e6`) | **Branch:** `feat/issue-856-docx-tech-report-builder` (`d708cae6`) | **Base:** `4b699aa4` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED` sau PR `#863`)

- **Thành phần chính:** Bổ sung `CCBADocxTheme` & XSD helpers ([`_report_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_theme.py)), Page 1 cover/chrome/KPIs/khối ký đối xứng ([`_report_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_chrome.py)), `TechnicalReportBuilder` / `build_tech_report_from_yaml` & CLI `ccba-ooxml tech-report` ([`_tech_report.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_tech_report.py), [`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng PEP 562 lazy exports (`78 → 81`) tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), 6 neo [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) (`LF SHA-256 ca1c57e8...`), [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml), [`docs/index.html`](../../../docs/index.html), và 4 unit/XML DOM tests ([`test_docx_tech_report.py`](../../../packages/ccba-ooxml/tests/test_docx_tech_report.py)).
- **Nghiệm thu:** `pytest packages/ccba-ooxml/tests` (`119 passed`), `run_verify_ooxml.py` (`6 passed`), `verify-patch --preset ci` (`7/7 PASSED`), `mypy` (`69` files clean), `check_spoke_leakage.py` (`0` violations), 3-page PDF Visual QA PASS, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.16s` / `29.67s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 861` exit `0`, và walkthrough PR [#862](https://github.com/vvChu/ccba-agent-platform/pull/862) (`357520a0`).

---

## 19. Lưu Trữ Phát Hành Trước Đó — Bộ Quy Chuẩn & Mẫu YAML IR Bảng Tính Song Ngữ XLSX (`PR #853` / `Part 2 of #851`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#853](https://github.com/vvChu/ccba-agent-platform/pull/853) (`22dc01a372ec8d58e9a87564015be17831a86b79`) | **Branch:** `proposal/xu-ly-van-phong-xlsx-calc-standards` (`718e5e05` -> `8fe88b44`, đồng bộ `19f8ece7`) | **Base:** `19f8ece7` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851) (`CLOSED`)

- **Thành phần chính:** Bổ sung [`xlsx-bang-tinh-ky-thuat-song-ngu.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/xlsx-bang-tinh-ky-thuat-song-ngu.md), [`calc_sheet_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/calc_sheet_template_schema.yaml), **Palette X4** trong [`xlsx-palettes.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/xlsx-palettes.md), [`xlsx-structure.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/structure/xlsx-structure.md), định tuyến Deep Seam & 5 bẫy thực chiến trong [`xlsx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/xlsx.md), nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) `v2.2.0`, kèm [`2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md`](../../../.agents/proposals/2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md).
- **Nghiệm thu:** `validate_skills.py --enforce-gpi` `77/77 PASSED` (`GPI = 9.50 < 12.0`), `106` governance tests pass, `ruff check`/`format` pass (`908` files), PDF smoke test A4 Portrait 4 trang (`Q=18`, `V=64.8`, `formula_errors=[]`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#851` `CLOSED`.

---

## 20. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Bảng Tính Song Ngữ & Windows Excel COM Engine (`PR #852` / `Part 1 of #851`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#852](https://github.com/vvChu/ccba-agent-platform/pull/852) (`e7530dd0dbe564453efa64a7a2ad57492f3884d4`) | **Branch:** `proposal/ooxml-xlsx-calc-sheet-and-excel-com` (`9cc97214` -> `978b46e2`, rebased trên `8b1ace7e`) | **Base:** `8b1ace7e` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851)

- **Thành phần chính:** Nâng cấp [`converter.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/converter.py) (`_convert_via_excel`, `xlsx_to_pdf`), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py) (`_recalc_via_excel_com`, `audit_xlsx_formula_errors`), bổ sung [`_calc_sheet.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_sheet.py), [`_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_theme.py), [`_calc_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_chrome.py), CLI `ccba-ooxml calc-sheet` ([`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng `ccba_ooxml.__all__` (`72 -> 78`), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) và [`2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md`](../../../.agents/proposals/2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md).
- **Nghiệm thu:** Tier 2 Boost (`121 passed`, `mypy` `66` files clean, `ruff` `82` files, `77/77` skills), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.34s` / `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 21. Lưu Trữ Phát Hành Trước Đó — Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp Chuẩn `ADR-0062` (`PR #846`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A

- **Thành phần chính:** Cập nhật [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) (`13 -> 14` spokes): đăng ký mới `SDS for Data Center` (`b35979ec03bf`, `project_delivery`) và nâng cấp 4 Windows spokes lên `ADR-0062` (`static_hash` + `archetype`, đạt `14/14` = `100%` chuẩn `ADR-0062`, `256-byte` RSA-2048 ciphertexts).
- **Nghiệm thu:** `sanitize_review_diff.py` `[PASS]`, `check_spoke_leakage.py` `0` violations, `door-triage` `PAVED_ROAD`, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS trên `9cc07fca`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 846` exit `0`, `compile_catalog.py --check` `[OK]`.

---

## 22. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 23. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 24. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 25. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
