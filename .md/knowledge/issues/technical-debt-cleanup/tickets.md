# Danh sách Tickets: Technical Debt Cleanup (`technical-debt-cleanup`)

👉 **Nguyên tắc:** Thực hiện lần lượt từng ticket ở **Biên giới (Frontier)**. Sau mỗi ticket, chạy lại test/check để đảm bảo không gãy tính năng cũ.

---

## Ticket 1: Khắc phục lỗi Pytest Timeout tại `packages/mdconverter/src/mdconverter/plugins/vn_legal/linter.py`

**Nghiệp vụ cần làm:**  
Tối ưu hàm `lint_directory()` trong plugin `vn_legal/linter.py` của package `mdconverter`. Bổ sung bộ lọc danh sách đen (blacklist directories: `.venv`, `.git`, `.md`, `node_modules`, `build`, `dist`) để ngăn việc đọc quét hàng loạt file Markdown rác dẫn đến timeout 10s khi chạy test suite.

**Bị chặn bởi:** Không có.

- [x] Thêm `EXCLUDED_DIRS = {".venv", ".git", ".md", "node_modules", "build", "dist", "__pycache__"}` vào `linter.py`.
- [x] Cập nhật `lint_directory()` để bỏ qua các thư mục trong `EXCLUDED_DIRS`.
- [x] Chạy kiểm thử `.venv\Scripts\python.exe -m pytest packages/mdconverter/tests/` qua `run_safe_eval_wrapper.py` và xác nhận PASS 100% không bị timeout.

---

## Ticket 2: Sửa 10 lỗi Mypy Typecheck trong package `mdconverter`

**Nghiệp vụ cần làm:**  
Sửa dứt điểm 10 lỗi type annotations do Mypy báo tại 5 file core của `mdconverter`.

**Bị chặn bởi:** Ticket 1.

- [x] Sửa lỗi subclassing `BaseConverter` & `no-any-return` tại `packages/mdconverter/src/mdconverter/core/pandoc.py`.
- [x] Sửa lỗi `no-any-return` tại `packages/mdconverter/src/mdconverter/core/pipeline.py`.
- [x] Sửa lỗi subclassing `BaseConverter` & `no-any-return` tại `packages/mdconverter/src/mdconverter/core/gemini.py`.
- [x] Sửa lỗi subclassing `LLMProvider` tại `packages/mdconverter/src/mdconverter/providers/gemini.py`.
- [x] Sửa lỗi subclassing `BaseConverter` & `no-any-return` tại `packages/mdconverter/src/mdconverter/core/llamaparse.py`.
- [x] Chạy `.venv\Scripts\python.exe -m mypy packages/mdconverter/src` và xác nhận không còn lỗi.

---

## Ticket 3: Kiểm chứng Toàn diện 5 CI Eval Gates

**Nghiệp vụ cần làm:**  
Khởi chạy toàn bộ hệ thống CI Gates trên nền tảng qua `scripts/run_harness_evals.py --all`.

**Bị chặn bởi:** Ticket 1 & Ticket 2.

- [x] Chạy `.venv\Scripts\python.exe scripts/run_safe_eval_wrapper.py --cmd ".venv\Scripts\python.exe scripts/run_harness_evals.py --all"`.
- [x] Xác nhận cả 5 Gates đều báo `✅ PASS` trong `diagnostics.json`.

