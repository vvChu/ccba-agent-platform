# Walkthrough: Issue #264 — Eliminate Cleanliness Gate Contradiction, Fix Legal Corpus Misidentification, & Auto-Sync Guardrail Scripts

## 1. Tổng Quan Issue #264
- **Branch:** `fix/issue-264-spoke-sync-guardrails` $\rightarrow$ `main`
- **Tiêu đề:** `fix(spoke-sync): eliminate cleanliness gate contradiction, fix legal corpus misidentification, and auto-sync guardrail scripts (#264)`
- **Issue liên quan:** [Issue #264](https://github.com/vvChu/ccba-agent-platform/issues/264)
- **Thể chế & Kiến trúc:** ADR 0041, ADR 0044, ADR 0050, ADR 0057, ADR 0058

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #265)

- **Review ID:** `PRR_kwDOQzfV088AAAABNQeOiA`

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `3994619505` | `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py` | `pull_latest_okf_bundles()` kiểm tra `project.name` phân biệt hoa/thường (case-sensitive) so với thư mục đã chuẩn hóa `.lower()`. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa so sánh không phân biệt hoa/thường: `str(proj.get("name", "")).lower() == "ccba-legal-knowledge"`. |
| `3994619519` | `scripts/spoke/sync/sdk_inspector.py` | `copy_if_needed()` coi sự hiện diện của thư mục `scripts/` là Python Spoke, có thể copy nhầm guardrail scripts sang Spoke không phải Python. | **ĐÃ KHẮC PHỤC**: Bỏ nhánh `or (self.spoke_root / "scripts").exists()`, chỉ sử dụng `is_python_spoke(self.spoke_root, self.project_type)` vốn đã kiểm tra đầy đủ chỉ dấu Python. |
| `3994619531` | `scripts/spoke/sync/sdk_inspector.py` | So sánh `project.name` phân biệt hoa/thường (case-sensitive) trong khi các phần khác dùng `.lower()`. | **ĐÃ KHẮC PHỤC**: Chuẩn hóa so sánh không phân biệt hoa/thường: `str(proj.get("name", "")).lower() == "ccba-legal-knowledge"` trong cả `sdk_inspector.py` và `engine.py`. |
| `3994619543` | `.md/knowledge/session_learnings.md` | Dấu backticks inline-code không cân bằng tại dòng RULE-4.5. | **ĐÃ KHẮC PHỤC**: Bỏ backticks quanh địa chỉ IP `100.83.192.30:8090` để đóng mở inline-code span chuẩn xác. |

---

## 3. Các Thay Đổi Cốt Lõi

### 2.1 Loại Bỏ Contradiction Giữa `safe_pytest.py` / `safe_runner.py` và `check_spoke_cleanliness.py`
- **Vấn đề:** Khối fallback `sys.path.insert(0, str(hub_harness_src))` trong `safe_pytest.py` và `safe_runner.py` vi phạm kiểm tra regex `SYS_PATH_HACK_PATTERN` của `check_spoke_cleanliness.py`. Đồng thời `safe_runner.py` chưa nằm trong `ALLOWLIST_SCRIPTS`.
- **Giải pháp:**
  - Gỡ bỏ hoàn toàn `sys.path.insert` trong `scripts/safe_pytest.py` và `scripts/safe_runner.py`, thay bằng `ImportError` tường minh chỉ dẫn cài đặt `pip install -e <hub_path>/packages/ccba-harness` hoặc chạy `python scripts/spoke_bootstrap.py`.
  - Thêm `"safe_runner.py"` vào `ALLOWLIST_SCRIPTS` trong `scripts/spoke/check_spoke_cleanliness.py`.

### 2.2 Sửa Lỗi Nhận Diện Nhầm Master Legal Corpus
- **Vấn đề:** Trong `scripts/spoke/sync/sdk_inspector.py` và `packages/ccba-legal-intel/src/ccba_legal/sync/engine.py`, việc kiểm tra `archetype == "knowledge_corpus"` hoặc `mode == "knowledge"` đã đánh đồng mọi kho tri thức cá nhân (như VvC Second Brain) thành Master Legal Corpus (`ccba-legal-knowledge`). Hậu quả là phân loại nhầm project type thành "Pháp điển" trên Dashboard và kích hoạt `master_corpus_preserved` (bỏ qua đồng bộ pháp lý).
- **Giải pháp:**
  - Chuẩn hóa: Chỉ coi là Master Legal Corpus khi repository name là `ccba-legal-knowledge` hoặc `workspace_context.yaml` chỉ định rõ `is_master: true` (hoặc `project.name == "ccba-legal-knowledge"`).
  - Tái ánh xạ `PROJECT_TYPE_ALIASES` trong `scripts/spoke/sync/coordinator.py`: Ánh xạ `knowledge_corpus`, `knowledge-base`, `knowledge_base`, `second-brain`, `second_brain` thành `"Tác vụ Admin"`.
  - Trong `SharedSdkInspector.resolve_packages_to_check()`, chỉ tự động gợi ý `ccba-legal-intel` cho `knowledge_corpus` nếu `project_type == "Pháp điển"` hoặc tên repo là `ccba-legal-knowledge`.

### 2.3 Tự Động Đồng Bộ Guardrail Scripts Khi Chạy `sync_spoke.py --apply`
- **Vấn đề:** Trước đây, kỹ năng `ccba-update-spoke` phải yêu cầu chạy lệnh PowerShell thủ công để copy `check_hub_import_depth.py` và `check_spoke_cleanliness.py` vào Spoke.
- **Giải pháp:**
  - Nâng cấp `TestGuardrailCopier`: Tự động đồng bộ idempotent 4 tệp guardrails:
    1. `conftest.py` (tại spoke root)
    2. `scripts/safe_pytest.py`
    3. `scripts/check_hub_import_depth.py`
    4. `scripts/check_spoke_cleanliness.py`
  - So sánh hash file thông qua `are_files_identical()` và trả về danh sách chi tiết các hành động (`status: NEW | UPDATED | UNCHANGED`).
  - Tích hợp `TestGuardrailCopier.copy_if_needed(dry_run)` vào `_sync_full_bundle` trong `coordinator.py` để ghi nhận các mục này vào bảng tổng kết kết quả đồng bộ.
  - Cập nhật `.agents/skills/ccba-update-spoke/SKILL.md` chuyển bước copy thủ công thành hành động tự động 100%.

---

## 3. Kết Quả Kiểm Thử & Kiểm Toán Tất Định

### 3.1 Unit & Integration Tests (100% Pass)
| Test Suite | Lệnh | Kết Quả |
| :--- | :--- | :---: |
| Spoke Sync Modules | `python scripts/safe_pytest.py -f scripts/tests/test_spoke_sync_modules.py` | ✅ 30/30 PASSED |
| Spoke Synchronizer | `python scripts/safe_pytest.py -f scripts/tests/test_spoke_synchronizer.py` | ✅ 8/8 PASSED |
| Taxonomy Integrity | `python scripts/safe_pytest.py -f tests/governance/test_taxonomy_integrity.py` | ✅ 11 PASSED (1 skipped) |
| Legal Intel Sync | `python scripts/safe_pytest.py -f packages/ccba-legal-intel/tests/test_sync.py packages/ccba-legal-intel/tests/test_sync_spoke.py` | ✅ 8/8 PASSED |
| Session Learnings Compaction | `python scripts/safe_pytest.py -f tests/governance/test_compact_session_learnings.py` | ✅ 7/7 PASSED |

### 3.2 ADR-0058 Deterministic Hard Completion Lock
Đã vượt qua cổng kiểm toán tất định của nền tảng:
```text
# 🛡️ Deterministic Patch Verification Report: ✅ ALL PASSED
- Overall Status: PASS
- Commands Executed: 2/2 passed (python -m ruff check ., python -m pytest tests/ -q)
- Total Duration: 30120.7 ms
```
