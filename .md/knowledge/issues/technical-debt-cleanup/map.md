# 🗺️ Wayfinding Map: Xử lý Nợ Kỹ thuật Codebase (Technical Debt Cleanup)

> **Trạng thái:** COMPLETED  
> **Mã tính năng:** `technical-debt-cleanup`  
> **Ngày hoàn thành:** 2026-07-23  


---

## 🎯 1. Điểm đích (Destination)

Đưa toàn bộ 5 chốt chặn kiểm chứng chất lượng mã nguồn (**CI Eval Gates**) của nền tảng về trạng thái **PASS 100%** bằng cách triệt hạ hoàn toàn 2 khoản nợ kỹ thuật tồn đọng trong `mdconverter`:
1. Sửa dứt điểm lỗi **Pytest Timeout 10s** khi quét linter trong `packages/mdconverter/src/mdconverter/plugins/vn_legal/linter.py`.
2. Sửa toàn bộ **10 lỗi Mypy Typecheck** tại 5 file core thuộc package `mdconverter`.

---

## 📝 2. Ghi chú (Notes)

- Nạp các kỹ năng liên quan: [eval-gate](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/eval-gate/SKILL.md), [code-review](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/code-review/SKILL.md), [tdd](file:///d:/GitHubProjects/ccba-agent-platform/.agents/skills/tdd/SKILL.md).
- Tuân thủ nguyên tắc **KISS (Keep It Simple, Stupid)**: Sửa đúng điểm lỗi, không refactor lan man sang các module không liên quan.
- Sau mỗi lần sửa, kiểm tra lại bằng lệnh bọc an toàn `run_safe_eval_wrapper.py`.

---

## 📌 3. Quyết định đã chốt (Decisions so far)

1. **[Báo cáo Kiểm tra Nợ kỹ thuật Toàn diện](file:///d:/GitHubProjects/ccba-agent-platform/.md/scratch/eval_runs/diagnostics.json)**: Quét toàn bộ codebase bằng `run_harness_evals.py --all` và khoanh vùng 2 điểm lỗi chính ở `mdconverter`.

---

## 🚀 4. Danh sách các Ticket Biên Giới (Frontier Tickets)

* **[Ticket 1: Khắc phục lỗi Pytest Timeout tại `packages/mdconverter/src/mdconverter/plugins/vn_legal/linter.py`](file:///d:/GitHubProjects/ccba-agent-platform/packages/mdconverter/src/mdconverter/plugins/vn_legal/linter.py)** `[AFK/Task]`
  - *Mục tiêu:* Tối ưu hàm `lint_directory()` loại bỏ các thư mục tạm (`.md/scratch`, `.venv`, `.git`, `node_modules`) khỏi phạm vi quét file để tránh lặp đệ quy/đọc file quá 10s.
  - *Đầu ra:* `pytest packages/mdconverter/tests/` chạy qua 100% không bị Timeout.

* **[Ticket 2: Sửa 10 lỗi Mypy Typecheck trong `mdconverter`](file:///d:/GitHubProjects/ccba-agent-platform/packages/mdconverter/src/mdconverter/core/pandoc.py)** `[AFK/Task]`
  - *Mục tiêu:* Bổ sung đầy đủ Type Hints cho `core/pandoc.py`, `core/gemini.py`, `core/pipeline.py`, `core/llamaparse.py`, và `providers/gemini.py`.
  - *Đầu ra:* Lệnh `mypy` cho `mdconverter` trả về `Success: no issues found`.

* **[Ticket 3: Xác minh Toàn diện 5 CI Eval Gates](file:///d:/GitHubProjects/ccba-agent-platform/scripts/run_harness_evals.py)** `[AFK/Task]`
  - *Mục tiêu:* Kích hoạt `run_harness_evals.py --all` qua `run_safe_eval_wrapper.py` để xác nhận cả 5 Gates đều PASS.
  - *Đầu ra:* Báo cáo `diagnostics.json` trả về `status: PASS`.

---

## 🌫️ 5. Sương mù chiến trận / Chưa xác định rõ (Not yet specified)

- Mở rộng thêm quy tắc linter pháp lý đối với các định dạng tài liệu đặc thù phát sinh sau này.

---

## 🚫 6. Ngoài phạm vi (Out of scope)

- Thay đổi API interface hoặc rewrite lại toàn bộ module `mdconverter`.
- Sửa đổi các package khác vốn đang PASS 100%.
