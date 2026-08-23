# Ticket 02: Quản Trị Registry TTL & Bộ Lọc Batch Sync

- **Type:** Task (AFK / Code Implementation)
- **Status:** open
- **Assignee:** Unassigned
- **Target Seam:** scripts/spoke/spoke_synchronizer.py, scripts/spoke/session_cleanup.py, scripts/sync_spoke.py
- **Reference:** ADR 0046 (Mục 2: Tiered Registry Registration & 60-Day TTL Sweep)

## Mục Tiêu
Nâng cấp hệ thống quản trị Registry của Hub để nhận diện và quản lý vòng đời Spoke cá nhân:
1. **Cờ Sandbox:** Ghi nhận thuộc tính is_sandbox: true và owner_email vào spoke_registry.yaml khi một Spoke có sub_type: personal_sandbox.
2. **Loại trừ khỏi Batch Sync:** Lệnh python scripts/sync_spoke.py --all mặc định bỏ qua các Spoke có is_sandbox: true (trừ khi có cờ --include-sandboxes).
3. **Quét Dọn TTL 60 Ngày:** Tự động phát hiện các Sandbox không có hoạt động đồng bộ trong 60 ngày, đánh dấu INACTIVE_SANDBOX và cung cấp lệnh dọn dẹp an toàn.

## Tiêu Chí Chấp Nhận (Acceptance Criteria)
- [ ] Thêm cờ --include-sandboxes vào CLI scripts/sync_spoke.py.
- [ ] Bổ sung hàm sweep_inactive_sandboxes(max_age_days=60, dry_run=False) trong scripts/spoke/session_cleanup.py.
- [ ] Viết unit test trong 	ests/test_sandbox_registry_ttl.py.
