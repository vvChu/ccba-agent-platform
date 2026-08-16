---
name: sync-upstream
description: Kiểm tra cập nhật và thẩm tra tính năng thượng nguồn (ADR-0040 Radar) kết hợp kích hoạt 1-Click Port qua /ccba-xia.
disable-model-invocation: true
category: utilities
keywords: [sync, upstream, update, porting, radar, xia]
metadata:
  author: CCBA
  version: "2.0.0"
---

# Kỹ năng: Radar Thượng Nguồn & Cầu Nối Porting (Upstream Radar & Handshake)

Kỹ năng này vận hành hệ thống Radar tự động giám sát các kho chứa thượng nguồn (được cấu hình linh hoạt tại [`.md/knowledge/upstream_sources.yaml`](../../../.md/knowledge/upstream_sources.yaml)), kiểm tra bản quyền, thẩm tra tính năng mới theo **Thể chế ADR-0040 (Kim tự tháp 3 Tầng)** qua AI Gateway và tự động sinh lệnh **1-Click Porting** với `/ccba-xia`.

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

### Nhịp 2: Thẩm tra Thể chế ADR-0040 (Constitutional Evaluation)
- Hỏi ý kiến người dùng trước khi quét sâu bằng AI: *"Tôi tìm thấy N file mới. Bạn có muốn kích hoạt AI Gateway thẩm tra theo thể chế ADR-0040 để cập nhật báo cáo khuyến nghị không?"*
- Nếu người dùng đồng ý, chạy script thẩm tra toàn diện:
  ```powershell
  python scripts/spoke/check_claudekit_updates.py
  ```
- **Tiêu chí phân tầng của AI Gateway:**
  * **Zero-Duplicate Check:** Đối chiếu với 77 skills hiện có trong `catalog.yaml`.
  * **Phân tầng Kim tự tháp:** Đề xuất rõ ràng: **Tier 1 (Master Deep Skill)**, **Tier 2 (Progressive Reference)** hay **Tier 3 (User Workflow)**.
  * **Đánh giá tương thích:** Khả năng chuyển đổi từ TS/Node sang chuẩn Python Monorepo (`ruff`, `mypy`, `pytest`).
- **Tiêu chí hoàn thành:** Báo cáo [port_recommendations.md](../../../.md/knowledge/port_recommendations.md) được cập nhật và bảo vệ nguyên vẹn vùng ghi chú của kỹ sư (`Parse-Protection`).

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
