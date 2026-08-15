# 🗺️ Wayfinding Map: Nâng Cấp & Hợp Nhất Bộ Công Cụ Tương Tác Spoke Toàn Diện (Spoke Tooling Suite Upgrade)

> **Mã định danh:** `wayfinder:spoke_tooling_suite_upgrade`  
> **Trạng thái:** `Active & Frontier Open`  
> **Ngày khởi tạo:** 2026-08-15  
> **Phạm vi tác động:** `scripts/spoke/`, `scripts/sync_spoke.py`, `scripts/adopt_spoke.py`, `scripts/ccba_platform_cli.py`, `/ccba-init-spoke`, `/ccba-update-spoke`, `/ccba-platform`

---

## 🎯 1. Điểm Đích (Destination)

Xây dựng bộ công cụ tương tác Hub ↔ Spoke đạt chuẩn công nghiệp, an toàn tuyệt đối, thống nhất 1 động cơ (Single Engine SSOT) và hỗ trợ quản trị đa dự án:
1. **An Toàn Không Phá Hủy & Chế Độ Xem Trước (Non-Destructive & Dry-Run Sync):** Nâng cấp `SpokeSynchronizer` để bảo toàn 100% các workflows/skills do Spoke tự viết nội bộ (không wipe thư mục), đồng thời hỗ trợ cờ `--dry-run` hiển thị báo cáo sai khác (Diff) chi tiết trước khi ghi file.
2. **Thống Nhất Cơ Chế Khởi Tạo & Đồng Bộ (Unified Core Engine):** Tái cấu trúc workflow `/ccba-init-spoke` sử dụng trực tiếp Deep Seam `SpokeSynchronizer` (thay cho script PowerShell copy thủ công), đảm bảo 100% Spoke mới được đăng ký mã hóa RSA vào Hub Registry ngay từ bước khởi tạo.
3. **Điều Phối Hàng Loạt & Giám Sát Trạng Thái (Multi-Spoke Batch Sync & Health Dashboard):** Bổ sung tính năng `sync-all` từ Hub (cập nhật đồng loạt các Spoke trong registry) và hiển thị bảng điều khiển trạng thái (Spoke Health / Drift Check) trực tiếp trong `/ccba-platform`.

---

## 📝 2. Ghi Chú & Rào Chắn (Notes & Guardrails)

* **Hiến pháp Hub-Spoke (ADR 0036 & ADR 0037):** Tuyệt đối không xóa đè hoặc phá hủy cấu hình tùy biến của Spoke.
* **Reuse-First Gate (P7.1):** Tái sử dụng và mở rộng các Deep Modules tại `scripts/spoke/` (`spoke_synchronizer.py`, `spoke_adopter.py`, `decrypt_spoke_registry.py`) thay vì viết các script rời rạc.
* **KISS Principle:** Ưu tiên giải pháp tinh gọn, rõ ràng, không tạo thêm các lớp trừu tượng thừa thãi.
* **Kỷ Luật Kiểm Thử (TDD):** Mọi tính năng mới (dry-run, selective merge, batch sync) đều phải có unit test tự động với thời gian chạy dưới 2.0s.

---

## ⚖️ 3. Quyết Định Đã Chốt (Decisions So Far)

* **[D01: Kiến Trúc Spoke Registry Mã Hóa RSA Asymmetric]:** Đã triển khai lưu trữ an toàn danh sách Spoke tại `.md/data/spoke_registry.yaml` sử dụng khóa công khai RSA 2048-bit (`registry_public_key.pem`) và giải mã bởi `decrypt_spoke_registry.py`.
* **[D02: Chuẩn Tiếp Nhận Spoke Hiện Hữu An Toàn (ADR 0036)]:** `spoke_adopter.py` đóng vai trò là mẫu chuẩn mực về khả năng tự động sao lưu (`.bak`), merge schema không phá hủy và hỗ trợ `--dry-run`.
* **[D03: Phân Định Rõ Vai Trò 3 Lệnh Vòng Đời Spoke]:**
  * `/ccba-init-spoke`: Dành riêng cho thư mục MỚI TINH (Greenfield).
  * `/ccba-adopt-spoke`: Dành riêng cho dự án ĐÃ CÓ CODE (Brownfield).
