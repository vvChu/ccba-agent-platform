# Walkthrough: Release PR #259 (Issue #255 — Package DetachedExecutionEngine in ccba-harness and Isolate Spoke Logs)

## 1. Tổng Quan Release
- **PR Number:** [#259](https://github.com/vvChu/ccba-agent-platform/pull/259)
- **Branch:** `fix/issue-255-package-detached-execution-engine` $\rightarrow$ `main`
- **Tiêu đề:** `fix(guardrails): package DetachedExecutionEngine in ccba-harness and isolate spoke test logs (#255)`
- **Issue liên quan:** [Issue #255](https://github.com/vvChu/ccba-agent-platform/issues/255)
- **Thể chế & Kiến trúc:** [ADR-0028](docs/adr/0028-deepen-detached-execution-engine.md), [ADR-0058](docs/adr/0058-automation-first-quality-framework-and-hard-completion-lock.md)
- **Mục tiêu hoàn thành:**
  - Đóng gói `DetachedExecutionEngine` thành Public Deep Seam chuẩn trong `packages/ccba-harness` (`ccba_harness.execution`), re-export tại top-level `ccba_harness`.
  - Chuẩn hóa `resolve_scratch_dir()` động tìm thư mục gốc dự án (`.git` / `pyproject.toml`) qua `Path.cwd()`, cách ly triệt để log test của Spoke về `<spoke>/.md/scratch/`, chấm dứt việc ghi đè hay phụ thuộc vào Hub.
  - Tách rời (decouple) `scripts/safe_pytest.py` và `scripts/safe_runner.py` khỏi `scripts/eval/process_safety.py` nội bộ, biến `process_safety.py` thành backward-compatibility re-export shim.
  - Bổ sung fallback `packages/ccba-harness/src` vào `sys.path` cho cả hai script CLI để hỗ trợ fresh checkout chưa cài editable install.
  - Chuẩn hóa thông điệp hướng dẫn guardrail trong `conftest.py` thành repository-agnostic placeholder (`<path/to/test_file.py>`) và bổ sung type hints đầy đủ cho pytest hooks.
  - Viết bộ unit tests toàn diện 13 test cases cho `DetachedExecutionEngine` với độ bao phủ 100%, thời gian thực thi SLA < 0.4s.

---

## 2. Giải Trình & Nghiệm Thu Các Ý Kiến Review Từ Copilot (PR #259)

Reviews: `PRR_kwDOQzfV088AAAABNInzTg`

| ID / Review | Tệp Tin | Vấn Đề Copilot Nêu | Trạng Thái & Giải Pháp Khắc Phục |
|---|---|---|---|
| `3987231464` | `scripts/safe_pytest.py` | `safe_pytest` hard-depends on an installed `ccba_harness` package. Hub fresh checkouts might fail with ImportError. | **ĐÃ KHẮC PHỤC** trong commit `47b3a70f`: Bổ sung cơ chế `try...except ImportError` fallback tự động thêm `packages/ccba-harness/src` vào `sys.path` nếu chạy trực tiếp từ Hub repo. |
| `3987231547` | `scripts/safe_runner.py` | `safe_runner` hard-depends on an installed `ccba_harness` package. Need fallback for fresh clone usage without editable install. | **ĐÃ KHẮC PHỤC** trong commit `47b3a70f`: Bổ sung cơ chế `try...except ImportError` fallback tự động thêm `packages/ccba-harness/src` vào `sys.path` nếu chạy trực tiếp từ Hub repo. |
| `3987231595` | `conftest.py` | Guardrail guidance prints `tests/test_example.py` which doesn't exist in the repo and can mislead users. | **ĐÃ KHẮC PHỤC** trong commit `47b3a70f`: Cập nhật ví dụ thành placeholder repo-agnostic `<path/to/test_file.py>` và bổ sung type hints `pytest.Parser`, `pytest.Config`, `pytest.Item` cho các pytest hooks. |

---

## 3. Chi Tiết Các Hạng Mục Đã Hoàn Thành

1. **Gói SDK Tier 0 (`ccba-harness`)**:
   - Thêm `packages/ccba-harness/src/ccba_harness/execution.py` chứa class `DetachedExecutionEngine`.
   - Re-export `DetachedExecutionEngine` trong `packages/ccba-harness/src/ccba_harness/__init__.py` và cập nhật `__all__`.
   - Cập nhật tài liệu hợp đồng trong `packages/ccba-harness/AGENTS.md`.
   - Viết 13 unit test cases tại `packages/ccba-harness/tests/test_execution.py`.
2. **Cách Ly Log Cục Bộ Cho Spoke**:
   - `resolve_scratch_dir()` quét ngược từ `Path.cwd()` tìm `.git` hoặc `pyproject.toml` để xác định project root.
   - Thư mục log `.md/scratch/` được tạo cục bộ tại project hiện hành thay vì trỏ nhầm về Hub hoặc site-packages.
3. **Decoupling CLI Scripts**:
   - Chuyển `scripts/safe_pytest.py` và `scripts/safe_runner.py` sang dùng engine từ `ccba_harness` với fallback path.
   - Chuyển `scripts/eval/process_safety.py` thành re-export shim để bảo toàn tương thích ngược cho mọi scripts cũ.
4. **Cập Nhật Thể Chế & Chỉ Số Nền Tảng**:
   - Cập nhật Evolution Note trong `docs/adr/0028-deepen-detached-execution-engine.md`.
   - Đồng bộ chỉ số `SKILL_COUNT: 68` trong `PLATFORM.md` và `README.md` qua `scripts/update_arch_stats.py`.

---

## 4. Kết Quả Kiểm Thử Toàn Diện (Pre-release Gate)

- **Isolated Stress Tests (`run_isolated_tests.py --all --stress`)**: PASS 100% tất cả packages.
- **Unit Tests `ccba-harness` (`tests/test_execution.py`)**: 13/13 passed (0.35s).
- **Harness Evals (`run_harness_evals.py`)**: PASS 100% 5/5 gates (Typecheck, Formatter, Seam Contracts, Isolated Tests, Architecture Drift).
- **GitHub Actions CI (PR #259)**: 6/6 checks PASS (Lint Markdown, Security Scan, Validate, Test Python 3.10/3.11/3.12).
