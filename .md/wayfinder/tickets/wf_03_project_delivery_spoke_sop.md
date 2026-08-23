# 🎫 Ticket WF-03: [AFK / Task] Bộ Quy Chuẩn & SOP Khởi Tạo Project Delivery Spoke trên OneDrive

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Task`  
> **Trạng thái**: `CLOSED` (Đã hoàn thành)  
> **Tài liệu SOP**: [project_delivery_spoke_setup.md](../../../docs/sop/project_delivery_spoke_setup.md)  
> **Template**: [workspace_context.delivery.yaml](../../../templates/workspace_context.delivery.yaml)  
> **Assignee**: *AI Platform Engineering*

---

## 1. Bối cảnh & Mục tiêu

Khác với các Spoke phát triển phần mềm (có kho Git riêng và mở PR), **Project Delivery Spoke** (như `D:\OneDrive - IBST BIM\00 Works\2026-04 DH Viet Nhat`) vận hành trên hệ thống tệp tin đám mây OneDrive/SharePoint của CCBA:
- Không sử dụng Git remote để tránh rò rỉ hồ sơ mật của khách hàng và tránh xung đột binary (Revit, AutoCAD, PDF scan).
- Vẫn cần kế thừa các AI Skills & Workflows từ Hub (`.agents/workflows/`, `.agents/skills/`).
- Cần có tệp `workspace_context.yaml` để Agent hiểu đúng thông tin dự án, tiêu chuẩn áp dụng, mốc tiến độ WBS.

---

## 2. Kết Quả Triển Khai

1. **Chuẩn hóa Mẫu `workspace_context.delivery.yaml`**:
   - Định nghĩa đầy đủ các trường: `project.name`, `project_code`, `national_project_id`, `contract_id`, `archetype: project_delivery`, `type: Thẩm tra thiết kế`, `mode: consulting`, `organizational_identity` (15 vai trò IDOP), `qc_governance` (cấp bậc thẩm tra, Quad-view Vision), `standards_applied`, `cde_structure`, `idop_staging`.
2. **Quy trình Khởi tạo 4 Bước (SOP)**:
   - Soạn thảo tài liệu chuẩn `docs/sop/project_delivery_spoke_setup.md` hướng dẫn chi tiết từ tạo thư mục OneDrive, sao chép cấu hình, kích hoạt `adopt_spoke.py` đến nộp hồ sơ vào IDOP Staging.
3. **Kiểm thử Xác minh Hoàn tất**:
   - `tests/test_delivery_spoke_setup.py` kiểm thử toàn bộ cấu trúc YAML và mô phỏng thành công quy trình adopt một Spoke Delivery mock.

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Soạn thảo tài liệu SOP `docs/sop/project_delivery_spoke_setup.md`.
- [x] Tạo template `templates/workspace_context.delivery.yaml`.
- [x] Kiểm thử mẫu khởi tạo trên một thư mục mock (`tests/test_delivery_spoke_setup.py`).
- [x] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.

