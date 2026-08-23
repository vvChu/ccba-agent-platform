# 🎫 Ticket WF-01: [HITL / Grilling] Làm rõ Giao thức Tương tác Kỹ sư khi Nộp Hồ sơ vào IDOP

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `HITL / Grilling`  
> **Trạng thái**: `OPEN` (Frontier)  
> **Assignee**: *Chưa gán*

---

## 1. Bối cảnh & Vấn đề Cần Giải Quyết

Trong hệ sinh thái IDOP CCBA, các Kỹ sư thực hiện công việc thẩm tra, lập mô hình BIM hoặc xuất báo cáo kỹ thuật tại Spoke dự án (trên OneDrive) hoặc Spoke cá nhân. Khi hoàn thành một mốc công việc (hoặc cần cập nhật WBS/PGV), dữ liệu cần được ghi nhận vào hệ thống 58 SharePoint Lists và 5TB Master OneDrive.

Tuy nhiên, chúng ta chưa chốt **phương thức tương tác tiện lợi và tự nhiên nhất** cho Kỹ sư:
- **Phương án A (CLI Command-driven)**: Kỹ sư (hoặc Agent theo lệnh của Kỹ sư) chạy lệnh CLI tường minh, ví dụ: `ccba idop submit --file report.md --task-id PGV-2026-001`.
- **Phương án B (Agent Auto-Detection & Workflow Hook)**: Khi Kỹ sư chạy các workflow như `/ccba-run-qc-pipeline` hoặc `/ccba-completion-checklist`, Agent tự động hỏi Kỹ sư: *"Bạn có muốn nộp báo cáo này vào IDOP không?"* và tự đóng gói JSON AST đẩy qua `IDOPBridge`.
- **Phương án C (Directory Watcher / File Drop)**: Kỹ sư chỉ cần copy file thành phẩm vào thư mục `.md/idop_staged/ready_to_push/`, một daemon hoặc tool chạy ngầm sẽ tự động quét và sync.

---

## 2. Câu hỏi Chất vấn Cốt lõi (Grilling Questions)

1. *Kỹ sư tại CCBA chủ yếu tương tác qua IDE (Gemini CLI / Antigravity / Cursor) hay tương tác trực tiếp qua file Explorer / Word / Excel?*
2. *Khi nộp hồ sơ, ai là người ký duyệt mốc: Kỹ sư tự nộp hay Chủ trì bộ môn / PM duyệt trước khi sync lên SharePoint?*
3. *Nếu xảy ra xung đột hoặc lỗi validation (Tier 1 Hard-Floor: ví dụ mã dự án không khớp hoặc sai lệch dòng tiền), Kỹ sư muốn nhận phản hồi ngay lập tức trên Terminal / Chat hay qua email cảnh báo M365?*

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] Phỏng vấn xong với Kỹ sư trưởng / Product Owner.
- [ ] Chốt giao thức tương tác chuẩn (Phương án A, B, C hoặc Hybrid).
- [ ] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.
- [ ] Unblock Ticket `[WF-04]`.
