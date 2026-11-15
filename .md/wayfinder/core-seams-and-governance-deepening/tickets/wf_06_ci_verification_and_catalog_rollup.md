# 🎫 WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Lõi & Hợp nhất Quản trị](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `OPEN` (Blocked by [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](wf_03_pep562_lazy_package_seams.md), [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](wf_04_unify_frontmatter_and_deepen_skill_validator.md), [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](wf_05_unify_stdlib_parameter_cleanliness_scanners.md))  
> **Assignee:** `Chưa gán`

---

## 1. Phạm vi Nghiệm thu Toàn hệ thống

1. Chạy đầy đủ **Bảng Xác nhận 4 Cổng (`ccba-codebase-design` Bước 5 / ADR-0058)**:
   - Cổng 1: `check_init_lazy_exports_parity` & `check_package_all_exports` (`0` vi phạm).
   - Cổng 2: `0` `ImportError` / regression trên toàn bộ test suite (`packages/*/tests`, `scripts/tests`, `tests/governance`).
   - Cổng 3: Benchmark subprocess `sys.modules` trước–sau `[đo thực tế]` trên `ccba_ai.routing`, `ccba_legal.models`, `ccba_harness.gpi`, `ccba_qc_core.jurisdiction`.
   - Cổng 4: `python -m ccba_harness verify-patch --preset ci` trả về exit `0`.
2. Đồng bộ `3` writers (`RULE-1.7`): `compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`, cộng cập nhật `packages/*/AGENTS.md`, `CONTEXT.md` (nếu có seam mới) và `.md/knowledge/index.md` / `log.md` (`WikiHealthLinter` exit `0`).
3. Đánh giá lại `FOG-002` (xem có cần mở đợt sau cho `ccba-pdf-prep` / `mdconverter` / `ccba-ooxml` không) và chuyển trạng thái [Bản đồ Định hướng](../map.md) sang `COMPLETED`.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [ ] Tất cả `4/4` cổng nghiệm thu và `verify-patch --preset ci` đạt exit `0`.
- [ ] Có bảng đối chứng số đo `[đo thực tế]` trước/sau cho cả `3` ứng viên.
- [ ] Tất cả các ticket ([WF-01: Phản biện & Chốt Thiết kế Chi tiết cho 3 Ứng viên Kiến trúc (PEP 562, Frontmatter Seam, Stdlib Parameter Scanner)](wf_01_grilling_architecture_design_lock.md), [WF-02: Thẩm định Kế hoạch Ngang hàng qua Peer Plan Audit (ADR-0067 One-Way Door Gate)](wf_02_peer_plan_audit_gate.md), [WF-03: Triển khai PEP 562 Lazy Package Seams, Deferred AIClient & Cô lập PyMuPDF cho 4 Package Lõi](wf_03_pep562_lazy_package_seams.md), [WF-04: Hợp nhất 9 Bộ Phân tích Frontmatter qua parse_markdown_frontmatter & Phân rã SkillValidator dưới 800 LOC](wf_04_unify_frontmatter_and_deepen_skill_validator.md), [WF-05: Chuẩn hóa Seam Quét Tham số, IP & Machine-Path Thuần Stdlib và Thu gọn check_spoke_cleanliness dưới 800 LOC](wf_05_unify_stdlib_parameter_cleanliness_scanners.md), [WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder](wf_06_ci_verification_and_catalog_rollup.md)) đóng (`CLOSED`) và [Bản đồ Định hướng](../map.md) chốt `COMPLETED`.
