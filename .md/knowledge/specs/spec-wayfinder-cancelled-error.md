# Spec: Khắc Phục Triệt Để Lỗi "User cancelled agent execution" & Đảm Bảo Tính Ổn Định AI Agent

## Problem Statement

Kỹ sư phần mềm và AI Agent khi thực hiện các quy trình tự động hóa phức tạp (như `/ccba-implement`, chạy bộ thử nghiệm pytest toàn diện, hoặc các tác vụ batch AI Gateway) thường xuyên gặp lỗi ngắt ngầm với thông báo misleading `"User cancelled agent execution"` mặc dù người dùng **không hề bấm hủy**.

Qua phân tích log kỹ thuật (forensic analysis), nguyên nhân được xác định đến từ hai trục:
1. **⚡ Server Daemon Restart**: Server AI Gateway/Spark bị ngắt kết nối micro-restart ngắn (1-2s) hoặc daemon bị restart làm ngắt các background process đang chờ kết quả.
2. **🧠 Context Budget / Turn Limit Exhaustion**: Vòng lặp sửa code - thử nghiệm (`edit -> test -> edit -> test`) kéo dài liên tục trên 15-20 lượt làm bùng nổ dung lượng ngữ cảnh token, dẫn đến lỗi cú pháp tool call `invalid_args` làm hệ thống tự động terminate phiên làm việc.

---

## Solution

Hệ thống triển khai một cơ chế phòng vệ 3 lớp (3-Tier Resilience Architecture):
1. **Detached Execution Layer**: Sử dụng bộ chạy cô lập `safe_runner.py` để tách tiến trình kiểm thử khỏi vòng đời trực tiếp của Client Daemon, đảm bảo kết quả kiểm thử không bị hủy chớp nhoáng khi daemon gặp sự cố micro-restart.
2. **Gateway Fault Tolerance**: Tích hợp cơ chế tự động thử lại với thời gian chờ tăng theo cấp số nhân (Exponential Backoff Retry) và chốt ngắt mạch (Circuit Breaker) trong lớp SDK kết nối AI Gateway (`ccba-ai`), giúp các cuộc gọi LLM tự hồi phục sau các đợt gián đoạn mạng ngắn hạn.
3. **Workflow & Context Guardrails**: Áp dụng quy tắc quản trị cấp cao tại Hiến pháp `AGENTS.md` bao gồm giới hạn số vòng lặp TDD (TDD Retry Cap = 5) và cơ chế ngắt sớm khẩn cấp (Invalid Args Circuit Breaker) để bảo toàn ngân sách ngữ cảnh và đưa ra thông báo bàn giao (handoff) chủ động trước khi bị crash.

---

## User Stories

1. As an **AI Agent Engineer**, I want pytest execution to run in a detached process wrapper, so that transient server daemon restarts do not kill active test runs or report false cancellation errors.
2. As a **Developer**, I want the `ccba-ai` SDK to automatically retry failed LLM API requests on transient 5xx or connection errors, so that temporary network glitches do not fail long-running batch operations.
3. As a **Platform Administrator**, I want a Circuit Breaker mechanism in the AI Gateway SDK, so that persistent backend outages trigger an immediate structured failure response instead of hanging background threads.
4. As an **AI Coding Agent**, I want a hard cap of 5 edit-test iterations per seam, so that I do not exhaust the context window and get terminated unexpectedly.
5. As a **User**, I want the agent to save Work-In-Progress (WIP) commits and request a new session when encountering repeated tool-call errors, so that my work is never lost to silent context crashes.
6. As a **Quality Engineer**, I want fast, scoped test execution by default, so that individual unit changes can be verified quickly without clogging the context log with full-suite test outputs.
7. As a **System Operator**, I want structured JSON error diagnostic logs on stderr when circuit breakers trip, so that self-healing debuggers can parse and act on the failure cause.

---

## Implementation Decisions

