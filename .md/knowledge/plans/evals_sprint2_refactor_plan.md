# 📋 Kế Hoạch Triển Khai Sprint 2: Hoàn Tất Tái Cấu Trúc Toàn Diện Module `evals`

> **Mã kế hoạch:** `PLAN-EVALS-SPRINT2`  
> **Phạm vi tác động:** `packages/ccba-harness/src/ccba_harness/evals/`  
> **Nhánh thực hiện:** `feat/evals-sprint2-dataset-fallback-scorers-mutex`  
> **Vai trò phối hợp:**  
> - **Lead Orchestrator & QC:** Antigravity  
> - **24/7 Remote Dispatcher & Watchdog:** Hermes Agent (`@dgx_hermes_vcc_bot`)  
> - **Execution Worker / Fast Coder:** Grok CLI  

---

## 🎯 Mục Tiêu Tổng Thể
Hoàn thành trọn vẹn 3 đề xuất còn lại (Đề xuất 6, 1, 5) trong bản kiến nghị 6 điểm của Grok:
1. **Phân giải Dataset 2 Tầng (ADR-0060 & Đề xuất 6):** Hỗ trợ fallback thông minh từ dataset đặc thù của skill sang dataset domain archetype chung, xóa bỏ toàn bộ kiểm tra thủ công.
2. **Module hóa gói Scorer (Đề xuất 1):** Tái cấu trúc file đơn `scorers.py` (2.550 dòng) thành package `scorers/` phân tách rõ trách nhiệm (`base`, `rule_based`, `semantic`, `code`), bảo đảm 100% re-export qua `__init__.py` (Zero-Breaking Changes).
3. **Bảo vệ Đột biến Git bằng Mutex Lock (Đề xuất 5 & RULE-2.9):** Tích hợp `FileMutexLock` với Dependency Injection và cơ chế bypass an toàn, ngăn ngừa xung đột nhánh khi chạy đa tiến trình mà không làm nghẽn test suite.

---

## 📝 Danh Mục Nhiệm Vụ (Task Breakdown & Checklist)

### [ ] Task 1: Cơ Chế Phân Giải Dataset 2 Tầng Fallback (ADR-0060)
- **Trạng thái:** ⏳ ĐANG CHỜ KÍCH HOẠT
- **Tệp sửa đổi:** 
  - `packages/ccba-harness/src/ccba_harness/evals/archetypes.py`
  - `packages/ccba-harness/src/ccba_harness/evals/runner.py`
- **Tệp kiểm thử:** `packages/ccba-harness/tests/test_archetypes_catalog.py`
- **Yêu cầu kỹ thuật:**
  - Trong `archetypes.py`: Nâng cấp hàm `resolve_domain_dataset(canonical_skill: str, root_dir: Path | None = None) -> Path`:
    - **Tầng 1 (Skill-Specific):** Kiểm tra xem có tệp dataset riêng cho skill không (ví dụ: `datasets/{canonical_skill}.jsonl` hoặc `evals/datasets/{canonical_skill}.jsonl`).
    - **Tầng 2 (Archetype-Fallback):** Nếu không có dataset riêng, tự động phân giải archetype qua `resolve_domain_archetype()` và trỏ về dataset của archetype tương ứng (ví dụ: `datasets/{archetype}.jsonl`).
    - **Exception Guard:** Nếu cả 2 đều không tồn tại, ném `FileNotFoundError` mô tả chi tiết cả 2 đường dẫn đã tìm kiếm.
  - Trong `runner.py`: Sử dụng trực tiếp `resolve_domain_dataset` đã nâng cấp.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - Bổ sung unit tests kiểm tra: (1) skill có dataset riêng, (2) skill fallback về archetype dataset, (3) skill không hợp lệ gây lỗi rõ ràng.
  - `pytest packages/ccba-harness/tests/test_archetypes_catalog.py` đạt 100% PASS.

---

