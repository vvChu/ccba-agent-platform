---
proposal_id: "2026-10-25_fix-spoke-sync-linux-registry-and-hygiene"
type: "skill"
name: "fix-spoke-sync-linux-registry-and-hygiene"
status: "open"
priority: "Cao"
related_issue: "#569"
proposed_by_project: "dgx-spark-toolkit"
proposed_by_archetype: "specialized_extension"
proposed_date: "2026-10-25"
applies_to:
  - "Phần mềm"
  - "Thẩm tra thiết kế"
  - "Pháp điển"
graduated_to: ""
supersedes_spoke_docs: []
---

# RFC Proposal: Chuẩn Hóa Tra Cứu Spoke Registry Trên Linux, Chặn Ô Nhiễm Pytest Heartbeat & Đồng Bộ Đường Dẫn Guardrails (#569)

## 1. Bối cảnh & Vấn đề Thực tế (Context & Problem)
Trong quá trình thực thi `/ccba-update-spoke` trên môi trường Linux POSIX tại các Spoke (`dgx-spark-toolkit` và `ccba-legal-knowledge`), phát hiện 4 điểm nghẽn:

1. **Lỗi mở rộng đường dẫn POSIX và thiếu Fallback trong `scripts/spoke/decrypt_spoke_registry.py`:**
   - Đường dẫn thư mục khóa dùng `os.path.expanduser(r"~\.gemini\antigravity\keys")` với dấu gạch chéo ngược `\`, khiến `posixpath.expanduser` trên Linux không mở rộng `~` thành `$HOME`.
   - Khi máy trạm hoặc máy chủ không lưu tệp `.pem` giải mã và chưa có tệp giải mã tạm (`spoke_registry_decrypted.yaml`), hàm `get_registered_spokes()` trả về danh sách rỗng `[]`, làm gãy lệnh `spoke-status` và `sync_spoke.py --all`, dù `.md/telemetry/spoke_heartbeats.yaml` đã lưu đầy đủ danh sách các Spoke cục bộ đang hoạt động.
2. **Ô nhiễm dữ liệu tạm từ `pytest` vào `spoke_registry.yaml` và `spoke_heartbeats.yaml`:**
   - Khi chạy test suite cho `SpokeSynchronizer` với `hub_root` trỏ về `PLATFORM_ROOT`, `SpokeRegistrar.register()` ghi trực tiếp các đường dẫn tạm `/tmp/pytest-of-*` vào Registry và Heartbeats của Hub.
3. **Bất biến thứ tự Inode (`Filesystem Inode Ordering Invariance`) và đếm trạng thái trong `coordinator.py`:**
   - Vòng lặp `_reconcile_existing_skills()` và `_reconcile_existing_workflows()` duyệt `iterdir()` không sắp xếp, và `_print_sync_summary_report()` chưa gộp trạng thái `REMOVED` / `DEPRECATED_MIGRATED_TO_SKILL` vào bộ đếm `deprecated_count`.
4. **Đồng bộ đường dẫn `scripts/_guardrails/` trong `ccba-update-spoke/SKILL.md` và `sys.path` trong `compile_catalog.py`:**
   - Tài liệu `ccba-update-spoke/SKILL.md` cần trỏ đúng về `scripts/_guardrails/check_spoke_cleanliness.py`, và `scripts/governance/compile_catalog.py` cần đảm bảo `HUB_ROOT` luôn có mặt trong `sys.path` khi gọi từ thư mục Spoke.

## 2. Giải pháp Kỹ thuật (Solution)
- **`scripts/spoke/decrypt_spoke_registry.py`:** Dùng `Path.home()` chuẩn đa nền tảng; lọc bỏ các đường dẫn tạm `/pytest-of-` khỏi `load_spoke_heartbeats()`; bổ sung **Case 3 Fallback** trong `get_registered_spokes()` để đọc danh sách Spoke hoạt động từ `spoke_heartbeats.yaml` kèm `workspace_context.yaml`.
- **`scripts/spoke/sync/registry.py`:** Bổ sung `_is_ephemeral_test_spoke_on_real_hub()` chặn ghi các Spoke tạm của `pytest` vào `PLATFORM_ROOT` thật.
- **`scripts/spoke/sync/coordinator.py`:** Bọc `sorted(..., key=lambda p: p.name)` cho `iterdir()` và cập nhật bộ đếm `deprecated_count` / `status_map`.
- **`.agents/skills/ccba-update-spoke/SKILL.md` & `scripts/governance/compile_catalog.py`:** Cập nhật đường dẫn `scripts/_guardrails/` và nạp `HUB_ROOT` vào `sys.path`.
