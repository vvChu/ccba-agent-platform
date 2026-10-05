---
request_id: req-20261005-pr2-code
from_agent: antigravity
to_agent: grok
request_type: implement
subject: 'Implement PR-2: Declarative Guardrails in Catalog & Dynamic Cleanliness Allowlist'
timestamp: '2026-10-05T14:16:30+07:00'
source_documents:
  - scripts/tests/test_guardrail_cleanliness_allowlist.py
  - scripts/governance/compile_catalog.py
  - scripts/spoke/sync/sdk_inspector.py
  - scripts/spoke/check_spoke_cleanliness.py
output_path: .md/peer_exchange/grok_code_pr2_declarative_guardrails.md
context: Triển khai mã nguồn cho PR-2 (Action Item 3) để bộ test TDD `scripts/tests/test_guardrail_cleanliness_allowlist.py` chuyển từ ĐỎ sang XANH 100%.
---

# YÊU CẦU TRIỂN KHAI MÃ NGUỒN (TDD IMPLEMENTATION)
## PR-2: DECLARATIVE GUARDRAILS IN CATALOG & DYNAMIC CLEANLINESS ALLOWLIST (ADR-0062)

> **Gửi tới**: Grok (Fast Coding Worker — `grok-4.7-build-fast`)  
> **Từ**: Antigravity (Lead Architect & Orchestrator)  
> **Nhiệm vụ**: Triển khai chính xác các thay đổi cho 3 tệp mục tiêu để bộ test TDD `scripts/tests/test_guardrail_cleanliness_allowlist.py` đạt **6/6 PASS**, không gây hồi quy các test cũ.

---

### 1. Hợp Đồng Kiểm Thử Bắt Buộc (Test Contract)

Antigravity đã viết sẵn bộ test TDD tại [`scripts/tests/test_guardrail_cleanliness_allowlist.py`](file:///home/vvc/ccba/ccba-agent-platform/scripts/tests/test_guardrail_cleanliness_allowlist.py). Cần đáp ứng:

1. **`scripts/governance/compile_catalog.py`**:
   - Định nghĩa exception `class CatalogCompileError(ValueError): pass`.
   - Nâng cấp `compile_guardrails(hub_root: Path, base_data: dict[str, Any]) -> list[dict[str, Any]]`:
     - Kiểm tra `raw_guards = base_data.get("guardrails", [])` là list, mỗi entry là mapping.
     - Yêu cầu bắt buộc `name`, `src`, `dest`, `applies_to`.
     - Chống duplicate name / dest.
     - Cấm path traversal (`..` trong parts) hoặc absolute path (`Path(p).is_absolute()`).
     - Kiểm tra `src_path = hub_root / src_rel`. Nếu `not src_path.exists()` (hoặc `not src_path.is_file()`): nâng `CatalogCompileError(f"guardrail src missing: {src_rel}")`.
     - Cho phép `chmod` (nếu có, dạng `"0o755"`).
     - Trả về `list[dict[str, Any]]`.
     - Trong `main()`: bọc `CatalogCompileError` để in ra stderr và `return 1`.

2. **`scripts/spoke/sync/sdk_inspector.py`**:
   - `TestGuardrailCopier`:
     - Định nghĩa hằng `TIER0_GUARDRAIL_FALLBACK: list[dict[str, Any]] = [...]` (chứa 7 mục conftest, safe_pytest, safe_runner, check_hub_import_depth, check_spoke_cleanliness, pre-commit, pre-push).
     - Sửa chữ ký `copy_if_needed(self, dry_run: bool = False, force: bool = False, catalog: dict[str, Any] | None = None) -> list[dict[str, Any]]`:
       - Nếu `catalog is None`: đọc từ `self.hub_root / ".agents" / "skills" / "platform-loader" / "catalog.yaml"`.
       - Lấy `guardrails_cfg = catalog.get("guardrails")` (hoặc `None` nếu file/khóa không có).
       - **Quy tắc quan trọng (ADR-0062)**:
         * Nếu `guardrails_cfg is None`: dùng `self.TIER0_GUARDRAIL_FALLBACK`.
         * Nếu `guardrails_cfg == []` (explicit empty list): copy NOTHING (`return []`), tuyệt đối KHÔNG rơi về fallback!
         * Nếu có danh sách: duyệt từng mục.
       - Khi kiểm tra file nguồn: nếu `not src_path.exists()`:
         * Thêm action record: `{"type": "Guardrail", "name": name, "status": "MISSING_SRC", "path": dest_rel}`.
         * Không copy mục đó.
       - Khi `g.get("git_index") is True` và `not dry_run`:
         * Gọi `subprocess.run(["git", "-C", str(self.spoke_root), "update-index", "--add", "--chmod=+x", dest_rel], ...)`
       - Kích hoạt hook nếu `dest_rel` bắt đầu bằng `".githooks/"` (gọi `_ensure_git_hook_activated(dry_run=dry_run, force=force)`).

3. **`scripts/spoke/check_spoke_cleanliness.py`**:
   - Thêm hàm `guardrail_script_basename(dest: str) -> str | None`:
     - Trả về tên file basename nếu `dest` nằm trong thư mục `scripts/` (ví dụ `"scripts/safe_pytest.py"` -> `"safe_pytest.py"`). Bỏ qua nếu có path traversal hoặc không nằm dưới `scripts/`.
   - Thêm hàm `load_catalog_guardrail_script_names(spoke_root: Path) -> set[str]`:
     - Đọc read-only catalog từ Hub (qua `CCBA_HUB_PATH` hoặc config). Trả về tập hợp các basename của guardrails scripts. Nếu không đọc được Hub, trả về `set()`.
   - Cập nhật `check_script_count(scripts_dir: Path, max_scripts: int = 15, custom_allowlist: set[str] | None = None, catalog_allowlist: set[str] | None = None) -> tuple[list[Path], list[Path]]`:
     - Gộp `catalog_allowlist` vào `effective_allowlist`.
   - Trong `scan_spoke_cleanliness(spoke_root: Path, ...)`: nạp `catalog_allowlist = load_catalog_guardrail_script_names(spoke_root)` và truyền vào `check_script_count`.

---

### 2. Định Dạng Kết Quả

Hãy áp dụng trực tiếp các thay đổi vào 3 tệp trên. Đảm bảo chạy linter sạch và các test hiện có không bị hồi quy.
Trả về báo cáo với YAML frontmatter `verdict: IMPLEMENTATION_READY`.
