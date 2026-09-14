# 🏆 Walkthrough: Gia Cố Spoke Sync Hygiene, Guardrails Distributor & Safe Pytest Scope Lock (Issue #274)

> **Mã Issue:** [#274](https://github.com/vvChu/ccba-agent-platform/issues/274)  
> **Nhánh thực thi:** `fix/issue-274-harden-spoke-sync-and-guardrails`  
> **Trạng thái:** ✅ **HOÀN THÀNH — VƯỢT QUA 100% CỔNG KIỂM ĐỊNH TẤT ĐỊNH (ADR-0058)**  
> **Proposal File:** [`.agents/proposals/2026-09-14_harden-spoke-sync-and-guardrails.md`](file:///d:/GitHubProjects/ccba-agent-platform/.agents/proposals/2026-09-14_harden-spoke-sync-and-guardrails.md)

---

## 1. Tóm Tắt Các Thay Đổi Đã Thực Hiện

### 🛡️ 1.1 Khóa Scope Chặt Chẽ Cho `safe_pytest` & Xử Lý Git Rename
- **Tệp sửa đổi:** [`packages/ccba-harness/src/ccba_harness/execution.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/execution.py)
  - Thêm `encoding="utf-8", errors="replace"` cho lệnh `git status --porcelain`.
  - Xử lý chuỗi file khi bị đổi tên trong git status (`R old -> new`) qua `filepath.split(" -> ")[-1].strip()`.
  - Nâng cấp `run_safe_pytest()`: cho phép `target_file` nhận cả dạng đơn `str` hoặc danh sách `list[str]`.
  - Phân tách chính xác giữa option flags của Pytest (như `--tb short`, `-k test_foo`) và đường dẫn tệp thực tế (`Path(arg).exists()`).
  - **Khóa cứng Scope:** Khi `not targets` và `not allow_unscoped`: in thông báo chỉ dẫn và `return 0` ngay lập tức, ngăn ngừa hoàn toàn việc chạy unscoped 400+ tests (~105.9s).
  - Tự động phát hiện động `default_paths` khi bật `--allow-unscoped` cho toàn bộ các packages trong Monorepo.

### 🚀 1.2 Nâng Cấp Wrapper CLI `safe_pytest.py`
- **Tệp sửa đổi:** [`scripts/safe_pytest.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/safe_pytest.py)
  - Cập nhật cờ `-f / --file` thành `nargs="+"`, cho phép truyền danh sách nhiều tệp kiểm thử cùng lúc:
    ```bash
    python scripts/safe_pytest.py -f file1.py file2.py file3.py
    ```

### 🧹 1.3 Gia Cố Spoke Git Hygiene (Chống Dirty Working Tree)
- **Tệp sửa đổi:**
  - [`scripts/spoke/spoke_bootstrap.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/spoke_bootstrap.py):
    - Bổ sung `.md/data/telemetry_summary.json` và `.md/data/*.json` vào rules của `ensure_gitignore_rule()`.
    - Di chuyển lời gọi `ensure_gitignore_rule()` lên trước rào chắn `is_python_project()`, bảo đảm tất cả Spoke (kể cả phi-Python) đều được bảo vệ sạch git.
  - [`scripts/spoke/sync/coordinator.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/coordinator.py):
    - Tự động gọi `SpokeBootstrapper(spoke_root, hub_root).ensure_gitignore_rule()` ngay trước khi ghi tệp `.md/data/telemetry_summary.json`.

### 📦 1.4 Phân Phối Guardrail `safe_runner.py`
- **Tệp sửa đổi:** [`scripts/spoke/sync/sdk_inspector.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/sdk_inspector.py)
  - Bổ sung `safe_runner.py` vào danh sách phân phối `items_to_copy` của `TestGuardrailCopier`.

### 🔤 1.5 Chuẩn Hóa Windows Subprocess UTF-8 (RULE-2.5)
- Thêm `encoding="utf-8", errors="replace"` cho toàn bộ 14 vị trí subprocess `text=True` trong:
  - [`packages/ccba-harness/src/ccba_harness/_guard.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/_guard.py)
  - [`packages/ccba-harness/src/ccba_harness/orchestrator.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/orchestrator.py)
  - [`packages/ccba-harness/src/ccba_harness/evals/tuner.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/ccba-harness/src/ccba_harness/evals/tuner.py)
  - [`scripts/spoke/sync/backup.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/backup.py)
  - [`scripts/spoke/sync/coordinator.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/sync/coordinator.py)
  - [`scripts/spoke/spoke_bootstrap.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/spoke_bootstrap.py)
  - [`scripts/spoke/upstream_evaluator.py`](file:///d:/GitHubProjects/ccba-agent-platform/scripts/spoke/upstream_evaluator.py)

---

## 2. Kết Quả Kiểm Thử & Nghiệm Thu (Verification Results)

### 2.1 Bộ Scoped Tests & Unit Tests Mới
| Module Kiểm Thử | Lệnh Thực Thi | Kết Quả |
| :--- | :--- | :---: |
| **Execution Engine** (Rename, Multi-files, Scope Lock) | `python -m pytest packages/ccba-harness/tests/test_execution.py -v` | ✅ **17/17 PASSED (0.47s)** |
| **Safe Pytest Wrapper** (Multi-file -f) | `python -m pytest scripts/tests/test_safe_pytest.py -v` | ✅ **3/3 PASSED (0.05s)** |
| **Spoke Synchronizer** (Guardrails Copier) | `python -m pytest scripts/tests/test_spoke_synchronizer.py -v` | ✅ **8/8 PASSED (0.22s)** |
| **Spoke Sync Modules** (Full Suite) | `python -m pytest scripts/tests/test_spoke_sync_modules.py -v` | ✅ **34/34 PASSED (2.95s)** |
| **Spoke SDK Detector & Gitignore** | `python -m pytest tests/test_spoke_sdk_detector.py -v` | ✅ **7/7 PASSED (0.56s)** |

### 2.2 Khóa Hoàn Tất Tất Định (ADR-0058 Hard Completion Lock)
Chạy lệnh: `python -m ccba_harness verify-patch --preset ci`
- **Ruff Check:** ✅ PASS (166.2ms)
- **Harness & Governance Tests:** ✅ PASS (32439.5ms)
- **Skills Validation & GPI Enforcement:** ✅ PASS (2899.1ms)
- **Compile Catalog:** ✅ PASS (460.3ms)
- **Sync Hub ADR Matrix:** ✅ PASS (336.9ms)
- **Tổng kết:** **5/5 Gates PASSED, exit code 0.**

---

## 3. Hướng Dẫn Kỹ Thuật Đồng Bộ Cho Spoke (`ccba-legal-knowledge`)

Khi hợp nhất nhánh lên `main`, Spoke `ccba-legal-knowledge` sẽ:
1. Chạy `/ccba-update-spoke` để tự động nhận `scripts/safe_runner.py` và cập nhật `.gitignore`.
2. Đối với Gate 10 của Spoke (`validate_legal_spoke.py`): Điều chỉnh để chạy chế độ non-mutating `--check` trong pre-commit hook (chỉ so khớp diff của 3 tệp: `README.md`, `TRACEABILITY_MATRIX.md`, `expansion_roadmap.md`), chỉ cập nhật đĩa khi gọi với cờ `--fix`.
