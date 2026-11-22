# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #852` (`Part 1 of #851`)
## Feature: Bilingual XLSX Calculation Sheet Deep Seam & Windows Excel COM Engine

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#852](https://github.com/vvChu/ccba-agent-platform/pull/852) (`e7530dd0dbe564453efa64a7a2ad57492f3884d4`) | **Branch:** `proposal/ooxml-xlsx-calc-sheet-and-excel-com` (`9cc97214` -> `978b46e2`, rebased trên `8b1ace7e`) | **Base:** `8b1ace7e` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851) (`OPEN`, chờ `PR #853` đóng)  
> **Trạng thái chung:** ✅ **PR #852 MERGED, 12/12 ISOLATED TEST TARGETS PASS (TRIHT), 8/8 CI CHECKS PASS, 0 UNRESOLVED PR COMMENTS, 78 PUBLIC DEEP SEAMS VERIFIED**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#852` (`Part 1 of #851`)

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Định tuyến PDF Excel COM (`win32`)** | [`converter.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/converter.py) | Bổ sung `_convert_via_excel`, `_resolve_pdf_engine`, và `xlsx_to_pdf` chuyển `.xlsx/.xls/.xlsm/.xlsb` sang `Excel.Application` trên `win32` (fallback `soffice`); Self-Healing khóa `AutomationSecurity=3`, `UpdateLinks=0`, và kiểm tra `verify_xlsx_zip_safety` cho `.xlsx/.xlsm`. | Verified |
| **2. Tính lại Công thức & Quét Lỗi** | [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py) | Giữ pure-stdlib ở top-level; thêm `_recalc_via_excel_com` (`AutomationSecurity=3`, `UpdateLinks=0`, `CalculateFullRebuild`), `audit_xlsx_formula_errors()`, `prefer_engine`/`export_pdf`/`check_errors`, cờ `formulas_evaluated`, và fail-loud khi thiếu engine xuất PDF. | Verified |
| **3. Bộ dựng Bảng tính Song ngữ & CLI** | [`_calc_sheet.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_sheet.py), [`_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_theme.py), [`_calc_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_chrome.py), [`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py) | Triển khai `CCBAExcelTheme` (Brand v3.4 + chuẩn hóa `#HEX` trong `make_side`/`theme_font`), `CalculationSheetBuilder`, `build_calc_sheet_from_yaml`, `resolve_formula`, `RULE-6.1` header + tỷ lệ logo động, footer escape `&` -> `&&`, A4 Portrait (`fitToHeight=0`), và CLI `ccba-ooxml calc-sheet`. | Verified |
| **4. Hợp đồng Seam, Harness & Proposal** | [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md`](../../../.agents/proposals/2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md) | Mở rộng `ccba_ooxml.__all__` / `_LAZY_EXPORTS` (`72 -> 78`), cập nhật `seam-contracts.yaml`, `covered_sha256` trong `verify-ccba-ooxml` (`sync_commit` `7259350d`), và chuyển proposal sang `status: "merged"`. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Tier 2 Boost Review & Self-Healing (`978b46e2` trong `/home/vvc/ccba/wt-hub-852`):**
  - `pytest packages/ccba-ooxml/tests packages/ccba-harness/.agents/skills/verify-ccba-ooxml/harness/test_ooxml_suite.py`: **121 passed, 1 deselected** (`2.43s`); `run_verify_ooxml.py`: **6 passed** (`0.20s`).
  - `mypy packages/ccba-ooxml/src --follow-imports=silent`: `Success: no issues found in 66 source files`; `ruff check` & `ruff format --check`: PASS (`82` files); AST function lengths: `over_50=[]` trên cả 5 module sửa đổi; `validate_skills.py --enforce-gpi`: **77/77 PASSED**.
- **Local TRIHT Cổng 0.1–0.3 trên PR `#852` (`978b46e2` trong `/home/vvc/ccba/wt-hub-852-release`):**
  - Cổng 0.1 & 0.3 (`check_release_cleanliness.py --phase pre/post`): `PASS` (`100%` Hermetic).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` `5.43s`, `ccba-diagram` `0.35s`, `ccba-harness` `13.15s`, `ccba-legal-intel` `48.31s`, `ccba-maskara` `0.30s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `2.86s`, `ccba-pdf-prep` `9.74s`, `ccba-qc-core` `1.16s`, `mdconverter` `2.31s`, `scripts` `15.73s`, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.34s` / total `30.00s`).
- **CI & Hậu hợp nhất trên `main` (`e7530dd0`, `--merge` theo `RULE-2.21`):**
  - `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 852` exit `0`, `reviewRequests` rỗng, nhánh remote `proposal/ooxml-xlsx-calc-sheet-and-excel-com` & worktree đã dọn sạch.
  - `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py`: **5 passed**, `run_verify_ooxml.py`: **6 passed**.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp Chuẩn `ADR-0062` (`PR #846`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A

- **Thành phần chính:** Cập nhật [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) (`13 -> 14` spokes): đăng ký mới `SDS for Data Center` (`b35979ec03bf`, `project_delivery`) và nâng cấp 4 Windows spokes lên `ADR-0062` (`static_hash` + `archetype`, đạt `14/14` = `100%` chuẩn `ADR-0062`, `256-byte` RSA-2048 ciphertexts).
- **Nghiệm thu:** `sanitize_review_diff.py` `[PASS]`, `check_spoke_leakage.py` `0` violations, `door-triage` `PAVED_ROAD`, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS trên `9cc07fca`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 846` exit `0`, `compile_catalog.py --check` `[OK]`.

---

## 4. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 5. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 6. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 7. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
