# Ticket 01: Thiết Kế & Hiện Thực Hóa Động Cơ SandboxPromoter

- **Type:** Task (AFK / Code Implementation)
- **Status:** closed
- **Assignee:** Antigravity AI Agent
- **Target Seam:** `scripts/spoke/sandbox_promoter.py` & `scripts/promote_sandbox.py`
- **Reference:** ADR 0046 (Mục 4: 3-Step Deliverable Promotion & PGV Handover)

## Mục Tiêu
Xây dựng Deep Seam `SandboxPromoter` điều phối toàn bộ quy trình thăng cấp bàn giao 3 bước:
1. **Pha 1 (Cleanse & Validate):** Chạy kiểm tra kỹ thuật Cấp 1, tự động gỡ bỏ thẻ thủy ấn `[CCBA SANDBOX DRAFT]` khi các điều kiện kiểm tra đạt chuẩn.
2. **Pha 2 (Target Ingestion):** Di chuyển/sao chép tệp sản phẩm sạch sang Spoke Dự Án đích (`project_delivery`) hoặc đẩy lên Hub qua `/ccba-propose-to-hub`.
3. **Pha 3 (PGV Sign-off Staging):** Tạo bản ghi dữ liệu đính kèm đường dẫn tệp sản phẩm, commit SHA và `pgv_code` lên hàng đợi `JobAssignments` trên IDOP để PM nghiệm thu.

## Kết Quả Thực Hiện (Resolution Summary)
- [x] Đã khởi tạo class `SandboxPromoter` (`scripts/spoke/sandbox_promoter.py`) với đầy đủ logic 3 pha và export tại `scripts/spoke/__init__.py`.
- [x] Đã xây dựng CLI `scripts/promote_sandbox.py` với cờ `--sandbox`, `--target`, `--files`, `--pgv`, `--dry-run`.
- [x] Bộ unit test `tests/test_sandbox_promoter.py` đạt 4/4 passed (100%).\n