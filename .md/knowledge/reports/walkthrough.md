# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #861` (`Part 1 of #856`)
## Feat(ooxml): Bộ Dựng Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 (`TechnicalReportBuilder`) & CLI `tech-report`

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#861](https://github.com/vvChu/ccba-agent-platform/pull/861) (`42e15a42eab82252cd4209189ff96f57f90e32e6`) | **Branch:** `feat/issue-856-docx-tech-report-builder` (`d708cae6`) | **Base:** `4b699aa4` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`OPEN` — `Part 1/2`, giữ mở cho PR 2 Tier 2A)  
> **Trạng thái chung:** ✅ **PR #861 MERGED (`--merge`), 12/12 TRIHT TARGETS PASS (`614` ROOT TESTS), `119` OOXML TESTS PASS, `8/8` CI CHECKS PASS, 0 UNRESOLVED PR COMMENTS, 3-PAGE PDF VISUAL QA PASS**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#861` (`Part 1 of #856`)

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Theme, Hình Học A4 & XSD Helpers** | [`_report_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_theme.py) | Bổ sung `CCBADocxTheme` (Brand v3.4: `#363883`, `#DA251C`, `#0093DD`, `#005A9C`), hằng số A4 (`11906 × 16838` DXA, `CONTENT_WIDTH = 9071` DXA), `apply_rfonts()` 4 khe `Segoe UI`, `normalize_hex()` idempotent, `wcag_safe_text_hex()` (`#0093DD → #005A9C`), `normalize_col_widths()`, `set_table_fixed_grid()`, `set_row_cant_split()`, `set_row_tbl_header()`, và XML fields `PAGE`/`NUMPAGES`. | Verified |
| **2. Cover, Chrome, KPIs & Atomic Sign-off** | [`_report_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_chrome.py) | Triển khai Page 1 cover (`different_first_page_header_footer = True`), logo động `logo_ccba_full.png`, khối cơ quan 2 cấp `RULE-6.1`, Document Control Matrix, running header 1 dòng `[3571, 5500]` DXA + tri-color footer `Trang PAGE / NUMPAGES`, KPI strip chuẩn WCAG, và khối ký đối xứng 2/3 cột (`4535 + 4536` / `3024 + 3023 + 3024` DXA). | Verified |
| **3. Section-Agnostic Builder & CLI** | [`_tech_report.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_tech_report.py), [`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py) | Bổ sung `TechnicalReportBuilder`, `load_report_spec()`, `build_tech_report_from_yaml()` hỗ trợ schema động `sections: [...]` (`kpis`, `paragraphs`, `bullets`, `callouts`, `tables` đa hàng tiêu đề, `subsections`), xuất Vector PDF qua `docx_to_pdf`, và subcommand CLI `ccba-ooxml tech-report`. | Verified |
| **4. Exports, Contracts, Anchors & Tests** | [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_docx_tech_report.py`](../../../packages/ccba-ooxml/tests/test_docx_tech_report.py) | Mở rộng PEP 562 lazy exports (`78 → 81`), tái biên dịch [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml) & [`docs/index.html`](../../../docs/index.html), cập nhật 6 neo `verify-ccba-ooxml` (`LF SHA-256 ca1c57e8...`) & Ruff TID251 (`pyproject.toml`), kèm `4` unit/XML DOM tests mới. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Shift-Left & Visual QA Gate (`d708cae6`):**
  - `pytest packages/ccba-ooxml/tests -q`: **119 passed**, 1 deselected (`3.31s`); `run_verify_ooxml.py`: **6 passed** (`0.21s`, 81 lazy exports parity); `pytest tests/governance/{test_module_budget_ratchet,test_dependency_contracts,test_seam_contracts_cli,test_catalog_compiler}.py -q`: **50 passed** (`2.48s`).
  - `ruff check`, `ruff format --check`, `mypy packages/ccba-ooxml/src --follow-imports=silent` (`69` source files clean), `check_ast_function_length` (`<= 50` LOC pass), `check_spoke_leakage.py` (`0` violations across `18` files), `check_hardcoded_parameters.py` (`0` violations), `sanitize_review_diff.py --check` (`[PASS]`), `verify-patch --preset ci`: **7/7 PASSED** (`17880.2 ms`).
  - **Visual QA Gate (LibreOffice `/usr/bin/soffice` + `ccba_pdf_prep`):** Xuất PDF `3` trang (`150 DPI` PNG) kiểm chứng Page 1 cover cân đối không tràn trang, header trang 2+ 1 dòng `[3571, 5500]`, metric `#005A9C` dưới viền `#0093DD`, bảng lặp `<w:tblHeader/>` ở trang 3, và khối ký nguyên tử 2 cột không lặp email/org.
- **TRIHT Pre-Release (`Cổng 0.1–0.3`), CI & Merge (`42e15a42`, `--merge --delete-branch` theo `RULE-2.21`):**
  - Cổng 0.1 (`--phase pre`) `PASS`; Cổng 0.2 `run_isolated_tests.py --all --stress` **12/12 targets PASS** (`ccba-ooxml` `3.52s`, `scripts` `15.51s`, `root-tests`: `614 passed, 1 skipped, 10 deselected` in `29.16s` / `29.67s`); Cổng 0.3 (`--phase post`) `PASS`.
  - GitHub CI `8/8` `SUCCESS`, `audit_pr_comments.py --pr 861` exit `0`, `reviewRequests` rỗng, `door-triage` `ONE_WAY_DOOR` (`tradeoff_card_valid: true`), `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` `[OK]`, `run_verify_ooxml.py` `6 passed`. Issue `#856` giữ `OPEN` kèm comment tiến độ (`#issuecomment-7079679808`) chờ PR 2/2.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Bộ Quy Chuẩn & Mẫu YAML IR Bảng Tính Song Ngữ XLSX (`PR #853` / `Part 2 of #851`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#853](https://github.com/vvChu/ccba-agent-platform/pull/853) (`22dc01a372ec8d58e9a87564015be17831a86b79`) | **Branch:** `proposal/xu-ly-van-phong-xlsx-calc-standards` (`718e5e05` -> `8fe88b44`, đồng bộ `19f8ece7`) | **Base:** `19f8ece7` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851) (`CLOSED`)

- **Thành phần chính:** Bổ sung [`xlsx-bang-tinh-ky-thuat-song-ngu.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/xlsx-bang-tinh-ky-thuat-song-ngu.md), [`calc_sheet_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/calc_sheet_template_schema.yaml), **Palette X4** trong [`xlsx-palettes.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/xlsx-palettes.md), [`xlsx-structure.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/structure/xlsx-structure.md), định tuyến Deep Seam & 5 bẫy thực chiến trong [`xlsx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/xlsx.md), nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) `v2.2.0`, kèm [`2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md`](../../../.agents/proposals/2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md).
- **Nghiệm thu:** `validate_skills.py --enforce-gpi` `77/77 PASSED` (`GPI = 9.50 < 12.0`), `106` governance tests pass, `ruff check`/`format` pass (`908` files), PDF smoke test A4 Portrait 4 trang (`Q=18`, `V=64.8`, `formula_errors=[]`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#851` `CLOSED`.

---

## 4. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Bảng Tính Song Ngữ & Windows Excel COM Engine (`PR #852` / `Part 1 of #851`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#852](https://github.com/vvChu/ccba-agent-platform/pull/852) (`e7530dd0dbe564453efa64a7a2ad57492f3884d4`) | **Branch:** `proposal/ooxml-xlsx-calc-sheet-and-excel-com` (`9cc97214` -> `978b46e2`, rebased trên `8b1ace7e`) | **Base:** `8b1ace7e` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851)

- **Thành phần chính:** Nâng cấp [`converter.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/converter.py) (`_convert_via_excel`, `xlsx_to_pdf`), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py) (`_recalc_via_excel_com`, `audit_xlsx_formula_errors`), bổ sung [`_calc_sheet.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_sheet.py), [`_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_theme.py), [`_calc_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_chrome.py), CLI `ccba-ooxml calc-sheet` ([`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng `ccba_ooxml.__all__` (`72 -> 78`), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) và [`2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md`](../../../.agents/proposals/2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md).
- **Nghiệm thu:** Tier 2 Boost (`121 passed`, `mypy` `66` files clean, `ruff` `82` files, `77/77` skills), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.34s` / `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 5. Lưu Trữ Phát Hành Trước Đó — Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp Chuẩn `ADR-0062` (`PR #846`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A

- **Thành phần chính:** Cập nhật [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) (`13 -> 14` spokes): đăng ký mới `SDS for Data Center` (`b35979ec03bf`, `project_delivery`) và nâng cấp 4 Windows spokes lên `ADR-0062` (`static_hash` + `archetype`, đạt `14/14` = `100%` chuẩn `ADR-0062`, `256-byte` RSA-2048 ciphertexts).
- **Nghiệm thu:** `sanitize_review_diff.py` `[PASS]`, `check_spoke_leakage.py` `0` violations, `door-triage` `PAVED_ROAD`, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS trên `9cc07fca`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 846` exit `0`, `compile_catalog.py --check` `[OK]`.

---

## 6. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 7. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 8. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 9. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
