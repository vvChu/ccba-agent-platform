# 🗺️ Wayfinder Map: Triển Khai Toàn Bộ Vòng Đời Spoke Cá Nhân (ADR 0046)

## 🎯 Điểm Đích (Destination)
Hệ thống hoàn chỉnh hỗ trợ trọn vẹn vòng đời của Spoke Cá Nhân (`specialized_extension` / `personal_sandbox`) theo tiêu chuẩn **ADR 0046** và **Quy chế CCBA 2026**, bao gồm:
1. Động cơ thăng cấp bàn giao 3 bước (`SandboxPromoter`) tự động gỡ Watermark, chuyển giao sang Spoke Dự Án (`project_delivery`) hoặc Hub proposal, và stage thông tin nghiệm thu PGV lên IDOP `JobAssignments`.
2. Cơ chế quản trị Registry: Đánh dấu `is_sandbox: true`, loại trừ khỏi batch sync mặc định và quét dọn TTL 60 ngày.
3. Rào chắn an toàn: Tự động chèn thủy ấn `[CCBA SANDBOX DRAFT]` và khóa cứng thẩm quyền tối đa ở Cấp 1 (Technical Check).
4. Bộ công cụ dòng lệnh (CLI), Workflow `/ccba-promote-sandbox` và bộ kiểm thử tự động đạt 100% PASS.

---

## 📝 Ghi Chú (Notes)
- **Tài liệu đối soát bắt buộc:**
  - `docs/adr/0046-personal-sandbox-lifecycle-and-charter-2026-alignment.md`
  - `docs/adr/0041-hub-spoke-ecosystem-taxonomy-and-archetypes.md`
  - `docs/adr/0043-idop-active-dev-resilience-and-fallback.md`
  - `d:/idop-ccba-way/.md/governance_constitution/03_ccba_charter_2026.md` (Quy chế CCBA 2026)
- **Môi trường:** Đảm bảo `IDOP_ENV=DEV` kích hoạt chế độ Mock Sandbox khi chạy test tự động.

---

## ⚖️ Quyết Định Đã Chốt (Decisions so far)
- [x] **[ADR 0046] Cấu Trúc YAML bám sát Quy Chế 2026:** Định danh 5 Phòng chức năng + 11 Ghế giải trình trong `workspace_context.yaml`.
- [x] **[ADR 0046] Đăng Ký Phân Tầng:** Sandbox được đánh dấu `is_sandbox: true`, TTL 60 ngày không hoạt động.
- [x] **[ADR 0046] Thủy Ấn Nghiên Cứu & QC Cap:** Chèn watermark `[CCBA SANDBOX DRAFT]` và chặn xuất bản Cấp 5 trực tiếp vào `CdeDocuments`.
- [x] **[ADR 0046] Quy Trình Promotion 3 Bước:** Cleanse/Validate $\rightarrow$ Target Ingestion $\rightarrow$ PGV Sign-off Staging.
- [x] **[T-01 Hoàn Tất] Động Cơ SandboxPromoter:** Xây dựng `SandboxPromoter` và CLI `scripts/promote_sandbox.py` (4/4 test passed).
- [x] **[T-02 Hoàn Tất] Quản Trị Registry TTL & Batch Sync:** Bổ sung `is_sandbox` flag, lọc batch sync và hàm `sweep_inactive_sandboxes()` (3/3 test passed).
- [x] **[T-03 Hoàn Tất] Rào Chắn Thủy Ấn Draft & QC Level 1 Cap:** Xây dựng `SandboxAuditor` bảo đảm an toàn báo cáo nháp và khóa quyền Cấp 1 (4/4 test passed).

---

## 🎫 Danh Sách Ticket Tại Biên Giới (Frontier Tickets)
- [x] **[T-01: Thiết Kế & Hiện Thực Hóa Động Cơ SandboxPromoter](tickets/01_sandbox_promoter_engine.md)** `[Task]` *(DONE)*
- [x] **[T-02: Quản Trị Registry TTL & Bộ Lọc Batch Sync](tickets/02_registry_ttl_and_batch_sync.md)** `[Task]` *(DONE)*
- [x] **[T-03: Rào Chắn Thủy Ấn Draft & QC Level 1 Cap Guardrail](tickets/03_sandbox_watermark_guardrail.md)** `[Task]` *(DONE)*

---

## 🏁 Trạng Thái Hoàn Thành (Destination Reached)
✅ **Bản đồ Wayfinder đã hoàn thành 100%!** Toàn bộ các quyết định kiến trúc trong ADR 0046 đã được hiện thực hóa, tích hợp vào các Deep Seams, cung cấp CLI entrypoint và kiểm thử đạt 11/11 tests PASSED.\n