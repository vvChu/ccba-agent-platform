# Ticket 02: Quản Trị Registry TTL & Bộ Lọc Batch Sync

- **Type:** Task (AFK / Code Implementation)
- **Status:** closed
- **Assignee:** Antigravity AI Agent
- **Target Seam:** `scripts/spoke/spoke_synchronizer.py`, `scripts/spoke/session_cleanup.py`, `scripts/sync_spoke.py`
- **Reference:** ADR 0046 (Mục 2: Tiered Registry Registration & 60-Day TTL Sweep)

## Mục Tiêu
Nâng cấp hệ thống quản trị Registry của Hub để nhận diện và quản lý vòng đời Spoke cá nhân:
1. **Cờ Sandbox:** Ghi nhận thuộc tính `is_sandbox: true` và `owner_email` vào `spoke_registry.yaml` khi một Spoke có `sub_type: personal_sandbox`.
2. **Loại trừ khỏi Batch Sync:** Lệnh `python scripts/sync_spoke.py --all` mặc định bỏ qua các Spoke có `is_sandbox: true` (trừ khi có cờ `--include-sandboxes`).
3. **Quét Dọn TTL 60 Ngày:** Tự động phát hiện các Sandbox không có hoạt động đồng bộ trong 60 ngày, đánh dấu `INACTIVE_SANDBOX` và dọn dẹp cache registry an toàn.

## Kết Quả Thực Hiện (Resolution Summary)
- [x] Nâng cấp `SpokeRegistrar.build_spoke_info()` tự động trích xuất cờ `is_sandbox` và `owner_email` từ `workspace_context.yaml`.
- [x] Nâng cấp `sync_all_spokes()` và CLI `scripts/sync_spoke.py` bổ sung cờ `--include-sandboxes` (mặc định loại trừ sandboxes để bảo vệ tài nguyên batch sync).
- [x] Xây dựng hàm `sweep_inactive_sandboxes()` trong `scripts/spoke/session_cleanup.py` quét dọn các sandbox quá 60 ngày không hoạt động.
- [x] Bộ test `tests/test_sandbox_registry_ttl.py` đạt 100% PASS (3/3 passed).\n