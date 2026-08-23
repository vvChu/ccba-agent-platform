# Wayfinder Navigation Map: Tự động hóa Khuyến nghị Vận hành & An Toàn Test Execution

**Mã vấn đề**: `issue-automated-operational-guardrails`
**Trạng thái bản đồ**: 🟢 **Đã hoàn thành** — Đã triển khai và kiểm thử thành công toàn bộ guardrails
**Khởi tạo**: 2026-07-24

---

## 🎯 Điểm đích (Destination)

Tự động hóa 100% việc thực thi kiểm thử an toàn (Scoped pytest + Detached process qua `safe_runner.py`) trong toàn bộ CCBA Agent Platform. Loại bỏ hoàn toàn sự phụ thuộc vào trí nhớ thủ công của người dùng hoặc Agent, ngăn chặn triệt để lỗi "User cancelled agent execution" do lặp test unscoped hoặc server restart.

---

## 📝 Ghi chú (Notes)

- **KISS (Keep It Simple, Stupid)**: Mã nguồn của hook và wrapper script không vượt quá 50-80 dòng, dễ duy trì.
- **Không phá vỡ DX (Developer Experience)**: Đảm bảo khi developer chạy pytest thủ công từ terminal vẫn giữ trải nghiệm mượt mà, chỉ chặn/cảnh báo khi chạy unscoped không mong muốn.
- **Tham chiếu theo tên**: Mọi trao đổi bắt buộc dùng tên ticket kèm link file Markdown tương ứng.

---

## 📋 Quyết định đã chốt (Decisions so far)

1. **[Thống nhất Kiến trúc Tự động hóa 4 Tầng](file:///d:/GitHubProjects/ccba-agent-platform/.md/knowledge/issues/automated-operational-guardrails/map.md#thống-nhất-kiến-trúc-tự-động-hóa-4-tầng)** — Kết hợp Constitutional Guardrails (Layer 1) + Workflow Rules + Pytest Hook (`conftest.py`) + Safe Wrapper CLI (`safe_pytest.py`).
2. **[Kế thừa Nền tảng Detached Runner](file:///d:/GitHubProjects/ccba-agent-platform/scripts/safe_runner.py)** — Tái sử dụng `safe_runner.py` (151 LOC) đã được chứng minh độ ổn định trong `issue-wayfinder-cancelled-execution`.

---

## 🚩 Frontier Tickets (Các ticket unblocked ở biên giới)

### Ticket 1: Triển khai Pytest Pre-Execution Enforcement Hook (`conftest.py`)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked (Sẵn sàng thực thi)
- **Mục tiêu**: Tạo `conftest.py` tại gốc dự án để kiểm tra và chặn các câu lệnh `pytest` unscoped (không truyền file test cụ thể), hiển thị hướng dẫn truyền target file rõ ràng.

### Ticket 2: Xây dựng Auto-Wrapper CLI Script (`scripts/safe_pytest.py`)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked (Sẵn sàng thực thi)
- **Mục tiêu**: Xây dựng `scripts/safe_pytest.py` hỗ trợ 2 tính năng:
  1. Tự động đọc `git status` để gợi ý/gán file test cho các file vừa sửa đổi.
  2. Tự động bọc câu lệnh chạy dưới dạng detached process qua `safe_runner.py`.

### Ticket 3: Đồng bộ hóa Mẫu lệnh trong Core Skills & Workflows
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by Ticket 1, Ticket 2
- **Mục tiêu**: Cập nhật tài liệu và câu lệnh mẫu trong các kỹ năng `eval-gate`, `implement`, `tdd` để mặc định sử dụng `safe_pytest.py`.

### Ticket 4: Kiểm thử Tự động hóa (Validation & Stress-Test)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by Ticket 1, Ticket 2, Ticket 3
- **Mục tiêu**: Giả lập các kịch bản chạy test (unscoped vs scoped, detached vs standard) để xác nhận 100% rào chắn tự động hoạt động chính xác.

---

## 🌫️ Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- **Tự động khôi phục test khi Daemon Restart**: Có nên tự động đăng ký Cron/Daemon watch để resume test khi daemon khởi động lại? (Cần đánh giá sau khi hoàn thành Ticket 1-3).

---

## 🚫 Ngoài phạm vi (Out of scope)

- Chỉnh sửa trực tiếp lõi của trình quản lý Antigravity Daemon/LiteLLM.
- Can thiệp vào hệ thống CI/CD bên ngoài ngoại trừ các script nội bộ của CCBA Platform.

---

*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
