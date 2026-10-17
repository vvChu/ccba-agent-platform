# 0067. One-Way Door Manifest, Cumulative Escalation, and Backpressure Circuit-Breaker

* **Status:** Accepted
* **Date:** 2026-10-17
* **Deciders:** CCBA Platform Core Team & Peer Agents (Grok, Gemini)
* **Consulted:** ADR 0009 (Pstack Disciplines), ADR 0058 (Deterministic Hard Completion Lock), ADR 0061 (Seam Capability Contracts), ADR 0065 (Peer Runtime Hardening)

---

## Context & Problem Statement

Khi quy mô tự động hóa của hệ thống tác tử AI trên CCBA Platform tăng cao, năng lực thẩm định nhận thức của Kỹ sư trưởng (Taste-Holder) trở thành nút cổ chai cốt lõi (Theory of Constraints). Trước ADR này, `.github/workflows/pr-verifier.yml` chỉ phân loại nhị phân giữa `IS_TWO_WAY_DOOR` (chỉ áp dụng cho PR thuần tài liệu `.md`) và luồng kiểm duyệt thông thường dựa trên các mẫu đường dẫn bash cứng:

1. **Thiếu Làn Đường Chuẩn Mực (`Paved Road`) Cho Mã Nguồn Cô Lập:**
   Các thay đổi mã nguồn nhỏ ($\le 200$ LOC), không chạm vào Schema, Public Deep Seam hay Hiến pháp nền tảng vẫn chịu chung ma sát chờ đợi với các thay đổi kiến trúc trọng yếu.
2. **Rủi Ro Lách Luật Bằng Chia Nhỏ Liên Tiếp (`Salami Slicing` / Cumulative Drift):**
   Nếu mở làn `Paved Road` đơn thuần theo ngưỡng dòng code ($\le 200$ LOC), các tác tử AI có thể chia một thay đổi kiến trúc lớn thành chuỗi $K \ge 3$ PR nhỏ liên tiếp trên cùng một package để lách cổng ký duyệt của Taste-Holder.
3. **Nguy Cơ Quá Tải Hàng Đợi & Suy Thoái Nhận Thức (`Cognitive Backpressure`):**
   Khi hàng đợi chờ duyệt vượt quá 5 PRs hoặc tồn đọng trên 24 giờ, việc tiếp tục sinh thêm PR tự động mới từ backlog gây bão thông báo (Slop Cannon) và làm giảm chất lượng thẩm định.
4. **Mô Tả Rủi Ro Văn Xuôi Thiếu Trọng Tâm:**
   Mục `## Merge Danger Assessment` trong PR template trước đây cho phép điền văn xuôi tự do, thiếu cấu trúc bắt buộc chỉ rõ bất biến cốt lõi và đoạn diff trọng tâm ($\le 30$ dòng).

---

## Decision Outcome

Ban hành kiến trúc kiểm soát 3 tầng (`TWO_WAY_DOOR`, `PAVED_ROAD`, `ONE_WAY_DOOR`) kết hợp cơ chế Leo thang Tích lũy và Phanh hãm Áp lực ngược trong `ccba_harness`:

### 1. Danh Mục Cửa Một Chiều Khai Báo (`One-Way Door Manifest` — 7 Nhóm Bắt Buộc)
Tách toàn bộ cấu hình thành từ điển khai báo `ONE_WAY_DOOR_MANIFEST` (`ccba_harness.door_policy`) gồm 7 nhóm thay đổi bắt buộc phải có chữ ký duyệt của Taste-Holder:
1. **`SCHEMA_MIGRATION`**: Thay đổi JSON/YAML Schema SSOT, cấu trúc cơ sở dữ liệu, Milvus/Neo4j collections.
2. **`AUTHZ_SECURITY`**: Quy tắc phân quyền ACL, RBAC/ROLE_ID, bộ lọc `ccba-maskara`, xử lý khóa mật mã và thông tin xác thực.
3. **`CROSS_SPOKE_CONTRACT`**: Hợp đồng giao diện liên Spoke (`seam-contracts.yaml`, `catalog_base.yaml`, `sync_spoke.py`, `adopt_spoke.py`).
4. **`PUBLIC_API_SEAM`**: Thay đổi danh sách xuất công khai `__all__` trong `packages/*/src/*/__init__.py`, `packages/*/AGENTS.md`, và giao diện CLI công khai.
5. **`PII_FINANCE_QUOTA`**: Cấu hình bảng giá AI Gateway, nhật ký chi tiêu (`SpendLogs`), hạn ngạch PGV/PCell.
6. **`DEPENDENCY_LICENSE`**: Thêm hoặc nâng cấp thư viện bên thứ ba trong `pyproject.toml`, `uv.lock`, `requirements*.txt`.
7. **`HUB_CONSTITUTION`**: Hiến pháp nền tảng (`*AGENTS.md`), hồ sơ quyết định kiến trúc (`docs/adr/*`), quy tắc vận hành (`docs/rules/*`), và quy trình CI (`.github/workflows/*`).

