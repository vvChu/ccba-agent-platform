# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #866` (`#865`)
## Fix(guardrails): Bổ Sung `frontend/src` Vào `DEFAULT_PRODUCTION_ROOTS` & SSOT Module Size Budget Cho Spokes

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#866](https://github.com/vvChu/ccba-agent-platform/pull/866) (`ac6f83dc9b5931426728ffa9d5e78ea1d908eb02`, hợp nhất `2026-11-22T14:41:33Z`) | **Branch:** `proposal/module-budget-frontend-src` (`97bae48e` -> `fb2fcd53`) | **Base:** `368cdbd1` | **Issue:** [#865](https://github.com/vvChu/ccba-agent-platform/issues/865) (`CLOSED`)  
> **Trạng thái chung:** ✅ **PR #866 MERGED (`--squash`), ISSUE #865 CLOSED, `809 passed` LOCAL TESTS (`6 skipped, 81 deselected`), `8/8` CI CHECKS PASS, 0 UNRESOLVED PR COMMENTS, `check_spoke_leakage.py` 0 VIOLATIONS, `--ratchet-update` CLI FLAG VERIFIED**

---

## 1. Tổng Kết Thay Đổi Mã Nguồn & Proposal — PR `#866` (`#865`)

| Thành Phần | Tệp Thay Đổi Chính (`4 files, +94/-5, 51 logic LOC`) | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Tier-0 Module Size Budget Seam** | [`_module_size_budget.py`](../../../packages/ccba-harness/src/ccba_harness/_module_size_budget.py) | Bổ sung `"frontend/src"` vào `DEFAULT_PRODUCTION_ROOTS` (`106 <= 120` LOC, thuần stdlib), giúp `iter_production_files()` và `peer_gate.check_module_size_budget()` quét `.py/.js/.ts/.tsx` dưới `frontend/src/` và cắt tỉa `node_modules`. | Verified |
| **2. Spoke Cleanliness SSOT Sync** | [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) | Đồng bộ `_DEFAULT_BUDGET_ROOTS` và bổ sung `_iter_budget_files()` để `_append_module_budget_violations()` và `_run_ratchet_update()` dùng `seam.DEFAULT_PRODUCTION_ROOTS` làm SSOT trên Spokes (`930 <= 941` LOC baseline). | Verified |
| **3. Regression & Parity Tests** | [`test_module_size_budget_seam.py`](../../../packages/ccba-harness/tests/test_module_size_budget_seam.py) | Bổ sung `test_frontend_src_tsx_enforced_and_roots_parity` kiểm chứng ép trần `frontend/src/*.tsx > 800` LOC, cắt tỉa `node_modules`, ratchet baseline và bất biến `_DEFAULT_BUDGET_ROOTS == DEFAULT_PRODUCTION_ROOTS`. | Verified |
| **4. RFC Proposal & Flag Correction** | [`2026-11-22_module-budget-frontend-src.md`](../../../.agents/proposals/2026-11-22_module-budget-frontend-src.md) | Tài liệu đề xuất ADR-0045 từ Spoke `IBST_UNIFIED_ERP` (Điểm rơi 5); hậu kiểm chuyển `status: "merged"` (`merged_commit: ac6f83dc`) và đính chính cờ CLI di trú Spoke từ `--update-budget-baseline` sang **`--ratchet-update`** (cũng đã ghi chú tại `#865`). | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0045` / `ADR-0058` / `ADR-0067`)

- **Worker 1–3 Local Review Worktree (`97bae48e`):**
  - **Worker 1 (Leakage & Privacy):** `check_spoke_leakage.py` (`4 files`, `0` critical violations, `0` warnings, exit `0`); `sanitize_review_diff.py --check --base origin/main --head HEAD` `[PASS]`.
  - **Worker 2 (Tests, Lint, Mypy & AST):** `pytest packages/ccba-harness/tests/ tests/governance/{test_module_budget_ratchet,test_parameter_scanner_parity,test_spoke_cleanliness_allowlist,test_workflow_script_parity}.py scripts/tests/{test_spoke_cleanliness,test_guardrail_cleanliness_allowlist,test_scope_pruner_and_manifest_cleanliness}.py -q` (**809 passed**, `6 skipped`, `81 deselected` in `14.51s`); `ruff check` (`0` errors) & `ruff format --check` (`174` files); `mypy packages/ccba-harness/src --follow-imports=silent` (`106` files clean); `check_ast_function_length` (`PASS`) & `check_module_size_budget` (`567` files `PASS`); mục `[Module Size Budget]` trong `check_spoke_cleanliness.py` (`151` files Hub `PASS`).
  - **Worker 3 (Docs & Catalog):** `validate_docs.py . --src scripts,packages --changed` exit `0`; `compile_catalog.py --check` `[OK]`; `compile_skills_docs.py --check` `[OK]`; `sync_hub_adr_matrix.py --check` `[PASS]` (`61` ADRs).
- **CI, Copilot & Post-Merge (`fb2fcd53` -> `ac6f83dc9b5931426728ffa9d5e78ea1d908eb02`, `--squash --delete-branch`):**
  - Rebased lên `368cdbd1` (`#867`), GitHub CI `8/8` `SUCCESS`, `mergeStateStatus: CLEAN`, `reviewRequests` rỗng, `audit_pr_comments.py --repo vvChu/ccba-agent-platform 866` exit `0`.
  - `0/4` tệp nằm trong `covered_paths` của `verify-ccba-*` (`RULE-2.21`), hợp nhất `--squash --delete-branch` tự động đóng Issue `#865` (`CLOSED`) và đăng biên bản nghiệm thu + đính chính cờ `--ratchet-update` tại `#issuecomment-7080740011`.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Thay `gemini-3.7-flash-high` Trong `ccba-ai-qc-pccc-audit` & Living Doc SSoT Parity (`PR #867` / `#847`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#867](https://github.com/vvChu/ccba-agent-platform/pull/867) (`368cdbd13c80b16f976b1ebb2a6a033c4f83814b`, hợp nhất `2026-11-22T14:35:28Z`) | **Branch:** `fix/issue-847-pccc-audit-living-doc-drift` (`42aac9ae`) | **Base:** `ccf3ab44` | **Issue:** [#847](https://github.com/vvChu/ccba-agent-platform/issues/847) (`CLOSED`)

- **Thành phần chính (`3 files, +149/-117`):** Thay thế `ModelArchetype.REASONING` / `gemini-3.7-flash-high` bằng `ModelArchetype.TIER_REASONING` / `"tier-reasoning"` (khớp [`routing.py`](../../../packages/ccba-ai/src/ccba_ai/routing.py)) trong [`SKILL.md`](../../../.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md) (`v1.0.1`); nhập khẩu `LIVING_DOC_BANNED_TOKENS` từ [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) vào [`audit_skills_hygiene.py`](../../../scripts/governance/audit_skills_hygiene.py) (`_scan_living_doc_drift()`, thu gọn `819` -> `782` LOC); bổ sung 2 test parity trong [`test_audit_skills_hygiene.py`](../../../tests/governance/test_audit_skills_hygiene.py).
- **Nghiệm thu:** `verify-patch --preset skill` (`4/4`) & `--preset ci` (`7/7`), `audit_skills_hygiene.py --check` (`77 GREEN`), `79` governance tests + `406` script tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.28s` / `29.84s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 867` exit `0`, Issue `#847` `CLOSED`, và walkthrough PR [#868](https://github.com/vvChu/ccba-agent-platform/pull/868) (`5c23674f`).

---

## 4. Lưu Trữ Phát Hành Trước Đó — Bộ Chuẩn Bảng Màu, Template Tier 2A & YAML Schema Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 (`PR #863` / `Part 2 of #856`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#863](https://github.com/vvChu/ccba-agent-platform/pull/863) (`478991cc8c65d5fc0bb3fe97f2bcc3d6de8786d0`, hợp nhất `2026-11-22T13:59:41Z`) | **Branch:** `docs/issue-856-docx-tech-report-standards` (`91d1f8e3`) | **Base:** `357520a0` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED`)

- **Thành phần chính (`5 files, +258/-1`):** Chuẩn hóa [`docx-ccba-brand.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/docx-ccba-brand.md), [`docx-ky-thuat-bao-cao-danh-gia.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/docx-ky-thuat-bao-cao-danh-gia.md), [`tech_report_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/tech_report_template_schema.yaml), định tuyến `TechnicalReportBuilder` / `build_tech_report_from_yaml` trong [`docx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/docx.md) và nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) lên `v2.3.0`.
- **Nghiệm thu:** `ccba-ooxml tech-report` (`success: true`), 3-page PDF Visual QA PASS, `verify-patch --preset ci` (`7/7 PASS`), `116` governance tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 863` exit `0`, Issue `#856` `CLOSED`, walkthrough PR [#864](https://github.com/vvChu/ccba-agent-platform/pull/864) (`ccf3ab44`).

