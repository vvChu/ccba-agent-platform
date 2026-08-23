# 🗺️ Wayfinder Map: Rào Chắn Toàn Vẹn Danh Mục Hub-Spoke (Taxonomy & Bundle Integrity Guard)

## 🎯 Điểm Đích (Destination)
Xây dựng và đưa vào vận hành hệ thống **phòng thủ tự động hóa 3 tầng** (Automated CI Gates, Centralized SSOT Taxonomy, End-to-End Archetype Test Matrix, Global Dead-Link Linter) đảm bảo 100%:
1. Mọi khai báo `applies_to` trong toàn bộ 64 Workflows và 73 Skills luôn khớp chính xác với `catalog.yaml.bundles`.
2. Các menu điều hướng toàn cục (`ccba-platform/SKILL.md`) không bao giờ chứa dead-link trỏ vào tài nguyên đã xóa.
3. Chuỗi công cụ `adopt -> bootstrap -> sync` vượt qua ma trận kiểm thử tự động trên toàn bộ 5 Archetypes và 7 Bundle Types mà không phát sinh bất kỳ runtime exception nào.
4. Đóng gói đầy đủ bài học kinh nghiệm (Patterns P7.20 & P7.21) vào `.md/knowledge/session_learnings.md`.

---

## 📝 Ghi Chú (Notes)
- **Tài liệu quy chuẩn:**
  - `docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md` (Taxonomy 5 Archetypes)
  - `docs/adr/0044-hub-spoke-shared-sdk-packaging-and-editable-linking.md` (Package Tiers)
  - `docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md` (Sandbox Lifecycle)
  - `.agents/skills/platform-loader/catalog.yaml` (SSOT Hub Bundles)
- **Tiêu chuẩn chất lượng:** Mọi test mới phải đạt 100% `pytest`, `ruff`, và `mypy` strict type checking.

---

## ⚖️ Quyết Định Đã Chốt (Decisions so far)
- [x] **[Bundle Pháp điển]** Đã đăng ký `Pháp điển: [_core, _software]` trong `catalog.yaml`.
- [x] **[Phân Tách Trách Nhiệm]** Giữ nguyên phân định: `archetype` định danh bản chất Spoke, `type` (bundle) quyết định gói kỹ năng cần phân phối.
- [x] **[Sửa Lỗi False Positive Sandbox]** Chỉ gán `is_sandbox: True` khi `sub_type == "personal_sandbox"` hoặc `guardrails.sandbox_mode is True`.
- [x] **[Đồng Bộ 5 Lệnh]** Đã cập nhật 7 tệp Workflows/Skills và 3 tệp mã nguồn Python cốt lõi.
- [x] **[T-01 Hoàn Tất] CI Gate Taxonomy & Bundles:** Xây dựng `test_taxonomy_integrity.py` quét đối soát `catalog.yaml` với 64 Workflows & 73 Skills.
- [x] **[T-02 Hoàn Tất] CI Gate Global Skills Dead-Links:** Xây dựng `test_global_skills_integrity.py` phát hiện và chặn đứng mọi dead-link trỏ vào Hub.
- [x] **[T-03 Hoàn Tất] Ma Trận Tích Hợp Lifecycle:** Xây dựng `test_archetype_lifecycle_matrix.py` kiểm thử 35/35 kịch bản (5 Archetypes x 7 Bundles) đạt 100% PASS.
- [x] **[T-04 Hoàn Tất] Đóng Gói Bài Học:** Ghi nhận Patterns P7.20, P7.21 và AP7.11 vào `session_learnings.md`.

---

## 🎫 Danh Sách Ticket Tại Biên Giới (Frontier Tickets)

- [x] **[T-01: CI Gate Kiểm Tra Toàn Vẹn Danh Mục Taxonomy & Bundles](tickets/01_taxonomy_and_bundle_ci_gate.md)** `[Task]` *(DONE)*
- [x] **[T-02: CI Gate Kiểm Tra Dead-Link Trong Global Skills](tickets/02_global_skills_deadlink_gate.md)** `[Task]` *(DONE)*
- [x] **[T-03: Ma Trận Kiểm Thử Tích Hợp Toàn Bộ Archetypes & Bundles](tickets/03_archetype_lifecycle_matrix_test.md)** `[Task]` *(DONE)*
- [x] **[T-04: Đóng Gói Bài Học Kinh Nghiệm Vào session_learnings.md](tickets/04_session_learnings_retrospective.md)** `[Task]` *(DONE)*

---

## 🏁 Trạng Thái Hoàn Thành (Destination Reached)
✅ **Bản đồ Wayfinder đã hoàn thành 100%!** Hệ thống phòng thủ tự động hóa 3 tầng đã được thiết lập, chuẩn hóa 100% applies_to trên toàn repo, tích hợp 3 bộ test gates mới và vượt qua toàn bộ 136 tests trên toàn hệ sinh thái.
