# Danh sách Tickets: Khung Quy Trình Tư Vấn Pháp Lý Tự Động CCBA

Tài liệu phân rã các công việc phát triển theo dạng lát cắt dọc (tracer bullets) dựa trên Spec [spec-tu-van-phap-luat-tu-dong.md](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/specs/spec-tu-van-phap-luat-tu-dong.md).

👉 Nguyên tắc: Chỉ thực hiện các ticket nằm ở Biên giới (Frontier) - là những ticket không bị chặn hoặc tất cả blockers của nó đã ở trạng thái [x] hoàn thành.

---

## Ticket 1: [Intake] Bóc tách 5 trục dữ kiện & Phỏng vấn định hướng tự động

**Nghiệp vụ cần làm:**  
Người dùng gửi câu hỏi tư vấn pháp lý, hệ thống tự động bóc tách 5 trục (*Đối tượng, Hành vi, Tác động, Phạm vi, Thời điểm*) và tự động đưa ra các câu hỏi phỏng vấn định hướng (Guided Interview) để lấp đầy các dữ kiện bị thiếu trước khi thực hiện tra cứu.

**Bị chặn bởi:** Không có — Có thể bắt đầu ngay (Frontier).

- [ ] Định nghĩa Pydantic schema `IntakeTaxonomy` trong `ccba_legal/intake.py`.
- [ ] Triển khai hàm `parse_intake_question(text: str)` bóc tách 5 trục dữ kiện.
- [ ] Triển khai hàm phát hiện thiếu tọa độ dữ kiện và sinh câu hỏi phỏng vấn gợi mở.
- [ ] Viết unit tests kiểm chứng trong `packages/ccba-legal-intel/tests/test_intake.py`.

---

## Ticket 2: [Conflict Engine] Xử lý xung đột VBPL & Định lượng Điểm số Rủi ro Xanh - Vàng - Đỏ

**Nghiệp vụ cần làm:**  
Khi tra cứu văn bản pháp luật, hệ thống tự động đối soát mối quan hệ xung đột theo 3 quy tắc Lex (*Lex Superior, Lex Posterior, Lex Specialis*), trích xuất Điều khoản Chuyển tiếp theo mốc thời gian, tính toán Risk Score (0-100) và gán nhãn cảnh báo trực quan: Xanh (80-100), Vàng (50-79), Đỏ (<50).

**Bị chặn bởi:** Ticket 1: `[Intake] Bóc tách 5 trục dữ kiện & Phỏng vấn định hướng tự động`

- [ ] Triển khai `LexConflictEngine` trong `ccba_legal/conflict.py` mã hóa 3 quy tắc xung đột Lex.
- [ ] Triển khai thuật toán trích xuất Điều khoản Chuyển tiếp đối soát mốc thời gian vụ việc.
- [ ] Định nghĩa `RiskAssessmentScore` và gán nhãn rủi ro `GREEN`, `YELLOW`, `RED`.
- [ ] Viết unit tests kiểm chứng trong `packages/ccba-legal-intel/tests/test_conflict.py`.

---

## Ticket 3: [Reporter] Báo cáo tư vấn Dual-Layer & Lưu vết vật lý file Markdown/Word

**Nghiệp vụ cần làm:**  
Hệ thống trả về báo cáo tư vấn 2 tầng (Tầng 1 Executive Summary cho quản lý + Tầng 2 Detailed Risk Matrix với 100% trích dẫn SOT nguyên văn có tọa độ chính xác `[Loại VB - Số hiệu - Điều - Khoản]`). Tự động xuất và lưu vết file báo cáo vật lý trong workspace.

**Bị chặn bởi:** Ticket 2: `[Conflict Engine] Xử lý xung đột VBPL & Định lượng Điểm số Rủi ro Xanh - Vàng - Đỏ`

- [ ] Cập nhật `ccba_legal/coordinator.py` khớp nối luồng Intake -> Conflict -> Reporter.
- [ ] Render giao diện Báo cáo Dual-Layer hỗ trợ trích dẫn SOT nguyên văn kèm tọa độ pháp lý.
- [ ] Tự động ghi nhận file báo cáo Markdown/Word lưu vết vật lý vào `.md/extracted_docs/` hoặc `.md/scratch/`.
- [ ] Viết integration tests kiểm chứng toàn trình luồng tư vấn.

---

## Ticket 4: [Dispatcher] Tùy chọn sinh Dự thảo Công văn Xin ý kiến Cơ quan Nhà nước chuẩn Nghị định 30

**Nghiệp vụ cần làm:**  
Đối với các trường hợp bị gán nhãn Rủi ro Đỏ (Score < 50), hệ thống mặc định phát cảnh báo rủi ro và hướng đi tiếp theo, đồng thời cung cấp tùy chọn kích hoạt sinh file dự thảo Công văn Xin ý kiến Hướng dẫn Cơ quan Nhà nước (`.docx`) chuẩn thể thức Nghị định 30/2020/NĐ-CP.

**Bị chặn bởi:** Ticket 3: `[Reporter] Báo cáo tư vấn Dual-Layer & Lưu vết vật lý file Markdown/Word`

- [ ] Thêm option kích hoạt sinh dự thảo công văn trên giao diện/CLI khi báo cáo đạt nhãn Rủi ro Đỏ.
- [ ] Tích hợp package `ccba-ooxml` / skill `copywriting` để nạp template và render file `.docx` công văn xin ý kiến hướng dẫn.
- [ ] Viết unit/integration tests cho module sinh công văn On-Demand.
