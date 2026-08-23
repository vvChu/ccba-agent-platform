# 🎫 Ticket WF-03: [AFK / Task] Bộ Quy Chuẩn & SOP Khởi Tạo Project Delivery Spoke trên OneDrive

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Task`  
> **Trạng thái**: `OPEN` (Frontier)  
> **Assignee**: *Chưa gán*

---

## 1. Bối cảnh & Mục tiêu

Khác với các Spoke phát triển phần mềm (có kho Git riêng và mở PR), **Project Delivery Spoke** (như `D:\OneDrive - IBST BIM\00 Works\2026-04 DH Viet Nhat`) vận hành trên hệ thống tệp tin đám mây OneDrive/SharePoint của Viện IBST:
- Không sử dụng Git remote để tránh rò rỉ hồ sơ mật của khách hàng và tránh xung đột binary (Revit, AutoCAD, PDF scan).
- Vẫn cần kế thừa các AI Skills & Workflows từ Hub (`.agents/workflows/`, `.agents/skills/`).
- Cần có tệp `workspace_context.yaml` để Agent hiểu đúng thông tin dự án, tiêu chuẩn áp dụng, mốc tiến độ WBS.

---

## 2. Nhiệm vụ Triển khai

1. **Chuẩn hóa Mẫu `workspace_context.yaml` cho Project Delivery Spoke**:
   - Bao gồm: `project_code`, `national_project_id`, `contract_id`, `archetype: project_delivery`, `standards_applied`, `milestones`, `assigned_roles`.
2. **Xây dựng Quy trình Khởi tạo Tối giản (1-Click / 1-Command Bootstrap SOP)**:
   - Kỹ sư chạy lệnh hoặc copy script khởi tạo $\rightarrow$ Tạo cấu trúc thư mục chuẩn `.md/`, tải các workflow cần thiết từ Hub cục bộ, thiết lập link tới `ccba-legal-knowledge`.
3. **Cơ chế Đồng bộ Xuôi (Downstream Sync without Git)**:
   - Sử dụng `SpokeSynchronizer` để copy cập nhật các workflow mới từ `D:\GitHubProjects\ccba-agent-platform` sang thư mục OneDrive của dự án.

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] Soạn thảo tài liệu SOP `docs/sop/project_delivery_spoke_setup.md`.
- [ ] Tạo template `templates/workspace_context.delivery.yaml`.
- [ ] Kiểm thử mẫu khởi tạo trên một thư mục mock.
- [ ] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.
