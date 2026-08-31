---
id: 209
title: "feat(workflows): Chuẩn hóa bộ đôi lệnh Upstream Contribution /ccba-issue-to-hub và /ccba-contribute-to-hub"
state: "needs-triage"
labels:

assignee: "none"
created_at: "2026-08-22T04:46:42Z"
updated_at: "2026-08-22T07:15:29Z"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context):
- Hiện tại quy trình đóng góp ngược từ Spoke lên Hub đang dùng tên \/ccba-propose-to-hub\, tên này dễ gây nhầm lẫn giữa việc 'Đóng góp Ý tưởng (Issue)' và 'Đóng góp Mã nguồn (PR)'.
- Cần chuẩn hóa thành một cặp lệnh đối xứng rõ ràng để hoàn thiện chu trình Upstream Contribution 2 chiều.

### 2. Đề xuất giải pháp (RFC Proposal):
1. **Bổ sung Workflow mới:** \/ccba-issue-to-hub\
   - Tự động gom ngữ cảnh thảo luận $\rightarrow$ Soạn RFC chuẩn $\rightarrow$ Tạo GitHub Issue trực tiếp lên Hub repo qua \gh issue create\.
2. **Chuẩn hóa Workflow hiện có:** Đổi tên \/ccba-propose-to-hub\ thành \/ccba-contribute-to-hub\
   - Giữ \/ccba-propose-to-hub\ làm Alias tương thích ngược (Backward compatibility).
   - Làm rõ vai trò: Chuyên trách đóng gói code, package, tests và mở GitHub Pull Request (PR) lên Hub.

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Tạo file workflow \.agents/workflows/ccba-issue-to-hub.md\ trên Hub.
- [ ] Cập nhật \.agents/workflows/ccba-contribute-to-hub.md\ (kèm alias cho \ccba-propose-to-hub\).
- [ ] Cập nhật Catalog và tài liệu Platform Hiến pháp (\AGENTS.md\).

---
*Được đề xuất và đóng góp từ Spoke \ccba-legal-knowledge\ (Upstream Feedback Loop)*

---

# 💬 Thảo luận (Discussion Log)
*(Chưa có thảo luận)*
