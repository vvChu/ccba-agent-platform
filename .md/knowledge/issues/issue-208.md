---
id: 208
title: "feat(sync-spoke): Triển khai cơ chế Safe-by-Default (Mặc định An toàn) cho quy trình /ccba-update-spoke"
state: "needs-triage"
labels:

assignee: "none"
created_at: "2026-08-22T04:33:21Z"
updated_at: "2026-08-22T05:59:52Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context):
Hiện tại quy trình \/ccba-update-spoke\ thực thi cập nhật trực tiếp hoặc yêu cầu người dùng phải tự nhớ truyền cờ \--dry-run\. Điều này tạo ra rủi ro tâm lý và có thể gây ghi đè ngoài ý muốn nếu Spoke đang có uncommitted changes.

### 2. Đề xuất giải pháp (RFC Proposal):
1. **Two-Phase Execution (Mặc định chạy 2 pha):**
   - Pha 1: Luôn tự động chạy \--dry-run\, hiển thị bảng Preview (\🟢 NEW\, \🔄 UPDATED\, \🛡️ PRESERVED\).
   - Pha 2: Yêu cầu người dùng xác nhận rõ ràng trước khi thực thi ghi đè thật.
2. **Git Working Tree Guard:**
   - Kiểm tra \git status\. Nếu thư mục \.agents/\ có uncommitted changes, yêu cầu \commit\ hoặc \stash\ trước khi sync để đảm bảo khả năng hoàn tác.
3. **Snapshot Backup & Undo:**
   - Tự động tạo bản sao lưu \.agents.bak_<timestamp>\ trước khi sync để có thể rollback tức thì.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Script \sync_spoke.py\ hỗ trợ cờ tương tác an toàn hoặc đặt hành vi \--dry-run\ trước làm mặc định.
- [ ] Workflow \ccba-update-spoke.md\ được cập nhật hướng dẫn Agent tuân thủ luồng 2 pha.
- [ ] Báo cáo tổng kết phân biệt rõ ràng các file được bảo lưu (\🛡️ PRESERVED\).

---
*Được đề xuất và đóng góp từ Spoke \ccba-legal-knowledge\ (Upstream Loop)*

---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
