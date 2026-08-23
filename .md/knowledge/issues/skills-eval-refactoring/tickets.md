# Danh sách Ticket Chi Tiết: Refactor & Tối ưu hóa Bộ Kiểm thử AI Skills (/ccba-skills-eval)

**Mã bản đồ**: `issue-skills-eval-refactoring`
**Đường dẫn bản đồ**: [map.md](map.md)

---

## ✅ Ticket 1: Rà soát & Tái thiết kế Schema Test Cases (`eval_*.json`)

- **Mã Ticket**: `ticket-skills-eval-1`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `.agents/skills/eval-gate/test_cases/eval_*.json`
- **Mục tiêu**:
  - Loại bỏ các prompt không đúng ngữ cảnh (quicksort trong `eval_copywriting.json`, fibonacci trong `eval_ccba-legal-intel.json`, sick leave email trong `eval_completion-checklist.json`).
  - Thay bằng negative cases liên quan trực tiếp tới rào chắn chuyên môn (ví dụ: yêu cầu copywriting hỏi về tính toán kết cấu thép $\rightarrow$ từ chối hoặc chuyển hướng đúng skill).
  - Chuẩn hóa cấu trúc assertions (regex pattern rõ ràng, negative_regex chặn placeholders `...` và `[...]`).

---

## ✅ Ticket 2: Bổ sung Test Cases cho các Skills Core Còn Thiếu

- **Mã Ticket**: `ticket-skills-eval-2`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `.agents/skills/eval-gate/test_cases/eval_*.json`
- **Mục tiêu**:
  - Tạo các file test case JSON mới cho các skill cốt lõi: `eval_tdd.json`, `eval_implement.json`, `eval_code-review.json`.
  - Đảm bảo mỗi file có đủ Happy Path & Negative assertions.

---

## ✅ Ticket 3: Nâng cấp Robustness & Dry-Run Mode cho `eval_runner.py`

- **Mã Ticket**: `ticket-skills-eval-3`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Tệp tin tác động**: `[MODIFY] .agents/skills/eval-gate/scripts/eval_runner.py`
- **Mục tiêu**:
  - Thêm flag `--dry-run` cho `eval_runner.py` để validate cú pháp JSON và regex patterns mà không gọi API LLM.
  - Tăng cường khả năng parse JSON output từ `run_llm_judge` bằng regex `json.loads(re.search(r"\{.*\}", cleaned_res, re.DOTALL).group())`.

---

## ✅ Ticket 4: Kiểm thử Nghiệm thu & Validation Suite

- **Mã Ticket**: `ticket-skills-eval-4`
- **Loại**: `Task [AFK]`
- **Trạng thái**: ✅ Completed
- **Mục tiêu**:
  - Thử nghiệm `--dry-run` trên toàn bộ test_cases directory (12 files, 29 test cases hợp lệ 100%).
  - Chạy `python .agents/skills/eval-gate/scripts/eval_runner.py --trials 1` để xác nhận 100% test cases đều pass hợp lệ.
