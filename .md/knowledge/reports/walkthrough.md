# Báo Cáo Nghiệm Thu Hoàn Thành (Walkthrough) — Phát Hành `PR #895`
## Fix(legal-intel): Khử Lỗi Bold-Glue `____`, Kiểm Định `MALFORMED_BOLD_GLUE`, NFC Gate 11 & Rào Chắn `ccba-legal-ingest` (Issue `#892`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#895](https://github.com/vvChu/ccba-agent-platform/pull/895) (`5d1a8af81c75110417928e3e7a8e0b01fe3a7de7`, hợp nhất `2026-11-24T04:37:05Z`) | **Branch:** `fix/issue-892-bold-glue-nfc-legal-ingest` (`bbdbf3e7` -> `b4d7b9ca`, đã xóa local & remote) | **Base:** `8154720a` | **Issue Đã Đóng:** [#892](https://github.com/vvChu/ccba-agent-platform/issues/892) (`CLOSED`)  
> **Trạng thái chung:** ✅ **PR #895 MERGED (`--squash`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.51s` / `30.23s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS, `door-triage` `ONE_WAY_DOOR` (`escalated_by_streak: true`, Tradeoff Card Valid), `compile_catalog.py --check` `[OK]`**

---

## 1. Tổng Kết Thay Đổi Kỹ Thuật — PR `#895`

