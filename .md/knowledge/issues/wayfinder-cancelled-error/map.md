# Wayfinder Navigation Map: Khắc phục lỗi "User cancelled agent execution" liên tục

**Mã vấn đề**: `issue-wayfinder-cancelled-execution`
**Trạng thái bản đồ**: 🗺️ Đang lập (Charting)

---

## 🎯 Điểm đích (Destination)
Hệ thống CCBA Agent Platform chạy ổn định toàn bộ các tác vụ nặng (Evaluations, Pytest suite, TVPL Crawler) trên môi trường cục bộ và kết nối vững chắc với Spark Server mà không bị ngắt kết nối nửa chừng do timeout, quá tải luồng, hay restart server đột ngột.

---

## 📝 Ghi chú (Notes)
- **KISS**: Không thêm các thư viện phức tạp nếu cấu hình timeout đơn giản có thể giải quyết được.
- **Tránh Parallel Run**: Khi phát hiện lỗi quá tải, ép chạy tuần tự các test case.
- **Lưu ý gỡ lỗi**: Đọc trực tiếp file `transcript.jsonl` khi có lỗi xảy ra để định vị tool call cuối cùng trước khi bị ngắt.

---

## 📋 Quyết định đã chốt (Decisions so far)
1. **Phân tích Log Lịch sử & Bằng chứng thực tế**:
   - Xác nhận qua thông báo Daemon: `[Notice] All your subagents and background tasks have been stopped due to server restart.`
   - Minh chứng ảnh chụp: Lệnh `pwsh -Command ".venv\Scripts\pytest packages/ccba-legal-intel/tests/ -v"` bị Cancelled trực tiếp do Server Daemon restart trong khi task đang chạy.

---

## 🛡️ Phương án Cô lập Triệt để (Isolation Strategy)

Để ngăn chặn lỗi này tái diễn, chúng ta áp dụng **Cơ chế Cô lập 3 Lớp (3-Tier Isolation Protocol)**:
1. **Lớp 1: Process Detaching (Cô lập Tiến trình)** — Không chạy lệnh dài hạn trực tiếp từ `run_command` terminal của Antigravity. Chạy script đệm nhả file log (`Start-Process` hoặc redirect `Out-File`) để tiến trình chạy độc lập với vòng đời của Agent Daemon.
2. **Lớp 2: Granular Test Slicing (Chia nhỏ Lượt chạy)** — Phân rã bộ test suite 53+ cases thành từng file đơn lẻ với độ dài < 10 giây/lượt, ngăn chặn quá tải RAM/CPU gây crash máy chủ Spark hoặc Daemon.
3. **Lớp 3: SDK Circuit Breaker** — Bổ sung retry loop trong package `ccba-ai` để nuốt lỗi gián đoạn mạng ngắt kết nối ngắn hạn.

---

## 🚩 Frontier Tickets (Các ticket unblocked ở biên giới)

### [Ticket 1: Thiết lập Script Runner Cô lập (Detached Process Runner)](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/wayfinder-cancelled-error/map.md#ticket-1)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**: Viết script `scripts/safe_runner.py` (hoặc PowerShell wrapper) giúp thực thi các lệnh pytest/evals ngầm, ghi log độc lập vào `.md/scratch/` và nhả quyền kiểm soát lập tức để Agent không bị dính vệt cancel khi Daemon restart.

### [Ticket 2: Phân rã & Chạy thử nghiệm Test Suite theo lát cắt dọc](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/wayfinder-cancelled-error/map.md#ticket-2)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**: Thực thi chạy kiểm thử từng file test đơn lẻ trong `packages/ccba-legal-intel/tests/` qua `safe_runner.py`, xác nhận 100% test cases pass mà không sinh ra lỗi "User cancelled".

### [Ticket 3: Bổ sung Circuit Breaker & Exponential Retry vào `ccba-ai`](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/wayfinder-cancelled-error/map.md#ticket-3)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**: Tích hợp decorator `tenacity` với retry 3 lần cho `ai.chat()` trong SDK `ccba-ai` để chịu đựng các đợt micro-restart 1-2 giây của Gateway Server Spark (:8090).

---

## 🌫️ Chưa xác định rõ (Not yet specified)
- *Ticket 4 (Tùy chọn)*: Tự động hóa việc dọn dẹp các background process treo (zombie processes) bằng pre-exec hook trước khi chạy test đợt mới.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
