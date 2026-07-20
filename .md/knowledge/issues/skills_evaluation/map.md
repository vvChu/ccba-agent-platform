# Bản đồ Định hướng: Đánh giá Kỹ năng AI (Skills Evaluation Map)

Bản đồ này vạch ra lộ trình nghiên cứu, thiết kế và triển khai hệ thống kiểm thử Evaluation Harness cho các kỹ năng AI của CCBA Platform.

---

## 🎯 Điểm đích (Destination)
Xây dựng thành công bộ khung đánh giá (Evaluation Framework) chuẩn cho các CCBA Skills. Toàn bộ 3 kỹ năng `copywriting`, `completion-checklist`, và `ccba-ai-qc-pccc-audit` đều vượt qua các bộ kiểm thử tự động với tỷ lệ độ tin cậy được đo lường cụ thể và tích hợp ổn định vào quy trình CI của dự án.

---

## 📝 Ghi chú (Notes)
- Ưu tiên phương án Regex Asserts để tối giản chi phí và độ trễ. Chỉ dùng LLM-as-a-Judge cho các phần thẩm tra logic phức tạp của PCCC.
- Đảm bảo môi trường chạy thử Evals được cô lập hoàn toàn (Isolated runs) để tránh mô hình đọc lại các lịch sử chạy trước đó.

---

## 🤝 Quyết định đã chốt (Decisions so far)
- **[Chốt 3 kỹ năng thí điểm](file:///d:/GitHubProjects/ccba-agent-platform/.md/projects/NC_Dont_Ship_Skills_Without_Evals/session_document.md):** Thống nhất triển khai thí điểm Evals cho `copywriting`, `completion-checklist`, và `ccba-ai-qc-pccc-audit` (Thông qua Brainstorm Session ngày 2026-07-20).
- **[Xây dựng thành công Core Eval Runner](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/scripts/eval_runner.py):** Đã code xong công cụ runner CLI Python hỗ trợ Regex Asserts và LLM Judge.
- **[Hoàn thành bộ Test Cases](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/test_cases/):** Thiết lập xong các tệp test cases JSON độc lập cho 3 kỹ năng thí điểm.

---

## 🌫️ Chưa xác định rõ (Not yet specified)
- Cơ chế tích hợp Core Eval Runner vào Git pre-commit hook hoặc GitHub Actions của CCBA Platform để chạy tự động trên mỗi diff.
- Quy chuẩn chấm điểm và Rubric chi tiết cho LLM-as-a-Judge trong bộ môn PCCC để đạt độ tin cậy >90.

---

## 🚫 Ngoài phạm vi (Out of scope)
- Sử dụng LLM tự động tạo Test Cases hàng loạt (chỉ dùng test cases do con người thiết kế để đảm bảo chất lượng).

---

## 🎫 Frontier Tickets (Vé Biên giới - Có thể thực hiện ngay)

### 1. `[Ticket #01: Xây dựng Core Eval Runner (eval_runner.py)](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/scripts/eval_runner.py)`
- **Loại:** Task [AFK]
- **Trạng thái:** Đã hoàn thành (Done)
- **Mô tả:** Viết script Python nhận file JSON test cases, gọi API mock Agent cô lập, thực hiện đối sánh kết quả bằng Regex và LLM-as-a-Judge, tính toán tỷ lệ Pass/Fail qua nhiều lần thử.

### 2. `[Ticket #02: Viết bộ test case cho copywriting (eval_copywriting.json)](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/test_cases/eval_copywriting.json)`
- **Loại:** Research [AFK]
- **Trạng thái:** Đã hoàn thành (Done)
- **Mô tả:** Thiết lập bộ 5-10 test cases kiểm thử kỹ năng `copywriting` (Nghị định 30, kiểm tra lỗi placeholder còn sót).

### 3. `[Ticket #03: Viết bộ test case cho completion-checklist (eval_checklist.json)](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/test_cases/eval_checklist.json)`
- **Loại:** Research [AFK]
- **Trạng thái:** Đã hoàn thành (Done)
- **Mô tả:** Thiết lập bộ 5-10 test cases kiểm thử kỹ năng `completion-checklist` (Nghị định 06/2021, kiểm tra cấu trúc hồ sơ hoàn thành).

### 4. `[Ticket #04: Viết bộ test case cho ccba-ai-qc-pccc-audit (eval_pccc.json)](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/test_cases/eval_pccc.json)`
- **Loại:** Research [AFK]
- **Trạng thái:** Đã hoàn thành (Done)
- **Mô tả:** Thiết lập bộ 5-10 test cases kiểm thử kỹ năng `ccba-ai-qc-pccc-audit` dựa trên tập dữ liệu ground truth PCCC và định nghĩa Rubric cho LLM Judge.