| Thành Phần | Tệp Thay Đổi Chính (`9 files, +219/-7`) | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Vá Gốc Bold-Glue `____`** | [`vbpl_admin.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/vbpl_admin.py), [`unit_normalizer.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/unit_normalizer.py) | Gỡ `re.sub` xóa anchor trùng lặp tại `_convert_docx_to_clean_markdown()` để gom SSOT về `normalize_docx_markdown()`; bổ sung `_strip_mammoth_anchors_and_glue()` khử các cặp delimiter bold/italic (`*__...__*`, `**...**`, `__...__`, `*...*`) bị tách qua 1+ thẻ `<a id="[^"]+"></a>` trước khi xóa anchor đơn lẻ và unescape, giữ nguyên 100% đường gạch chân biểu mẫu `_____`. | Verified |
| **2. Kiểm Định `MALFORMED_BOLD_GLUE`** | [`visual_parity.py`](../../../packages/ccba-legal-intel/src/ccba_legal/visual_parity.py) | Bổ sung `_MALFORMED_BOLD_GLUE_RE` (`(?:\s|^)____(?=[A-Za-zÀ-ỹ0-9])`), `_is_bold_glue_exempt()` miễn trừ `templates/` & `sources/`, và cờ `in_code_fence` bỏ qua khối code Markdown trong `lint_document()`, không gây false positive cho ô điền biểu mẫu (`_____ [ghi tên...]`, `Ngày ____ tháng ____`, `Số: ____/QĐ-BXD`). | Verified |
| **3. Chuẩn Hóa Unicode NFC** | [`provenance.py`](../../../packages/ccba-legal-intel/src/ccba_legal/provenance.py) | Bổ sung `unicodedata.normalize("NFC", ...)` trong `normalize_text()` (Gate 0), `compute_docx_to_markdown_parity()` -> `norm_words()`, và bộ lọc preamble hành chính (`"căn cứ "`, `"theo đề nghị "`, `"nơi nhận:"`...), đưa tỷ lệ khớp NFD DOCX ↔ NFC Markdown về `100.0%`. | Verified |
| **4. Skill `ccba-legal-ingest` `v1.4.0` & Tests** | [`SKILL.md`](../../../.agents/skills/ccba-legal-ingest/SKILL.md), [`test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py), [`test_vbpl_admin_templates.py`](../../../packages/ccba-legal-intel/tests/test_vbpl_admin_templates.py), [`test_visual_parity.py`](../../../packages/ccba-legal-intel/tests/test_visual_parity.py), [`test_provenance.py`](../../../packages/ccba-legal-intel/tests/test_provenance.py) | Nâng `ccba-legal-ingest` lên `v1.4.0` (`GPI 24.50`), bổ sung rào chắn đối soát tiêu đề/số hiệu `tvpl_url` kế thừa ở Bước 0 và bắt buộc `--bundle <slug>` với `hydrate_sources_from_vault.py --push` ở Bước 3; đăng ký `"scripts/hydrate_sources_from_vault.py"` trong `SPOKE_SPECIFIC_SCRIPTS`; bổ sung unit tests hồi quy Mammoth DOCX in-memory, `MALFORMED_BOLD_GLUE` và NFD↔NFC parity. | Verified |

---

## 2. Bằng Chứng Kiểm Chứng Thực Nghiệm & Hậu Hợp Nhất (`ADR-0058` / `ADR-0067`)

- **Giao thức TRIHT Pre-Release (Cổng 0.1–0.3):**
  - Cổng 0.1 (`check_release_cleanliness.py --phase pre`): exit `0` (stash tác vụ song song `wip: concurrent work before release PR #895`, working tree sạch 100%).
  - Cổng 0.2 (`run_isolated_tests.py --all --stress`): **12/12 targets PASS** (`ccba-ai` `4.97s`, `ccba-diagram` `0.30s`, `ccba-harness` `11.70s`, `ccba-legal-intel` `48.03s`, `ccba-maskara` `0.35s`, `ccba-notebooklm` `0.40s`, `ccba-ooxml` `6.02s`, `ccba-pdf-prep` `9.69s`, `ccba-qc-core` `1.21s`, `mdconverter` `2.36s`, `scripts` `16.55s`, `root-tests` **`616 passed, 1 skipped, 10 deselected` in `29.51s`** / `30.23s`).
  - Cổng 0.3 (`check_release_cleanliness.py --phase post`): exit `0` (`100% Hermetic`).
- **Shift-Left & Package Verification:**
  - `pytest` 3 file test trọng tâm: `22 passed in 0.24s`; `packages/ccba-legal-intel/tests`: `473 passed, 2 skipped, 20 deselected in 48.38s`.
  - `verify-patch --preset code --target packages/ccba-legal-intel`: `4/4 PASS` (`ruff check`, `ruff format --check`, `mypy --follow-imports=silent`, `pytest`); `verify-patch --preset skill`: `4/4 PASS`; `run_verify_legal_intel.py`: `6 passed in 0.09s`.
  - `check_dependency_contracts.py` (`562` files), `sanitize_review_diff.py --base origin/main --head HEAD --check` (`[PASS]`), `evaluate-gpi` (`24.50` — Tier 2B `ALLOWED`).
- **CI, Copilot & Post-Merge (`5d1a8af81c75110417928e3e7a8e0b01fe3a7de7`, `--squash --delete-branch`):**
  - GitHub Actions CI trên PR `#895`: **8/8 PASS** (`PR Danger Triage & Verifier Gate` `1m20s`, `CI/Deterministic Parity` `1m13s`, `CI/Lint Markdown` `8s`, `CI/Test - Python 3.10/3.11/3.12` `2m34s`/`2m4s`/`1m58s`, `Security & Privacy Scan` `8s`, `Documentation Check` `26s`).
  - `audit_pr_comments.py --pr 895`: exit `0`; `door-triage --enforce-tradeoff-card`: `ONE_WAY_DOOR` (`escalated_by_streak: true`, `cumulative_streak: 3`, Tradeoff Card Valid).
  - Post-merge: `compile_catalog.py --check` `[OK]`, Issue `#892` `CLOSED` (đã gỡ `in-progress`), nhánh `fix/issue-892-bold-glue-nfc-legal-ingest` đã xóa local & remote.

---

## 3. Lưu Trữ Phát Hành Trước Đó — Cấu Hình `--verify-timeout` / `CCBA_VERIFY_TIMEOUT` & Chẩn Đoán Timeout (`PR #893` / `#889`)

> **Pull Request Đã Hợp Nhất (`--merge --delete-branch` theo `RULE-2.21`):** [#893](https://github.com/vvChu/ccba-agent-platform/pull/893) (`2f135728943920041ad146bc7b4bcbc46cfe786a`, hợp nhất `2026-11-24T03:50:11Z`) | **Branch:** `feat/issue-889-configurable-verify-timeout` (`f686ff6b` -> `227175bc`, đã xóa local & remote) | **Base:** `a2f371d1` | **Issue Đã Đóng:** [#889](https://github.com/vvChu/ccba-agent-platform/issues/889) (`CLOSED`, `#issuecomment-7121478815`)

- **Thành phần chính (`14 files, +514/-47`):** Bổ sung `DEFAULT_VERIFY_TIMEOUT = 180.0`, `CCBA_VERIFY_TIMEOUT`, `parse_positive_verify_timeout()`, `resolve_verify_timeout()` và `format_verify_failure_lines()` ([`base.py`](../../../scripts/spoke/sync/base.py)); truyền timeout qua `verify_spoke()` và các hàm đồng bộ ([`coordinator.py`](../../../scripts/spoke/sync/coordinator.py)); thêm `--verify-timeout SECONDS` ([`cli.py`](../../../scripts/spoke/sync/cli.py)) & cập nhật [`ccba-update-spoke`](../../../.agents/skills/ccba-update-spoke/SKILL.md) (`4293 <= 4412` tokens, `GPI 14.00`); thêm `39` unit tests ([`test_spoke_verify_timeout.py`](../../../scripts/tests/test_spoke_verify_timeout.py)) và re-anchor `7` [`verify-ccba-*`](../../../packages/ccba-harness/.agents/skills/verify-ccba-code-review/SKILL.md).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.36s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 893` exit `0`, `git cat-file -e <sync_commit>^{commit}` exit `0` trên `7/7` suites, `test_verification_harness_dogfood.py` `5 passed`, `compile_catalog.py --check` `[OK]`, walkthrough PR [#894](https://github.com/vvChu/ccba-agent-platform/pull/894) (`8154720a`).

---

## 4. Lưu Trữ Phát Hành Trước Đó — Mở Rộng Bao Đóng Phụ Thuộc Nội Bộ Hub & Đưa `ccba-maskara` Vào `tier0` (`PR #890` / `#888`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#890](https://github.com/vvChu/ccba-agent-platform/pull/890) (`fc85177ed3a9ae014fa8d6d739397e5e278ad6aa`, hợp nhất `2026-11-24T01:31:12Z`) | **Branch:** `fix/issue-888-spoke-bootstrap-transitive-deps` (`02cd2d58`, đã xóa local & remote) | **Base:** `6a21510f` | **Issue Đã Đóng:** [#888](https://github.com/vvChu/ccba-agent-platform/issues/888) (`CLOSED`, `2026-11-24T01:31:14Z`)

- **Thành phần chính (`5 files, +562/-162`):** Tạo [`_bootstrap_deps.py`](../../../scripts/spoke/_bootstrap_deps.py) (`157` LOC, `<= 40` LOC/hàm) chuẩn hóa PEP 503/508, đọc `[project.dependencies]`, tính bao đóng chuyển tiếp chống chu trình và sắp xếp Kahn; thu gọn [`spoke_bootstrap.py`](../../../scripts/spoke/spoke_bootstrap.py) (`867` -> `741` LOC) cho cả `resolve_install_set()` và `_resolve_legacy_target_packages()`; thêm `ccba-maskara` vào `package_bindings.tier0` trong [`catalog_base.yaml`](../../../.agents/skills/platform-loader/catalog_base.yaml) & biên dịch [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml); bổ sung 9 unit tests trong [`test_declarative_package_bindings.py`](../../../scripts/tests/test_declarative_package_bindings.py).
- **Nghiệm thu:** Clean-venv E2E (`enterprise_governance` `6/6`, `project_delivery` `8/8`), `pytest scripts/tests/ -q` (`419 passed, 3 deselected`), `verify-patch --preset ci` (`7/7`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.43s` / `30.07s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 890` exit `0`, Issue `#888` `CLOSED`, walkthrough PR [#891](https://github.com/vvChu/ccba-agent-platform/pull/891) (`a2f371d1`).

---

## 5. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `actions/cache` Từ Version 4 Lên Version 6 (`PR #870`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#870](https://github.com/vvChu/ccba-agent-platform/pull/870) (`06d9132638e4279ccf5f86ef9dc8b41766d89ed5`, hợp nhất `2026-11-23T16:41:11Z`) | **Branch:** `dependabot/github_actions/actions/cache-6` (đã xóa remote) | **Base:** `4f5f658c` | **Issue:** N/A

- **Thành phần chính (`3 files, +4/-4`):** Nâng cấp `actions/cache@v4` -> `actions/cache@v6` trong [`.github/workflows/ci.yml`](../../../.github/workflows/ci.yml), [`.github/workflows/nightly-slow-tests.yml`](../../../.github/workflows/nightly-slow-tests.yml) và [`.github/workflows/pr-verifier.yml`](../../../.github/workflows/pr-verifier.yml).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `30.04s` / `30.73s`), `7/7` CI `SUCCESS`, `audit_pr_comments.py --pr 870` exit `0`, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid).

---

## 6. Lưu Trữ Phát Hành Trước Đó — Chuẩn Hóa Hướng Dẫn CLI/Seam Môi Trường Spoke Cho Maskara, Retrospective, Release Skills (`PR #880` / `#874`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#880](https://github.com/vvChu/ccba-agent-platform/pull/880) (`4f5f658cb977cad86917db68ef51733e7062a0d2`, hợp nhất `2026-11-23T16:36:01Z`) | **Branch:** `docs/issue-874-spoke-cli-skills` (đã xóa local & remote) | **Base:** `f2021607` | **Issue Đã Đóng:** [#874](https://github.com/vvChu/ccba-agent-platform/issues/874) (`CLOSED`, `2026-11-23T16:36:04Z`)  
> **Trạng thái chung:** ✅ **PR #880 MERGED (`--squash`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.75s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS, `door-triage` PASS, `compile_catalog.py --check` `[OK]`, SPOKE SYNC APPLIED (`ccba-legal-knowledge`)**

- **Thành phần chính (`3 files, +48/-26`):** Nâng [`ccba-maskara`](../../../.agents/skills/ccba-maskara/SKILL.md) lên `v1.0.1` chuẩn hóa CLI đa môi trường `maskara` / `python -m ccba_maskara.cli` và seam `maskara_scanner.v1`; nâng [`ccba-session-retrospective`](../../../.agents/skills/ccba-session-retrospective/SKILL.md) lên `v1.7.4` ưu tiên `scripts/sync_adr_matrix.py` trên Spoke có SSOT và siết chặt token ratchet budget; biên dịch lại `headings` cho `ccba-maskara` tại [`docs/index.html`](../../../docs/index.html).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 880` exit `0`, Issue `#874` `CLOSED`, Spoke sync applied `ccba-legal-knowledge`.

---

## 7. Lưu Trữ Phát Hành Trước Đó — Mặc Định `docProps/core.xml` `IBST - CCBA` & Khối Ký Tùy Chọn (`PR #884` / `#883`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#884](https://github.com/vvChu/ccba-agent-platform/pull/884) (`0fb9cf28c26f36008a923788fe11e288541f471b`, hợp nhất `2026-11-23T15:46:44Z`) | **Branch:** `feat/issue-883-ooxml-core-props-signoff` (`419c4b0f` -> rebased `e079c3c6`, đã xóa local & remote) | **Base:** `5e62429c` | **Issue Đã Đóng:** [#883](https://github.com/vvChu/ccba-agent-platform/issues/883) (`CLOSED`, `2026-11-23T15:46:47Z`)  
> **Trạng thái chung:** ✅ **PR #884 MERGED (`--squash`), TRIHT CỔNG 0.1–0.3 PASS (`12/12` TARGETS, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.86s`), `8/8` CI CHECKS PASS, `0` UNRESOLVED PR COMMENTS, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid), `compile_catalog.py --check` `[OK]`**

- **Thành phần chính (`6 files, +144/-23`, `161` logic LOC):** Chuẩn hóa `IBST/CCBA` -> `IBST - CCBA` (`_report_chrome.py`); mở rộng `render_signoff_block(..., title=...)`; opt-in `header_include_revision`; gán `author`/`last_modified_by` và xóa `"generated by python-docx"` (`_tech_report.py`); bổ sung OpenXML DOM tests (`test_docx_tech_report.py`); đồng bộ schema và nâng `ccba-xu-ly-van-phong` `v2.3.2`.
- **Nghiệm thu:** `pytest packages/ccba-ooxml/tests` (`120 passed`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#883` `CLOSED`, walkthrough PR [#885](https://github.com/vvChu/ccba-agent-platform/pull/885) (`f2021607`).

---

## 8. Lưu Trữ Phát Hành Trước Đó — Gia Cố Rào Chắn Hậu Chỉnh Tay Word (`ccba-xu-ly-van-phong` v2.3.1) & Đường Dẫn Guardrails Spoke (`ccba-session-retrospective` v1.7.3) (`PR #876`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#876](https://github.com/vvChu/ccba-agent-platform/pull/876) (`843032defd57d1279e9c9e25b7a3c5d42ade2323`, hợp nhất `2026-11-23T15:12:58Z`) | **Branch:** `proposal/harden-docx-post-edit-and-spoke-retrospective-cli` (`99f10474` -> `f4b791af` -> `8f1ec7ab`) | **Base:** `65d91fc0` | **Refs:** [#874](https://github.com/vvChu/ccba-agent-platform/issues/874)

- **Thành phần chính (`4 files, +49/-21`):** Nâng [`ccba-xu-ly-van-phong`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) lên `v2.3.1` với Rào chắn #5 (`Post-Manual-Word-Edit Hygiene`) & tính tùy chọn dòng tiêu đề khối ký tại [`docx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/docx.md); nâng [`ccba-session-retrospective`](../../../.agents/skills/ccba-session-retrospective/SKILL.md) lên `v1.7.3` sửa đường dẫn `scripts/spoke/` qua `CCBA_HUB_PATH` và bổ sung hướng dẫn Spoke non-git; lưu hồ sơ đề xuất [`2026-11-23_harden-docx-post-edit-and-spoke-retrospective-cli.md`](../../../.agents/proposals/2026-11-23_harden-docx-post-edit-and-spoke-retrospective-cli.md) (`status: "merged"`, `843032de`).
- **Nghiệm thu:** Tier 2 Boost (`77 GREEN`, `verify-patch --preset skill` `4/4`, `79 passed in 2.94s`, `tests/governance/` `367 passed, 1 skipped, 9 deselected in 12.74s` trên `f4b791af`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, walkthrough PR [#881](https://github.com/vvChu/ccba-agent-platform/pull/881) (`21224846`).

---

## 9. Lưu Trữ Phát Hành Trước Đó — Gia Cố Nhận Diện `VBPL_ADMIN`, Cắt `Nơi nhận:`, `legal_basis` & Timeout Tải/Hydrate (`PR #877` / `#873`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#877](https://github.com/vvChu/ccba-agent-platform/pull/877) (`8d6ff9a1b47c84a32586001c3921b7944cb84dcb`, hợp nhất `2026-11-23T14:41:53Z`) | **Branch:** `fix/issue-873-harden-vbpl-ingest` (`58ac8f6c` -> `93a50e70` -> `386bcab9`, đã xóa local & remote) | **Base:** `ee9dbe71` | **Issue Đã Đóng:** [#873](https://github.com/vvChu/ccba-agent-platform/issues/873) (`CLOSED`, `2026-11-23T14:41:55Z`)

- **Thành phần chính (`10 files, +582/-149`, `+194` net logic LOC):** Bổ sung `_ADMIN_NUM_RE`, `_ADMIN_TYPES` và `_is_vbpl_admin_hint()` tại [`archetype_scanner.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/archetype_scanner.py) kèm sửa `\x08` -> `\b`; chia sẻ `_BODY_START_RE`, sửa `sig_pattern`, `_dump_yaml_no_aliases()` và `_infer_vbpl_doc_type()` tại [`vbpl_admin.py`](../../../packages/ccba-legal-intel/src/ccba_legal/converters/vbpl_admin.py); nâng timeout tải Chrome/hydrator tại [`session.py`](../../../packages/ccba-legal-intel/src/ccba_legal/session.py), [`cdp.py`](../../../packages/ccba-legal-intel/src/ccba_legal/cdp.py), [`tier_downloader.py`](../../../packages/ccba-legal-intel/src/ccba_legal/crawler/tier_downloader.py), [`hydrator.py`](../../../packages/ccba-legal-intel/src/ccba_legal/hydrator.py); nâng [`SKILL.md`](../../../.agents/skills/ccba-legal-ingest/SKILL.md) `v1.3.1` (`GPI 24.50`) và bổ sung unit tests hồi quy.
- **Nghiệm thu:** `467 passed, 2 skipped, 20 deselected`, tái chuyển đổi `4` mẫu DOCX đạt `0 Errors, 0 Warnings`, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.62s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, walkthrough PR [#879](https://github.com/vvChu/ccba-agent-platform/pull/879) (`65d91fc0`).

---

## 10. Lưu Trữ Phát Hành Trước Đó — Chuẩn Hóa Phát Hiện `GENERIC` `ERROR` & Chống False Positive `SYSTEM_MESSAGE` Trong `evals.miner` (`PR #875`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#875](https://github.com/vvChu/ccba-agent-platform/pull/875) (`8a9f47c63fcbb274e7779ab449469d1d3e827831`, hợp nhất `2026-11-23T14:03:36Z`) | **Branch:** `fix/miner-generic-error-and-system-msg` (`a2e6aff4`, đã xóa local & remote) | **Base:** `badce709` | **Issue:** N/A

- **Thành phần chính (`2 files, +150/-35`):** Bổ sung `_TRACEBACK_MARKER` và `_classify_jsonl_step_response()` trong [`miner.py`](../../../packages/ccba-harness/src/ccba_harness/evals/miner.py) (`518` LOC, `max_fn_len <= 50`) để chỉ gắn lỗi khi `status == "ERROR"` hoặc chứa traceback thực sự, tách `active_user_prompt` khỏi `pending_planner_prompt`; bổ sung `4` unit tests trong [`test_miner.py`](../../../packages/ccba-harness/tests/test_miner.py) (`10/10` passed in `0.51s`).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `30.01s` / `30.64s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `door-triage` `ONE_WAY_DOOR` (Tradeoff Card Valid), walkthrough PR [#878](https://github.com/vvChu/ccba-agent-platform/pull/878) (`ee9dbe71`).

---

## 11. Lưu Trữ Phát Hành Trước Đó — Kiểm Toán Song Song Hai Spoke (`ERP` Sóng 4 × `IDOP` Bridge Sóng 3) & Lộ Trình R&D Hub-Spoke CCBA WAY (`PR #871`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#871](https://github.com/vvChu/ccba-agent-platform/pull/871) (`67b6cb3ef97449aa4dadf47dee833741b9951f91`, hợp nhất `2026-11-23T04:43:20Z`) | **Branch:** `docs/hub-spoke-idop-ccba-way-research` (`585a106c` -> `bd4d8d75`) | **Base:** `e5dc4bf6` | **Issue:** N/A

- **Thành phần chính (`2 files, +172 insertions`):** Xuất bản [`research-hub-spoke-idop-ccba-way-next-steps.md`](../research_and_studies/research-hub-spoke-idop-ccba-way-next-steps.md) và đăng ký tại [`index.md`](../index.md) (kiểm toán `IBST_UNIFIED_ERP` Sóng 4 × `IDOP-CCBA-WAY` Issue `#177` Bridge Sóng 3, phát hiện va chạm chéo PG `:5433`, vạch lộ trình `H0.2 -> R1 -> R4`, nâng Node.js `v26.13.1` LTS).
- **Nghiệm thu:** `validate_docs.py .md/knowledge --changed` (`32/32`), `verify-patch --preset doc` (`1/1`), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `32.55s` / `34.42s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 871` exit `0`, `compile_catalog.py --check` `[OK]`, walkthrough PR [#872](https://github.com/vvChu/ccba-agent-platform/pull/872) (`badce709`).

---

## 12. Lưu Trữ Phát Hành Trước Đó — Bổ Sung `frontend/src` Vào `DEFAULT_PRODUCTION_ROOTS` & SSOT Module Size Budget (`PR #866` / `#865`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#866](https://github.com/vvChu/ccba-agent-platform/pull/866) (`ac6f83dc9b5931426728ffa9d5e78ea1d908eb02`, hợp nhất `2026-11-22T14:41:33Z`) | **Branch:** `proposal/module-budget-frontend-src` (`97bae48e` -> `fb2fcd53`) | **Base:** `368cdbd1` | **Issue:** [#865](https://github.com/vvChu/ccba-agent-platform/issues/865) (`CLOSED`)

- **Thành phần chính (`4 files, +94/-5, 51 logic LOC`):** Bổ sung `"frontend/src"` vào `DEFAULT_PRODUCTION_ROOTS` tại [`_module_size_budget.py`](../../../packages/ccba-harness/src/ccba_harness/_module_size_budget.py); đồng bộ SSOT sang [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) (`930 <= 941` LOC); bổ sung `test_frontend_src_tsx_enforced_and_roots_parity` trong [`test_module_size_budget_seam.py`](../../../packages/ccba-harness/tests/test_module_size_budget_seam.py); cập nhật [`2026-11-22_module-budget-frontend-src.md`](../../../.agents/proposals/2026-11-22_module-budget-frontend-src.md) (`status: "merged"`, `merged_commit: ac6f83dc`, đính chính cờ `--ratchet-update`).
- **Nghiệm thu:** `809 passed, 6 skipped, 81 deselected` (`14.51s`), `ruff`/`mypy`/`check_spoke_leakage.py` (`0` violations), `validate_docs.py`/`compile_catalog.py`/`compile_skills_docs.py`/`sync_hub_adr_matrix.py` (`61` ADRs) PASS, `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#865` `CLOSED`, walkthrough PR [#869](https://github.com/vvChu/ccba-agent-platform/pull/869) (`e5dc4bf6`).

---

## 13. Lưu Trữ Phát Hành Trước Đó — Thay `gemini-3.7-flash-high` Trong `ccba-ai-qc-pccc-audit` & Living Doc SSoT Parity (`PR #867` / `#847`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch`):** [#867](https://github.com/vvChu/ccba-agent-platform/pull/867) (`368cdbd13c80b16f976b1ebb2a6a033c4f83814b`, hợp nhất `2026-11-22T14:35:28Z`) | **Branch:** `fix/issue-847-pccc-audit-living-doc-drift` (`42aac9ae`) | **Base:** `ccf3ab44` | **Issue:** [#847](https://github.com/vvChu/ccba-agent-platform/issues/847) (`CLOSED`)

- **Thành phần chính (`3 files, +149/-117`):** Thay thế `ModelArchetype.REASONING` / `gemini-3.7-flash-high` bằng `ModelArchetype.TIER_REASONING` / `"tier-reasoning"` (khớp [`routing.py`](../../../packages/ccba-ai/src/ccba_ai/routing.py)) trong [`SKILL.md`](../../../.agents/skills/ccba-ai-qc-pccc-audit/SKILL.md) (`v1.0.1`); nhập khẩu `LIVING_DOC_BANNED_TOKENS` từ [`check_spoke_cleanliness.py`](../../../scripts/spoke/check_spoke_cleanliness.py) vào [`audit_skills_hygiene.py`](../../../scripts/governance/audit_skills_hygiene.py) (`_scan_living_doc_drift()`, thu gọn `819` -> `782` LOC); bổ sung 2 test parity trong [`test_audit_skills_hygiene.py`](../../../tests/governance/test_audit_skills_hygiene.py).
- **Nghiệm thu:** `verify-patch --preset skill` (`4/4`) & `--preset ci` (`7/7`), `audit_skills_hygiene.py --check` (`77 GREEN`), `79` governance tests + `406` script tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `616 passed, 1 skipped, 10 deselected` in `29.28s` / `29.84s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 867` exit `0`, Issue `#847` `CLOSED`, và walkthrough PR [#868](https://github.com/vvChu/ccba-agent-platform/pull/868) (`5c23674f`).

---

## 14. Lưu Trữ Phát Hành Trước Đó — Bộ Chuẩn Bảng Màu, Template Tier 2A & YAML Schema Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 (`PR #863` / `Part 2 of #856`)

> **Pull Request Đã Hợp Nhất (`--squash --delete-branch` theo `RULE-2.21`):** [#863](https://github.com/vvChu/ccba-agent-platform/pull/863) (`478991cc8c65d5fc0bb3fe97f2bcc3d6de8786d0`, hợp nhất `2026-11-22T13:59:41Z`) | **Branch:** `docs/issue-856-docx-tech-report-standards` (`91d1f8e3`) | **Base:** `357520a0` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED`)

- **Thành phần chính (`5 files, +258/-1`):** Chuẩn hóa [`docx-ccba-brand.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/docx-ccba-brand.md), [`docx-ky-thuat-bao-cao-danh-gia.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/docx-ky-thuat-bao-cao-danh-gia.md), [`tech_report_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/tech_report_template_schema.yaml), định tuyến `TechnicalReportBuilder` / `build_tech_report_from_yaml` trong [`docx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/docx.md) và nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) lên `v2.3.0`.
- **Nghiệm thu:** `ccba-ooxml tech-report` (`success: true`), 3-page PDF Visual QA PASS, `verify-patch --preset ci` (`7/7 PASS`), `116` governance tests pass, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 863` exit `0`, Issue `#856` `CLOSED`, walkthrough PR [#864](https://github.com/vvChu/ccba-agent-platform/pull/864) (`ccf3ab44`).

---

## 15. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Báo Cáo Đánh Giá Kỹ Thuật DOCX CCBA Brand v3.4 & CLI `tech-report` (`PR #861` / `Part 1 of #856`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#861](https://github.com/vvChu/ccba-agent-platform/pull/861) (`42e15a42eab82252cd4209189ff96f57f90e32e6`) | **Branch:** `feat/issue-856-docx-tech-report-builder` (`d708cae6`) | **Base:** `4b699aa4` | **Issue:** [#856](https://github.com/vvChu/ccba-agent-platform/issues/856) (`CLOSED` sau PR `#863`)

- **Thành phần chính:** Bổ sung `CCBADocxTheme` & XSD helpers ([`_report_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_theme.py)), Page 1 cover/chrome/KPIs/khối ký đối xứng ([`_report_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_report_chrome.py)), `TechnicalReportBuilder` / `build_tech_report_from_yaml` & CLI `ccba-ooxml tech-report` ([`_tech_report.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/docx/_tech_report.py), [`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng PEP 562 lazy exports (`78 → 81`) tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), 6 neo [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) (`LF SHA-256 ca1c57e8...`), [`catalog.yaml`](../../../.agents/skills/platform-loader/catalog.yaml), [`docs/index.html`](../../../docs/index.html), và 4 unit/XML DOM tests ([`test_docx_tech_report.py`](../../../packages/ccba-ooxml/tests/test_docx_tech_report.py)).
- **Nghiệm thu:** `pytest packages/ccba-ooxml/tests` (`119 passed`), `run_verify_ooxml.py` (`6 passed`), `verify-patch --preset ci` (`7/7 PASSED`), `mypy` (`69` files clean), `check_spoke_leakage.py` (`0` violations), 3-page PDF Visual QA PASS, TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.16s` / `29.67s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 861` exit `0`, và walkthrough PR [#862](https://github.com/vvChu/ccba-agent-platform/pull/862) (`357520a0`).

---

## 16. Lưu Trữ Phát Hành Trước Đó — Bộ Quy Chuẩn & Mẫu YAML IR Bảng Tính Song Ngữ XLSX (`PR #853` / `Part 2 of #851`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#853](https://github.com/vvChu/ccba-agent-platform/pull/853) (`22dc01a372ec8d58e9a87564015be17831a86b79`) | **Branch:** `proposal/xu-ly-van-phong-xlsx-calc-standards` (`718e5e05` -> `8fe88b44`, đồng bộ `19f8ece7`) | **Base:** `19f8ece7` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851) (`CLOSED`)

- **Thành phần chính:** Bổ sung [`xlsx-bang-tinh-ky-thuat-song-ngu.md`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/xlsx-bang-tinh-ky-thuat-song-ngu.md), [`calc_sheet_template_schema.yaml`](../../../.agents/skills/ccba-xu-ly-van-phong/templates/calc_sheet_template_schema.yaml), **Palette X4** trong [`xlsx-palettes.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/color/xlsx-palettes.md), [`xlsx-structure.md`](../../../.agents/skills/ccba-xu-ly-van-phong/standards/structure/xlsx-structure.md), định tuyến Deep Seam & 5 bẫy thực chiến trong [`xlsx.md`](../../../.agents/skills/ccba-xu-ly-van-phong/resources/xlsx.md), nâng [`SKILL.md`](../../../.agents/skills/ccba-xu-ly-van-phong/SKILL.md) `v2.2.0`, kèm [`2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md`](../../../.agents/proposals/2026-11-22_xu-ly-van-phong-xlsx-calc-standards.md).
- **Nghiệm thu:** `validate_skills.py --enforce-gpi` `77/77 PASSED` (`GPI = 9.50 < 12.0`), `106` governance tests pass, `ruff check`/`format` pass (`908` files), PDF smoke test A4 Portrait 4 trang (`Q=18`, `V=64.8`, `formula_errors=[]`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, Issue `#851` `CLOSED`.

---

## 17. Lưu Trữ Phát Hành Trước Đó — Bộ Dựng Bảng Tính Song Ngữ & Windows Excel COM Engine (`PR #852` / `Part 1 of #851`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#852](https://github.com/vvChu/ccba-agent-platform/pull/852) (`e7530dd0dbe564453efa64a7a2ad57492f3884d4`) | **Branch:** `proposal/ooxml-xlsx-calc-sheet-and-excel-com` (`9cc97214` -> `978b46e2`, rebased trên `8b1ace7e`) | **Base:** `8b1ace7e` | **Issue:** [#851](https://github.com/vvChu/ccba-agent-platform/issues/851)

- **Thành phần chính:** Nâng cấp [`converter.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/converter.py) (`_convert_via_excel`, `xlsx_to_pdf`), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py) (`_recalc_via_excel_com`, `audit_xlsx_formula_errors`), bổ sung [`_calc_sheet.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_sheet.py), [`_theme.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_theme.py), [`_calc_chrome.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/_calc_chrome.py), CLI `ccba-ooxml calc-sheet` ([`cli.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/cli.py)), mở rộng `ccba_ooxml.__all__` (`72 -> 78`), cập nhật [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md) và [`2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md`](../../../.agents/proposals/2026-11-22_ooxml-xlsx-calc-sheet-and-excel-com.md).
- **Nghiệm thu:** Tier 2 Boost (`121 passed`, `mypy` `66` files clean, `ruff` `82` files, `77/77` skills), TRIHT Cổng 0.1–0.3 (**12/12 targets PASS**, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.34s` / `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 18. Lưu Trữ Phát Hành Trước Đó — Đăng Ký Spoke `SDS for Data Center` & Nâng Cấp Chuẩn `ADR-0062` (`PR #846`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#846](https://github.com/vvChu/ccba-agent-platform/pull/846) (`ad4dc12c7b76d698ef728b5c0b641b1359dec37a`) | **Branch:** `chore/sync-windows-spoke-registry-adr0062` (`bb5f7d50` -> `9cc07fca`, rebased trên `4083d561`) | **Base:** `4083d561` | **Issue:** N/A

- **Thành phần chính:** Cập nhật [`spoke_registry.yaml`](../../../.md/data/spoke_registry.yaml) (`13 -> 14` spokes): đăng ký mới `SDS for Data Center` (`b35979ec03bf`, `project_delivery`) và nâng cấp 4 Windows spokes lên `ADR-0062` (`static_hash` + `archetype`, đạt `14/14` = `100%` chuẩn `ADR-0062`, `256-byte` RSA-2048 ciphertexts).
- **Nghiệm thu:** `sanitize_review_diff.py` `[PASS]`, `check_spoke_leakage.py` `0` violations, `door-triage` `PAVED_ROAD`, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS trên `9cc07fca`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 846` exit `0`, `compile_catalog.py --check` `[OK]`.

---

## 19. Lưu Trữ Phát Hành Trước Đó — Phân Tách Operations OS & Financial Ledger Trong `HUB-ADR-0060` (`PR #854` / `#849`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#854](https://github.com/vvChu/ccba-agent-platform/pull/854) (`6d1d3f5e7e6dc671b7da2531f7c522f8fc64df56`) | **Branch:** `docs/issue-849-adr-0060-erp-sor-separation` (`1b85482c`) | **Base:** `609afbc1` | **Issue:** [#849](https://github.com/vvChu/ccba-agent-platform/issues/849) (`CLOSED`)

- **Thành phần chính:** Cập nhật [`0060-4hub-federated-spokes-architecture.md`](../../../docs/adr/0060-4hub-federated-spokes-architecture.md) (Mục 1 & Mục 7 Amendment `2026-11-22`): phân tách cứng SOR điều hành (`IDOP-CCBA-WAY`) khỏi SOR sổ cái `31v` (`IBST_UNIFIED_ERP` trên `[Spoke PG16 loopback]`), ủy thác chi tiết vận hành Spoke về Spoke ADR-0011 (`Accepted`), đặt cầu Closed-Loop `IDOP → ERP` loopback-only (`127.0.0.1`), xác thực kép + taxonomy fail-closed SHA-256 (`IBST_IDOP_TAXONOMY_DIR`), và chuẩn hóa 5 trục tương tác IBST.
- **Nghiệm thu:** Grok Peer Audit Pass 2 `APPROVE_PLAN` (`risk_score: 2`, `0` blocking), `validate_docs.py` / `sync_hub_adr_matrix.py --check` (`61` ADRs) / `verify-patch --preset adr,doc` / `door-triage` (`ONE_WAY_DOOR`, `tradeoff_card_valid: true`) PASS, TRIHT Cổng 0.1–0.3 (`12/12` targets PASS, `root-tests` `614 passed, 1 skipped, 10 deselected` in `29.47s` / total `30.00s`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 854` exit `0`, Issue `#849` `CLOSED` (`#issuecomment-7074500733`).

---

## 20. Lưu Trữ Phát Hành Trước Đó — Phát Hành Đợt Kép `PR #845` (`#844`) & `PR #848` (`#842`)

> **PR `#845` Đã Hợp Nhất (`--squash`):** [#845](https://github.com/vvChu/ccba-agent-platform/pull/845) (`76f48be83790a24ec28817b7f8d3f5e8f44086e8`) | **Issue:** [#844](https://github.com/vvChu/ccba-agent-platform/issues/844) (`CLOSED`) | **Branch:** `fix/issue-844-md-spoke-retrospective-gates` (`e2a42753`)  
> **PR `#848` Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#848](https://github.com/vvChu/ccba-agent-platform/pull/848) (`deeae22d7564f629f54298403cae9d24f0c71dd1`) | **Issue:** [#842](https://github.com/vvChu/ccba-agent-platform/issues/842) (`CLOSED`) | **Branch:** `feat/issue-842-ooxml-xlsx-seam` (`07c6549e`, rebased trên `76f48be8`)

- **Thành phần chính PR `#845`:** Bổ sung `resolve_target_adr_dir()`, `--adr-dir`, `--create-adr-dir` tại [`sync_hub_adr_matrix.py`](../../../scripts/sync_hub_adr_matrix.py); thêm `--profile generic-spoke` tại [`compact_session_learnings.py`](../../../scripts/governance/compact_session_learnings.py); nâng `/ccba-session-retrospective` `v1.7.2`; bổ sung 5 ca test tại [`test_sync_adr_matrix.py`](../../../tests/governance/test_sync_adr_matrix.py) và [`test_compact_session_learnings.py`](../../../tests/governance/test_compact_session_learnings.py).
- **Thành phần chính PR `#848`:** Triển khai deep subpackage `ccba_ooxml.xlsx` ([`xlsx/__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/xlsx/__init__.py), PEP 562 lazy exports tại [`__init__.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/__init__.py), [`calc.py`](../../../packages/ccba-ooxml/src/ccba_ooxml/calc.py), [`seam-contracts.yaml`](../../../seam-contracts.yaml), [`verify-ccba-ooxml/SKILL.md`](../../../packages/ccba-harness/.agents/skills/verify-ccba-ooxml/SKILL.md), [`test_xlsx.py`](../../../packages/ccba-ooxml/tests/test_xlsx.py), [`2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md`](../decisions/2026-11-22_issue_842_ooxml_xlsx_seam_grilling_resolution.md)).
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS` x2), `8/8` CI `SUCCESS` x2, `audit_pr_comments.py` exit `0`, `git cat-file -e 7259350d8020834c52ab88e4c5681e165612cc8b^{commit}` exit `0`, `compile_catalog.py --check` PASS, `test_verification_harness_dogfood.py` `5 passed`, `run_verify_ooxml.py` `6 passed`.

---

## 21. Lưu Trữ Phát Hành Trước Đó — Siết Chặt Startup `.env` ASGI & Neo `.ruff.toml` `conftest.py` (`PR #841`)

> **Pull Request Đã Hợp Nhất (`--merge` theo `RULE-2.21`):** [#841](https://github.com/vvChu/ccba-agent-platform/pull/841) (`3d582834d0e652f7932318daa3cc83456dabe778`) | **Issue Đã Đóng:** [#840](https://github.com/vvChu/ccba-agent-platform/issues/840) (`CLOSED`) | **Branch:** `docs/issue-840-harden-asgi-env-conftest-ruff` (`f9e3e71f` -> `c3ce5041`) | **Base:** `a0282a9e`

- **Thành phần chính:** Bổ sung checklist startup `.env` & session active (`api.md`), bump `/ccba-code-review` `v1.8.1`, bump `/ccba-implement` `v1.2.2` neo `./conftest.py` và `urlunparse()`, re-anchor `verify-ccba-code-review` & `verify-ccba-implement` tại `a0282a9e`.
- **Nghiệm thu:** TRIHT Cổng 0.1–0.3 (`12/12 targets PASS`), `8/8` CI `SUCCESS`, `audit_pr_comments.py --pr 841` exit `0`, `test_verification_harness_dogfood.py` `5 passed`.

---

## 22. Lưu Trữ Phát Hành Trước Đó — Nâng Cấp `/ccba-book-compiler` v1.5.4 (`PR #817`)

> **Pull Request Đã Hợp Nhất (`--squash`):** [#817](https://github.com/vvChu/ccba-agent-platform/pull/817) (`1de529cb5a47274d6d570f310b87bff193274140`) | **Nhánh:** `feat/book-compiler-v154` (`ba079377` -> `1de529cb`) | **Base:** `170c04f3`

| Thành Phần | Tệp Thay Đổi Chính | Nội Dung Kỹ Thuật Cốt Lõi | Trạng Thái |
| :--- | :--- | :--- | :---: |
| **1. Đồng bộ Kernel Skill `v1.5.4`** | [`.agents/skills/ccba-book-compiler/SKILL.md`](../../../.agents/skills/ccba-book-compiler/SKILL.md) | Nâng phiên bản `1.5.3` -> `1.5.4` (`6-Phase SOP v1.5.4`); đăng ký hai Spoke pipeline seams mới (`scripts/pipeline/book_staging_recovery.py`, `scripts/pipeline/book_link_verifier.py`) và cập nhật Bất biến #1 cho phép staging lũy đẳng từ thư mục `<Book_Stem>_MD` sạch hoặc khi `.epub`/`.pdf` gốc đã lưu trữ (đối ứng Spoke PR `vvChu/vvc-second-brain-scripts#144`). | Verified |
| **2. Đăng ký Parity Seams của Spoke** | [`tests/governance/test_workflow_script_parity.py`](../../../tests/governance/test_workflow_script_parity.py) | Bổ sung `scripts/pipeline/book_link_verifier.py` và `scripts/pipeline/book_staging_recovery.py` vào `SPOKE_SPECIFIC_SCRIPTS` để bảo đảm 100% kiểm định liên kết nội tuyến trong skill. | Verified |
| **3. Tái biên dịch Cổng Tài liệu Tĩnh** | [`docs/index.html`](../../../docs/index.html) | Cập nhật cổng web tĩnh qua `python3 scripts/governance/compile_skills_docs.py --write` và đối soát qua `--check`. | Verified |

- **TRIHT & Dual-Gate (`PR #817`):** Cổng 0.1 `PASS`, Cổng 0.2 **12/12 PASS** (`root-tests` `602 passed, 1 skipped, 10 deselected` in `27.93s`), Cổng 0.3 `PASS`; `8/8` CI `SUCCESS`, `audit_pr_comments.py` Exit Code `0` (`IC_kwDOQzfV088AAAABoRr_IA`), Grok Pass 3 `APPROVE_PLAN` (`3b5fd6e0-d35f-4560-973a-244bf9aa7245`, `risk_score: 2`, `0` blocking).
