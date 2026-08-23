# 🎫 Ticket WF-01: [HITL / Grilling] Làm rõ Giao thức Tương tác Kỹ sư khi Nộp Hồ sơ vào IDOP

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `HITL / Grilling`  
> **Trạng thái**: `CLOSED` (Đã hoàn thành)  
> **Assignee**: *AI Platform Engineering & Kỹ sư Trưởng*

---

## 1. Bối cảnh & Vấn đề Cần Giải Quyết

Trong hệ sinh thái IDOP CCBA, các Kỹ sư thực hiện công việc thẩm tra, lập mô hình BIM hoặc xuất báo cáo kỹ thuật tại Spoke dự án (trên OneDrive) hoặc Spoke cá nhân. Khi hoàn thành một mốc công việc (hoặc cần cập nhật WBS/PGV), dữ liệu cần được ghi nhận vào hệ thống 58 SharePoint Lists và 5TB Master OneDrive.

---

## 2. Quyết Định Đã Chốt Qua Phỏng Vấn (Grilling Decisions)

1. **Phương thức Tương tác Chính: Hybrid Workflow + CLI**:
   - Agent tự động đề xuất nộp sau khi Kỹ sư chạy xong các Workflow thẩm tra/nghiệm thu (ví dụ `/ccba-ai-qc-pccc-audit`, `/completion-checklist`).
   - Cung cấp thêm bộ lệnh CLI tường minh `ccba idop submit --file ... --task-id ...` cho Kỹ sư chủ động thao tác.
2. **Quy trình Ký duyệt Phân cấp 2 Tầng**:
   - **Tầng 1 (Kỹ sư Thực thi)**: Stage hồ sơ vào `.md/idop_staged/` và vượt qua bộ kiểm tra tự động AI Pre-Submission Gate.
   - **Tầng 2 (Chủ trì Hợp đồng / PM)**: Xác nhận lệnh nộp chính thức để đẩy bản ghi và tài liệu lên SharePoint IDOP của CCBA.
3. **Cơ chế Phản hồi Vi phạm: Tức thì tại Chat/Terminal**:
   - Khi hồ sơ vi phạm Tier 1 Hard-Floor (mã dự án không khớp, viện dẫn luật hết hiệu lực, sai lệch dòng tiền số học), hệ thống lập tức hiển thị bảng lỗi chi tiết tại Terminal/Chat và chặn tạo biên bản nộp.

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Phỏng vấn xong với Kỹ sư trưởng / Product Owner.
- [x] Chốt giao thức tương tác chuẩn (Hybrid Workflow + CLI).
- [x] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.
- [x] Unblock Ticket `[WF-04]`.

