# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)
## Features: `.md`-Based Spoke Retrospective Gates & Lazy `ccba_ooxml.xlsx` Seam

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`)  
> **Trạng thái chung:** ✅ **2/2 PRs MERGED, 12/12 ISOLATED TEST TARGETS PASS (TRIHT x2), 8/8 CI CHECKS PASS x2, 0 UNRESOLVED PR COMMENTS, ISSUES #844 & #842 CLOSED**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#845` (`#844`)

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Spoke ADR Matrix No-Orphan & Exit Code** | [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py) | Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` (ưu tiên `docs/adr` rồi `.md/adr`, tránh tạo thư mục mồ côi), sửa exit `1` khi `not success`, tách helper giữ `795 <= 800` LOC. | Verified |
| **2. Profile `generic-spoke`** | [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py) | Thêm `--profile generic-spoke`, `--max-lines` (mặc định `115` dòng) và chặn `--compact` dưới `generic-spoke`. | Verified |
| **3. Skill `/ccba-session-retrospective` `v1.7.2`** | [`SKILL.md`](../../../.agents/skills/ccba-session-retrospective/SKILL.md) | Nâng `1.7.1` -> `1.7.2` (`6,507 / 6,584` tokens), cập nhật Bước 2/4/5 tương thích Spoke dùng `.md/`. | Verified |
| **4. Kiểm thử đơn vị Governance** | [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py), [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py) | Bổ sung 5 ca kiểm thử tự động cho `.md/adr`, `--dry-run`, `--create-adr-dir`, `generic-spoke` và tương thích ngược. | Verified |

---

## 2. Tổng Kết Thay Đổi Kỹ Thuật — PR `#848` (`#842`)

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Deep Subpackage `ccba_ooxml.xlsx`** | [`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), [`_safety.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_safety.py), [`_filler.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_filler.py), [`_writer.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_writer.py), [`_reader.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_reader.py), [`_models.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_models.py) | Triển khai `XlsxTemplateFiller`, `XlsxWorkbookWriter`, `XlsxReader`, `XlsxFillConfig`, `XlsxHeaderStyle`, `sanitize_xlsx_value`, `XlsxMediaLimitError`, `MergedCellWriteError`; preflight stdlib `RULE-5.13` trước mọi `load_workbook()`, chống formula injection & bảo vệ `MergedCell` / `TemplateProtectionError`. | Verified |
| **2. PEP 562 Lazy Exports & `calc.py`** | [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`pyproject.toml`](../../../packages/ccba-ooxml/pyproject.toml), [`AGENTS.md`](../../../packages/ccba-ooxml/AGENTS.md) | Mở rộng exports `64 -> 72`, thêm `openpyxl>=3.1.0`, giữ import gốc `< 25 ms` không nạp `openpyxl`, và siết fallback `calc.recalc_xlsx` bằng preflight + `finally: wb.close()`. | Verified |
| **3. Contracts, Linter, Portal & Anchor** | [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`pyproject.toml`](../../../pyproject.toml), [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml), [`index.html`](../../../docs/index.html), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`INDEX.md`](../../../packages/ccba-harness/features/INDEX.md) | Mở rộng `ooxml_processor.v1` (`out` thêm `xlsx`), cập nhật `TID251` & `ignore_missing_imports` (`openpyxl.*`), tái biên dịch catalog/portal, nâng chốt `64 -> 72` và re-anchor SHA-256 LF giữ `sync_commit` `7259350d`. | Verified |
| **4. Kiểm thử Round-Trip & Isolation + Biên bản Grilling** | [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`test_phase1_ooxml_seams.py`](../../../packages/ccba-ooxml/tests/test_phase1_ooxml_seams.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md) | Kiểm chứng XML DOM round-trip, 3 modes `on_merged`, preflight `xl/media/* > 2 MiB` trước `load_workbook()`, latency `< 25 ms`, và lưu biên bản Grilling + Grok Peer Plan Audit `APPROVE_PLAN`. | Verified |

---

## 3. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **TRIHT Cổng 0.1–0.3 trên PR `#845` (`e2a42753`):**
  - Cổng 0.1 & 0.3 (`check_release_cleanliness.py --phase pre/post`): `PASS` (100% Hermetic).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` 4.87s, `ccba-diagram` 0.35s, `ccba-harness` 11.60s, `ccba-legal-intel` 47.60s, `ccba-maskara` 0.35s, `ccba-notebooklm` 0.40s, `ccba-ooxml` 2.16s, `ccba-pdf-prep` 9.67s, `ccba-qc-core` 1.10s, `mdconverter` 2.36s, `scripts` 15.24s, `root-tests` `614 passed, 1 skipped, 10 deselected` in 29.52s).
  - `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 845` exit `0`, merge `--squash` @ `76f48be8`, Issue `#844` `CLOSED`.
- **TRIHT Cổng 0.1–0.3 trên PR `#848` đã rebase (`07c6549e`):**
  - Cổng 0.1 & 0.3 (`check_release_cleanliness.py --phase pre/post`): `PASS` (100% Hermetic).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ooxml` `103 passed, 1 deselected` in 2.46s; `root-tests` `614 passed, 1 skipped, 10 deselected` in 29.56s; cùng 10 package targets còn lại đều `PASS`).
  - `8/8` CI `SUCCESS` trên commit `07c6549e`, `audit_pr_comments.py --pr 848` exit `0`, `door-triage` `tradeoff_card_valid: true`.
- **Hậu hợp nhất trên `main` (`deeae22d`, `--merge` theo `RULE-2.21`):**
  - `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`.
  - `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` **5 passed** (`0.24s`), `run_verify_ooxml.py` **6 passed** (`0.24s`), Issue `#842` `CLOSED` (gỡ nhãn `in-progress`, comment `#issuecomment-7073929557`), nhánh feature local & remote đã dọn sạch.

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
