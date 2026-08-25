---
description: Workflow quản trị toàn diện vòng đời quyết định kiến trúc ADR
disable-model-invocation: true
bundle: _governance
command: /ccba-adr-lifecycle
triggers:
- ccba-adr-lifecycle
- tao adr
- cap nhat adr
- adr sync
- adr lifecycle
---
# Workflow: Quản Trị Vòng Đời Quyết Định Kiến Trúc (/ccba-adr-lifecycle)

> **Mô tả:** Workflow tự động hóa quản lý vòng đời ADR: Khởi tạo file mới theo chuẩn YAML Frontmatter -> Lan truyền trạng thái thay thế (Cascading Supersedes) -> Tự động tái biên dịch bảng mục lục `README.md` và Ma trận Quan hệ Kỹ năng `TRACEABILITY_MATRIX.md` -> Chạy cổng kiểm định chống lệch pha CI.

---

## 🚀 Các Bước Thực Hiện Của Agent

### 1. Xác Định Hành Động Cần Thực Hiện
Agent lắng nghe yêu cầu của người dùng để chọn 1 trong 3 nhánh xử lý:
- **Nhánh A (Tạo ADR mới):** Người dùng muốn ghi nhận quyết định kiến trúc mới.
- **Nhánh B (Cập nhật / Thay thế ADR cũ):** Người dùng muốn điều chỉnh trạng thái (ACCEPTED -> SUPERSEDED / DEPRECATED).
- **Nhánh C (Đồng bộ & Kiểm định):** Người dùng muốn quét lại ma trận và kiểm tra link.

---

### 2. Thực Thi & Tự Động Hóa (Tương ứng với nhánh)

#### Khi Tạo Mới (Nhánh A):
* Tự động dò số hiệu lớn nhất tiếp theo trong `docs/adr/`.
* Khởi tạo file `docs/adr/00XX-<slug>.md` với template chuẩn.
* Hướng dẫn người dùng hoặc tự động điền các mục: Trạng thái, Bối cảnh, Quyết định, Hệ quả.

#### Khi Cập Nhật Trạng Thái (Nhánh B):
* Mở ADR cũ cần thay thế và cập nhật trạng thái `SUPERSEDED by ADR-00XX`.
* Kiểm tra các tài liệu hoặc skills đang phụ thuộc vào ADR cũ để phát cảnh báo.

#### Khi Đồng Bộ & Kiểm Định (Nhánh C):
* Chạy lệnh biên dịch:
  ```powershell
  python scripts/sync_adr_matrix.py
  ```
* Chạy cổng kiểm định:
  ```powershell
  python scripts/validate_adr_parity.py
  ```

---

### 3. Báo Cáo Nghiệm Thu
* In ra bảng tóm tắt số lượng ADR, số liên kết sống được ghi nhận, và trạng thái $100\%$ Parity.
