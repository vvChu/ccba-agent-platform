# 🎫 Ticket WF-04: [AFK / Task] Đóng gói Tiện ích CLI `ccba-spoke` Hỗ trợ Kỹ sư Thao tác Staging và Đồng bộ

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](file:///d:/GitHubProjects/ccba-agent-platform/.md/wayfinder/idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Task`  
> **Trạng thái**: `BLOCKED`  
> **Bị chặn bởi**: [Ticket WF-01](file:///d:/GitHubProjects/ccba-agent-platform/.md/wayfinder/tickets/wf_01_idop_submission_interface.md)  
> **Assignee**: *Chưa gán*

---

## 1. Bối cảnh & Mục tiêu

Sau khi [Ticket WF-01](file:///d:/GitHubProjects/ccba-agent-platform/.md/wayfinder/tickets/wf_01_idop_submission_interface.md) chốt giao thức tương tác nộp hồ sơ, chúng ta cần đóng gói công cụ CLI tiện ích `ccba-spoke` (hoặc module lệnh trong package `ccba-core`) để Kỹ sư có thể:
1. `ccba-spoke sync`: Đồng bộ kỹ năng & workflows mới nhất từ Hub cục bộ vào Spoke hiện tại.
2. `ccba-spoke stage`: Đóng gói và lưu hồ sơ/báo cáo vào Local Staging Queue (`.md/idop_staged/`).
3. `ccba-spoke flush`: Kích hoạt `IDOPBridge` đẩy các bản ghi trong queue lên 58 SharePoint Lists và 5TB Master OneDrive.
4. `ccba-spoke status`: Kiểm tra trạng thái kết nối tới AI Gateway Server Spark và IDOP M365.

---

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] Triển khai mã nguồn CLI với các lệnh `sync`, `stage`, `flush`, `status`.
- [ ] Viết unit tests kiểm thử các ca online/offline và idempotent replay.
- [ ] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.