---

## 5. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 & CLI `tech-report` (`PR #861` / `Part 1 of #856`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#861](https://github.com/vvChu/ccba-agent-platform/pull/861) (`42e15a42eab82252cd4209189ff96f57f90e32e6`) | **Branch:** `feat/issue-856-docx-tech-report-builder` (`d708cae6`) | **Base:** `4b699aa4` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED` sau PR `#863`)

- **Thành phần chính:** Bổ sung `CCBADocxTheme` & XSD helpers ([`_report_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_theme.py)), Page 1 cover/chrome/KPIs/khối ký đối xứng ([`_report_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_chrome.py)), `TechnicalReportBuilder` / `build_tech_report_from_yaml` & CLI `ccba-ooxml tech-report` ([`_tech_report.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_tech_report.py), [`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng PEP 562 lazy exports (`78 → 81`) tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), 6 neo [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) (`LF SHA-256 ca1c57e8...`), [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml), [`docs/index.html`](../../../docs/index.html), và 4 unit/XML DOM tests ([`test_docx_tech_report.py`](../../../packages/ccba-ooxml/tests/test_docx_tech_report.py)).
- **Nghiệm thu:** `pytest packages/ccba-ooxml/tests` (`119 passed`), `run_verify_ooxml.py` (`6 passed`), `verify-patch --preset ci` (`7/7 PASSED`), `mypy` (`69` files clean), `check_spoke_leakage.py` (`0` violations), 3-page PDF Visual QA PASS, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.16s` / `29.67s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 861` exit `0`, và walkthrough PR [#862](https://github.com/vvChu/ccba-agent-platform/pull/862) (`357520a0`).

---

## 6. Lưu Trữ Phát Hành Trước Đó — Bộ Quy Chuẩn & Mẫu YAML IR Bảng Tính Song Ngữ XLSX (`PR #853` / `Part 2 of #851`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#853](https://github.com/vvChu/ccba-agent-platform/pull/853) (`22dc01a372ec8d58e9a87564015be17831a86b79`) | **Branch:** `proposal/xu-ly-van-phong-xlsx-calc-standards` (`718e5e05` -> `8fe88b44`, đồng bộ `19f8ece7`) | **Base:** `19f8ece7` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851) (`CLOSED`)

- **Thành phần chính:** Bổ sung [`xlsx-bang-tinh-ky-thuat-song-ngu.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/xlsx-bang-tinh-ky-thuat-song-ngu.md), [`calc_sheet_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/calc_sheet_template_schema.yaml), **Palette X4** trong [`xlsx-palettes.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/xlsx-palettes.md), [`xlsx-structure.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/structure/xlsx-structure.md), định tuyến Deep Seam & 5 bẫy thực chiến trong [`xlsx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/xlsx.md), nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) `v2.2.0`, kèm [`2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md`](../../../.agents/proposals/2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md).
- **Nghiệm thu:** `validate_skills.py --enforce-gpi` `77/77 PASSED` (`GPI = 9.50 < 12.0`), `106` governance tests pass, `ruff check`/`format` pass (`908` files), PDF smoke test A4 Portrait 4 trang (`Q=18`, `V=64.8`, `formula_errors=[]`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#851` `CLOSED`.

---

## 7. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Bảng Tính Song Ngữ & Windows Excel COM Engine (`PR #852` / `Part 1 of #851`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#852](https://github.com/vvChu/ccba-agent-platform/pull/852) (`e7530dd0dbe564453efa64a7a2ad57492f3884d4`) | **Branch:** `proposal/ooxml-xlsx-calc-sheet-and-excel-com` (`9cc97214` -> `978b46e2`, rebased trên `8b1ace7e`) | **Base:** `8b1ace7e` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851)

- **Thành phần chính:** Nâng cấp [`converter.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/converter.py) (`_convert_via_excel`, `xlsx_to_pdf`), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py) (`_recalc_via_excel_com`, `audit_xlsx_formula_errors`), bổ sung [`_calc_sheet.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_sheet.py), [`_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_theme.py), [`_calc_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_chrome.py), CLI `ccba-ooxml calc-sheet` ([`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng `ccba_ooxml.__all__` (`72 -> 78`), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) và [`2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md`](../../../.agents/proposals/2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md).
- **Nghiệm thu:** Tier 2 Boost (`121 passed`, `mypy` `66` files clean, `ruff` `82` files, `77/77` skills), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.34s` / `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 8. Lưu Trữ Phát Hành Trước Đó — Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp Chuẩn `ADR-0062` (`PR #846`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A

- **Thành phần chính:** Cập nhật [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) (`13 -> 14` spokes): đăng ký mới `SDS for Data Center` (`b35979ec03bf`, `project_delivery`) và nâng cấp 4 Windows spokes lên `ADR-0062` (`static_hash` + `archetype`, đạt `14/14` = `100%` chuẩn `ADR-0062`, `256-byte` RSA-2048 ciphertexts).
- **Nghiệm thu:** `sanitize_review_diff.py` `[PASS]`, `check_spoke_leakage.py` `0` violations, `door-triage` `PAVED_ROAD`, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS trên `9cc07fca`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 846` exit `0`, `compile_catalog.py --check` `[OK]`.

---

## 9. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 10. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 11. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 12. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
