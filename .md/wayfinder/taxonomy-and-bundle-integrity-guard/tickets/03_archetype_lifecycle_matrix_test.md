# 🎫 Ticket 03: Ma Trận Kiểm Thử Tích Hợp Toàn Bộ Archetypes & Bundles

## 🎯 Mục Tiêu (Goal)
Tạo tệp kiểm thử tích hợp `tests/test_archetype_lifecycle_matrix.py`:
1. Parameterize qua toàn bộ 5 Archetypes: `project_delivery`, `enterprise_governance`, `knowledge_corpus`, `specialized_extension`, `platform_hub`.
2. Parameterize qua toàn bộ 7 Bundle Types: `Phần mềm`, `Thẩm tra thiết kế`, `Thiết kế`, `Kiểm định`, `BIM`, `Tác vụ Admin`, `Pháp điển`.
3. Kiểm tra chuỗi thao tác:
   - `detect_spoke_stack` nhận diện đúng default type / archetype.
   - `merge_workspace_context` tạo ra file YAML hợp lệ với đầy đủ metadata.
   - `SpokeBootstrapper(check_only=True)` nhận diện đúng gói Tier 0/Tier 1 cho archetype đó.
   - `SpokeSynchronizer(dry_run=True)` phân giải bundle thành công mà không raise `ValueError` hay missing bundle.

## 🛠️ Yêu Cầu Kỹ Thuật
- Chạy bằng `pytest tests/test_archetype_lifecycle_matrix.py`.
- Đảm bảo 0 runtime exception.
- Đạt 100% `mypy` và `ruff`.