Các thay đổi mã nguồn nằm ngoài 7 nhóm trên, có tổng diff logic $\le 200$ LOC và vượt qua 100% `verify-patch` được xếp vào tầng **`PAVED_ROAD`**.

### 2. Thuật Toán Leo Thang Tích Lũy (`Cumulative Escalation` — $K \ge 3$ trong 72h)
Để chống hiện tượng Salami Slicing mà không phạt nhầm thói quen tạo nhiều atomic commits trong cùng một nhánh PR:
- Hệ thống tính chuỗi **$K \ge 3$ PRs/merges liên tiếp trên nhánh đích (`main`) trong cửa sổ trượt 72 giờ** chạm vào cùng một `canonical_module` (`packages/<pkg_name>`) trên `PAVED_ROAD` mà chưa có xác nhận trực tiếp của Taste-Holder.
- Khi chạm ngưỡng $K \ge 3$, PR hiện hành tự động được nâng cấp lên **`ONE_WAY_DOOR`**.
- Hỗ trợ trích xuất lịch sử trực tiếp từ `git log` cục bộ (`load_recent_merges_from_git`) đảm bảo vận hành 100% offline và tương thích với fork CI.

### 3. Cơ Chế Phanh Hãm Áp Lực Ngược (`Backpressure Circuit-Breaker` & Anti-Deadlock Bypass)
Hàm `evaluate_backpressure_queue` (`ccba_harness.backpressure`) giám sát hàng đợi các thẻ `ONE_WAY_DOOR` đang chờ duyệt:
- **Ngưỡng ngắt mạch:** Tự động kích hoạt `is_tripped = True` khi `pending_count > 5` hoặc `oldest_age_hours > 24.0`, tạm dừng việc nhận thêm tác vụ tự động mới từ backlog.
- **Điều khoản chống Deadlock (`bypass_active = True`):** Luôn cho phép các bản cập nhật/sửa lỗi trên các PR đang mở sẵn trong hàng đợi (`is_existing_pr_update=True`) và các nhánh vá lỗi khẩn cấp (`is_hotfix=True`) đi qua để giải phóng hàng đợi.

### 4. Chuẩn Hóa `Tradeoff Card` & Hậu Kiểm Ngẫu Nhiên Tất Định 10% (`Deterministic Sample Audit`)
- **Tradeoff Card (`validate_tradeoff_card`):** Mọi PR thuộc diện `ONE_WAY_DOOR` bắt buộc khai báo đủ 3 trường: `Core Invariant`, `Invalidation Condition`, và `Git Hunk Reference` (liên kết dòng `#L<start>-L<end>` hoặc khối diff $\le 30$ dòng).
- **10% Deterministic Sample Audit (`is_sampled_for_audit`):** Sử dụng hàm băm tất định `int(sha256(f"{repo}:{pr_number}").hexdigest(), 16) % 10 == 0` để chọn đúng 10% PR trên `PAVED_ROAD` đưa vào diện hậu kiểm định kỳ, bảo toàn tính bất biến (idempotency) khi chạy lại GitHub Actions.

---

## Consequences

### Positive
- **High-Throughput Paved Road:** Các thay đổi mã nguồn chuẩn mực $\le 200$ LOC đi qua đường ống kiểm định tự động nhanh chóng mà không làm nghẽn hàng đợi của Taste-Holder.
- **Zero Salami-Slicing Drift:** Chuỗi thay đổi tích lũy $K \ge 3$ trên cùng một package tự động được khóa lại để kiểm tra kiến trúc tổng thể.
- **30-Second Review Ergonomics:** Cấu trúc `Tradeoff Card` buộc người tạo PR chỉ rõ đoạn code trọng tâm $\le 30$ dòng và điều kiện bác bỏ thiết kế.

### Negative
- **Template Discipline:** Các PR chạm vào `ONE_WAY_DOOR` (như sửa `AGENTS.md`, `__init__.py`, hoặc `pyproject.toml`) bắt buộc phải điền đầy đủ 3 mục của `Tradeoff Card` thay vì để trống.
