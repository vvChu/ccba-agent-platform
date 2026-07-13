# ADR 0018: Loại bỏ skill ccba-idop-scaffolder khỏi Central Hub

* **Trạng thái:** Approved
* **Người đề xuất:** Antigravity AI Agent
* **Ngày quyết định:** 2026-07-13

---

## 1. Ngữ cảnh (Context)
Skill `ccba-idop-scaffolder` cùng các mã nguồn bổ trợ (`idop_scaffolder.py`, `verify_idop_setup.py`) ban đầu được lưu trữ trên Central Hub nhằm cung cấp bộ công cụ tự động hóa việc scaffold cấu trúc thư mục CDE SharePoint và mã nguồn React App cho nền tảng IDOP. 

Tuy nhiên, trong quá trình phát triển, chúng tôi nhận thấy:
1. IDOP đang được xây dựng và thảo luận ý tưởng thiết kế trong một dự án Spoke chuyên biệt dành riêng cho IDOP.
2. Các thông tin cấu hình, triggers và script liên quan đến việc scaffold IDOP trên Hub gây nhiễu cho các phiên thảo luận thiết kế chung của nền tảng Hub.
3. Các Spoke dự án thông thường (như QC, MEP, PCCC Audit) chỉ cần đồng bộ các quy chuẩn kiểm tra chất lượng từ Hub, hoàn toàn không cần tự scaffold hay khởi tạo hạ tầng IDOP từ đầu.

## 2. Quyết định (Decisions)
Chúng tôi thống nhất thực hiện các thay đổi sau:
1. **Loại bỏ hoàn toàn** thư mục skill `.agents/skills/idop-scaffolder/` (bao gồm `SKILL.md`) khỏi Central Hub.
2. **Xóa bỏ các tệp tin script bổ trợ** trực tiếp cho skill này bao gồm `scripts/idop_scaffolder.py` và tệp kiểm thử tương ứng `scripts/verify_idop_setup.py`.
3. **Cập nhật danh mục** `catalog.yaml` để xóa bỏ đăng ký của skill `ccba-idop-scaffolder`.
4. **Giữ nguyên tiền tố IDOP** trong các lớp xử lý và tệp tin thuộc bộ công cụ QC (như `IDOPDiscovery`, `IDOPAuditEngine`) để đảm bảo tính ổn định và tránh lỗi regression diện rộng.

Mã nguồn của bộ scaffolder này đã được sao lưu và sẽ được duy trì nội bộ bên trong Spoke chuyên biệt phát triển nền tảng IDOP.

## 3. Hệ quả (Consequences)
*   **Tích cực:** Central Hub trở nên gọn nhẹ, sạch sẽ và không còn bị nhiễu thông tin bởi các lệnh khởi tạo hạ tầng IDOP cụ thể trong các phiên thảo luận thiết kế Hub.
*   **Tiêu cực:** Các Spoke dự án thông thường sẽ không còn tiếp cận được lệnh scaffold IDOP trực tiếp từ Hub (điều này thực tế không ảnh hưởng vì họ không có nhu cầu sử dụng công cụ này).

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
