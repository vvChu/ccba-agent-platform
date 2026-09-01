# CCBA Execution Guardrails & Async Task Policy

> **Tài liệu Tham chiếu Quy chuẩn Thực thi (Layer 2)**  
> Áp dụng cho toàn bộ các tác vụ lập trình, chạy kiểm thử, và điều phối quy trình ngầm trên CCBA Platform.

---

## 1. Scoped Test Execution (Kiểm thử Cô lập)
- Nghiêm cấm kích hoạt các lệnh kiểm thử toàn diện (unscoped `pytest`) trên toàn bộ repository mà không chỉ định rõ phạm vi.
- Luôn chỉ định rõ file test hoặc module mục tiêu: ví dụ `pytest packages/{pkg}/tests/test_file.py` hoặc cờ loại trừ `-m "not slow and not stress"`.

---

## 2. Bounded Async Task, Zero-Polling & Reactive Wakeup Invariant
- Khi một lệnh chạy dưới dạng tác vụ ngầm (Background Task) như `run_harness_evals.py`, `pytest`, hoặc `gh pr checks`:
  - **Nguyên lý Reactive Wakeup (Thức dậy theo sự kiện):** Hệ thống tự động đánh thức và gửi thông báo cho Agent ngay khi tác vụ hoàn thành. Agent **NGHIÊM CẤM** tự tạo vòng lặp kín để thăm dò (`polling loop`) bằng `manage_task status`.
  - **Quy tắc kiểm tra tiến độ:**
    - Agent chỉ được gọi `manage_task status` tối đa **2 lần** để kiểm tra các tác vụ ngắn hạn (< 5 giây).
    - Nếu tác vụ vẫn ở trạng thái **RUNNING** sau 2 lần kiểm tra, Agent **BẮT BUỘC** dừng gọi tool (kết thúc lượt - End Turn) hoặc chuyển sang làm việc độc lập khác. Tuyệt đối không lặp polling liên tiếp làm ô nhiễm giao diện (UI noise), phình to context window và lãng phí token.
  - **Rào chắn lệnh theo dõi CI (`gh pr checks`):** Nghiêm cấm chạy `gh pr checks --watch` kết hợp lặp `manage_task status`. Thay vào đó, chạy `gh pr checks` đơn lẻ hoặc khởi chạy `--watch` rồi lập tức dừng lượt để hệ thống tự động trả về kết quả khi CI hoàn tất.
  - **Rào chắn Review Requests của Copilot (Chống Race Condition):** Nghiêm cấm kích hoạt `gh pr merge` khi `gh pr view --json reviewRequests` vẫn còn chứa bot reviewer (`copilot-pull-request-reviewer`). Phải đợi bot hoàn thành nộp bài review và đối soát toàn bộ comments trước khi merge.

---

## 3. TDD Retry Cap & Early Escalation (Giới Hạn Vòng Lặp & Điểm Cắt Lỗi)
- Trong vòng lặp Red→Green→Refactor (TDD) hoặc edit→test, Agent chỉ được lặp lại tối đa **5 vòng** cho cùng một seam hoặc test file.
- **Quy tắc Cắt Lỗi Sớm (Early Escalation tại vòng 3):**
  - Nếu sau **3 vòng test liên tiếp** vẫn không pass do lỗi logic sâu, race condition, hoặc xung đột đa file: Agent **bắt buộc dừng thử mù**, không được tiếp tục đoán mò cách sửa.
  - Agent phải lập tức đóng gói **Deep Problem Brief** (gồm: Triệu chứng lỗi, Giả thuyết đã thử nhưng sai, Các code seams liên quan, Log lỗi then chốt).
- **Hành động tại vòng 5 (Hard Stop):**
  - Nếu chạm mốc 5 vòng, Agent dừng ngay lập tức, commit Work-In-Progress (WIP), xuất Deep Problem Brief và kích hoạt **Boost Escalation Gate** (Mục 9) — tuyệt đối không lặp tiếp làm cạn kiệt ngân sách ngữ cảnh.

---

## 4. Anti-Duplicate Background Runner
- Nghiêm cấm Agent kích hoạt nhiều lệnh chạy ngầm (`run_command` async) cho cùng một script test runner hoặc harness evaluation.
- Mọi script test runner ngầm bắt buộc phải tích hợp Singleton Process Lock (`ensure_single_instance()`) và kiểm tra tiến trình cũ trước khi khởi động.

---

## 5. Safe Process Termination Invariant
- Khi viết hoặc thực thi bất kỳ logic nào có chức năng dọn dẹp hoặc duy trì đơn tiến trình (`ensure_single_instance()`), Agent **bắt buộc phải loại trừ** cả tiến trình hiện tại (`os.getpid()`) và tiến trình cha (`os.getppid()`).
- Nghiêm cấm kích hoạt `taskkill` hoặc `proc.terminate()` lên `os.getppid()` để tránh làm sập Agent Server Host.

