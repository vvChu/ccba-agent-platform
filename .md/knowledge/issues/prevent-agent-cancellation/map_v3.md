# Bản đồ Định hướng Wayfinder: Kiến trúc Chống Hủy Lượt Tự động (Anti-Cancellation Architecture)

> **Mã Bản đồ:** `WAYFINDER-003`  
> **Trạng thái:** Active  
> **Ngày khởi tạo:** 2026-08-12  

---

## 🎯 1. Điểm đích (Destination)

Xây dựng **Kiến trúc Chống Hủy Lượt Tự động (Anti-Cancellation Architecture)** tối ưu và bền vững nhất cho CCBA Agent Platform, triệt hạ hoàn toàn rủi ro bị Server Host dập ngắt (`User cancelled agent execution`) do cơ chế 25-30s Watchdog hoặc Server Host Restart.

---

## 📝 2. Ghi chú & Phân tích Nguyên nhân Gốc rễ (Root Cause Analysis)

- **Vì sao Watchdog 25-30s lại dập ngắt Agent?**
  - Khi Agent khởi chạy một lệnh qua `run_command`, nếu lệnh đó là tiến trình con trực tiếp (Direct Child Process) và lượt chạy của Agent (Agent Turn) kéo dài > 25s mà chưa `End Turn`, Server Host sẽ ngắt lượt và bắn tín hiệu `SIGINT / KeyboardInterrupt` diệt cả tiến trình con.
- **Triết lý giải pháp:** Không cố gắng kéo dài thời gian Watchdog của Server Host (vì là thiết lập cố định của IDE/Platform), mà **thay đổi mô thức tương tác**: đưa thời gian mỗi lượt của Agent về **< 2 giây** và tách rời hoàn toàn tiến trình chạy ngầm khỏi cây tiến trình của Agent.

---

## 💡 3. Bảng so sánh 3 Giải pháp Kỹ thuật Tối ưu

| Giải pháp Kỹ thuật | Cơ chế Hoạt động | Ưu điểm | Nhược điểm |
|---|---|---|---|
| **Phương án 1: Detached Process Runner (`safe_runner.py`)** | Sử dụng `CREATE_NEW_PROCESS_GROUP` (Windows) hoặc `start_new_session=True` để tách hẳn tiến trình chạy test ra khỏi cây tiến trình của Agent Host. | Tiến trình chạy ngầm **sống độc lập 100%**, kể cả khi Agent Host restart hay ngắt lượt. | Cần cơ chế đọc log/status từ đĩa khi tác vụ hoàn thành. |
| **Phương án 2: Async Schedule Polling (`schedule` tool)** | Agent bật task ngầm $\rightarrow$ Đặt timer `schedule(15s)` $\rightarrow$ **End Turn lập tức (< 2s)**. Khi timer nổ, Agent mới dậy kiểm tra `manage_task status`. | Lượt của Agent chỉ tốn < 2s $\rightarrow$ **100% miễn nhiễm với Watchdog 25s**. | Cần 2-3 lượt nhả lượt ngắn để hoàn thành tác vụ dài. |
| **Phương án 3: Micro-Batching Execution** | Chia nhỏ tập 22 test files thành 4 đợt (mỗi đợt 5 files, chạy < 5s/đợt). | Mỗi đợt chạy cực nhanh, dễ kiểm soát traceback rủi ro. | Tổng thời gian chạy lâu hơn do tốn 4 lần startup overhead. |

---

## 🚧 4. Ticket ở Biên giới (Frontier - Unblocked Tickets)

### 🎫 Ticket 1: Nâng cấp `safe_runner.py` hỗ trợ Process Detachment Tuyệt đối
- **Phân loại:** `Task` [AFK]
- **Mục tiêu:** Bổ sung `creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP` trong `safe_runner.py` trên Windows để tiến trình test hoàn toàn tách biệt khỏi Agent Host process tree.

### 🎫 Ticket 2: Chuẩn hóa Quy trình Async Task Polling (`schedule` + `End Turn`)
- **Phân loại:** `Research & Workflow` [AFK]
- **Mục tiêu:** Đưa quy tắc "Khởi chạy task $\rightarrow$ Đặt `schedule(15s)` $\rightarrow$ End Turn ngay lập tức" vào `AGENTS.md` §4 và các workflow `ccba-implement`, `ccba-run-qc-pipeline`.

### 🎫 Ticket 3: Tự động hóa Micro-Batching trong `run_isolated_tests.py`
- **Phân loại:** `Task` [AFK]
- **Mục tiêu:** Thêm tham số `--batch-size 5` vào `run_isolated_tests.py` để chia nhỏ tập test suite lớn thành các chunk chạy < 5 giây mỗi đợt.

---

## 🌫️ 5. Sương mù chiến trận (Not yet specified)

- **[Auto-resuming State Manager]:** Tự động khôi phục vị trí test đang chạy dở nếu máy tính người dùng bị sập nguồn đột ngột.