### 1. Detached Process Execution Architecture
- Triển khai bộ chạy kịch bản độc lập có khả năng chạy nền detached khỏi phiên chính của Agent.
- Bộ chạy cung cấp interface dòng lệnh hỗ trợ kích hoạt tác vụ (`--command`), kiểm tra trạng thái (`--status`), và xuất log kết quả theo định dạng JSON.
- Đảm bảo mã thoát (exit code) và stdout/stderr được bảo lưu nguyên vẹn vào tệp log để Agent chính truy vấn an toàn sau khi tác vụ kết thúc.

### 2. AI Gateway SDK Resilience (`ccba-ai`)
- Nâng cấp `AIClient` và `AsyncAIClient` để bọc tất cả các thao tác tương tác API (`chat`, `chat_multi`, `stream`, `transcribe`) qua một lớp Retry Logic.
- Tự động bắt các ngoại lệ lỗi kết nối mạng (Connection Error, Timeout, HTTP 502/503/504).
- Cấu hình thử lại tối đa 3 lần với khoảng thời gian delay tăng lũy thừa (1s -> 2s -> 4s).
- Tích hợp mô hình Circuit Breaker 3 trạng thái (`CLOSED`, `OPEN`, `HALF_OPEN`) với ngưỡng lỗi liên tiếp và thời gian hồi phục để chặn cascade failure.

### 3. Core Policy & Workflow Guardrails
- Cập nhật quy tắc bắt buộc tại `AGENTS.md` (Layer 1 Constitution):
  - **TDD Retry Cap**: Bắt buộc dừng lặp sau tối đa 5 vòng cho cùng một seam; lưu WIP commit và xin chỉ thị người dùng.
  - **Scoped Test Execution**: Cấm kích hoạt `pytest` toàn bộ kho mã nguồn mà không chỉ định rõ tệp test mục tiêu trừ khi chạy chốt qua detached runner.
  - **Invalid Args Circuit Breaker**: Phát hiện lỗi cú pháp gọi tool `invalid_args` ≥ 2 lần liên tiếp là tín hiệu cạn token; ép buộc ngắt phiên an toàn lập tức.

---

## Testing Decisions

### Test Seams
1. **SDK Seam**: Interface phương thức public của `AIClient` và `AsyncAIClient` trong package `ccba-ai`. Kiểm thử khả năng retry khi mock các phản hồi lỗi từ server OpenAI/LiteLLM.
2. **Runner Seam**: Interface CLI của `safe_runner.py`. Kiểm thử việc chạy lệnh thành công, thất bại, và ghi log trạng thái ra đĩa đệm.
3. **Policy Seam**: Các bộ linter và validator tài liệu (`validate_skills.py`, `validate_docs.py`) kiểm tra tính tuân thủ của các quy tắc trong `AGENTS.md` và `SKILL.md`.

### Prior Art
- Tham chiếu mô hình Circuit Breaker từ `resources/circuit_breaker.py` (VvC Wiki Health v7.4).
- Tham chiếu quy trình test TDD trong `skills/tdd/SKILL.md`.

---

## Out of Scope

- Can thiệp trực tiếp vào mã nguồn hạ tầng Antigravity Client UI (phần mềm client VS Code bên ngoài) để sửa hiển thị chuỗi ký tự `"User cancelled agent execution"`.
- Thay đổi cấu hình phần cứng hoặc restart policy của Server Spark Gateway (100.83.192.30).

---

## Further Notes

- Kế hoạch triển khai mã nguồn cụ thể cho Ticket 3 đã được lập sẵn tại [implementation_plan.md](file:///C:/Users/chuvu/.gemini/antigravity/brain/37699796-52bb-464f-be93-af5d82403d41/implementation_plan.md).
- Tài liệu Đặc tả Kỹ thuật này được duy trì công khai tại `.md/knowledge/specs/spec-wayfinder-cancelled-error.md` để phục vụ đối soát và phân rã ticket trong các chu trình phát triển tiếp theo.
