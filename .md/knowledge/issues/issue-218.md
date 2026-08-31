---
id: 218
title: "refactor(governance): add branch assertion guard and closed-loop spoke sync to contribute-to-hub workflow"
state: "needs-triage"
labels:

assignee: "none"
created_at: "2026-08-23T12:13:34Z"
updated_at: "2026-08-23T13:20:05Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
Trong quá trình thực thi chu trình đóng góp ngược (Upstream Contribution Loop) từ Spoke lên Hub:
1. **Rủi ro Commit Nhầm vào Main:** Tại Bước 3 của quy trình `/ccba-contribute-to-hub`, nếu Agent chưa chuyển sang nhánh `proposal/[tên-đề-xuất]` mà tiến hành commit, commit sẽ bị ghi trực tiếp vào `main`, làm mất khả năng tạo PR độc lập qua GitHub CLI.
2. **Thiếu Cơ Chế Đóng Vòng (Closed-Loop Sync Gap):** Sau khi PR được Hub Maintainer kiểm duyệt và Squash Merge, phía Spoke thiếu quy trình chuẩn hóa để:
   - Tự động/chủ động phát hiện PR đã được hợp nhất (`state: MERGED`).
   - Tái cài đặt package ở chế độ Editable (`pip install -e`).
   - Chạy bộ kiểm thử hồi quy tại Spoke (`validate_legal_spoke.py`).
   - Tự động dọn dẹp các nhánh `proposal/...` cũ và ghi nhận `session_learnings.md`.

### 2. Đề xuất giải pháp (RFC Proposal):
1. **Bổ sung Chốt Chặn Nhánh Tiền Commit (Pre-Commit Branch Assertion):**
   - Chèn kiểm tra bắt buộc tại Bước 3 của `ccba-contribute-to-hub.md`: Ngăn chặn mọi thao tác commit nếu `git branch --show-current` trả về `main`.
2. **Bổ sung Bước 7: Vòng Khép Kín Hậu Hợp Nhất (Closed-Loop Spoke Sync Gate):**
   - Chuẩn hóa 4 bước hậu hợp nhất tại Spoke:
     - `Bước 7.1`: Kiểm tra trạng thái PR qua `gh pr view <PR_NUMBER> --json state`.
     - `Bước 7.2`: Chạy `/ccba-update-spoke` hoặc `sync_spoke.py --spoke . --apply` để kéo workflows/skills mới.
     - `Bước 7.3`: Cài đặt lại package liên quan `pip install -e "[hub_path]/packages/[package-name]"`.
     - `Bước 7.4`: Chạy CI kiểm toán Spoke và dọn dẹp nhánh đề xuất cũ.
3. **Đồng bộ hóa với `ccba-review-proposal.md`:**
   - Cập nhật Bước 5 của quy trình thẩm định trên Hub để tự động phát thông báo hướng dẫn Spoke chạy chu trình đóng vòng.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Bổ sung Pre-Commit Branch Assertion vào `.agents/workflows/ccba-contribute-to-hub.md`.
- [ ] Bổ sung Bước 7 Closed-Loop Spoke Sync Gate vào `.agents/workflows/ccba-contribute-to-hub.md`.
- [ ] Cập nhật hướng dẫn Spoke Sync trong `.agents/workflows/ccba-review-proposal.md`.
- [ ] Kiểm tra tính tương thích của `sync_spoke.py` và chạy thử nghiệm thành công.

---
*Được đề xuất tự động từ Spoke `ccba-legal-knowledge` qua workflow `/ccba-issue-to-hub`.*


---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
