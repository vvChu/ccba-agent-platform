---
name: ccba-contribute-to-hub
description: Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub kèm Vòng
  lặp Dừng chờ CI & Copilot Review (Self-Healing Gate)
applies_to:
- Phần mềm
- Thẩm tra thiết kế
- Thiết kế
- Kiểm định
bundle: _core
tier: kernel
disable-model-invocation: true
command: /ccba-contribute-to-hub
user-invocable: true
gpi:
  s: 3.0
  k: 3.0
  a: 1.0
  p: 1.0
triggers:
- contribute
- contribute to hub
- đóng góp mã nguồn
- tạo pr lên hub
- mở proposal
- ccba-contribute-to-hub
- ccba-propose-to-hub
- propose-to-hub
- ccba-create-pr
- create-pr
- ccba-review-proposal
- review-proposal
---

# Workflow: Contribute to Hub (Đóng Góp Mã Nguồn Ngược Lên Hub Chuẩn OKF v2.0)

Quy trình chuẩn hóa để đóng gói mã nguồn, tests, proposal và mở GitHub Pull Request (PR) kèm hoàn tất thẩm định tự động từ Spoke lên Platform Hub (`ccba-agent-platform`). *(Lệnh: `/ccba-contribute-to-hub`)*

---

## 📋 Bước 1: Thu thập Thông tin, Liên Kết Issue & Cổng Kiểm Lọc R&D
Ghi nhận đầy đủ thông tin cốt lõi:
1. **Liên kết Issue & Cổng Tự Động Phân Loại Scope (Smart Scope-Aware Issue Gate):**
   - **Nếu có `--issue [ID]`:** Kế thừa trực tiếp mã Issue để liên kết và đóng tự động (`Closes #[ID]`).
   - **Nếu KHÔNG có `--issue`:** Agent tự động đánh giá quy mô thay đổi:
     * 🟢 **Quy mô Lớn (Major Scope):** Thêm module/deep seam mới trong `packages/`, cập nhật kiến trúc (ADR), hoặc thay đổi $\ge 100$ dòng code / $\ge 3$ files $\rightarrow$ **Agent chủ động gợi ý/tự động tạo 1 GitHub Issue** trên Hub để ghi nhận Changelog, Ký ức dài hạn (Traceability) và gắn vào PR.
     * ⚪ **Quy mô Nhỏ / Nội bộ (Minor Scope):** Vá lỗi nhỏ, sửa typo, cập nhật docstring, refactor nội bộ $< 100$ dòng $\rightarrow$ **Bỏ qua tạo Issue** để tránh làm rác Issue Tracker, mở PR trực tiếp.
2. **Loại đề xuất:** `tool` (Package trong `packages/`), `skill` (`.agents/skills/`), `workflow` (`.agents/workflows/`), hoặc `rules`.
3. **Tên đề xuất:** Dạng kebab-case (ví dụ: `modernize-annex-engine-okf-v23`).
4. **Mô tả & Vấn đề giải quyết:** Nỗi đau thực tế đã giải quyết tại Spoke.
5. **Cổng Kiểm Lọc R&D (Graduation Pre-Flight Gate):**
   - Đảm bảo mã nguồn đã được làm sạch qua `/ccba-graduate-rd` (loại bỏ 100% `print`, đường dẫn hardcoded, rác tạm; có đủ Type Hints & Docstrings Google style).
   - Test suite cục bộ trong `packages/[pkg]/tests/` phải đạt **100% PASS** trước khi tạo Proposal.
- **Tiêu chí hoàn thành:** Thu thập đầy đủ thông tin scope, tên đề xuất, liên kết issue và đảm bảo code đã clean qua `/ccba-graduate-rd`.

---

