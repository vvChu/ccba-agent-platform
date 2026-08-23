---
proposal_id: "2026-08-23_closed_loop_spoke_sync_and_branch_guard"
type: "workflow"
name: "closed-loop-spoke-sync-and-branch-guard"
status: "open"
priority: "Cao"
proposed_by_project: "ccba-legal-knowledge"
proposed_by_archetype: "knowledge_corpus"
proposed_date: "2026-08-23"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Tác vụ Admin"
---

# Proposal: Branch Assertion Guard & Closed-Loop Spoke Sync Gate

## 1. Bối cảnh & Vấn đề Cốt lõi (Problem Statement)
Trong quá trình vận hành Upstream Contribution Loop giữa Spoke và Hub theo Issue #218:
1. **Rủi ro Commit Nhầm vào Main:** Khi thực thi Bước 3 tại Hub, nếu Agent chưa chuyển nhánh mà tiến hành commit, commit sẽ đi thẳng vào `main`, làm mất cơ chế Pull Request.
2. **Thiếu Chu Trình Đóng Vòng Hậu Hợp Nhất:** Khi PR được Hub merge, Spoke chưa có bộ quy trình 4 bước chuẩn để tự động nhận biết, đồng bộ workflows/skills, cập nhật package editable và dọn dẹp nhánh đề xuất.

## 2. Giải pháp Kỹ thuật Triển khai (Technical Implementation)
1. **Pre-Commit Branch Assertion Guard (`ccba-contribute-to-hub.md` - Bước 3):**
   - Cưỡng chế kiểm tra `git branch --show-current` khác `main` trước khi cho phép commit.
2. **Closed-Loop Spoke Sync Gate (`ccba-contribute-to-hub.md` - Bước 7):**
   - Bước 7.1: Xác nhận PR đã chuyển trạng thái `MERGED`.
   - Bước 7.2: Kéo workflows/skills mới về Spoke (`sync_spoke.py --spoke . --apply`).
   - Bước 7.3: Cài đặt lại package ở chế độ Editable (`pip install -e`).
   - Bước 7.4: Chạy kiểm thử hồi quy Spoke (`validate_legal_spoke.py`), xóa nhánh đề xuất cũ và lưu nhật ký.
3. **Đồng bộ hóa với `ccba-review-proposal.md`:**
   - Cập nhật Bước 5 của quy trình thẩm định để liên kết trực tiếp với Bước 7 của quy trình đóng góp.

## 3. Tiêu chí Nghiệm thu & Liên kết
- **Issue liên kết:** Closes #218
- **Tương thích:** 100% với cơ chế Safe-by-Default của `/ccba-update-spoke` và `sync_spoke.py`.
