---
id: 226
title: "feat(questionnaire): dual-track engine for upstream hub rfc and downstream multi-format project delivery"
state: "closed"
labels:
  - "enhancement"
  - "resolved"
assignee: "vvChu"
created_at: "2026-09-01T02:46:23Z"
updated_at: "2026-09-05T06:16:00Z"
pr: 238
pr_url: "https://github.com/vvChu/ccba-agent-platform/pull/238"
---

# 📖 Mô tả (Description)
### 1. Bối cảnh & Vấn đề (Context & Problem):
Kỹ năng `/ccba-to-questionnaire` hiện tại sinh ra tệp Markdown (`.md`) thuần túy với các câu hỏi mở trống trơn (`> [Nhập câu trả lời tại đây]`). Trong thực tế vận hành hệ sinh thái CCBA Hub-Spoke, mô hình này bộc lộ 3 hạn chế lớn:
1. **Chưa phân định bối cảnh kích hoạt (Context Ambiguity)**: Không phân biệt giữa nhu cầu gửi đề xuất kỹ thuật lên Hub (Platform Track) và nhu cầu gửi phiếu làm rõ thông số kỹ thuật/pháp lý cho Chủ đầu tư, Tư vấn thiết kế, Ban QLDA (Delivery Track).
2. **Rào cản tải nhận thức cho người nhận**: Người nhận bận rộn ngại viết văn bản dài, dẫn đến tình trạng chậm phản hồi hoặc bỏ qua bảng hỏi.
3. **Thiếu đa dạng định dạng truyền thống**: Đối tác và Lãnh đạo ngoài ngành phần mềm không thể đọc và phản hồi trực tiếp trên file Markdown thô, cần các định dạng văn phòng chuẩn (Word `.docx`, Web Landing Page, Email, QR Code).

### 2. Đề xuất giải pháp (RFC Proposal):
Nâng cấp `/ccba-to-questionnaire` thành **Hệ Thống Khảo Sát & Thu Thập Quyết Định Đa Kênh Tương Tác (Dual-Track Questionnaire Engine v2.0)**:

#### A. Phân Luồng Ngữ Cảnh Kép (Dual-Track Context Routing):
- **Nhánh 1: Spoke ➔ Hub (Platform Track)**: Dành cho thắc mắc, đề xuất tính năng, báo lỗi nền tảng $\rightarrow$ Tự động đóng gói và tích hợp trực tiếp với `/ccba-issue-to-hub` để mở GitHub Issue / RFC Proposal lên repository trung tâm.
- **Nhánh 2: Spoke Dự Án ➔ Đối Tác (Delivery Track)**: Dành cho làm rõ thông số thiết kế, PCCC, quy chuẩn, nghiệm thu HSHT với Chủ đầu tư/TVTK $\rightarrow$ Tự động sinh bộ xuất bản đa kênh (Word `.docx`, Web Form, Email, Chat).

#### B. Khung Trắc Nghiệm 3 Tầng Thông Minh (Pre-filled Hypotheses):
- Tự động sinh 3 kịch bản giải pháp có sẵn kèm 1 dòng tóm tắt đánh đổi (Trade-off summary):
  - **Phương án A**: Chuẩn mực / Khuyến nghị (Standard) ⭐
  - **Phương án B**: Tối giản / Nhanh gọn (Quick-Win)
  - **Phương án C**: Mở rộng dài hạn (Scalable)

#### C. Bộ Xuất Bản Đa Kênh (Omni-Format Adapter):
- **Word `.docx`**: Biểu mẫu Phiếu lấy ý kiến CCBA có format trang trọng, bảng chọn và khung phê duyệt.
- **Web Landing Page & QR Code**: Form trực quan host trên Server Spark (`:8095/q/<uuid>`) hoặc SharePoint CDE, hỗ trợ quét QR trên điện thoại và tự lưu tiến độ (LocalStorage).
- **Micro Chat Snippet**: Đoạn tóm tắt <15 dòng cho Zalo/Teams kèm cú pháp phản hồi siêu tốc (`1A, 2B, 3C`).
- **Email HTML Table**: Bảng so sánh trực quan chèn thẳng vào email.

#### D. Chu Trình Nạp Hai Chiều Khép Kín (Two-Way Execution Loop):
- Hỗ trợ lệnh `/ccba-to-questionnaire --reply "1A, 2B"` để Agent tự động nạp kết quả, tick chọn phương án và chuyển hóa tức thì thành Đặc tả (`/ccba-to-spec`) hoặc Task phát triển (`/ccba-to-tickets`).

### 3. Tiêu chí nghiệm thu (Acceptance Criteria):
- [ ] Cập nhật `to-questionnaire/SKILL.md` với bộ định tuyến Dual-Track Router (Platform vs Delivery).
- [ ] Tích hợp xuất file Word `.docx` qua package `ccba-ooxml` / `docx`.
- [ ] Xây dựng generator tệp HTML Form độc lập và tích hợp endpoint web trên Server Spark.
- [ ] Hỗ trợ lệnh nạp kết quả `--reply` để tự động kích hoạt `/ccba-to-spec` và `/ccba-to-tickets`.
- [ ] Cập nhật workflow wrapper `ccba-to-questionnaire.md` với đầy đủ tài liệu hướng dẫn.

---
*Được đề xuất tự động từ Spoke `vvc_working_space` qua workflow `/ccba-issue-to-hub`.*