## 🔍 Bước 2: Kiểm tra Trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent **bắt buộc** kiểm tra hệ sinh thái Hub:
1. Đọc `.md/workspace_context.yaml` để lấy `hub_path`.
2. Đọc `<hub_path>/.agents/skills/platform-loader/catalog.yaml`, `packages/`, `<hub_path>/.agents/AGENTS.md`, `PLATFORM.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Đề xuất nâng cấp/mở rộng thay vì tạo mới trùng lặp.
- **Tiêu chí hoàn thành:** Xác nhận không trùng lặp chức năng với các skill, tool hiện hữu trong `catalog.yaml` và `PLATFORM.md`.

---

## 📦 Bước 3: Đóng Gói Mã Nguồn & Tạo Proposal Trên Branch Mới
Thực thi tại thư mục Hub (`hub_path`):
1. **Đồng bộ nhánh & Khóa bảo vệ nhánh (Pre-Commit Branch Assertion):**
   ```bash
   BRANCH_NAME="proposal/${ISSUE_ID:+issue-${ISSUE_ID}-}${PROPOSAL_NAME}"
   git checkout main && git pull origin main && git checkout -b "$BRANCH_NAME"
   [ "$(git branch --show-current)" = "main" ] && { echo "❌ Lỗi: Đang ở main!"; exit 1; }
   ```
2. **Đóng gói Mã nguồn & Tests vào Package tương ứng:**
   - Code: `packages/[pkg]/src/[submodule]/`, Public Deep Seam: `packages/[pkg]/src/__init__.py`, Tests: `packages/[pkg]/tests/`.
   - Format, linting & cập nhật kiến trúc:
     ```bash
     python -m ruff check --fix packages/[pkg]/ && python -m ruff format packages/[pkg]/ && python scripts/update_arch_stats.py
     ```
3. **Ghi nhận tệp Proposal (`.agents/proposals/[YYYY-MM-DD]_[tên-đề-xuất].md` - ADR 0045):**
   ```yaml
   ---
   proposal_id: "[YYYY-MM-DD]_[tên-đề-xuất]"
   type: "tool" # "tool" | "skill" | "workflow" | "rules"
   name: "[tên-đề-xuất]"
   status: "open"
   priority: "Cao"
   related_issue: "#[ISSUE_ID]" # Liên kết Issue nếu có
   proposed_by_project: "[tên-spoke]"
   proposed_by_archetype: "knowledge_corpus"
   proposed_date: "YYYY-MM-DD"
   applies_to: ["Phần mềm", "Thẩm tra thiết kế"]
   ---
   ```
4. **Kiểm Định Cục Bộ, Leakage Guard & Push:**
   Chạy đồng bộ catalog và kiểm định toàn bộ kỹ năng trước khi commit:
   ```bash
   python scripts/governance/compile_catalog.py
   python scripts/validate_skills.py
   python scripts/governance/check_spoke_leakage.py
   git add -A && git commit -m "feat([scope]): add [tên-đề-xuất] and proposal" && git push origin "$BRANCH_NAME"
   ```
- **Tiêu chí hoàn thành:** Nhánh mới được tạo, mã nguồn đóng gói, proposal ghi nhận, catalog đồng bộ và pass toàn bộ `scripts/validate_skills.py` cùng `check_spoke_leakage.py`.

---

## 🚀 Bước 4: Mở GitHub Pull Request (PR Flow Tự Đóng Issue)
- **Tự động qua GitHub CLI (Tự động gắn mã Closes #[ISSUE_ID]):**
  ```bash
  PR_BODY="Automated proposal submission from Spoke [tên-spoke].${ISSUE_ID:+ Closes #${ISSUE_ID}}"
  gh pr create --title "feat([scope]): add [tên-đề-xuất]" --body "$PR_BODY" --base main --head "$BRANCH_NAME"
  ```
- **Thủ công:** Truy cập `[PR-creation-URL]/pull/new/[BRANCH_NAME]`.
- **Tiêu chí hoàn thành:** Pull Request được mở thành công trên GitHub liên kết đúng branch và Issue ID.

---

## 🔄 Bước 5: Vòng Lặp Dừng Chờ & Tự Làm Xanh CI (Self-Healing Loop)

> [!IMPORTANT]
> **Tuyệt đối không kết thúc quy trình ngay sau khi mở PR.** Agent phải đồng hành cho đến khi $100\%$ CI Tích Xanh.

1. **Dừng chờ động (Grace Period):** Dùng `schedule` hẹn giờ kiểm tra: PR nhỏ (<100 dòng) `45s`, PR vừa (100-500 dòng) `60s-90s`, PR lớn (>500 dòng) `90s-180s`.
2. **Kiểm tra song song 2 cổng (Dual-Gate):**
   - CI Status: `gh pr checks <PR_NUMBER>`
   - Copilot Review: `gh pr view <PR_NUMBER> --json reviews,comments --jq '.reviews[] | select(.author.login=="copilot-pull-request-reviewer")'`
3. **Tự khắc phục (Self-Healing Action):**
   - Nếu CI Fail: Đọc log qua `gh run view <RUN_ID> --log-failed` $\rightarrow$ Sửa lỗi $\rightarrow$ Commit & push bản vá.
   - Nếu Copilot góp ý: Refactor code đối soát với chuẩn CCBA $\rightarrow$ Commit & push.
   - Tiêu chí: Lặp lại đến khi `gh pr checks <PR_NUMBER>` pass 100%.
- **Tiêu chí hoàn thành:** 100% CI Checks pass xanh và toàn bộ review của Copilot (nếu có) được giải quyết triệt để.

---

## ✅ Bước 6: Báo Cáo Hoàn Tất & Sẵn Sàng Merge
Tổng hợp báo cáo: Link PR, kết quả CI, tóm tắt góp ý đã sửa, và thông báo Maintainer kích hoạt `/ccba-contribute-to-hub [PR_NUMBER]`.
- **Tiêu chí hoàn thành:** Báo cáo hoàn tất tổng hợp link PR và kích hoạt `/ccba-contribute-to-hub`.

---

## 🔄 Bước 7: Vòng Khép Kín Hậu Hợp Nhất (Closed-Loop Spoke Sync Gate)
Sau khi PR được Squash Merge vào Hub `main`, thực thi chu trình 4 bước đóng vòng tại Spoke:
1. **Xác nhận Hợp nhất:** `gh pr view <PR_NUMBER> --json state,mergedAt --jq '.state'` (phải là `MERGED`).
2. **Đồng bộ Downstream:** Chạy `/ccba-update-spoke` hoặc `python [hub_path]\scripts\sync_spoke.py --spoke . --apply`.
3. **Tái cài đặt Editable Package:** `pip install -e "[hub_path]\packages\[package-name]"` (nếu là `tool`).
4. **Hồi quy & Dọn dẹp:** Chạy kiểm thử Spoke (`python scripts\validate_legal_spoke.py`), xóa branch `git branch -D proposal/[tên-đề-xuất]`, và ghi log vào `.md/knowledge/session_learnings.md`.
- **Tiêu chí hoàn thành:** Nhánh feature được merge, Spoke downstream đồng bộ thành công và `session_learnings.md` được cập nhật.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*


## Progressive Disclosure & Reference Index (Level 3)

Khi thực thi các tác vụ chuyên sâu, Agent sử dụng công cụ `view_file` để nạp hướng dẫn chi tiết theo nhu cầu:

| Tệp Tham Chiếu | Ngữ Cảnh Triệu Hồi & Mục Đích Sử Dụng |
| :--- | :--- |
| `references/propose_to_hub.md` | Quy trình đề xuất kỹ năng/tính năng mới từ Spoke lên Hub trung tâm |
| `references/pull_request_guide.md` | Hướng dẫn kiểm tra chất lượng và tạo Pull Request chuẩn mực |
| `references/proposal_review_sop.md` | Quy trình chuẩn SOP thẩm định các đề xuất Pull Request từ Spoke gửi lên Hub |

