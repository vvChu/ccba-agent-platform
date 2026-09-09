# ccba-sync-upstream — Reference Guide

> **Mục đích & Ngữ cảnh sử dụng:** Hướng dẫn kiểm tra và kéo cập nhật tính năng mới từ Hub về dự án Spoke
> **Mô tả gốc:** Kiểm tra cập nhật và thẩm tra tính năng thượng nguồn (ADR-0057 Radar) kết hợp kích hoạt 1-Click Port qua /ccba-xia.

---

# Kỹ năng: Radar Thượng Nguồn & Cầu Nối Porting (Upstream Radar & Handshake)

Kỹ năng này vận hành hệ thống Radar tự động giám sát các kho chứa thượng nguồn (được cấu hình linh hoạt tại [`.md/knowledge/upstream_sources.yaml`](../../../.md/knowledge/upstream_sources.yaml)), kiểm tra bản quyền, thẩm tra tính năng mới theo **Thể chế ADR-0057 & RES-2026-ARCH-001 v1.2 (Khung Quyết Định Phân Rã Hai Giai Đoạn)** qua AI Gateway và tự động sinh lệnh **1-Click Porting** với `/ccba-xia`.

---

## Quy trình 3 Nhịp (Process)

### Nhịp 1: Trinh sát & Radar Cập nhật (Recon & Diff Radar)
- Chạy script Python để tự động clone/fetch các kho chứa thượng nguồn về `.md/scratch/repos/` ở chế độ kiểm tra:
  ```powershell
  python scripts/spoke/check_claudekit_updates.py --check-only
  ```
- **Kiểm tra Bản quyền (License Audit):** Tự động phân loại giấy phép repo nguồn (PERMISSIVE, COPYLEFT, PROPRIETARY, UNKNOWN).
- **Tiêu chí hoàn thành:** Script chạy thành công với exit code 0. Toàn bộ kho nguồn được cập nhật, in ra danh sách thay đổi và SHA tương ứng.
- **Cơ chế tự chữa lành (Self-Healing):** Nếu gặp lỗi Git index corruption hoặc đứt kết nối mạng, Agent xóa sạch thư mục `.md/scratch/repos/<repo-name>` và tiến hành Clean Clone lại.

### Nhịp 2: Thẩm tra Thể chế ADR-0057 & RES-2026-ARCH-001 v1.2 (Constitutional Evaluation)
- Hỏi ý kiến người dùng trước khi quét sâu bằng AI: *"Tôi tìm thấy N file mới. Bạn có muốn kích hoạt AI Gateway thẩm tra theo thể chế ADR-0057 (Khung Quyết Định Hai Giai Đoạn & Radar GPI) để cập nhật báo cáo khuyến nghị không?"*
- Nếu người dùng đồng ý, chạy script thẩm tra toàn diện:
  ```powershell
  python scripts/spoke/check_claudekit_updates.py
  ```
- **Tiêu chí phân tầng của AI Gateway:**
  * **Zero-Duplicate Check:** Đối chiếu với 100 skills hiện có trong `catalog.yaml`.
  * **Khung Quyết Định Phân Rã Hai Giai Đoạn (ADR-0057):**
    - Cổng 0 (Determinism Gate): Tác vụ xác định 100% -> **Tier 1: Package Function / Deep Seam** trong `packages/*/src/`.
    - Cổng 1 (Orchestration Gate): Tác vụ đa tác tử/checkpoints/HITL -> **Tier 3: Composite Orchestrator** trong `.agents/workflows/`.
    - Giai đoạn 2 (Chỉ số GPI): $GPI < 12.0$ -> **Tier 2A: Progressive Reference** trong `references/*.md`; $GPI \ge 12.0$ -> **Tier 2B: Standalone Kernel Skill** trong `.agents/skills/ccba-<name>/`.
  * **Đánh giá tương thích:** Khả năng chuyển đổi từ TS/Node sang chuẩn Python Monorepo (`ruff`, `mypy`, `pytest`).
- **Tiêu chí hoàn thành:** Báo cáo `.md/knowledge/port_recommendations.md` được cập nhật và bảo vệ nguyên vẹn vùng ghi chú của kỹ sư (`Parse-Protection`).

### Nhịp 3: Chuyển giao Kiểm soát sang `/ccba-xia` (1-Click Port Handshake)
- Đọc nội dung cập nhật tại `port_recommendations.md` và trình bày tóm tắt cho người dùng.
- Hiển thị cú pháp gọi lệnh `/ccba-xia` tương ứng với từng kỹ năng được khuyến nghị, ví dụ:
  ```text
  /ccba-xia https://github.com/mattpocock/skills <skill-name> --compare
  ```
- Kỹ sư kích hoạt lệnh `/ccba-xia` để khởi chạy quy trình 6 Pha (đặc biệt là Hard Gate Pha 4 chống hallucination).
- **Tiêu chí hoàn thành:** Người dùng nhận được bảng khuyến nghị kèm liên kết lệnh 1-Click Porting rõ ràng.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*

*Nội dung này được tạo bởi AI Agent và cần được xem xét bởi chuyên gia pháp lý và kỹ thuật trước khi áp dụng.*
