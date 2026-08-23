# 🎫 Ticket 01: CI Gate Kiểm Tra Toàn Vẹn Danh Mục Taxonomy & Bundles

## 🎯 Mục Tiêu (Goal)
Tạo tệp kiểm thử tự động `tests/governance/test_taxonomy_integrity.py` tích hợp vào hệ thống CI:
1. Đọc `bundles` từ `catalog.yaml` (7 loại: Phần mềm, Thẩm tra thiết kế, Thiết kế, Kiểm định, BIM, Tác vụ Admin, Pháp điển).
2. Quét tất cả `.agents/workflows/*.md` và `.agents/skills/**/SKILL.md`. Kiểm tra: Mọi phần tử trong `applies_to` (nếu có) PHẢI thuộc 7 bundles chuẩn.
3. Kiểm tra danh mục trong CLI `scripts/adopt_spoke.py` `--type` và `scripts/sync_spoke.py` phải khớp chính xác với `catalog.yaml`.
4. Kiểm tra `ARCHETYPE_TIER1_DEFAULTS` trong `scripts/spoke/spoke_bootstrap.py` phải chứa đúng các archetype theo ADR 0041.

## 🛠️ Yêu Cầu Kỹ Thuật
- Chạy bằng `pytest tests/governance/test_taxonomy_integrity.py`.
- Báo lỗi rõ ràng: Tên file, dòng bị lệch, giá trị không hợp lệ.
- Đạt 100% `mypy` và `ruff`.