* **[D04: Cơ Chế Non-Destructive Selective Merge & Dry-Run Preview]:** Đã triển khai và kiểm chứng qua TDD (`tests/test_spoke_synchronizer.py` 4/4 passed). Động cơ `SpokeSynchronizer` bảo toàn 100% các workflow nội bộ riêng của Spoke (không wipe thư mục), phân loại chi tiết trạng thái (`NEW`, `UPDATED`, `UNCHANGED`, `PRESERVED`) và xuất báo cáo mô phỏng trực quan khi chạy với cờ `--dry-run`.
* **[D05: Thống Nhất Động Cơ Khởi Tạo Greenfield (Single Engine SSOT)]:** Đã tái cấu trúc Bước 5 trong `.agents/workflows/ccba-init-spoke.md` sử dụng trực tiếp `python "$hub\scripts\sync_spoke.py" --spoke .`, loại bỏ hoàn toàn các đoạn script copy PowerShell thủ công lỗi thời và tự động đăng ký RSA vào Hub Registry (`tests/test_init_spoke_integration.py` 2/2 passed).
* **[D06: Multi-Spoke Batch Sync Engine & Spoke Health Dashboard]:** Đã triển khai `sync_all_spokes()` và `display_spoke_health_dashboard()`, tích hợp tham số `--all` cho `sync_spoke.py` và subcommand `spoke-status` vào `ccba-platform` CLI (`tests/test_spoke_batch_sync.py` 3/3 passed).

---

## 🧭 4. Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

* **Toàn bộ 3/3 Ticket tại Biên giới đã hoàn thành 100%!**

### 🎫 Ticket 1: [Design/TDD] Nâng Cấp `SpokeSynchronizer` với `--dry-run` và Selective Workflow Merge
* **Mã:** `TICKET-SPOKE-01`
* **Loại:** `Task [AFK]`
* **Trạng thái:** `COMPLETED` ✅ (Đã triển khai tại `scripts/spoke/spoke_synchronizer.py` và `scripts/sync_spoke.py`, test suite 4/4 passed)

### 🎫 Ticket 2: [Task] Tái Cấu Trúc `/ccba-init-spoke` Thống Nhất Gọi `SpokeSynchronizer`
* **Mã:** `TICKET-SPOKE-02`
* **Loại:** `Task [AFK]`
* **Trạng thái:** `COMPLETED` ✅ (Đã cập nhật `.agents/workflows/ccba-init-spoke.md` và kiểm thử tích hợp qua `tests/test_init_spoke_integration.py` 2/2 passed)

### 🎫 Ticket 3: [Design/TDD] Xây Dựng Tính Năng Multi-Spoke Batch Sync (`--all`) & Health Dashboard
* **Mã:** `TICKET-SPOKE-03`
* **Loại:** `Task [AFK]`
* **Trạng thái:** `COMPLETED` ✅ (Đã triển khai trong `spoke_synchronizer.py`, `sync_spoke.py`, `ccba_platform_cli.py` và test suite `test_spoke_batch_sync.py` 3/3 passed)

---

## 🏁 5. Kết Luận Bản Đồ Wayfinder (Mission Accomplished)

Bản đồ định hướng `wayfinder:spoke_tooling_suite_upgrade` đã hoàn thành **100% mục tiêu** đề ra:
1. Đã thống nhất toàn bộ quy trình khởi tạo/tiếp nhận/cập nhật Spoke về chung 1 động cơ Deep Seam `SpokeSynchronizer` và `spoke_adopter.py`.
2. Bảo vệ an toàn tuyệt đối dữ liệu và workflow nội bộ của Spoke (Non-destructive selective merge).
3. Cung cấp bộ công cụ điều phối hàng loạt `python scripts/sync_spoke.py --all [--dry-run]` và bảng giám sát `ccba-platform spoke-status`.

---

## 🌫️ 5. Sương Mù Chiến Trận / Chưa Xác Định Rõ (Not Yet Specified)

* **[FOG-01: Auto-Detect & Prompt for Python Shared Package SDKs]:** Khi Spoke là dự án Python/Phần mềm, làm thế nào để `sync_spoke` tự động phát hiện xem Spoke đã cài đặt các package dùng chung (`ccba-ai`, `ccba-ooxml`) ở chế độ editable (`pip install -e`) hay chưa để đưa ra cảnh báo thân thiện mà không gây chậm tiến trình sync? Sẽ được giải tỏa sau khi hoàn thành `TICKET-SPOKE-01`.

---

## 🚫 6. Ngoài Phạm Vi (Out of Scope)

* **Tự động `git commit` hoặc `git push` trong Spoke:** Việc commit/push mã nguồn tại Spoke phải do Kỹ sư hoặc Agent tại Spoke quyết định, Hub Sync Engine không can thiệp vào Git history của Spoke.
* **Xóa tệp tin mã nguồn nghiệp vụ của Spoke:** Không xóa bất kỳ tệp tin nào ngoài các tệp do chính Platform quản lý.
