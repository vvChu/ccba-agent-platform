# 🎫 Ticket WF-04: [AFK / Task] Đóng gói Tiện ích CLI `ccba-spoke` Hỗ trợ Kỹ sư Thao tác Staging và Đồng bộ

> **Thuộc bản đồ**: [🗺️ Bản đồ Định hướng IDOP Hub-Spoke Ecosystem](../idop_spoke_ecosystem_map.md)  
> **Loại ticket**: `AFK / Task`  
> **Trạng thái**: `CLOSED` (Đã hoàn thành)  
> **Module Source**: [`scripts/spoke/spoke_cli.py`](../../../scripts/spoke/spoke_cli.py)  
> **Entrypoint CLI**: `ccba-spoke`  
> **Assignee**: *AI Platform Engineering*

---

## 1. Bối cảnh & Mục tiêu

Sau khi [Ticket WF-01](wf_01_idop_submission_interface.md) chốt giao thức tương tác nộp hồ sơ, chúng ta cần đóng gói công cụ CLI tiện ích `ccba-spoke` (hoặc module lệnh trong package `ccba-core`) để Kỹ sư có thể:
1. `ccba-spoke sync`: Đồng bộ kỹ năng & workflows mới nhất từ Hub cục bộ vào Spoke hiện tại.
2. `ccba-spoke stage`: Đóng gói và lưu hồ sơ/báo cáo vào Local Staging Queue (`.md/idop_staged/`).
3. `ccba-spoke flush`: Kích hoạt `IDOPBridge` đẩy các bản ghi trong queue lên 58 SharePoint Lists IDOP của CCBA.
4. `ccba-spoke status`: Kiểm tra trạng thái kết nối tới AI Gateway Server Spark và IDOP M365.

---

## 2. Kết Quả Triển Khai

1. **Module CLI `scripts/spoke/spoke_cli.py`**:
   - Đã triển khai đầy đủ các lệnh: `status`, `sync`, `stage`, `submit`, `flush`.
   - Tích hợp **AI Pre-Submission Gate** (chặn văn bản pháp lý hết hiệu lực như NĐ 06/2021, kiểm tra tính toàn vẹn metadata dự án, mã dự án, email chủ sở hữu).
   - Tự động sinh biên nhận PGV JSON (`PGV-<timestamp>-<task_id>.json`) với trạng thái `STAGED_LOCAL` và mã băm SHA-256.
   - Cơ chế `flush` hỗ trợ **Idempotent Replay** chuyển trạng thái sang `SYNCED_SHAREPOINT`.
2. **Đăng ký Entry Point**: Đã đăng ký lệnh `ccba-spoke = "scripts.spoke.spoke_cli:main"` trong `pyproject.toml`.
3. **Kiểm Thử Toàn Diện**: `tests/test_spoke_cli.py` (5/5 tests PASSED) và `tests/test_cli_console_scripts.py` (3/3 tests PASSED).

---

## 3. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Triển khai mã nguồn CLI với các lệnh `sync`, `stage`, `flush`, `status`.
- [x] Viết unit tests kiểm thử các ca online/offline và idempotent replay.
- [x] Cập nhật kết quả vào mục *Decisions so far* trên Bản đồ Wayfinder.