---

# 💬 Thảo luận (Discussion Log)
> **@Antigravity AI Agent (Triage)** (2026-09-01T10:15:00Z):
> Đã hoàn tất quy trình sàng lọc và thẩm định kỹ thuật (Triage). 
> Xác nhận đề xuất nâng cấp `/ccba-to-questionnaire` thành **Dual-Track Questionnaire Engine v2.0** hoàn toàn khả thi và cần thiết để mở rộng tương tác bất đồng bộ (Platform Track vs Delivery Track) cũng như hỗ trợ xuất bản đa kênh (.docx, Web HTML, Micro Chat, Email) và nạp kết quả `--reply`.
> Đã gán nhãn `enhancement` và chuyển trạng thái sang `ready-for-agent`. Đính kèm Agent Brief chi tiết bên dưới.

---

## Agent Brief

**Phân loại:** enhancement
**Tóm tắt yêu cầu:** Nâng cấp `/ccba-to-questionnaire` thành Dual-Track Questionnaire Engine v2.0 hỗ trợ phân luồng Platform/Delivery, gợi ý khung trắc nghiệm 3 tầng, xuất bản đa kênh (.docx, Web HTML Form, Micro Chat, Email) và cơ chế nạp kết quả `--reply`.

### Hành vi hiện tại (Current behavior)
1. `to-questionnaire/SKILL.md` (v1.1.0) chỉ tạo file Markdown (`.md`) chứa câu hỏi mở trống trơn (`> [Nhập câu trả lời tại đây]`).
2. Chưa phân định luồng công việc nội bộ Hub (Platform Track) với luồng thu thập quyết định dự án ngoài công trường / chủ đầu tư (Delivery Track).
3. Thiếu các định dạng xuất bản văn phòng (.docx, HTML Form, Chat snippet ngắn, Email table) khiến đối tác phi kỹ thuật khó phản hồi.
4. Thiếu cơ chế nạp ngược phản hồi tự động vào hệ sinh thái CCBA để kích hoạt `/ccba-to-spec` hoặc `/ccba-to-tickets`.

### Hành vi mong muốn (Desired behavior)
1. **Dual-Track Context Router**:
   - Nhánh 1: *Platform Track* (Spoke ➔ Hub RFCs): Tự động tích hợp `/ccba-issue-to-hub` để mở GitHub Issue.
   - Nhánh 2: *Delivery Track* (Spoke ➔ CĐT / TVTK / BQLDA): Tự động sinh bộ xuất bản đa kênh.
2. **Pre-filled Hypotheses Matrix**:
   - Tự động sinh 3 phương án lựa chọn mặc định cho mỗi câu hỏi trọng tâm:
     - Phương án A: Chuẩn mực / Khuyến nghị (Standard) ⭐
     - Phương án B: Nhanh gọn / Tối giản (Quick-Win)
     - Phương án C: Mở rộng dài hạn (Scalable)
3. **Omni-Format Adapters**:
   - Sinh file `.md` gốc theo chuẩn Knowledge Base tại `.md/knowledge/questionnaires/`.
   - Xuất file Word `.docx` đẹp, chuyên nghiệp qua `docx` / `ccba-ooxml`.
   - Sinh file HTML Form độc lập (tự lưu LocalStorage, tích hợp preview Web & mã QR).
   - Đoạn tóm tắt Micro Chat Snippet (<15 dòng) cho Zalo/Teams (cú pháp phản hồi siêu tốc: `1A, 2B, 3C`).
   - Bảng so sánh HTML Table cho Email.
4. **Two-Way Execution Loop (`--reply`)**:
   - Hỗ trợ cờ `--reply "1A, 2B"` để Agent tự động nạp kết quả vào file Markdown, đánh dấu lựa chọn và chuyển tiếp sang `/ccba-to-spec` hoặc `/ccba-to-tickets`.

### Các Interface & Kiểu dữ liệu chính (Key interfaces)
- `.agents/skills/to-questionnaire/SKILL.md`: Cập nhật toàn diện quy trình Dual-Track, Pre-filled hypotheses, Omni-Format và Two-Way loop.
- `.agents/workflows/ccba-to-questionnaire.md`: Cập nhật mô tả lệnh và các cờ tham số (`--track`, `--format`, `--reply`).
- Generator modules / helper templates cho `.docx` và HTML Form.

### Tiêu chuẩn nghiệm thu (Acceptance criteria)
- [ ] Cập nhật `to-questionnaire/SKILL.md` đạt chuẩn CCBA SKILL format với Dual-Track Router và Pre-filled Hypotheses.
- [ ] Hỗ trợ xuất đồng thời Markdown, Word `.docx`, Web HTML Form độc lập, Micro Chat Snippet và Email Table.
- [ ] Hỗ trợ cú pháp nạp phản hồi `--reply "<answers>"` tự động cập nhật bảng hỏi.
- [ ] Cập nhật workflow `/ccba-to-questionnaire` tương ứng trong `.agents/workflows/ccba-to-questionnaire.md`.
- [ ] Bổ sung test/eval scenario cho `to-questionnaire` trong `tests/` hoặc `skills-eval`.

### Phạm vi loại trừ (Out of scope)
- Không can thiệp vào cấu trúc lưu trữ của Issue Tracker ngoài việc tích hợp gọi `/ccba-issue-to-hub`.
