# Bản Đồ Định Hướng (Wayfinder Map): Ổn Định Hệ Thống & Chống Nghẽn Tiến Trình Ngầm

## 🎯 1. Điểm đích (Destination)
Nền tảng CCBA Agent Platform tự động duy trì sự ổn định tuyệt đối (Zero Crashes / Zero Duplicate Process Overload) khi khởi chạy các tác vụ kiểm thử (CI Gates) và lệnh tự động. Loại bỏ hoàn toàn tình trạng Agent bị restart hoặc rơi vào trạng thái `User cancelled agent execution` do cạn kiệt tài nguyên CPU/RAM hoặc treo tiến trình ngầm.

---

## 📝 2. Ghi chú (Notes)
- Kế thừa trực tiếp bộ công cụ kiểm định sẵn có: `scripts/run_harness_evals.py`, `scripts/session_cleanup.py`.
- Áp dụng chiến lược "Phòng thủ 2 lớp": Lớp Mã nguồn (Process Lock) + Lớp Hiến pháp (Execution Guardrails trong AGENTS.md).

---

## 🟢 3. Quyết định đã chốt (Decisions so far)
- [x] **[Thêm Singleton Lock vào run_harness_evals.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/run_harness_evals.py#L12-L46)**: Đã tích hợp hàm `ensure_single_instance()` tự động phát hiện và thu hồi (terminate) tiến trình trùng lặp/treo từ trước qua `psutil` hoặc `wmic`.
- [x] **[Sửa Zombie Cleanup trong session_cleanup.py](file:///d:/GitHubProjects/ccba-agent-platform/scripts/session_cleanup.py#L17)**: Đã bổ sung import `time` và hoàn thiện hàm `clean_zombies()` thu hồi tiến trình mồ côi > 15 phút.
- [x] **[Cưỡng chế Mặc định Scoped Evaluation](file:///d:/GitHubProjects/ccba-agent-platform/scripts/run_harness_evals.py#L73)**: Đã thiết lập mặc định chạy theo git diff (file bị sửa đổi) để tối ưu hiệu suất, tránh ngốn 100% CPU.
- [x] **[Tự động hóa Pre-Eval Process Health Check](file:///d:/GitHubProjects/ccba-agent-platform/scripts/run_harness_evals.py#L12-L26)**: Kiểm tra dung lượng đĩa trống (< 2GB sẽ đưa ra cảnh báo) trước khi khởi chạy CI Gates.
- [x] **[Cập nhật Hiến pháp AGENTS.md & Workflows Standard](file:///d:/GitHubProjects/ccba-agent-platform/.agents/AGENTS.md#L61)**: Đã đóng gói quy tắc Anti-Duplicate Background Runner vào `AGENTS.md` và `eval-gate/SKILL.md`.

---

## 🚀 4. Ticket Biên giới (Frontier - Open Tickets)
- Không có — Tất cả các ticket trong bản đồ định hướng đã hoàn thành xuất sắc!

---

## 🌫️ 5. Chưa xác định rõ (Not yet specified)
- Cơ chế tự khôi phục trạng thái làm việc (Auto-Resume state) khi Extension Host của IDE bị đứt kết nối mạng đột ngột.

---

## ⛔ 6. Ngoài phạm vi (Out of scope)
- Thay đổi core engine hoặc IPC protocol của VS Code IDE (nằm ngoài quyền hạn repository).
