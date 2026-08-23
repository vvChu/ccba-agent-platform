---
description: Đóng gói mã nguồn, tests, proposal từ Spoke và mở PR lên Hub kèm Vòng lặp Dừng chờ CI & Copilot Review (Self-Healing Gate)
applies_to:
  - Phần mềm
  - Thẩm tra thiết kế
  - Thiết kế
  - Kiểm định
bundle: _core
disable-model-invocation: true
command: /ccba-contribute-to-hub
triggers:
  - contribute
  - contribute to hub
  - đóng góp mã nguồn
  - tạo pr lên hub
  - mở proposal
  - ccba-contribute-to-hub
---
# Workflow: Contribute to Hub (Đóng Góp Mã Nguồn Ngược Lên Hub Chuẩn OKF v2.0)

Quy trình chuẩn hóa để đóng gói mã nguồn, tests, proposal và mở GitHub Pull Request (PR) kèm hoàn tất thẩm định tự động từ Spoke lên Platform Hub (`ccba-agent-platform`). *(Alias: `/ccba-propose-to-hub`)*

---

## 📋 Bước 1: Thu thập Thông tin & Mã Nguồn Đóng Gói
Ghi nhận đầy đủ 6 thông tin cốt lõi:
1. **Loại đề xuất:** `tool` (Package trong `packages/`), `skill` (`.agents/skills/`), `workflow` (`.agents/workflows/`), hoặc `rules`.
2. **Tên đề xuất:** Dạng kebab-case (ví dụ: `legislative-consolidator-okf-v2`).
3. **Mô tả & Vấn đề giải quyết:** Nỗi đau thực tế đã giải quyết tại Spoke.
4. **Mã nguồn & Tests:** File code và file test tại Spoke đã pass $100\%$ kiểm thử cục bộ.
5. **Dự án áp dụng & Mức độ ưu tiên:** Bộ môn áp dụng và "Cao" / "Trung bình" / "Thấp".

---

## 🔍 Bước 2: Kiểm tra Trùng lặp (Duplicate Detection)
Trước khi tạo mới, Agent **bắt buộc** kiểm tra hệ sinh thái Hub:
1. Đọc `.md/workspace_context.yaml` để lấy `hub_path`.
2. Đọc `<hub_path>/.agents/skills/platform-loader/catalog.yaml`, `packages/`, `<hub_path>/.agents/AGENTS.md`, `PLATFORM.md`.
*Nếu phát hiện đã tồn tại thành phần tương tự:* Đề xuất nâng cấp/mở rộng thay vì tạo mới trùng lặp.

---

## 📦 Bước 3: Đóng Gói Mã Nguồn & Tạo Proposal Trên Branch Mới
Thực thi tại thư mục Hub (`hub_path`):
1. **Đồng bộ nhánh & Khóa bảo vệ nhánh (Pre-Commit Branch Assertion):**
   ```bash
   git checkout main && git pull origin main && git checkout -b proposal/[tên-đề-xuất]
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
   proposed_by_project: "[tên-spoke]"
   proposed_by_archetype: "knowledge_corpus"
   proposed_date: "YYYY-MM-DD"
   applies_to: ["Phần mềm", "Thẩm tra thiết kế"]
   ---
   ```
4. **Leakage Guard & Push:**
   ```bash
   python scripts/governance/check_spoke_leakage.py
   git add -A && git commit -m "feat([scope]): add [tên-đề-xuất] and proposal" && git push origin proposal/[tên-đề-xuất]
   ```

---

## 🚀 Bước 4: Mở GitHub Pull Request (PR Flow)
- **Tự động qua GitHub CLI:**
  ```bash
  gh pr create --title "feat([scope]): add [tên-đề-xuất]" --body "Automated proposal submission." --base main --head proposal/[tên-đề-xuất]
  ```
- **Thủ công:** Truy cập `[PR-creation-URL]/pull/new/proposal/[tên-đề-xuất]`.

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

---

## ✅ Bước 6: Báo Cáo Hoàn Tất & Sẵn Sàng Merge
Tổng hợp báo cáo: Link PR, kết quả CI, tóm tắt góp ý đã sửa, và thông báo Maintainer kích hoạt `/ccba-review-proposal [PR_NUMBER]`.

---

## 🔄 Bước 7: Vòng Khép Kín Hậu Hợp Nhất (Closed-Loop Spoke Sync Gate)
Sau khi PR được Squash Merge vào Hub `main`, thực thi chu trình 4 bước đóng vòng tại Spoke:
1. **Xác nhận Hợp nhất:** `gh pr view <PR_NUMBER> --json state,mergedAt --jq '.state'` (phải là `MERGED`).
2. **Đồng bộ Downstream:** Chạy `/ccba-update-spoke` hoặc `python [hub_path]\scripts\sync_spoke.py --spoke . --apply`.
3. **Tái cài đặt Editable Package:** `pip install -e "[hub_path]\packages\[package-name]"` (nếu là `tool`).
4. **Hồi quy & Dọn dẹp:** Chạy kiểm thử Spoke (`python scripts\validate_legal_spoke.py`), xóa branch `git branch -D proposal/[tên-đề-xuất]`, và ghi log vào `.md/knowledge/session_learnings.md`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
