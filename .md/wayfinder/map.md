# Bản đồ Định hướng Wayfinder: Tối ưu hóa Test Suite & Khắc phục Lỗi Exec Cancelled

> **Mã Bản đồ:** `WAYFINDER-001`  
> **Trạng thái:** Active  
> **Ngày khởi tạo:** 2026-08-11  

---

## 🎯 1. Điểm đích (Destination)

Xây dựng hệ thống thực thi kiểm thử (Test Execution) và lập trình đại lý (Agent Execution) hoàn toàn ổn định, không bị treo (hang) hay bị ngắt lời (`User cancelled agent execution`):
- Toàn bộ 22 file test trong `ccba-legal-intel` tương thích hoàn toàn với cấu trúc `src/` layout (`src/ccba_legal/`), chạy cô lập với thời gian phản hồi < 3s/file.
- Loại bỏ triệt để các rủi ro làm ngắt phiên Agent (unscoped `pytest`, interactive stdin, unhandled timeout).
- Dọn dẹp và commit sạch sẽ các thay đổi refactoring lên Git repository.

---

## 📝 2. Ghi chú (Notes)

- **Nguyên tắc KISS:** Ưu tiên script đơn giản trong `.md/scripts/` thay vì cấu hình phức tạp.
- **Rào chắn `AGENTS.md`:** Nghiêm cấm chạy `pytest` không chỉ định file (`unscoped pytest`). Mọi lượt chạy test phải đi qua `.md/scripts/run_isolated_tests.py` hoặc chỉ định đích danh tệp test.
- **Process Guard:** Mọi script test runner phải tự động dọn dẹp `.lock` file và loại trừ `os.getpid()` / `os.getppid()` để không gây ngắt tiến trình Agent host.

---

## ✅ 3. Quyết định đã chốt (Decisions so far)

1. **[Refactor `ccba-legal-intel` sang `src-layout`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/src)**
   - *Tóm tắt:* Đã di chuyển toàn bộ code nghiệp vụ từ root package `ccba_legal/` vào `src/ccba_legal/` và xóa bỏ `secret_credential.*`.
2. **[Tạo Script Isolated Test Runner](file:///d:/GitHubProjects/ccba-agent-platform/.md/scripts/run_isolated_tests.py)**
   - *Tóm tắt:* Đã tạo `.md/scripts/run_isolated_tests.py` giúp chạy từng file test độc lập với timeout 5 giây, xuất báo cáo benchmark Markdown tự động.

---

## 🚧 4. Ticket ở Biên giới (Frontier - Unblocked Tickets)

### 🎫 Ticket 1: [Kiểm chứng & Sửa lỗi 23 Test Files theo `src-layout`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/tests)
- **Phân loại:** `Task` [AFK]
- **Assignee:** `Agentic AI`
- **Mục tiêu:** Chạy runner cô lập `.md/scripts/run_isolated_tests.py`, xác định các test case bị lỗi import path hoặc timeout, sửa triệt để để 100% test file đạt trạng thái `PASSED`.
- **Trạng thái:** 🟡 In Progress (Đang thực thi runner cô lập)

### 🎫 Ticket 2: [Cấu hình `pyproject.toml` & Dọn dẹp Git Workspace](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-legal-intel/pyproject.toml)
- **Phân loại:** `Task` [AFK]
- **Assignee:** `Agentic AI`
- **Mục tiêu:** Đảm bảo `pyproject.toml` chỉ định `where = ["src"]`, bổ sung `.gitignore` cho các tệp credential rác, stage và commit các thay đổi refactoring hợp lệ.
- **Trạng thái:** 🟢 Ready to Execute

### 🎫 Ticket 3: [Cài đặt Safety Guardrails chống Timeout cho Agent Execution](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/git-guardrails)
- **Phân loại:** `Research/Task` [AFK]
- **Assignee:** `Agentic AI`
- **Mục tiêu:** Đảm bảo các lệnh CLI chạy qua `run_command` luôn có cờ `PAGER=cat` và thời gian `WaitMsBeforeAsync` hợp lý, không để lộ interactive prompt gây cancel phiên làm việc.
- **Trạng thái:** 🟢 Ready to Execute

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- **[Tự động hóa pre-commit hook cho `ccba-legal-intel` src-layout]:** Cần xác định xem pre-commit config hiện tại (`.pre-commit-config.yaml`) có cần điều chỉnh path khi format `src/` hay không.

---

## 🚫 6. Ngoài phạm vi (Out of scope)

- **Thay đổi logic nghiệp vụ RAG / Crawler:** Không sửa đổi logic tính toán RAG hoặc parser trừ khi test fail do việc thay đổi đường dẫn import `src/`.
