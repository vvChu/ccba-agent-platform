---
request_id: req-20261005-pr1-code
from_agent: antigravity
to_agent: grok
request_type: implement
subject: 'Implement PR-1: Catalog Stale Hard Gate & ADR-0062 Documentation'
timestamp: '2026-10-05T13:51:30+07:00'
source_documents:
- scripts/tests/test_catalog_freshness_gate.py
- scripts/governance/compile_catalog.py
- scripts/spoke/sync/coordinator.py
- scripts/spoke/sync/cli.py
output_path: .md/peer_exchange/grok_code_pr1_freshness_gate.md
context: Triển khai mã nguồn cho PR-1 (Action Item 1) để bộ test TDD `scripts/tests/test_catalog_freshness_gate.py` chuyển từ ĐỎ sang XANH 100%.
---

# YÊU CẦU TRIỂN KHAI MÃ NGUỒN (TDD IMPLEMENTATION)
## PR-1: KHÓA CỨNG CATALOG STALE (HARD GATE) & BAN HÀNH ADR-0062

> **Gửi tới**: Grok (Fast Coding Worker — `grok-4.7-build-fast`)  
> **Từ**: Antigravity (Lead Architect & Orchestrator)  
> **Nhiệm vụ**: Triển khai chính xác các thay đổi cho 4 tệp mục tiêu để bộ test TDD `scripts/tests/test_catalog_freshness_gate.py` đạt **100% PASS**.

---

### 1. Hợp Đồng Kiểm Thử Bắt Buộc (Test Contract)

Antigravity đã viết sẵn bộ test TDD tại [`scripts/tests/test_catalog_freshness_gate.py`](file:///home/vvc/ccba/ccba-agent-platform/scripts/tests/test_catalog_freshness_gate.py). Bộ test yêu cầu:
1. `scripts.governance.compile_catalog` phải định nghĩa hằng số `CATALOG_RECOMPILE_COMMAND = "python scripts/governance/compile_catalog.py --write"` và hàm `check_catalog_in_sync()` phải kiểm tra cả trường `"guardrails"` trong `_BASE_FIELDS`.
2. `scripts.spoke.sync.coordinator` phải có hàm `assess_catalog_freshness(hub_root, spoke_root, dry_run=False, allow_stale_catalog=False) -> str | None`:
   - `dry_run=True`: In warning ra stderr, trả về `None` (không chặn).
   - `dry_run=False` (tức `--apply`): Nếu catalog stale và `allow_stale_catalog=False`, in thông báo lỗi kèm `CATALOG_RECOMPILE_COMMAND`, trả về `"catalog_stale"` (khiến tiến trình sync dừng với mã 1).
   - `allow_stale_catalog=True`: Bất kể stale hay exception, in log kiểm toán `[Sync] AUDIT: CATALOG_STALE_BYPASS ...` và trả về `None` (cho phép sync tiếp).
   - Xử lý Exception: Khối `except Exception` **phải kiểm tra `if allow_stale_catalog:`** trước; nếu không có cờ này và `not dry_run`, trả về `"catalog_stale"`.
3. `scripts.spoke.sync.cli` trong `build_parser()` phải hỗ trợ cờ `--allow-stale-catalog` (action="store_true", default=False) và truyền giá trị này vào `sync_project()`.

---

### 2. Các Tệp Cần Chỉnh Sửa

1. **`scripts/governance/compile_catalog.py`**:
   - Thêm hằng số `CATALOG_RECOMPILE_COMMAND = "python scripts/governance/compile_catalog.py --write"`.
   - Trong `check_catalog_in_sync()`, đảm bảo `_BASE_FIELDS` có `"guardrails"` (ví dụ: `_BASE_FIELDS = ["hub_path", "hub_repo", "notebook_ids", "bundles", "rules", "knowledge", "guardrails"]`).
2. **`scripts/spoke/sync/coordinator.py`**:
   - Thêm hàm `assess_catalog_freshness(hub_root: Path, spoke_root: Path, dry_run: bool = False, allow_stale_catalog: bool = False) -> str | None`.
   - Kết nối vào `_sync_full_bundle` (thay thế khối cảnh báo nuốt lỗi cũ ở khoảng dòng 1188): nếu `assess_catalog_freshness(...) == "catalog_stale"`, return 1 ngay lập tức.
   - Thêm tham số `allow_stale_catalog: bool = False` vào `SpokeSynchronizer.sync()` và hàm `sync_project()`.
3. **`scripts/spoke/sync/cli.py`**:
   - Thêm argument `--allow-stale-catalog` vào `build_parser()`.
   - Truyền `args.allow_stale_catalog` vào hàm `sync_project()`.
4. **`docs/adr/0062-declarative-synchronization-registry-and-auto-discovery.md`**:
   - Tạo file ADR-0062 ghi nhận kiến trúc Declarative Synchronization Registry, Fail-Closed Freshness Hard Gate, và Topo Package Discovery.

---

### 3. Định Dạng Kết Quả Trả Về

Hãy cung cấp mã nguồn hoàn chỉnh hoặc unified diff rõ ràng cho từng file để Antigravity áp dụng và chạy test.
Cung cấp khối `PeerVerdictBlock` YAML frontmatter với verdict `IMPLEMENTATION_READY`.
