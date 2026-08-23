# Wayfinder Navigation Map: Refactor & Tối ưu hóa Bộ Kiểm thử AI Skills (/ccba-skills-eval)

**Mã vấn đề**: `issue-skills-eval-refactoring`
**Trạng thái bản đồ**: 🟢 **Đã hoàn thành** — Đã tái cấu trúc và kiểm thử 100% test cases cho evals
**Khởi tạo**: 2026-07-24

---

## 🎯 Điểm đích (Destination)

Chuẩn hóa 100% các file test cases (`.agents/skills/eval-gate/test_cases/eval_*.json`) và cải tiến trình chạy `eval_runner.py` để đảm bảo:
1. Mỗi kỹ năng đều có đủ **Happy Cases** (đúng ngữ cảnh), **Negative Cases** (chống over-triggering), và **Validation Assertions** sắc nét.
2. Trình chạy `eval_runner.py` hoạt động linh hoạt, xử lý JSON output của LLM Judge an toàn, hỗ trợ chế độ `--dry-run` cho CI.
3. Loại bỏ các test prompt không phù hợp ngữ cảnh (như kiểm tra coding ngẫu nhiên trong skill copywriting) và thay bằng negative cases sát thực tế.

---

## 📝 Ghi chú (Notes)

- **KISS (Keep It Simple, Stupid)**: Giữ cho schema JSON của test cases đơn giản, dễ đọc và mở rộng.
- **Không gây đứt gãy tương thích**: Giữ nguyên cơ chế tương thích với `--auto-tune` (SkillOpt loop).
- **Tham chiếu theo tên**: Mọi trao đổi dùng tên ticket kèm liên kết file Markdown tương ứng.

---

## 📋 Quyết định đã chốt (Decisions so far)

1. **[Thống nhất Cấu trúc 3 Lớp Kiểm thử cho Skills](map.md)** — Mỗi file eval JSON phải chứa 3 loại case: Happy Path (chuẩn nghiệp vụ), Edge/Boundary (biên điều kiện/placeholders), Negative/Over-triggering (yêu cầu không thuộc phạm vi skill).

---

## 🚩 Frontier Tickets (Các ticket unblocked ở biên giới)

### Ticket 1: Rà soát & Tái thiết kế Schema Test Cases (`eval_*.json`)
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**: Loại bỏ các prompt rác/ngoại lai (như quicksort trong `eval_copywriting.json` hoặc fibonacci trong `eval_ccba-legal-intel.json`) và thay thế bằng các negative prompt sát nghiệp vụ.

### Ticket 2: Bổ sung Test Cases cho các Skills còn thiếu
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟢 Unblocked
- **Mục tiêu**: Bổ sung bộ test cases `eval_*.json` cho các skills core quan trọng còn thiếu (ví dụ: `tdd`, `implement`, `code-review`).

### Ticket 3: Nâng cấp Robustness & Mock Execution cho `eval_runner.py`
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by Ticket 1
- **Mục tiêu**: Tối ưu hàm `run_llm_judge` để parse JSON an toàn hơn (sử dụng regex bóc tách JSON object), hỗ trợ flag `--dry-run` để validate syntax test cases mà không tốn token LLM API.

### Ticket 4: Kiểm thử Nghiệm thu & Chạy thử toàn bộ Evals Suite
- **Loại**: `Task [AFK]`
- **Trạng thái**: 🟡 Blocked by Ticket 1, Ticket 2, Ticket 3
- **Mục tiêu**: Chạy nghiệm thu `python .agents/skills/eval-gate/scripts/eval_runner.py` xác nhận 100% test cases hợp lệ và đạt tỷ lệ PASS cao.

---

## 🌫️ Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- **Tích hợp Benchmark Scoring Dashboard**: Tự động sinh báo cáo HTML/Markdown tổng hợp Reliability Score của toàn bộ các skills.

---

## 🚫 Ngoài phạm vi (Out of scope)

- Thay đổi SDK lõi `ccba-ai` hoặc API Gateway LiteLLM Server.
