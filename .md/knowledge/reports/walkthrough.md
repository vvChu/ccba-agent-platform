# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #854` (`#849`)
## Docs: Phân Tách Cứng Operations OS (`IDOP-CCBA-WAY`) & Financial Ledger Spoke (`IBST_UNIFIED_ERP`) Trong `HUB-ADR-0060`

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)  
> **Trạng thái chung:** ✅ **PR #854 MERGED, 12/12 ISOLATED TEST TARGETS PASS (TRIHT), 8/8 CI CHECKS PASS, 0 UNRESOLVED PR COMMENTS, ISSUE #849 CLOSED**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#854` (`#849`)

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Sơ đồ `FEDERATED SPOKES` & Mục 1** | [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) | Giữ nguyên `bim-planner` và trục `┴` (`33` space lề trái, `33` ký tự lòng khung), thay `ibim_accounting` & `AC_IBSTBM2 / PP_IBSTBM` bằng IBST_UNIFIED_ERP (`31v` Ledger, `[Spoke PG16 loopback]`), thêm câu đếm `4 Hub nền tảng + Operations SOR + Federated Spokes` và cập nhật vai trò SOR của `IDOP-CCBA-WAY`. | Verified |
| **2. Mục 7 Amendment 2026-11-22 & Consequences** | [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md#L184-L223) | Phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (IBST_UNIFIED_ERP), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`) song song Mục 4, xác thực kép + taxonomy fail-closed SHA-256 (IBST_IDOP_TAXONOMY_DIR), 5 trục tương tác Viện KHCN Xây dựng (IBST), tách 2 cải tiến skill sang PR riêng. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Grok Peer Audit (`arch_audit` + `signoff_diff`):** Pass 1 `APPROVE_WITH_CONDITIONS` (`risk_score: 3`, session `b4eb4062-5262-4f73-a50f-cb9d526e474d`) -> Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking conditions, `degraded_reasoning: false`, session `1c31283c-0587-4d77-99cc-013f0ff30599`).
- **Local Shift-Left & TRIHT Cổng 0.1–0.3 trên PR `#854` (`1b85482c` trong `/home/vvc/ccba/wt-hub-849`):**
  - `validate_docs.py . --src scripts,packages --changed`: exit `0` (0 hard errors, 0 warning mới), `sync_hub_adr_matrix.py --check`: `[PASS]` (61 ADRs), `check_spoke_leakage.py`: 0 violations, `sanitize_review_diff.py --check`: `[PASS]`, `maskara.py scan --root .`: exit `0`, `verify-patch --preset adr` & `--preset doc`: `PASS`, `door-triage --enforce-tradeoff-card`: `ONE_WAY_DOOR` / `HUB_CONSTITUTION`, `tradeoff_card_valid: true`.
  - Cổng 0.1 & 0.3 (`check_release_cleanliness.py --phase pre/post`): `PASS` (100% Hermetic).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` 5.28s, `ccba-diagram` 0.35s, `ccba-harness` 13.06s, `ccba-legal-intel` 48.85s, `ccba-maskara` 0.35s, `ccba-notebooklm` 0.40s, `ccba-ooxml` 2.56s, `ccba-pdf-prep` 9.66s, `ccba-qc-core` 1.15s, `mdconverter` 2.37s, `scripts` 15.98s, `root-tests` `614 passed, 1 skipped, 10 deselected` in 29.47s / total 30.00s).
- **CI & Hậu hợp nhất trên `main` (`6d1d3f5e`, `--squash`):**
  - `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, `reviewRequests` rỗng.
  - `compile_catalog.py --check` PASS, `sync_hub_adr_matrix.py --check` PASS, Issue `#849` `CLOSED` (gỡ nhãn `in-progress`, comment `#issuecomment-7074500733`), nhánh feature local/remote & worktree đã dọn sạch.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 4. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 5. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