### [ ] Task 2: Tái Cấu Trúc & Module Hóa `scorers.py` thành Package `scorers/`
- **Trạng thái:** ⏳ ĐANG CHỜ KÍCH HOẠT
- **Tệp tạo mới / Tái cấu trúc:**
  - `packages/ccba-harness/src/ccba_harness/evals/scorers/__init__.py`
  - `packages/ccba-harness/src/ccba_harness/evals/scorers/base.py`
  - `packages/ccba-harness/src/ccba_harness/evals/scorers/rule_based.py`
  - `packages/ccba-harness/src/ccba_harness/evals/scorers/semantic.py`
  - `packages/ccba-harness/src/ccba_harness/evals/scorers/code.py`
- **Tệp xóa bỏ:** `packages/ccba-harness/src/ccba_harness/evals/scorers.py`
- **Yêu cầu kỹ thuật:**
  - Tách tệp 2.550 dòng thành các module chuyên biệt:
    - `base.py`: Chứa `BaseScorer`, `ScoreResult`, typing interfaces và các abstract methods.
    - `rule_based.py`: Chứa `ExactMatchScorer`, `RegexScorer`, `KeywordScorer`, `FormatScorer`.
    - `semantic.py`: Chứa LLM-as-a-judge scorers, semantic similarity, rubrics scorers.
    - `code.py`: Chứa syntax scorers, AST checkers, lint-based evaluation scorers.
  - `__init__.py`: BẮT BUỘC `__all__` và re-export 100% tất cả các lớp, hàm của file cũ để đảm bảo không một import bên ngoài nào bị gãy (**Zero-Breaking Change**).
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - Tất cả các module đang import `from ccba_harness.evals.scorers import ...` đều hoạt động bình thường mà không cần sửa code.
  - `pytest packages/ccba-harness/tests/test_evals_engine.py` đạt 100% PASS.

---

### [ ] Task 3: Tích Hợp `FileMutexLock` Cho Tuner Git Mutation (RULE-2.9)
- **Trạng thái:** ⏳ ĐANG CHỜ KÍCH HOẠT
- **Tệp sửa đổi:** `packages/ccba-harness/src/ccba_harness/evals/tuner.py`
- **Tệp kiểm thử:** `packages/ccba-harness/tests/test_tuner_git_lock.py`
- **Yêu cầu kỹ thuật:**
  - Xây dựng lớp ngữ cảnh `GitMutexLock`:
    - Sử dụng cơ chế file locking (`fcntl.flock` trên POSIX) tại `.git/evals_tuner.lock`.
    - Thiết lập timeout an toàn (mặc định 30s) chống treo vô hạn.
  - **Tuân thủ nghiêm ngặt RULE-2.9 (Dependency Injection & Safe Bypass):**
    - Nhận tham số `lock_enabled: bool = True` hoặc cho phép tiêm custom lock qua constructor `GitRatchetOptimizer(..., git_lock=...)`.
    - Nếu `dry_run=True` hoặc đang trong môi trường mock testing, tự động bypass lock để loại bỏ 100% nguy cơ deadlock trong CI/test suite.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - Thêm test suite `test_tuner_git_lock.py` kiểm chứng khả năng khóa tương hỗ và tự động giải phóng lock khi exception.
  - Toàn bộ `pytest packages/ccba-harness/tests/test_tuner*.py` đạt 100% PASS.

---

## 🛡️ Khóa Cứng Nghiệm Thu Toàn Trình (Hard Completion Lock)
Sau khi cả 3 Task hoàn thành:
1. `python -m ruff check packages/ccba-harness` (0 errors)
2. `python -m ruff format --check packages/ccba-harness` (0 formatting issues)
3. `python scripts/governance/wiki_health_linter.py` (100% healthy, 0 orphan notes - tuân thủ RULE-2.15)
4. `python -m ccba_harness verify-patch --preset eval` (100% PASS)
5. `python -m ccba_harness verify-patch --preset code` (100% PASS)
