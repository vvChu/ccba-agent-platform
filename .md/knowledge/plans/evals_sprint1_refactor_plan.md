# 📋 Kế Hoạch Triển Khai Sprint 1: Khai Báo Hóa & Gia Cố Chống Chịu Lỗi Cho Module `evals`

> **Mã kế hoạch:** `PLAN-EVALS-SPRINT1`  
> **Phạm vi tác động:** `packages/ccba-harness/src/ccba_harness/evals/`  
> **Nhánh thực hiện:** `feat/evals-sprint1-declarative-and-fault-tolerant`  
> **Vai trò phối hợp:**  
> - **Lead Orchestrator & QC:** Antigravity  
> - **Execution Worker / Coder:** Grok CLI (`session: 01a0e338-3f20-7f21-a9c0-b8dba5b9f2d3`)  

---

## 🎯 Mục Tiêu Tổng Thể
Triển khai trọn vẹn 3 đề xuất cốt lõi (Đề xuất 2, 4, 3) từ đợt phân tích kiến trúc của Grok nhằm:
1. **Khai báo hóa cấu hình (Declarative Config - RULE-1.13):** Di dời gần 400 dòng mẫu prompt đột biến cứng trong `tuner.py` thành `mutation_strategies.yaml`.
2. **Quy về SSOT duy nhất (ADR-0058 & RULE-1.10):** Xóa bỏ từ điển tĩnh `SKILL_DATASET_ALIASES` trong `runner.py`, phân giải dataset $100\%$ qua `archetypes.py`.
3. **Phòng thủ chiều sâu (Fault-Tolerant):** Bọc an toàn các lượt chạy scorer trong `runner.py`, chống sập toàn bộ đợt kiểm thử khi một custom scorer gặp ngoại lệ.

---

## 📝 Danh Mục Nhiệm Vụ (Task Breakdown & Checklist)

### [x] Task 1: Khai báo hóa chiến lược đột biến prompt (`mutation_strategies.yaml`)
- **Trạng thái:** ✅ HOÀN TẤT (Commit `9acf1bb2`, 167/167 tests passed, 402 dòng code thừa đã được loại bỏ).
- **Tệp tạo mới:** `packages/ccba-harness/src/ccba_harness/evals/mutation_strategies.yaml`
- **Tệp sửa đổi:** `packages/ccba-harness/src/ccba_harness/evals/tuner.py`
- **Yêu cầu kỹ thuật:**
  - Trích xuất toàn bộ các bộ chiến lược `(name, content)` của 17 archetypes (`academic`, `bim_governance`, `bim_rase`, `bim`, `coding`, `orchestration`, `tech_qc`, `legal`, `grilling`, `adr`, `risk`, `skill_repair`, `legal_tooling`, `office`, `visual_design`, `visual`, `platform_tooling`) vào `mutation_strategies.yaml`.
  - Trong `tuner.py`: Xây dựng hàm `load_mutation_strategies() -> dict[str, list[tuple[str, str]]]` có cache Singleton `_CACHED_MUTATION_STRATEGIES`.
  - Cập nhật hàm `GitRatchetOptimizer.propose_mutation()` để đọc từ cấu hình đã nạp, thay thế toàn bộ chuỗi `if/elif` dài 400 dòng bằng lookup $O(1)$.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - `pytest packages/ccba-harness/tests/test_tuner*.py` đạt 100% PASS.
  - `propose_mutation` hoạt động chính xác tương đương trước khi refactor.

### [x] Task 2: Hợp nhất SSOT Dataset Resolution và dọn dẹp `SKILL_DATASET_ALIASES`
- **Trạng thái:** ✅ HOÀN TẤT (22/22 tests passed, gỡ bỏ 67 dòng từ điển tĩnh `SKILL_DATASET_ALIASES`, quy về SSOT qua `archetypes.py`).
- **Tệp sửa đổi:** `packages/ccba-harness/src/ccba_harness/evals/runner.py`
- **Yêu cầu kỹ thuật:**
  - Gỡ bỏ hoàn toàn từ điển hardcoded `SKILL_DATASET_ALIASES` (dòng 310–376 trong `runner.py`).
  - Trong hàm `load_eval_dataset(canonical_skill)`:
    - Sử dụng `resolve_domain_archetype(canonical_skill)` và `resolve_domain_dataset(canonical_skill)` từ `archetypes.py`.
    - Tìm kiếm tệp dataset dựa trên định danh trả về từ SSOT.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - `pytest packages/ccba-harness/tests/test_archetypes_catalog.py packages/ccba-harness/tests/test_evals_engine.py` đạt 100% PASS.
  - Không còn tồn tại biến `SKILL_DATASET_ALIASES` trong codebase.

### [ ] Task 3: Tăng cường tính chống chịu lỗi (Fault-Tolerant) cho `EvalRunner`
- **Tệp sửa đổi:** `packages/ccba-harness/src/ccba_harness/evals/runner.py`
- **Tệp kiểm thử:** `packages/ccba-harness/tests/test_evals_engine.py`
- **Yêu cầu kỹ thuật:**
  - Trong `runner.py:87-88`: Xây dựng hàm `_safe_score_item(scorer, task_output, item)` có bọc `try...except Exception as exc`.
  - Nếu scorer raise Exception: Trả về `ScoreResult(scorer_name=scorer.name, score=0.0, reasoning=f"Scorer execution failed: {type(exc).__name__}: {exc}")`.
  - Trong `asyncio.gather(*score_tasks, return_exceptions=True)`: Kiểm tra nếu phần tử trả về là Exception thì chuyển đổi thành `ScoreResult` an toàn với score `0.0`.
- **Tiêu chí nghiệm thu (Acceptance Criteria):**
  - Bổ sung 1 unit test trong `test_evals_engine.py` kiểm chứng trường hợp một Scorer bị crash (ví dụ cố tình raise `RuntimeError`) thì Runner vẫn hoàn tất với exit code an toàn và ghi nhận điểm 0 cho scorer đó.
  - Toàn bộ suite `pytest packages/ccba-harness/tests` đạt 100% PASS.

---

## 🛡️ Khóa Cứng Nghiệm Thu Toàn Trình (Hard Completion Lock)
Sau khi cả 3 Task hoàn thành:
1. `python -m ruff check packages/ccba-harness` (0 errors)
2. `python -m ruff format --check packages/ccba-harness` (0 formatting issues)
3. `python -m ccba_harness verify-patch --preset eval` (100% PASS)
4. `python -m ccba_harness verify-patch --preset code` (100% PASS)