---

## 6. Task Log Readiness Check
- Nghiêm cấm gọi `view_file` tới tệp `task-XXX.log` lập tức ngay sau lượt `run_command` async mà không kiểm tra xem tệp tin log đã thực sự được hệ thống tạo và ghi dữ liệu lên ổ đĩa hay chưa.
- Phải dùng `manage_task status` hoặc chờ thông báo hoàn tất từ hệ thống trước khi đọc log.

---

## 7. Invalid Args Circuit Breaker
- Khi gặp lỗi `model output error: invalid tool call error (invalid_args)` từ **2 lần liên tiếp trở lên**, đây là tín hiệu context budget sắp cạn kiệt.
- Agent phải **dừng ngay lập tức**, commit WIP nếu có thay đổi chưa lưu, tóm tắt trạng thái công việc hiện tại, và thông báo cho người dùng mở phiên mới để tiếp tục — không được cố gắng chạy thêm bất kỳ tool call nào.

---

## 8. 2-Tier Test Speed Compliance
- Mọi tệp kiểm thử đơn vị (Unit Test) mới viết bắt buộc phải chạy dưới 2.0 giây.
- Các tệp test tích hợp mạng, Chromium CDP, hoặc LLM latency nặng bắt buộc phải được dán decorator `@pytest.mark.slow` hoặc `@pytest.mark.stress` để tự động loại trừ khỏi vòng lặp kiểm thử nhanh hàng ngày (`-m "not slow"`).

---

## 9. Boost Deep Reasoning Protocol & Escalation Gate
- Khi xử lý các bài toán kỹ thuật có độ phức tạp cao vượt quá khả năng xử lý của vòng lặp đơn lẻ (Single-turn ReAct), Agent và Kỹ sư CCBA áp dụng quy chuẩn **Boost Deep Reasoning**:
  - **Trường hợp kích hoạt:**
    1. **Concurrency & Race Conditions:** Xung đột tiến trình nền, mutex lock (`TVPLSessionMutex`), pipeline đa tiến trình (VvC Second Brain daemons, IDOP staging sync).
    2. **Polyglot Monorepo Deep Refactoring:** Tái cấu trúc hoặc trích xuất Deep Seams qua nhiều package Python/TypeScript đồng thời.
    3. **Thẩm định Pháp lý & Xung đột Quy chuẩn Đa ngành:** Xử lý các điều khoản chồng chéo, xung đột ranh giới thẩm quyền (Luật 55/2024, NĐ 105/2025, QCVN 06, TCVN 3890).
    4. **Bế tắc TDD (Chạm ngưỡng 3–5 vòng test fail):** Khi TDD Retry Cap bị kích hoạt.
  - **Quy chuẩn Đóng Gói Deep Problem Brief:**
    Khi kích hoạt Escalation Gate, Agent phải tổng hợp tệp hoặc thông điệp chuẩn mực:
    ```markdown
    ### 🔬 Deep Problem Brief
    - **Vấn đề cốt lõi (Failure Manifest):** [Mô tả ngắn gọn lỗi kỹ thuật/test fail]
    - **Các giả thuyết đã kiểm chứng & Thất bại (Tested Hypotheses):** [Liệt kê 2-3 cách sửa đã thử và lý do fail]
    - **Vùng ảnh hưởng (Seams Involved):** [Danh sách files / classes / functions liên quan]
    - **Logs / Error Trace:** [Trích đoạn log lỗi then chốt]
    - **Khuyến nghị hành động:** [Đề xuất người dùng kích hoạt `/boost` kèm brief này để chạy chu trình suy luận đa tác nhân]
    ```
  - **Rào chắn An Toàn Đa Tác Nhân (Two-Layer Sub-Agent Guardrail — ADR 0035):**
    Khi quy trình CCBA tự động mô phỏng hoặc khởi tạo các subagents chạy ngầm theo mô hình 3 pha của Boost (Strategy $\rightarrow$ Parallel Workers $\rightarrow$ Synthesis):
    1. **Giới hạn Độ sâu (Depth Limit = 1):** Nghiêm cấm subagent spawn thêm subagent con để chống bùng nổ đệ quy.
    2. **Giới hạn Công cụ (Tool Scoping):** Subagents chỉ được cấp quyền công cụ đọc (`view_file`, `grep_search`, `read_resource`) và chạy kiểm thử cô lập (`run_command` scoped test), tuyệt đối không cấp quyền chỉnh sửa file hoặc lệnh Git nguy hiểm.
    3. **Giới hạn Số Lượng (Max Workers):** Tối đa 3 subagents chạy song song trong một phiên điều tra/nghiên cứu.

