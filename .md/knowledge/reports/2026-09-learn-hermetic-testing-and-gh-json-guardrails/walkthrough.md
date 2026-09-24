# Báo Cáo Nghiệm Thu Kỹ Thuật (Walkthrough): Chuẩn Hóa Kiến Trúc Buồng Kín & Rào Chắn GitHub CLI

> **Mã công việc:** `feat/learn-hermetic-testing-and-gh-json-guardrails`  
> **Tiêu chuẩn áp dụng:** ADR-0030 (Compacted Knowledge Budget $\le 10\text{ KB}$), ADR-0058 (Deterministic Hard Completion Lock), Guardrail 12 & 13.  
> **Thời điểm hoàn thành:** 2026-09-24  
> **Môi trường:** Linux Workstation (`.venv/bin/python` — Python 3.12.3)

---

## 1. CCBA Charter Governance & QC Matrix (ADR-0058)

- **Cấp độ Kiểm định (QC Level):** Level 2 (Architecture Parity & CI Gate Integrity)
- **Trạng thái cổng tất định (Hard Completion Lock):** ✅ **100% PASS (Exit Code 0)**

### Bảng Kết Quả Thực Thi Kiểm Định

| Công cụ kiểm định | Mục tiêu | Kết quả | Ghi chú |
| :--- | :--- | :---: | :--- |
| `compact_session_learnings.py --check` | Ngân sách $\le 10\text{ KB}$ & 14 Invariants | ✅ **PASS** | 9.87 KB (10,106 bytes) $\le 10.0\text{ KB}$ |
| `ruff check` | Conftest, runner, mock test | ✅ **PASS** | 0 lỗi cú pháp hoặc style |
| `verify-patch --preset doc` | `docs/rules/execution_guardrails.md` | ✅ **PASS** | Cổng kiểm tra tài liệu chuẩn mực |
| `pytest tests/governance/` | Bộ kiểm thử quản trị nền tảng | ✅ **PASS** | 213/213 passed (9.21s) |
| `run_isolated_tests.py --all --stress` | Toàn bộ 12 test targets monorepo | ✅ **PASS** | 100% test suites buồng kín, 0 test fail |
| `check_release_cleanliness.py` | Kiểm tra ô nhiễm `.md/data/` | ✅ **PASS** | 0 tệp registry bị sửa đổi bởi test suite |

---

## 2. Chi Tiết Các Thay Đổi Kiến Trúc

### 2.1. Cắt đứt rò rỉ biến môi trường máy trạm (RULE-2.9)
- **`conftest.py`:** Bổ sung autouse fixture `isolate_ccba_hub_env` để tự động gỡ bỏ `CCBA_HUB_PATH` và `HUB_PATH` khi bất kỳ bài test nào khởi chạy.
- **`scripts/eval/run_isolated_tests.py`:** Làm sạch môi trường `clean_env` trước khi khởi tạo tiến trình con `subprocess.Popen`, đảm bảo tính tương thích tuyệt đối trên mọi hệ điều hành (Linux, macOS, Windows PowerShell).

### 2.2. Khắc phục triệt để điểm ô nhiễm dữ liệu của NotebookLM
- **`packages/ccba-notebooklm/tests/test_mock_client.py`:** Bổ sung cô lập `REGISTRY_FILE` trỏ vào `tmp_path / "sources_registry.yaml"` trong fixture `clean_env`. Loại bỏ hoàn toàn việc test suite ghi đè trường `updated_at` vào `.md/data/sources_registry.yaml`.

### 2.3. Bổ sung RULE-2.9 và bảo toàn ngân sách ADR-0030
- **`.md/knowledge/session_learnings.md`:** 
  - Thêm `RULE-2.9 [Test Fixture Isolation & Hub Discovery Decoupling]`.
  - Cắt tỉa câu chữ tại `RULE-1.7`, `RULE-2.6`, `RULE-2.7`, giúp dung lượng tệp duy trì ở mức **9.87 KB** (dưới trần 10.0 KB) và bảo toàn trọn vẹn 14 `REQUIRED_INVARIANTS`.

### 2.4. Chuẩn hóa phân cấp Guardrail 12
- **`docs/rules/execution_guardrails.md`:**
  - `12.1. Safe File-Based Input Invariant for Mutations (-F / --body-file)`: Bảo vệ các lệnh ghi dữ liệu chống shell injection.
  - `12.2. Safe JSON Parameterization for Queries (gh issue/pr view)`: Bắt buộc dùng `--json` khi tra cứu để chống lỗi GraphQL Deprecation của Classic Projects.
