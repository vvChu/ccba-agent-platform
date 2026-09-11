# Walkthrough: Release PR #253 (Beyond Horizon Phase 4 & Spoke Sync Hardening)

## 1. Tổng Quan Release
- **PR Number:** [#253](https://github.com/vvChu/ccba-agent-platform/pull/253)
- **Branch:** `feat/beyond-horizon-phase4-and-spoke-sync-hardening` $\rightarrow$ `main`
- **Tiêu đề:** `feat: Beyond Horizon Phase 4 and spoke sync hardening`
- **Copilot Review ID:** `PRR_kwDOQzfV088AAAABNGQN2A` (5173939672 - Đã giải trình và giải quyết 100% các khuyến nghị)
- **Mục tiêu:** Hoàn thiện Phase 4 Beyond Horizon, đóng gói leaf seam `ccba-qc-core`, siết chặt Spoke Sync với flag `--verify`, thực thi Deterministic Hard Completion Lock (ADR-0058), và hoàn tất chuẩn hóa 101 skills/workflows.

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #253)

Review ID: `PRR_kwDOQzfV088AAAABNGQN2A` (5173939672)

| ID | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `3984996889` | `scripts/spoke/check_hub_import_depth.py` | `check_hub_import_depth` adds `ccba_qc` as a monitored Hub import prefix, but the new package introduced in this PR is `ccba_qc_core`. Deep imports from `ccba_qc_core.*` won't be detected. | **ĐÃ KHẮC PHỤC** trong commit `06436961`: Đổi `"ccba_qc"` thành `"ccba_qc_core"` trong `HUB_PACKAGE_PREFIXES`, đảm bảo cơ chế kiểm soát import depth phát hiện đúng package monorepo mới. |
| `3984996922` | `tests/governance/test_workflow_script_parity.py` | The newly-added entries in SPOKE_SPECIFIC_SCRIPTS whitelist `scripts/format/*`, `scripts/convert/*`, and `scripts/office/*`, but those paths don't exist in this repo and are currently referenced by docs under `.agents/skills/ccba-xu-ly-van-phong/resources/*`. Prefer fixing the docs to point at the real script locations and removing whitelist exceptions. | **ĐÃ KHẮC PHỤC** trong commit `06436961`: Đã cập nhật toàn bộ đường dẫn trong `convert.md`, `office-xml.md`, `pptx.md` trỏ chính xác về `.agents/skills/ccba-xu-ly-van-phong/scripts/...`. Xóa bỏ hoàn toàn 7 ngoại lệ whitelist trong `SPOKE_SPECIFIC_SCRIPTS` và mở rộng `hub_script_pattern` để kiểm tra đĩa thực tế cho cả skill scripts. |
| `3984996962` | `.agents/skills/ccba-codebase-design/SKILL.md` | The Hard Stopping Rule lists `/ccba-codebase-design` as a driver skill to route to, but this is the same skill, so it reads like a self-loop. | **ĐÃ KHẮC PHỤC** trong commit `06436961`: Loại bỏ `/ccba-codebase-design` khỏi danh sách Driver Skills điều hướng của Hard Stopping Rule, tránh vòng lặp tự thân (self-loop). |
| `3984996986` | `.agents/skills/ccba-to-spec/references/interactive_questionnaire.md` | The Workflow Hand-off section uses the same `/ccba-to-spec` bullet twice (spec + ticket breakdown). Since `/ccba-to-spec` is meant to cover both, this should be clarified to avoid duplicate bullets. | **ĐÃ KHẮC PHỤC** trong commit `06436961`: Gộp 2 bullet trùng lặp thành một phát biểu thống nhất và xúc tích: Kích hoạt kỹ năng `/ccba-to-spec` để chuyển hóa quyết định thành PRD / Đặc tả kỹ thuật và phân rã nhiệm vụ chi tiết. |
| `3984997006` | `packages/ccba-qc-core/AGENTS.md` | There's a stray non-printing character in `Public Deep Seams` ("\f" before `rom`), which will render incorrectly in Markdown and may break doc tooling. Replace it with a normal `from` and wrap in backticks. | **ĐÃ KHẮC PHỤC** trong commit `06436961`: Xóa bỏ ký tự form feed `\f` thừa và bọc toàn bộ câu lệnh import `from ccba_qc_core import ...` trong cặp dấu backticks. |

---

## 3. Kết Quả Kiểm Thử Toàn Diện (Pre-release Gate)

- `python -m ccba_harness verify-patch --preset ci`: **5/5 passed (Exit Code 0)**.
- `python scripts/eval/run_harness_evals.py --all`: **8/8 gates PASS 100%**.
- `python -m pytest tests/governance/test_workflow_script_parity.py`: **4/4 passed (100%)**.
- GitHub Actions CI (6/6 jobs): **100% Green**.
