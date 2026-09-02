# ADR 0052: Boost Deep Reasoning Protocol, Early Escalation & Multi-Agent Hierarchy

## 1. Trạng Thái (Status)
**ACCEPTED & ADOPTED** (2026-09-01)

## 2. Bối Cảnh (Context)
Trong quá trình vận hành các chu trình phát triển phần mềm (SDLC), nghiên cứu kiến trúc và kiểm soát chất lượng thiết kế/pháp lý trên CCBA Platform, các Agent thường gặp phải những bài toán có độ phức tạp cao (concurrency, race conditions, xung đột ranh giới quy chuẩn, polyglot deep refactoring).
Khi gặp các bài toán này, các hạn chế sau đã được ghi nhận:
1. **Bế tắc TDD & Đoán Mò (Blind Guessing Loops):** Khi kiểm thử thất bại liên tiếp, Agent có xu hướng lặp lại các phương án chắp vá cho tới khi cạn kiệt ngân sách ngữ cảnh (Context Exhaustion).
2. **Thiếu Phản Biện Đa Tác Nhân:** Kỹ năng `ccba-research` chỉ sử dụng 1 subagent đơn lẻ, dẫn tới hiện tượng thiên kiến xác nhận (Confirmation Bias) khi đánh giá các quyết định kiến trúc lớn hoặc xung đột pháp luật.
3. **Chưa Có Cơ Chế Leo Thang Chuẩn Hóa:** Hệ thống thiếu cơ chế chuyển giao bài toán từ vòng lặp ReAct đơn luồng sang chu trình suy luận đa tác nhân chuyên sâu (**Deep Multi-Agent Reasoning**) như tính năng `/boost` của Google Antigravity.

## 3. Quyết Định Thiết Kế (Decisions)

### A. Thiết Lập Điểm Cắt Lỗi Sớm & Boost Escalation Gate
- Cập nhật quy chuẩn thực thi ([`docs/rules/execution_guardrails.md`](../rules/execution_guardrails.md)):
  - **Early Escalation tại Vòng 3:** Sau 3 vòng edit→test liên tiếp thất bại do lỗi logic sâu hoặc xung đột đa file, Agent **bắt buộc dừng thử mù**, lập tức đóng gói **`Deep Problem Brief`**.
  - **Hard Stop tại Vòng 5:** Chạm ngưỡng 5 vòng, Agent dừng ngay lập tức, commit WIP và kích hoạt **`Boost Escalation Gate`** để đề xuất người dùng thực thi `/boost [brief]`.

### B. Cấu Trúc Đóng Gói Deep Problem Brief
- Quy chuẩn hóa mẫu dữ liệu đóng gói khi kích hoạt Escalation Gate:
  - **Failure Manifest:** Triệu chứng lỗi cốt lõi.
  - **Tested Hypotheses:** Danh sách 2-3 giả thuyết đã kiểm chứng và lý do thất bại.
  - **Seams Involved:** Danh sách files/classes/functions liên quan.
  - **Error Logs:** Trích đoạn log then chốt.
  - **Actionable Recommendation:** Khuyến nghị kích hoạt `/boost` kèm nội dung brief.

### C. Triển Khai Kiến Trúc Suy Luận 3 Pha (Three-Phase Reasoning Hierarchy)
- Áp dụng cấu trúc 3 pha của Antigravity Boost vào các Master Skills và Research Workflows của CCBA:
  - **Pha 1 (Goal & Strategy Formulation):** Phân rã bài toán, xác định các workstreams độc lập.
  - **Pha 2 (Parallel Multi-Agent Execution):** Khởi chạy các Subagents chuyên biệt song song (ví dụ: `Proponent` vs `Challenger` trong `ccba-research`).
  - **Pha 3 (Synthesis & Delivery):** Hợp nhất kết quả, phản biện chéo và xuất báo cáo chuẩn 5 phần.

### D. Cưỡng Chế Rào Chắn Đa Tác Nhân (Two-Layer Sub-Agent Guardrail — ADR 0035)
- Để ngăn chặn bùng nổ đệ quy subagents và cạn kiệt token:
  - **Depth Limit = 1:** Nghiêm cấm subagent con spawn thêm subagents.
  - **Read-Only Scoping:** Subagents chỉ được cấp quyền đọc (`view_file`, `grep_search`, `read_resource`) và chạy scoped test cô lập.
  - **Worker Cap:** Tối đa 3 subagents chạy song song trong một phiên.

## 4. Hệ Quả (Consequences)
- **Tiết Kiệm Context & Token:** Chặn đứng triệt để các vòng lặp đoán mò vô ích sau 3 vòng test fail.
- **Nâng Cao Chất Lượng Nghiên Cứu:** Mô hình Dual-Agent Adversarial giúp loại bỏ thiên kiến và phát hiện sớm các rủi ro bảo mật (Maskara) và phá vỡ Deep Seams.
- **Tương Thích Tuyệt Đối với Hệ Sinh Thái Antigravity:** Tận dụng tối đa sức mạnh của slash command `/boost` trên cả IDE và CLI.
