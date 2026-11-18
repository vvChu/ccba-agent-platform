# 🎫 WF-06: Kiểm định Liên thông 4 Cổng ADR-0058, Đồng bộ Catalog/Docs SSOT & Đóng Bản đồ Wayfinder

> **Thuộc bản đồ:** [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md)  
> **Loại ticket:** `Task [AFK]`  
> **Trạng thái:** `CLOSED` *(Hoàn tất `2026-11-18` qua Rollup PR-4 sau khi hợp nhất đủ `PR #804..#808`)*  
> **Assignee:** `Antigravity`  
> **Phụ thuộc:** Ticket chốt hạ đóng bản đồ `WAYFINDER-WORKSPACE-MASKARA-OOXML-20261118`

---

## 1. Phạm vi Nghiệm thu Toàn hệ thống

1. **Chạy đủ Bảng Xác Nhận 4 Cổng Hoàn Tất (`/ccba-codebase-design` Bước 5 & [ADR-0058](../../../../docs/adr/0058-live-collaboration-artifacts-workspace-mirroring-and-charter-alignment.md)):**
   - **Cổng 1:** `check_dependency_contracts.py` (`check_init_lazy_exports_parity` & `check_package_all_exports`) đạt `0` vi phạm trên toàn bộ `10` packages.
   - **Cổng 2:** `0` `ImportError` / regression trên toàn bộ test suite (`packages/*/tests`, `scripts/tests`, `tests/`).
   - **Cổng 3:** Bảng đối chứng số đo `[đo thực tế]` trước/sau cho cả 3 ứng viên:
     - *Ứng viên #1:* Độ trễ nạp `ccba_harness` / `ccba_legal`, hành vi `resolve_project_root()` trên Delivery Spoke không `.git`.
     - *Ứng viên #2:* Kết quả test `sk-proj-*`, `sk-ant-*`, `github_pat_*`, SĐT, CCCD 12 số với dialect parity (`maskara`/`bracket_suffix`/`bracket_prefix`) và số đo `import ccba_maskara` dùng helper nội bộ `_get_default_scanner()`.
     - *Ứng viên #3:* Số lần gọi `lxml.etree.parse()` trên `DOCXSchemaValidator` + `RedliningValidator` (&le; `16` lần trên gói 16 tệp), thời gian `validate_report()`, tỷ lệ `parser=None` (`0%`), `line_number` khác `None`, kích thước `validation/base.py` `&lt; 350 LOC` (`pptx.py` tách backlog riêng), và ZIP packing tất định.
   - **Cổng 4:** `python -m ccba_harness verify-patch --preset ci` thoát mã `0` (`ALL PASSED`).
2. **Đồng bộ 3 SSOT Writers (`RULE-1.7`) & Tri thức Hệ thống:**
   - Chạy `compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`.
   - Cập nhật `packages/*/AGENTS.md` cho các public seam mới (`resolve_workspace_and_hub_roots`, `WorkspaceHubContext`, `redact_secrets_and_pii`), cập nhật [CONTEXT.md](../../../../CONTEXT.md) nếu có khái niệm mới, gỡ `ccba_ai/client.py` (`753 LOC`) khỏi [module_budget_baseline.json](../../../../packages/ccba-harness/src/ccba_harness/module_budget_baseline.json#L1-L11) (`COND-BUDGET-CLIENT`), và đăng ký vào LLM-Wiki (`.md/knowledge/index.md` / `WikiHealthLinter` exit `0`).
3. **Đánh giá `[FOG-003]` & Đóng Bản đồ:**
   - Kiểm tra kích thước còn lại của [registry.py](../../../../packages/ccba-legal-intel/src/ccba_legal/registry.py) hậu `WF-03` để chốt xử lý hoặc chuyển giao thành ticket backlog rõ ràng.
   - Đóng ticket `WF-06` (`CLOSED`) và chuyển [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md) sang `COMPLETED`.

## 2. Tiêu chí Hoàn thành (Completion Criteria)

- [x] Tự gán `Assignee` trên ticket trước khi thực thi (`Antigravity`).
- [x] Đạt `4/4` cổng nghiệm thu trong `/ccba-codebase-design` Bước 5 và `verify-patch --preset ci` exit `0`.
- [x] Toàn bộ `3` SSOT writers (`compile_catalog.py`, `compile_skills_docs.py --write`, `sync_hub_adr_matrix.py`), `validate_docs.py` và `WikiHealthLinter` sạch lỗi.
- [x] Có bảng đối chứng số đo `[đo thực tế]` trước/sau cho cả `3` ứng viên (ghi nhận trong `map.md`) và chốt kết luận `[FOG-003]`: `ccba_legal/registry.py` còn `1,242 LOC` hậu `WF-03` là logic parser/CRUD đặc thù `LegalRegistryManager` ngoài phạm vi Workspace/Hub seam, giữ nguyên trong `module_budget_baseline.json` và tách riêng thành ticket backlog đợt sau.
- [x] Tất cả `6` ticket (`WF-01`..`WF-06`) ở trạng thái `CLOSED` và [🗺️ Bản đồ Định hướng: Làm sâu Seam Workspace/Hub, Maskara & OOXML](../map.md) chuyển trạng thái `COMPLETED`.

---
*Tạo bởi CCBA — Trung tâm Tư vấn và Ứng dụng BIM trong Xây dựng*
